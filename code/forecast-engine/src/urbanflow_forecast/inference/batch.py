from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pymysql

from urbanflow_forecast.analysis import analyze_forecasts
from urbanflow_forecast.data import load_feature_dataset
from urbanflow_forecast.inference.model_selection import select_model
from urbanflow_forecast.training.windowed import FEATURE_COLUMNS


INTERVAL = pd.Timedelta(minutes=30)
ONE_DAY = pd.Timedelta(hours=24)


@dataclass(frozen=True)
class BatchPredictionConfig:
    features_path: Path | str
    observations_path: Path | str
    output_dir: Path | str
    baseline_metrics_path: Path | str
    tcn_metrics_path: Path | str | None = None
    horizon: int = 48
    prediction_lag: int = 48
    minimum_improvement: float = 0.05
    write_mysql: bool = False
    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "urbanflow")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "urbanflow_dev")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "urbanflow")


def run_batch_prediction(
    config: BatchPredictionConfig,
) -> dict[str, Any]:
    """Generate future forecasts, persist them, and analyze the output."""

    selection = select_model(
        config.baseline_metrics_path,
        config.tcn_metrics_path,
        config.minimum_improvement,
    )
    output_path = Path(config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if selection["selected_model"] == "seasonal_naive":
        observations = load_virtual_observations(config.observations_path)
        forecasts = build_seasonal_future_forecasts(
            observations,
            horizon=config.horizon,
            prediction_lag=config.prediction_lag,
        )
        forecasts["model_version"] = selection["model_version"]
    elif selection["selected_model"] == "tcn":
        features = load_feature_dataset(config.features_path)
        forecasts = _build_tcn_future_forecasts(
            features,
            model_path=Path(config.tcn_metrics_path).parent / "model.pt",
            horizon=config.horizon,
        )
        forecasts["model_version"] = selection["model_version"]
    else:
        raise ValueError(f"unsupported selected model: {selection['selected_model']}")

    forecasts = forecasts.sort_values(
        ["station_id", "horizon_step"]
    ).reset_index(drop=True)
    forecasts.to_parquet(
        output_path / "forecast_results.parquet",
        index=False,
    )
    forecasts.to_csv(
        output_path / "forecast_results.csv",
        index=False,
    )

    analysis_summary = analyze_forecasts(forecasts, output_path)
    run_id = None
    if config.write_mysql:
        run_id = _write_forecasts_to_mysql(
            forecasts,
            config,
            selection,
        )
        analysis_summary["forecast_run_id"] = run_id

    manifest = {
        "model_selection": selection,
        "analysis": analysis_summary,
        "forecast_start": forecasts["target_time"].min().isoformat(),
        "forecast_end": forecasts["target_time"].max().isoformat(),
        "rows": int(len(forecasts)),
        "output_files": [
            "forecast_results.parquet",
            "forecast_results.csv",
            "station_forecast_ranking.csv",
            "forecast_timeline.csv",
            "analysis_summary.json",
            "station_ranking.png",
            "forecast_timeline.png",
        ],
    }
    (output_path / "batch_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_virtual_observations(path: Path | str) -> pd.DataFrame:
    """Load complete generated observations for future inference."""

    frame = pd.read_csv(path)
    frame["event_timestamp"] = pd.to_datetime(
        frame["event_time"],
        errors="raise",
    )
    return frame.sort_values(
        ["station_id", "event_timestamp"]
    ).reset_index(drop=True)


def build_seasonal_future_forecasts(
    features: pd.DataFrame,
    horizon: int = 48,
    prediction_lag: int = 48,
) -> pd.DataFrame:
    """Forecast beyond the last observed timestamp using Seasonal Naive."""

    rows: list[dict[str, Any]] = []
    for station_id, station_frame in features.groupby(
        "station_id",
        sort=True,
        observed=True,
    ):
        ordered = station_frame.sort_values("event_timestamp")
        demand_by_time = dict(
            zip(
                ordered["event_timestamp"],
                ordered["demand_count"].astype(float),
            )
        )
        last_row = ordered.iloc[-1]
        origin_time = pd.Timestamp(last_row["event_timestamp"])
        city_id = str(last_row["city_id"])

        for step in range(1, horizon + 1):
            target_time = origin_time + INTERVAL * step
            history_time = target_time - INTERVAL * prediction_lag
            if history_time not in demand_by_time:
                continue

            rows.append(
                {
                    "city_id": city_id,
                    "station_id": station_id,
                    "forecast_origin": origin_time,
                    "target_time": target_time,
                    "horizon_step": step,
                    "predicted_demand": float(demand_by_time[history_time]),
                }
            )

    return pd.DataFrame(rows)


def _build_tcn_future_forecasts(
    features: pd.DataFrame,
    model_path: Path,
    horizon: int,
) -> pd.DataFrame:
    import torch

    from urbanflow_forecast.models import TCNRegressor
    from urbanflow_forecast.training.windowed import FeatureStandardizer

    payload = torch.load(model_path, map_location="cpu")
    model_config = payload["config"]
    standardizer_data = payload["standardizer"]
    standardizer = FeatureStandardizer(
        means=np.asarray(standardizer_data["means"], dtype=np.float32),
        standard_deviations=np.asarray(
            standardizer_data["standard_deviations"],
            dtype=np.float32,
        ),
        demand_mean=float(standardizer_data["demand_mean"]),
        demand_std=float(standardizer_data["demand_std"]),
    )
    model = TCNRegressor(
        input_size=len(FEATURE_COLUMNS),
        output_size=horizon,
        channels=tuple(model_config["channels"]),
        kernel_size=model_config["kernel_size"],
        dropout=model_config["dropout"],
        use_seasonal_residual=model_config["use_seasonal_residual"],
        seasonal_lag=model_config["horizon"],
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()

    rows: list[dict[str, Any]] = []
    input_length = int(model_config["input_length"])
    for station_id, station_frame in features.groupby(
        "station_id",
        sort=True,
        observed=True,
    ):
        ordered = station_frame.sort_values("event_timestamp")
        if len(ordered) < input_length:
            continue
        window = ordered.tail(input_length)
        input_values = standardizer.transform_features(
            window[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
        )
        with torch.no_grad():
            prediction_scaled = model(
                torch.from_numpy(input_values).unsqueeze(0)
            ).numpy()[0]
        predictions = standardizer.inverse_demand(prediction_scaled)

        origin_time = pd.Timestamp(window.iloc[-1]["event_timestamp"])
        city_id = str(window.iloc[-1]["city_id"])
        for step, predicted_demand in enumerate(predictions, start=1):
            rows.append(
                {
                    "city_id": city_id,
                    "station_id": station_id,
                    "forecast_origin": origin_time,
                    "target_time": origin_time + INTERVAL * step,
                    "horizon_step": step,
                    "predicted_demand": max(0.0, float(predicted_demand)),
                }
            )

    return pd.DataFrame(rows)


def _write_forecasts_to_mysql(
    forecasts: pd.DataFrame,
    config: BatchPredictionConfig,
    selection: dict[str, Any],
) -> int:
    connection = pymysql.connect(
        host=config.mysql_host,
        port=config.mysql_port,
        user=config.mysql_user,
        password=config.mysql_password,
        database=config.mysql_database,
        charset="utf8mb4",
        autocommit=False,
    )

    try:
        with connection.cursor() as cursor:
            data_cutoff = pd.Timestamp(
                forecasts["forecast_origin"].min()
            ).to_pydatetime()
            forecast_start = pd.Timestamp(
                forecasts["target_time"].min()
            ).to_pydatetime()
            city_id = str(forecasts.iloc[0]["city_id"])

            cursor.execute(
                """INSERT INTO forecast_run
                   (city_id, model_version, feature_version, data_cutoff,
                    forecast_start, horizon_steps, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (
                    city_id,
                    selection["model_version"],
                    "feature-v1",
                    data_cutoff,
                    forecast_start,
                    int(forecasts["horizon_step"].max()),
                    "success",
                ),
            )
            run_id = int(cursor.lastrowid)

            cursor.executemany(
                """INSERT INTO forecast_result
                   (forecast_run_id, city_id, station_id, target_time,
                    horizon_step, predicted_demand)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                     predicted_demand = VALUES(predicted_demand)""",
                [
                    (
                        run_id,
                        row.city_id,
                        row.station_id,
                        pd.Timestamp(row.target_time).to_pydatetime(),
                        int(row.horizon_step),
                        float(row.predicted_demand),
                    )
                    for row in forecasts.itertuples(index=False)
                ],
            )
        connection.commit()
        return run_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

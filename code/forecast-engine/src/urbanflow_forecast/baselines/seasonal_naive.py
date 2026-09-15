from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from urbanflow_forecast.data import load_feature_dataset
from urbanflow_forecast.evaluation import (
    calculate_metrics,
    evaluate_predictions,
    plot_seasonal_naive_results,
)


INTERVAL = pd.Timedelta(minutes=30)
ONE_DAY = pd.Timedelta(hours=24)


def add_seasonal_naive_prediction(
    frame: pd.DataFrame,
    prediction_lag: int = 48,
) -> pd.DataFrame:
    """Predict each target from the target observed one seasonal cycle earlier."""

    if prediction_lag < 1:
        raise ValueError("prediction_lag must be positive")

    result = frame.copy()
    result = result.sort_values(["station_id", "event_timestamp"])
    result["seasonal_naive_prediction"] = result.groupby(
        "station_id",
        sort=False,
    )["target_next_30m"].shift(prediction_lag)

    result["absolute_error"] = (
        result["target_next_30m"] - result["seasonal_naive_prediction"]
    ).abs()

    return result.dropna(
        subset=["target_next_30m", "seasonal_naive_prediction"]
    ).reset_index(drop=True)


def run_seasonal_naive_baseline(
    features_path: Path | str,
    output_dir: Path | str,
    prediction_lag: int = 48,
) -> dict[str, Any]:
    """Run the Seasonal Naive baseline and persist predictions and metrics."""

    features = load_feature_dataset(features_path)
    predictions = add_seasonal_naive_prediction(
        features,
        prediction_lag=prediction_lag,
    )

    one_step_metrics, metrics_by_station = evaluate_predictions(predictions)
    multi_step_predictions = pd.concat(
        [
            build_multi_step_seasonal_naive(
                features,
                split="validation",
                horizon=48,
                prediction_lag=prediction_lag,
            ),
            build_multi_step_seasonal_naive(
                features,
                split="test",
                horizon=48,
                prediction_lag=prediction_lag,
            ),
        ],
        ignore_index=True,
    )
    multi_step_metrics = _evaluate_multi_step(multi_step_predictions)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    prediction_columns = [
        "split",
        "event_timestamp",
        "station_id",
        "demand_count",
        "target_next_30m",
        "seasonal_naive_prediction",
        "absolute_error",
    ]
    prediction_output = predictions[prediction_columns].sort_values(
        ["split", "station_id", "event_timestamp"]
    )
    prediction_output.to_parquet(
        output_path / "predictions.parquet",
        index=False,
    )
    prediction_output.to_csv(
        output_path / "predictions.csv",
        index=False,
    )
    multi_step_predictions.to_parquet(
        output_path / "predictions_48step.parquet",
        index=False,
    )
    multi_step_predictions.to_csv(
        output_path / "predictions_48step.csv",
        index=False,
    )

    metrics_output = {
        "model": "seasonal_naive",
        "prediction_lag": prediction_lag,
        "features_path": str(Path(features_path)),
        "one_step": one_step_metrics,
        "multi_step": multi_step_metrics,
    }
    (output_path / "metrics.json").write_text(
        json.dumps(metrics_output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    metrics_rows = []
    for split, values in one_step_metrics["by_split"].items():
        metrics_rows.append({"split": split, **values})
    pd.DataFrame(metrics_rows).to_csv(
        output_path / "metrics_by_split.csv",
        index=False,
    )
    metrics_by_station.to_csv(
        output_path / "metrics_by_station.csv",
        index=False,
    )
    horizon_rows = []
    for split, split_metrics in multi_step_metrics["by_split"].items():
        for horizon, values in split_metrics["by_horizon"].items():
            horizon_rows.append(
                {
                    "split": split,
                    "horizon_step": horizon,
                    **values,
                }
            )
    pd.DataFrame(horizon_rows).to_csv(
        output_path / "metrics_by_horizon.csv",
        index=False,
    )
    plot_seasonal_naive_results(
        one_step_predictions=prediction_output,
        multi_step_metrics=multi_step_metrics,
        output_dir=output_path,
    )

    return metrics_output


def build_multi_step_seasonal_naive(
    frame: pd.DataFrame,
    split: str = "test",
    horizon: int = 48,
    prediction_lag: int = 48,
) -> pd.DataFrame:
    """Forecast future horizons from each origin in the selected split."""

    if horizon < 1:
        raise ValueError("horizon must be positive")
    if prediction_lag < horizon:
        raise ValueError("prediction_lag must be at least the forecast horizon")

    required = {"station_id", "event_timestamp", "demand_count", "split"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"multi-step input is missing columns: {missing}")

    rows: list[dict[str, Any]] = []
    for station_id, station_frame in frame.groupby(
        "station_id",
        sort=True,
        observed=True,
    ):
        ordered = station_frame.sort_values("event_timestamp")
        demands = dict(
            zip(
                ordered["event_timestamp"],
                ordered["demand_count"].astype(float),
            )
        )
        origins = ordered[ordered["split"] == split]

        for origin in origins.itertuples(index=False):
            origin_time = origin.event_timestamp
            for step in range(1, horizon + 1):
                target_time = origin_time + INTERVAL * step
                history_time = target_time - INTERVAL * prediction_lag
                if target_time not in demands or history_time not in demands:
                    continue

                actual = demands[target_time]
                predicted = demands[history_time]
                rows.append(
                    {
                        "split": split,
                        "origin_timestamp": origin_time,
                        "target_timestamp": target_time,
                        "station_id": station_id,
                        "horizon_step": step,
                        "target_next_30m": actual,
                        "seasonal_naive_prediction": predicted,
                        "absolute_error": abs(actual - predicted),
                    }
                )

    return pd.DataFrame(rows)


def _evaluate_multi_step(predictions: pd.DataFrame) -> dict[str, Any]:
    overall = calculate_metrics(
        predictions["target_next_30m"],
        predictions["seasonal_naive_prediction"],
    )
    def horizon_metrics(frame: pd.DataFrame) -> dict[int, dict[str, Any]]:
        return {
            int(horizon): calculate_metrics(
                horizon_frame["target_next_30m"],
                horizon_frame["seasonal_naive_prediction"],
            )
            for horizon, horizon_frame in frame.groupby(
                "horizon_step",
                sort=True,
                observed=True,
            )
        }

    by_split = {}
    for split, frame in predictions.groupby(
        "split",
        sort=True,
        observed=True,
    ):
        by_split[str(split)] = {
            "overall": calculate_metrics(
                frame["target_next_30m"],
                frame["seasonal_naive_prediction"],
            ),
            "by_horizon": horizon_metrics(frame),
        }

    return {
        "overall": overall,
        "by_horizon": horizon_metrics(predictions),
        "by_split": by_split,
    }

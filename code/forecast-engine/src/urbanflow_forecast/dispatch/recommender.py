from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pymysql

from urbanflow_forecast.locales import dispatch_reason


@dataclass(frozen=True)
class DispatchConfig:
    output_dir: Path | str = Path("data/dispatch-v1")
    decision_horizon: int = 4
    safety_stock_ratio: float = 0.10
    language: str = os.getenv("URBANFLOW_LANGUAGE", "en")
    write_mysql: bool = False
    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "urbanflow")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "urbanflow_dev")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "urbanflow")


def run_dispatch_recommendations(
    config: DispatchConfig,
) -> dict[str, Any]:
    """Build, persist, and summarize dispatch recommendations."""

    connection = pymysql.connect(
        host=config.mysql_host,
        port=config.mysql_port,
        user=config.mysql_user,
        password=config.mysql_password,
        database=config.mysql_database,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT forecast_run_id
                   FROM forecast_run
                   WHERE status = 'success'
                   ORDER BY forecast_run_id DESC
                   LIMIT 1"""
            )
            run = cursor.fetchone()
            if run is None:
                raise RuntimeError("no successful forecast run is available")
            run_id = int(run["forecast_run_id"])

            cursor.execute(
                """SELECT f.station_id, f.target_time, f.horizon_step,
                          f.predicted_demand
                   FROM forecast_result f
                   WHERE f.forecast_run_id = %s
                     AND f.horizon_step <= %s
                   ORDER BY f.station_id, f.horizon_step""",
                (run_id, config.decision_horizon),
            )
            forecasts = pd.DataFrame(cursor.fetchall())

            cursor.execute(
                """SELECT i.city_id, i.station_id, d.station_name,
                          i.snapshot_time, i.capacity, i.available_bikes,
                          i.available_docks, i.station_status,
                          d.latitude, d.longitude
                   FROM station_inventory_snapshot i
                   JOIN station_dim d ON i.station_id = d.station_id
                   WHERE i.snapshot_time = (
                       SELECT MAX(snapshot_time)
                       FROM station_inventory_snapshot
                   )
                   ORDER BY i.station_id"""
            )
            stations = pd.DataFrame(cursor.fetchall())
    finally:
        connection.close()

    recommendations, summary = build_dispatch_plan(
        stations=stations,
        forecasts=forecasts,
        decision_horizon=config.decision_horizon,
        safety_stock_ratio=config.safety_stock_ratio,
        language=config.language,
    )
    recommendations["forecast_run_id"] = run_id

    output_path = Path(config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    recommendations.to_csv(
        output_path / "dispatch_recommendations.csv",
        index=False,
    )
    recommendations.to_parquet(
        output_path / "dispatch_recommendations.parquet",
        index=False,
    )
    summary["forecast_run_id"] = run_id
    (output_path / "dispatch_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if config.write_mysql:
        _write_recommendations(recommendations, run_id, config)

    return summary


def build_dispatch_plan(
    stations: pd.DataFrame,
    forecasts: pd.DataFrame,
    decision_horizon: int = 4,
    safety_stock_ratio: float = 0.10,
    language: str = "en",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Match station deficits to nearby surplus stations."""

    if decision_horizon < 1:
        raise ValueError("decision_horizon must be positive")
    if safety_stock_ratio < 0:
        raise ValueError("safety_stock_ratio cannot be negative")

    forecasts = forecasts.copy()
    forecasts["predicted_demand"] = pd.to_numeric(
        forecasts["predicted_demand"],
        errors="raise",
    ).astype(float)

    stations = stations.copy()
    for column in ("capacity", "available_bikes", "available_docks"):
        stations[column] = pd.to_numeric(
            stations[column],
            errors="raise",
        ).astype(int)
    for column in ("latitude", "longitude"):
        stations[column] = pd.to_numeric(
            stations[column],
            errors="raise",
        ).astype(float)

    forecast_window = forecasts[
        forecasts["horizon_step"] <= decision_horizon
    ].copy()
    demand = (
        forecast_window.groupby("station_id", observed=True)
        .agg(
            near_term_demand=("predicted_demand", "sum"),
            peak_demand=("predicted_demand", "max"),
            first_target_time=("target_time", "min"),
        )
        .reset_index()
    )
    station_state = stations.merge(
        demand,
        on="station_id",
        how="left",
        validate="one_to_one",
    ).fillna({"near_term_demand": 0.0, "peak_demand": 0.0})
    station_state["safety_stock"] = np.maximum(
        2,
        np.ceil(station_state["near_term_demand"] * safety_stock_ratio),
    ).astype(int)
    station_state["target_bikes"] = (
        station_state["near_term_demand"].round().astype(int)
        + station_state["safety_stock"]
    )
    station_state["balance"] = (
        station_state["available_bikes"] - station_state["target_bikes"]
    )

    deficits = station_state[station_state["balance"] < 0].copy()
    surpluses = station_state[station_state["balance"] > 0].copy()
    deficits["remaining"] = -deficits["balance"]
    surpluses["remaining"] = surpluses["balance"]
    deficits["priority_score"] = (
        deficits["remaining"]
        + deficits["peak_demand"] * 0.25
        + (deficits["available_bikes"] <= 2).astype(int) * 2
    )
    deficits = deficits.sort_values("priority_score", ascending=False)
    if "snapshot_time" in stations.columns:
        recommendation_time = pd.to_datetime(
            stations["snapshot_time"],
            errors="raise",
        ).max()
    else:
        recommendation_time = pd.Timestamp.now().floor("min")

    recommendations: list[dict[str, Any]] = []
    for deficit in deficits.itertuples(index=False):
        remaining = int(deficit.remaining)
        while remaining > 0:
            candidates = surpluses[surpluses["remaining"] > 0].copy()
            if candidates.empty:
                break
            candidates["distance_km"] = candidates.apply(
                lambda row: _haversine_km(
                    float(deficit.latitude),
                    float(deficit.longitude),
                    float(row["latitude"]),
                    float(row["longitude"]),
                ),
                axis=1,
            )
            source = candidates.sort_values("distance_km").iloc[0]
            quantity = min(remaining, int(source["remaining"]))

            recommendations.append(
                {
                    "recommendation_time": recommendation_time,
                    "dispatch_deadline": pd.Timestamp(
                        deficit.first_target_time
                    ),
                    "from_station_id": str(source["station_id"]),
                    "from_station_name": str(source["station_name"]),
                    "to_station_id": str(deficit.station_id),
                    "to_station_name": str(deficit.station_name),
                    "recommended_quantity": quantity,
                    "distance_km": round(float(source["distance_km"]), 3),
                    "priority_score": round(float(deficit.priority_score), 4),
                    "shortage_before": int(deficit.remaining),
                    "shortage_after": int(remaining - quantity),
                    "current_available_bikes": int(deficit.available_bikes),
                    "near_term_demand": round(float(deficit.near_term_demand), 2),
                    "safety_stock": int(deficit.safety_stock),
                    "target_bikes": int(deficit.target_bikes),
                    "reason": _dispatch_reason(
                        language=language,
                        horizon_minutes=decision_horizon * 30,
                        near_term_demand=float(deficit.near_term_demand),
                        available_bikes=int(deficit.available_bikes),
                        target_bikes=int(deficit.target_bikes),
                    ),
                    "status": "pending",
                }
            )
            remaining -= quantity
            surpluses.loc[
                surpluses["station_id"] == source["station_id"],
                "remaining",
            ] -= quantity

    recommendation_frame = pd.DataFrame(recommendations)
    total_shortage_before = int(deficits["remaining"].sum())
    total_quantity = (
        int(recommendation_frame["recommended_quantity"].sum())
        if not recommendation_frame.empty
        else 0
    )
    total_shortage_after = max(0, total_shortage_before - total_quantity)
    reduction = (
        (total_shortage_before - total_shortage_after)
        / total_shortage_before
        * 100.0
        if total_shortage_before
        else 0.0
    )

    summary = {
        "station_count": int(len(station_state)),
        "deficit_station_count": int(len(deficits)),
        "surplus_station_count": int(len(surpluses)),
        "decision_horizon_steps": decision_horizon,
        "decision_horizon_minutes": decision_horizon * 30,
        "total_shortage_before": total_shortage_before,
        "recommendation_count": int(len(recommendation_frame)),
        "total_quantity_recommended": total_quantity,
        "total_shortage_after": total_shortage_after,
        "shortage_reduction_pct": round(reduction, 2),
    }
    return recommendation_frame, summary


def _haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    radius = 6371.0
    lat_a = math.radians(latitude_a)
    lat_b = math.radians(latitude_b)
    delta_lat = math.radians(latitude_b - latitude_a)
    delta_lon = math.radians(longitude_b - longitude_a)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def _dispatch_reason(
    *,
    language: str,
    horizon_minutes: int,
    near_term_demand: float,
    available_bikes: int,
    target_bikes: int,
) -> str:
    return dispatch_reason(
        language,
        horizon_minutes=horizon_minutes,
        near_term_demand=near_term_demand,
        available_bikes=available_bikes,
        target_bikes=target_bikes,
    )


def _write_recommendations(
    recommendations: pd.DataFrame,
    run_id: int,
    config: DispatchConfig,
) -> None:
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
            cursor.execute(
                "DELETE FROM dispatch_recommendation WHERE forecast_run_id = %s",
                (run_id,),
            )
            if not recommendations.empty:
                cursor.executemany(
                    """INSERT INTO dispatch_recommendation
                       (forecast_run_id, recommendation_time, dispatch_deadline,
                        from_station_id, to_station_id, recommended_quantity,
                        distance_km, priority_score, shortage_before,
                        shortage_after, near_term_demand, safety_stock,
                        target_bikes, reason, status)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                               %s, %s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE
                         recommended_quantity = VALUES(recommended_quantity),
                         distance_km = VALUES(distance_km),
                         priority_score = VALUES(priority_score),
                         shortage_before = VALUES(shortage_before),
                         shortage_after = VALUES(shortage_after),
                         near_term_demand = VALUES(near_term_demand),
                         safety_stock = VALUES(safety_stock),
                         target_bikes = VALUES(target_bikes),
                         reason = VALUES(reason)""",
                    [
                        (
                            run_id,
                            pd.Timestamp(row.recommendation_time).to_pydatetime(),
                            pd.Timestamp(row.dispatch_deadline).to_pydatetime(),
                            row.from_station_id,
                            row.to_station_id,
                            int(row.recommended_quantity),
                            float(row.distance_km),
                            float(row.priority_score),
                            int(row.shortage_before),
                            int(row.shortage_after),
                            float(row.near_term_demand),
                            int(row.safety_stock),
                            int(row.target_bikes),
                            row.reason,
                            row.status,
                        )
                        for row in recommendations.itertuples(index=False)
                    ],
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

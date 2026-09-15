from __future__ import annotations

from datetime import datetime

from app import __version__
from app.config import HEALTH_MAX_FORECAST_AGE_HOURS
from app.db import query_one


def get_health() -> dict:
    """Return API, database, and data-readiness health."""

    try:
        query_one("SELECT 1 AS ok")
    except Exception as exc:  # pragma: no cover - depends on live database
        return {
            "status": "unavailable",
            "version": __version__,
            "database": {
                "status": "unavailable",
                "error_type": type(exc).__name__,
            },
            "data": {"status": "unknown"},
        }

    latest_forecast = query_one(
        """SELECT forecast_run_id, data_cutoff, forecast_start, generated_at
           FROM forecast_run
           WHERE status = 'success'
           ORDER BY forecast_run_id DESC
           LIMIT 1"""
    )
    latest_inventory = query_one(
        """SELECT MAX(snapshot_time) AS snapshot_time
           FROM station_inventory_snapshot"""
    )
    latest_dispatch = query_one(
        """SELECT MAX(forecast_run_id) AS forecast_run_id,
                  MAX(created_at) AS generated_at
           FROM dispatch_recommendation"""
    )

    forecast_run_id = (
        int(latest_forecast["forecast_run_id"])
        if latest_forecast
        else None
    )
    dispatch_run_id = (
        int(latest_dispatch["forecast_run_id"])
        if latest_dispatch and latest_dispatch["forecast_run_id"] is not None
        else None
    )
    inventory_time = (
        latest_inventory["snapshot_time"] if latest_inventory else None
    )
    inventory_time_value = (
        inventory_time.isoformat()
        if hasattr(inventory_time, "isoformat")
        else inventory_time
    )
    forecast_age_hours = None
    if latest_forecast and latest_forecast["generated_at"]:
        forecast_age_hours = round(
            (
                datetime.now()
                - latest_forecast["generated_at"]
            ).total_seconds()
            / 3600,
            2,
        )

    if latest_forecast is None:
        data_status = "missing_forecast"
    elif (
        forecast_age_hours is not None
        and forecast_age_hours > HEALTH_MAX_FORECAST_AGE_HOURS
    ):
        data_status = "stale_forecast"
    elif inventory_time is None:
        data_status = "missing_inventory"
    elif dispatch_run_id is None:
        data_status = "missing_dispatch"
    elif dispatch_run_id != forecast_run_id:
        data_status = (
            "updating"
            if forecast_age_hours is not None
            and forecast_age_hours <= 5 / 60
            else "stale_dispatch"
        )
    else:
        data_status = "ready"

    return {
        "status": (
            "ok"
            if data_status in {"ready", "updating"}
            else "degraded"
        ),
        "version": __version__,
        "database": {"status": "ok"},
        "data": {
            "status": data_status,
            "forecast_run_id": forecast_run_id,
            "dispatch_forecast_run_id": dispatch_run_id,
            "inventory_snapshot_time": inventory_time_value,
            "forecast_age_hours": forecast_age_hours,
            "max_forecast_age_hours": HEALTH_MAX_FORECAST_AGE_HOURS,
        },
    }

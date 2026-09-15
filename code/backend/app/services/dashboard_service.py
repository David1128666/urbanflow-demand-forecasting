from datetime import datetime

from app.db import query, query_one
from app.locales import translate
from app.services.dispatch_service import get_dispatch_summary
from app.services.inventory_service import get_inventory_summary


def get_dashboard_summary() -> dict:
    stations = query_one("SELECT COUNT(*) AS count FROM station_dim")["count"]
    observations = query_one(
        "SELECT COUNT(*) AS count FROM demand_observation"
    )["count"]
    latest_run = query_one(
        """SELECT forecast_run_id, model_version, data_cutoff,
                  forecast_start, horizon_steps, generated_at
           FROM forecast_run
           WHERE status = 'success'
           ORDER BY forecast_run_id DESC
           LIMIT 1"""
    )

    forecast_summary = None
    top_stations: list[dict] = []
    peak_periods: list[dict] = []

    if latest_run:
        run_id = latest_run["forecast_run_id"]
        forecast_summary = query_one(
            """SELECT COUNT(*) AS rows_count,
                      COUNT(DISTINCT station_id) AS station_count,
                      SUM(predicted_demand) AS total_demand,
                      MIN(predicted_demand) AS min_demand,
                      MAX(predicted_demand) AS max_demand
               FROM forecast_result
               WHERE forecast_run_id = %s""",
            (run_id,),
        )
        top_stations = query(
            """SELECT f.station_id, s.station_name,
                      ROUND(SUM(f.predicted_demand), 2) AS total_demand,
                      ROUND(AVG(f.predicted_demand), 2) AS mean_demand,
                      ROUND(MAX(f.predicted_demand), 2) AS peak_demand,
                      COALESCE(d.suggested_bikes, 0) AS suggested_bikes,
                      COALESCE(d.shortage_before, 0) AS short_term_shortage,
                      COALESCE(i.available_bikes, 0) AS available_bikes
               FROM forecast_result f
               JOIN station_dim s ON f.station_id = s.station_id
               LEFT JOIN (
                   SELECT to_station_id,
                          SUM(recommended_quantity) AS suggested_bikes,
                          MAX(shortage_before) AS shortage_before
                   FROM dispatch_recommendation
                   WHERE forecast_run_id = %s
                   GROUP BY to_station_id
               ) d ON f.station_id = d.to_station_id
               LEFT JOIN station_inventory_snapshot i
                 ON f.station_id = i.station_id
                AND i.snapshot_time = (
                    SELECT MAX(snapshot_time)
                    FROM station_inventory_snapshot
                )
               WHERE f.forecast_run_id = %s
               GROUP BY f.station_id, s.station_name, d.suggested_bikes,
                        d.shortage_before, i.available_bikes
               ORDER BY total_demand DESC
               LIMIT 10""",
            (run_id, run_id),
        )
        peak_periods = query(
            """SELECT target_time AS window_start,
                      DATE_ADD(target_time, INTERVAL 30 MINUTE) AS window_end,
                      ROUND(SUM(predicted_demand), 2) AS aggregate_demand
               FROM forecast_result
               WHERE forecast_run_id = %s
               GROUP BY target_time
               ORDER BY aggregate_demand DESC
               LIMIT 5""",
            (run_id,),
        )

    dispatch_summary = get_dispatch_summary()
    latest_inventory_time = query_one(
        """SELECT MAX(snapshot_time) AS snapshot_time
           FROM station_inventory_snapshot"""
    )
    forecast_run_id = (
        latest_run["forecast_run_id"] if latest_run else None
    )
    dispatch_run_id = dispatch_summary.get("forecast_run_id")
    inventory_time = (
        latest_inventory_time["snapshot_time"]
        if latest_inventory_time
        else None
    )
    if latest_run is None:
        consistency_status = "missing_forecast"
    elif inventory_time is None:
        consistency_status = "missing_inventory"
    elif dispatch_run_id is None:
        consistency_status = "missing_dispatch"
    elif dispatch_run_id != forecast_run_id:
        generated_at = latest_run.get("generated_at") if latest_run else None
        forecast_age_minutes = (
            (datetime.now() - generated_at).total_seconds() / 60
            if generated_at is not None
            else None
        )
        consistency_status = (
            "updating"
            if forecast_age_minutes is not None
            and 0 <= forecast_age_minutes <= 5
            else "stale_dispatch"
        )
    else:
        consistency_status = "ready"

    return {
        "station_count": stations,
        "observation_count": observations,
        "inventory_summary": get_inventory_summary(),
        "dispatch_summary": dispatch_summary,
        "latest_run": latest_run,
        "forecast_summary": forecast_summary,
        "top_stations": top_stations,
        "peak_periods": peak_periods,
        "data_mode": "virtual",
        "data_mode_label": translate("dashboard.data_mode_label"),
        "business_definition": translate("dashboard.business_definition"),
        "run_consistency": {
            "status": consistency_status,
            "is_ready": consistency_status == "ready",
            "forecast_run_id": forecast_run_id,
            "dispatch_forecast_run_id": dispatch_run_id,
            "inventory_snapshot_time": inventory_time,
            "message": translate(
                f"dashboard.consistency.{consistency_status}"
            ),
        },
    }

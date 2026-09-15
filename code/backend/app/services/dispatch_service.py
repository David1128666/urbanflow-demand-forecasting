from app.db import query, query_one
from app.locales import translate


def _latest_run_id() -> int | None:
    row = query_one(
        """SELECT MAX(forecast_run_id) AS run_id
           FROM dispatch_recommendation"""
    )
    return row["run_id"] if row else None


def get_dispatch_summary() -> dict:
    run_id = _latest_run_id()
    if run_id is None:
        return _empty_dispatch_summary()
    row = query_one(
        """SELECT
             (SELECT COUNT(*)
              FROM dispatch_recommendation
              WHERE forecast_run_id = %s) AS recommendation_count,
             COUNT(*) AS target_station_count,
             SUM(total_quantity) AS total_quantity,
             SUM(shortage_before) AS total_shortage_before,
             SUM(shortage_after) AS total_shortage_after
           FROM (
               SELECT to_station_id,
                      SUM(recommended_quantity) AS total_quantity,
                      MAX(shortage_before) AS shortage_before,
                      MIN(shortage_after) AS shortage_after
               FROM dispatch_recommendation
               WHERE forecast_run_id = %s
               GROUP BY to_station_id
           ) station_summary""",
        (run_id, run_id),
    )
    if row is None:
        return _empty_dispatch_summary()
    before = int(row["total_shortage_before"] or 0)
    after = int(row["total_shortage_after"] or 0)
    near_term = query_one(
        """SELECT COALESCE(SUM(predicted_demand), 0) AS near_term_orders,
                  MIN(target_time) AS decision_window_start,
                  DATE_ADD(MAX(target_time), INTERVAL 30 MINUTE)
                    AS decision_window_end
           FROM forecast_result
           WHERE forecast_run_id = %s
             AND horizon_step <= 4""",
        (run_id,),
    )
    metadata = query_one(
        """SELECT COUNT(DISTINCT from_station_id) AS source_station_count,
                  ROUND(SUM(distance_km), 2) AS total_transfer_distance_km,
                  MIN(dispatch_deadline) AS first_deadline,
                  MAX(recommendation_time) AS recommendation_time
           FROM dispatch_recommendation
           WHERE forecast_run_id = %s""",
        (run_id,),
    )
    latest_forecast_run = query_one(
        """SELECT MAX(forecast_run_id) AS run_id
           FROM forecast_run
           WHERE status = 'success'"""
    )
    latest_forecast_run_id = (
        int(latest_forecast_run["run_id"])
        if latest_forecast_run and latest_forecast_run["run_id"] is not None
        else None
    )
    near_term_orders = float(near_term["near_term_orders"] or 0)
    avoided_orders = before - after
    row["shortage_reduction_pct"] = (
        round((before - after) / before * 100, 2) if before else 0.0
    )
    row["deficit_station_count"] = row["target_station_count"]
    row["total_quantity_recommended"] = row["total_quantity"]
    row["forecast_run_id"] = run_id
    row["near_term_orders"] = round(near_term_orders, 1)
    row["decision_window_start"] = near_term["decision_window_start"]
    row["decision_window_end"] = near_term["decision_window_end"]
    row["source_station_count"] = int(metadata["source_station_count"] or 0)
    row["total_transfer_distance_km"] = float(
        metadata["total_transfer_distance_km"] or 0
    )
    row["first_deadline"] = metadata["first_deadline"]
    row["recommendation_time"] = metadata["recommendation_time"]
    row["estimated_risk_orders_avoided"] = avoided_orders
    row["near_term_order_coverage_pct"] = (
        round(avoided_orders / near_term_orders * 100, 2)
        if near_term_orders
        else 0.0
    )
    row["latest_forecast_run_id"] = latest_forecast_run_id
    row["is_current"] = latest_forecast_run_id == run_id
    row["status"] = "current" if row["is_current"] else "stale"
    row["result_basis"] = translate("dispatch.result_basis")
    return row


def get_dispatch_recommendations(limit: int = 100) -> list[dict]:
    run_id = _latest_run_id()
    if run_id is None:
        return []
    rows = query(
        """SELECT d.recommendation_id, d.forecast_run_id,
                  d.recommendation_time, d.dispatch_deadline,
                  d.from_station_id, source.station_name AS from_station_name,
                  d.to_station_id, target.station_name AS to_station_name,
                  d.recommended_quantity, d.distance_km, d.priority_score,
                  d.shortage_before, d.shortage_after, d.reason, d.status,
                  d.near_term_demand, d.safety_stock, d.target_bikes,
                  i.available_bikes AS current_available_bikes,
                  i.available_docks AS current_available_docks
           FROM dispatch_recommendation d
           JOIN station_dim source ON d.from_station_id = source.station_id
           JOIN station_dim target ON d.to_station_id = target.station_id
           LEFT JOIN station_inventory_snapshot i
             ON d.to_station_id = i.station_id
            AND i.snapshot_time = (
                SELECT MAX(snapshot_time)
                FROM station_inventory_snapshot
            )
           WHERE d.forecast_run_id = %s
           ORDER BY d.priority_score DESC, d.distance_km
           LIMIT %s""",
        (run_id, limit),
    )
    for row in rows:
        row["priority_score"] = float(row["priority_score"])
        row["shortage_reduction"] = (
            int(row["shortage_before"]) - int(row["shortage_after"])
        )
        row["shortage_reduction_pct"] = (
            round(
                row["shortage_reduction"]
                / int(row["shortage_before"])
                * 100,
                1,
            )
            if row["shortage_before"]
            else 0.0
        )
        priority_level = _priority_level(row["priority_score"])
        row["priority_level"] = priority_level
        row["priority_label"] = translate(
            f"dispatch.priority.{priority_level}"
        )
        row["status_label"] = (
            translate("dispatch.status.pending")
            if row["status"] == "pending"
            else str(row["status"])
        )
        row["action_text"] = translate(
            "dispatch.action_text",
            quantity=int(row["recommended_quantity"]),
            source=row["from_station_name"],
            target=row["to_station_name"],
            deadline=_format_time(row["dispatch_deadline"]),
        )
        if row["near_term_demand"] is not None:
            row["reason_text"] = _dispatch_reason(row)
        else:
            row["reason_text"] = row["reason"]
        deadline_delta = (
            row["dispatch_deadline"] - row["recommendation_time"]
        )
        row["lead_time_minutes"] = max(
            0,
            int(deadline_delta.total_seconds() // 60),
        )
        if row["target_bikes"] is not None:
            row["target_bikes"] = int(row["target_bikes"])
        elif row["current_available_bikes"] is not None:
            row["target_bikes"] = (
                int(row["current_available_bikes"])
                + int(row["shortage_before"])
            )
        else:
            row["target_bikes"] = None
    return rows


def _priority_level(score: float) -> str:
    if score >= 30:
        return "critical"
    if score >= 20:
        return "high"
    if score >= 10:
        return "medium"
    return "low"


def _dispatch_reason(row: dict) -> str:
    return translate(
        "dispatch.reason",
        demand=float(row["near_term_demand"]),
        available=int(row["current_available_bikes"] or 0),
        target=int(row["target_bikes"] or 0),
    )


def _format_time(value) -> str:
    return value.strftime("%m-%d %H:%M")


def _empty_dispatch_summary() -> dict:
    return {
        "recommendation_count": 0,
        "target_station_count": 0,
        "total_quantity": 0,
        "total_shortage_before": 0,
        "total_shortage_after": 0,
        "shortage_reduction_pct": 0.0,
        "deficit_station_count": 0,
        "total_quantity_recommended": 0,
        "forecast_run_id": None,
        "latest_forecast_run_id": None,
        "is_current": False,
        "status": "not_generated",
        "near_term_orders": 0.0,
        "decision_window_start": None,
        "decision_window_end": None,
        "source_station_count": 0,
        "total_transfer_distance_km": 0.0,
        "first_deadline": None,
        "recommendation_time": None,
        "estimated_risk_orders_avoided": 0,
        "near_term_order_coverage_pct": 0.0,
        "result_basis": translate("dispatch.result_basis"),
    }

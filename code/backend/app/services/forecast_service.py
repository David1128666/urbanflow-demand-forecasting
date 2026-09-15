import math
from datetime import timedelta

from app.db import query, query_one
from app.locales import translate
from app.services.inventory_service import get_latest_inventory


def get_latest_run(city_id: str | None = None) -> dict | None:
    if city_id:
        return query_one(
            """SELECT forecast_run_id, city_id, model_version,
                      feature_version, data_cutoff, forecast_start,
                      horizon_steps, status, generated_at
               FROM forecast_run
               WHERE status = 'success' AND city_id = %s
               ORDER BY forecast_run_id DESC
               LIMIT 1""",
            (city_id,),
        )
    return query_one(
        """SELECT forecast_run_id, city_id, model_version,
                  feature_version, data_cutoff, forecast_start,
                  horizon_steps, status, generated_at
           FROM forecast_run
           WHERE status = 'success'
           ORDER BY forecast_run_id DESC
           LIMIT 1"""
    )


def get_latest_forecasts(
    station_id: str | None = None,
    limit: int = 1000,
) -> dict | None:
    run = get_latest_run()
    if run is None:
        return {
            "run": None,
            "points": [],
            "operation_summary": None,
        }

    conditions = ["r.forecast_run_id = %s"]
    params: list = [run["forecast_run_id"]]
    if station_id:
        conditions.append("r.station_id = %s")
        params.append(station_id)
    params.append(limit)

    points = query(
        f"""SELECT r.city_id, r.station_id, s.station_name,
                   r.target_time, r.horizon_step, r.predicted_demand
            FROM forecast_result r
            LEFT JOIN station_dim s ON r.station_id = s.station_id
            WHERE {' AND '.join(conditions)}
            ORDER BY r.station_id, r.horizon_step
            LIMIT %s""",
        params,
    )
    for point in points:
        point["window_start"] = point["target_time"]
        point["window_end"] = point["target_time"] + timedelta(minutes=30)

    return {
        "run": run,
        "points": points,
        "operation_summary": _build_operation_summary(
            station_id=station_id,
            points=points,
        ),
    }


def _build_operation_summary(
    station_id: str | None,
    points: list[dict],
) -> dict | None:
    if not station_id or not points:
        return None

    ordered_points = sorted(points, key=lambda point: point["horizon_step"])
    demand_values = [
        float(point["predicted_demand"]) for point in ordered_points
    ]
    next_two_hours = sum(
        demand_values[index]
        for index, point in enumerate(ordered_points)
        if int(point["horizon_step"]) <= 4
    )
    peak_index = max(range(len(demand_values)), key=demand_values.__getitem__)
    peak_point = ordered_points[peak_index]
    first_point = ordered_points[0]

    inventory_rows = get_latest_inventory(station_id)
    inventory = inventory_rows[0] if inventory_rows else {}
    available_bikes = int(inventory.get("available_bikes") or 0)
    available_docks = int(inventory.get("available_docks") or 0)
    station_status = str(inventory.get("station_status") or "unknown")

    safety_stock = max(2, math.ceil(next_two_hours * 0.10))
    target_bikes = round(next_two_hours) + safety_stock
    recommended_replenishment = max(0, target_bikes - available_bikes)
    has_inventory = bool(inventory_rows)

    if recommended_replenishment > 0 and available_bikes <= 5:
        operation_status = translate("operation.status.urgent")
    elif recommended_replenishment > 0:
        operation_status = translate("operation.status.replenish")
    elif station_status == "full" or available_docks <= 3:
        operation_status = translate("operation.status.return_pressure")
    else:
        operation_status = translate("operation.status.normal")

    if not has_inventory:
        recommended_action = translate("operation.action.no_inventory")
    elif recommended_replenishment > 0:
        recommended_action = translate(
            "operation.action.replenish",
            demand=next_two_hours,
            available=available_bikes,
            target=target_bikes,
            quantity=recommended_replenishment,
            deadline=first_point["target_time"].strftime("%m-%d %H:%M"),
        )
    elif station_status == "full" or available_docks <= 3:
        recommended_action = translate(
            "operation.action.return_pressure",
            available=available_bikes,
            docks=available_docks,
        )
    else:
        recommended_action = translate(
            "operation.action.normal",
            available=available_bikes,
            target=target_bikes,
        )

    return {
        "station_id": station_id,
        "station_name": inventory.get("station_name"),
        "snapshot_time": inventory.get("snapshot_time"),
        "current_available_bikes": available_bikes if has_inventory else None,
        "current_available_docks": available_docks if has_inventory else None,
        "station_status": station_status,
        "station_status_label": inventory.get("station_status_label"),
        "next_2h_orders": round(next_two_hours, 1),
        "next_24h_orders": round(sum(demand_values), 1),
        "peak_window_orders": round(demand_values[peak_index], 1),
        "peak_window_start": peak_point["target_time"],
        "peak_window_end": peak_point["window_end"],
        "safety_stock": safety_stock,
        "target_bikes": target_bikes,
        "recommended_replenishment": recommended_replenishment,
        "operation_status": operation_status,
        "recommended_action": recommended_action,
        "decision_deadline": first_point["target_time"],
        "demand_unit": translate("operation.demand_unit"),
        "demand_window_minutes": 30,
    }

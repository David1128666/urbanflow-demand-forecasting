from app.db import query, query_one
from app.locales import translate


def get_latest_inventory(station_id: str | None = None) -> list[dict]:
    conditions = [
        "i.snapshot_time = (SELECT MAX(snapshot_time) "
        "FROM station_inventory_snapshot)"
    ]
    params: list = []
    if station_id:
        conditions.append("i.station_id = %s")
        params.append(station_id)

    rows = query(
        f"""SELECT i.city_id, i.station_id, d.station_name,
                   i.snapshot_time, i.capacity, i.available_bikes,
                   i.available_docks, i.station_status,
                   ROUND(i.available_bikes / NULLIF(i.capacity, 0) * 100, 1)
                     AS availability_pct
            FROM station_inventory_snapshot i
            JOIN station_dim d ON i.station_id = d.station_id
            WHERE {' AND '.join(conditions)}
            ORDER BY i.station_id""",
        params,
    )
    for row in rows:
        status = str(row["station_status"])
        row["station_status_label"] = translate(
            f"station_status.{status}"
        )
        row["operational_note"] = translate(f"station_note.{status}")
    return rows


def get_inventory_summary() -> dict:
    row = query_one(
        """SELECT COUNT(*) AS station_count,
                  SUM(capacity) AS total_capacity,
                  SUM(available_bikes) AS total_available_bikes,
                  SUM(available_docks) AS total_available_docks,
                  SUM(station_status IN ('empty', 'low')) AS shortage_stations,
                  SUM(station_status = 'full') AS full_stations,
                  MAX(snapshot_time) AS snapshot_time,
                  ROUND(
                    SUM(available_bikes) / NULLIF(SUM(capacity), 0) * 100,
                    1
                  ) AS fleet_utilization_pct
           FROM station_inventory_snapshot
           WHERE snapshot_time = (
               SELECT MAX(snapshot_time) FROM station_inventory_snapshot
           )"""
    )
    if row is None:
        return {
            "station_count": 0,
            "total_capacity": 0,
            "total_available_bikes": 0,
            "total_available_docks": 0,
            "shortage_stations": 0,
            "full_stations": 0,
            "snapshot_time": None,
            "fleet_utilization_pct": 0,
        }
    return row

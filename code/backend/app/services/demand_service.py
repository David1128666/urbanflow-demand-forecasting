from datetime import datetime

from app.db import query


def get_demand_history(
    station_id: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 500,
) -> list[dict]:
    conditions = ["station_id = %s"]
    params: list = [station_id]

    if start_time is not None:
        conditions.append("window_start >= %s")
        params.append(start_time)
    if end_time is not None:
        conditions.append("window_start < %s")
        params.append(end_time)

    params.append(limit)
    return query(
        f"""SELECT city_id, station_id, window_start, window_end,
                   demand_count, temperature, precipitation, is_holiday,
                   data_version
            FROM (
                SELECT city_id, station_id, window_start, window_end,
                       demand_count, temperature, precipitation, is_holiday,
                       data_version
                FROM demand_observation
                WHERE {' AND '.join(conditions)}
                ORDER BY window_start DESC
                LIMIT %s
            ) recent
            ORDER BY window_start""",
        params,
    )


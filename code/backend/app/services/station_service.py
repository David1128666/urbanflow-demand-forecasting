from app.db import query, query_one


def list_stations(
    city_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    if city_id:
        return query(
            """SELECT station_id, city_id, station_name, longitude, latitude,
                      capacity, region_id, is_active
               FROM station_dim
               WHERE city_id = %s
               ORDER BY station_id
               LIMIT %s OFFSET %s""",
            (city_id, limit, offset),
        )
    return query(
        """SELECT station_id, city_id, station_name, longitude, latitude,
                  capacity, region_id, is_active
           FROM station_dim
           ORDER BY station_id
           LIMIT %s OFFSET %s""",
        (limit, offset),
    )


def get_station(station_id: str) -> dict | None:
    return query_one(
        """SELECT station_id, city_id, station_name, longitude, latitude,
                  capacity, region_id, is_active, created_at, updated_at
           FROM station_dim
           WHERE station_id = %s""",
        (station_id,),
    )


from __future__ import annotations

import argparse
import csv
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import pymysql


@dataclass(frozen=True)
class MysqlLoaderConfig:
    stations_path: Path
    snapshots_path: Path
    observations_path: Path
    host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    port: int = int(os.getenv("MYSQL_PORT", "3306"))
    user: str = os.getenv("MYSQL_USER", "urbanflow")
    password: str = os.getenv("MYSQL_PASSWORD", "urbanflow_dev")
    database: str = os.getenv("MYSQL_DATABASE", "urbanflow")
    batch_size: int = 1000


@dataclass(frozen=True)
class MysqlLoadResult:
    stations_loaded: int
    snapshots_loaded: int
    observations_loaded: int


def load_virtual_data(config: MysqlLoaderConfig) -> MysqlLoadResult:
    """Load generated station and demand CSV files into MySQL."""

    if not config.stations_path.is_file():
        raise FileNotFoundError(config.stations_path)
    if not config.snapshots_path.is_file():
        raise FileNotFoundError(config.snapshots_path)
    if not config.observations_path.is_file():
        raise FileNotFoundError(config.observations_path)
    if config.batch_size < 1:
        raise ValueError("batch_size must be positive")

    connection = pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        charset="utf8mb4",
        autocommit=False,
    )

    stations_loaded = 0
    snapshots_loaded = 0
    observations_loaded = 0

    try:
        with connection.cursor() as cursor:
            for batch in _batches(
                _station_rows(config.stations_path),
                config.batch_size,
            ):
                cursor.executemany(
                    """INSERT INTO station_dim
                       (station_id, city_id, station_name, longitude, latitude,
                        capacity, region_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE
                         station_name = VALUES(station_name),
                         longitude = VALUES(longitude),
                         latitude = VALUES(latitude),
                         capacity = VALUES(capacity),
                         region_id = VALUES(region_id),
                         is_active = 1""",
                    batch,
                )
                stations_loaded += len(batch)

            for batch in _batches(
                _snapshot_rows(config.snapshots_path),
                config.batch_size,
            ):
                cursor.executemany(
                    """INSERT INTO station_inventory_snapshot
                       (city_id, station_id, snapshot_time, capacity,
                        available_bikes, available_docks, station_status)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE
                         capacity = VALUES(capacity),
                         available_bikes = VALUES(available_bikes),
                         available_docks = VALUES(available_docks),
                         station_status = VALUES(station_status)""",
                    batch,
                )
                snapshots_loaded += len(batch)

            for batch in _batches(
                _observation_rows(config.observations_path),
                config.batch_size,
            ):
                cursor.executemany(
                    """INSERT INTO demand_observation
                       (city_id, station_id, window_start, window_end,
                        demand_count, temperature, precipitation, is_holiday,
                        data_version)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE
                         demand_count = VALUES(demand_count),
                         temperature = VALUES(temperature),
                         precipitation = VALUES(precipitation),
                         is_holiday = VALUES(is_holiday)""",
                    batch,
                )
                observations_loaded += len(batch)

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return MysqlLoadResult(
        stations_loaded=stations_loaded,
        snapshots_loaded=snapshots_loaded,
        observations_loaded=observations_loaded,
    )


def _station_rows(path: Path) -> Iterable[tuple[Any, ...]]:
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            yield (
                row["station_id"],
                row["city_id"],
                row["station_name"],
                float(row["longitude"]),
                float(row["latitude"]),
                int(row["capacity"]),
                row["region_id"],
            )


def _observation_rows(path: Path) -> Iterable[tuple[Any, ...]]:
    interval = timedelta(minutes=30)
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            window_start = datetime.strptime(
                row["event_time"],
                "%Y-%m-%d %H:%M:%S",
            )
            yield (
                row["city_id"],
                row["station_id"],
                window_start,
                window_start + interval,
                int(row["demand_count"]),
                float(row["temperature"]),
                float(row["precipitation"]),
                int(row["is_holiday"]),
                row["data_version"],
            )


def _snapshot_rows(path: Path) -> Iterable[tuple[Any, ...]]:
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            yield (
                row["city_id"],
                row["station_id"],
                datetime.strptime(
                    row["snapshot_time"],
                    "%Y-%m-%d %H:%M:%S",
                ),
                int(row["capacity"]),
                int(row["available_bikes"]),
                int(row["available_docks"]),
                row["station_status"],
            )


def _batches(
    rows: Iterable[tuple[Any, ...]],
    batch_size: int,
) -> Iterable[list[tuple[Any, ...]]]:
    batch: list[tuple[Any, ...]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load generated UrbanFlow data into MySQL."
    )
    parser.add_argument(
        "--stations-path",
        type=Path,
        default=Path("data/virtual-v1/stations.csv"),
    )
    parser.add_argument(
        "--snapshots-path",
        type=Path,
        default=Path("data/virtual-v1/station_snapshots.csv"),
    )
    parser.add_argument(
        "--observations-path",
        type=Path,
        default=Path("data/virtual-v1/demand_observations.csv"),
    )
    parser.add_argument("--batch-size", type=int, default=1000)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = load_virtual_data(
        MysqlLoaderConfig(
            stations_path=args.stations_path,
            snapshots_path=args.snapshots_path,
            observations_path=args.observations_path,
            batch_size=args.batch_size,
        )
    )
    print(f"stations_loaded={result.stations_loaded}")
    print(f"snapshots_loaded={result.snapshots_loaded}")
    print(f"observations_loaded={result.observations_loaded}")


if __name__ == "__main__":
    main()

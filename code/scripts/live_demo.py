"""Continuously update the local demo with new virtual demand windows."""

from __future__ import annotations

import argparse
import csv
import os
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pymysql


CODE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = CODE_ROOT.parent
INTERVAL = timedelta(minutes=30)


@dataclass(frozen=True)
class LiveDemoConfig:
    data_dir: Path
    interval_seconds: int = 8
    predict_every: int = 3
    max_cycles: int = 0
    seed: int = 2026
    language: str = "en"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Continuously append virtual demand windows, refresh inventory, "
            "and periodically rerun forecast and dispatch."
        )
    )
    parser.add_argument("--interval-seconds", type=int, default=8)
    parser.add_argument("--predict-every", type=int, default=3)
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=0,
        help="0 keeps running until Ctrl+C.",
    )
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--language", choices=("en", "zh-CN"), default="en")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=CODE_ROOT / "data",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_env_file(CODE_ROOT / ".env")
    load_env_file(PROJECT_ROOT / ".env")
    config = LiveDemoConfig(
        data_dir=args.data_dir.resolve(),
        interval_seconds=max(1, args.interval_seconds),
        predict_every=max(1, args.predict_every),
        max_cycles=max(0, args.max_cycles),
        seed=args.seed,
        language=args.language,
    )
    return run_live_demo(config)


def run_live_demo(config: LiveDemoConfig) -> int:
    rng = random.Random(config.seed)
    connection = _connect()
    try:
        state = _load_state(connection)
        cycles = 0
        print(
            "Live demo started. Press Ctrl+C to stop. "
            f"next_window={state['next_time']:%Y-%m-%d %H:%M}",
            flush=True,
        )
        while config.max_cycles == 0 or cycles < config.max_cycles:
            rows = _build_next_window(connection, state, rng)
            _write_rows(connection, rows)
            _append_observations_csv(
                config.data_dir / "virtual-v1" / "demand_observations.csv",
                rows,
            )
            cycles += 1
            print(
                f"[live] cycle={cycles} window={state['next_time']:%Y-%m-%d %H:%M} "
                f"stations={len(rows)}",
                flush=True,
            )

            if cycles % config.predict_every == 0:
                _refresh_predictions(config)

            state = _advance_state(state)
            if config.max_cycles == 0 or cycles < config.max_cycles:
                time.sleep(config.interval_seconds)
    except KeyboardInterrupt:
        print("\nLive demo stopped.", flush=True)
    finally:
        connection.close()
    return 0


def _connect() -> pymysql.Connection:
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "urbanflow"),
        password=os.getenv("MYSQL_PASSWORD", "urbanflow_dev"),
        database=os.getenv("MYSQL_DATABASE", "urbanflow"),
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def _load_state(connection: pymysql.Connection) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT MAX(window_start) AS latest_window
               FROM demand_observation"""
        )
        latest_window = cursor.fetchone()["latest_window"]
        if latest_window is None:
            raise RuntimeError(
                "No demand observations are available. Run the demo pipeline first."
            )

        cursor.execute(
            """SELECT o.city_id, o.station_id, o.demand_count,
                      o.temperature, o.precipitation, o.is_holiday,
                      d.capacity, i.available_bikes, i.available_docks
               FROM demand_observation o
               JOIN station_dim d ON o.station_id = d.station_id
               LEFT JOIN station_inventory_snapshot i
                 ON i.station_id = o.station_id
                AND i.snapshot_time = (
                    SELECT MAX(snapshot_time)
                    FROM station_inventory_snapshot
                )
               WHERE o.window_start = %s
               ORDER BY o.station_id""",
            (latest_window,),
        )
        latest_rows = cursor.fetchall()

    return {
        "next_time": latest_window + INTERVAL,
        "stations": {
            row["station_id"]: {
                "city_id": row["city_id"],
                "station_id": row["station_id"],
                "demand_count": int(row["demand_count"]),
                "temperature": row["temperature"],
                "precipitation": row["precipitation"],
                "is_holiday": row["is_holiday"],
                "capacity": int(row["capacity"]),
                "available_bikes": int(row["available_bikes"] or 0),
                "available_docks": int(row["available_docks"] or 0),
            }
            for row in latest_rows
        },
    }


def _advance_state(state: dict[str, Any]) -> dict[str, Any]:
    advanced = dict(state)
    advanced["next_time"] = state["next_time"] + INTERVAL
    advanced["stations"] = {
        station_id: dict(station)
        for station_id, station in state["stations"].items()
    }
    return advanced


def _build_next_window(
    connection: pymysql.Connection,
    state: dict[str, Any],
    rng: random.Random,
) -> list[dict[str, Any]]:
    next_time = state["next_time"]
    previous_day = next_time - timedelta(days=1)
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT station_id, demand_count
               FROM demand_observation
               WHERE window_start = %s""",
            (previous_day,),
        )
        previous_day_demand = {
            row["station_id"]: int(row["demand_count"])
            for row in cursor.fetchall()
        }

    rows: list[dict[str, Any]] = []
    for station_id, station in sorted(state["stations"].items()):
        base_demand = previous_day_demand.get(
            station_id,
            int(station["demand_count"]),
        )
        demand = max(0, round(base_demand * rng.gauss(1.0, 0.12)))
        available_ratio = (
            int(station["available_bikes"]) / int(station["capacity"])
            if int(station["capacity"])
            else 0
        )
        returns = max(0, round(demand * rng.uniform(0.96, 1.12)))
        if available_ratio < 0.20:
            returns += rng.randint(0, 2)
        available_bikes = max(
            0,
            min(
                int(station["capacity"]),
                int(station["available_bikes"]) - demand + returns,
            ),
        )
        available_docks = int(station["capacity"]) - available_bikes
        window_end = next_time + INTERVAL
        status = _station_status(
            available_bikes,
            available_docks,
            int(station["capacity"]),
        )
        event_time = next_time.strftime("%Y-%m-%d %H:%M:%S")

        rows.append(
            {
                **station,
                "event_id": (
                    f"live_{next_time.strftime('%Y%m%d%H%M')}_{station_id}"
                ),
                "event_time": event_time,
                "window_start": next_time,
                "window_end": window_end,
                "snapshot_time": window_end,
                "demand_count": demand,
                "available_bikes": available_bikes,
                "available_docks": available_docks,
                "station_status": status,
                "data_version": "live-demo",
            }
        )

    state["stations"] = {
        row["station_id"]: {
            **row,
            "demand_count": row["demand_count"],
            "available_bikes": row["available_bikes"],
            "available_docks": row["available_docks"],
        }
        for row in rows
    }
    return rows


def _station_status(
    available_bikes: int,
    available_docks: int,
    capacity: int,
) -> str:
    ratio = available_bikes / capacity if capacity else 0
    if ratio <= 0.10:
        return "empty"
    if ratio <= 0.25:
        return "low"
    if ratio >= 0.85 or available_docks <= 3:
        return "full"
    return "normal"


def _write_rows(
    connection: pymysql.Connection,
    rows: list[dict[str, Any]],
) -> None:
    with connection.cursor() as cursor:
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
            [
                (
                    row["city_id"],
                    row["station_id"],
                    row["window_start"],
                    row["window_end"],
                    row["demand_count"],
                    row["temperature"],
                    row["precipitation"],
                    row["is_holiday"],
                    row["data_version"],
                )
                for row in rows
            ],
        )
        cursor.executemany(
            """INSERT INTO realtime_demand_metrics
               (city_id, station_id, window_start, window_end,
                demand_count, event_count)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
                 demand_count = VALUES(demand_count),
                 event_count = VALUES(event_count)""",
            [
                (
                    row["city_id"],
                    row["station_id"],
                    row["window_start"],
                    row["window_end"],
                    row["demand_count"],
                    1,
                )
                for row in rows
            ],
        )
        cursor.executemany(
            """INSERT INTO station_inventory_snapshot
               (city_id, station_id, snapshot_time, capacity,
                available_bikes, available_docks, station_status)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
                 available_bikes = VALUES(available_bikes),
                 available_docks = VALUES(available_docks),
                 station_status = VALUES(station_status)""",
            [
                (
                    row["city_id"],
                    row["station_id"],
                    row["snapshot_time"],
                    row["capacity"],
                    row["available_bikes"],
                    row["available_docks"],
                    row["station_status"],
                )
                for row in rows
            ],
        )
    connection.commit()


def _append_observations_csv(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:
    file_exists = path.is_file() and path.stat().st_size > 0
    fieldnames = [
        "event_id",
        "city_id",
        "station_id",
        "event_time",
        "demand_count",
        "temperature",
        "precipitation",
        "is_holiday",
        "is_anomaly",
        "data_version",
    ]
    with path.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "event_id": row["event_id"],
                    "city_id": row["city_id"],
                    "station_id": row["station_id"],
                    "event_time": row["event_time"],
                    "demand_count": row["demand_count"],
                    "temperature": row["temperature"],
                    "precipitation": row["precipitation"],
                    "is_holiday": row["is_holiday"],
                    "is_anomaly": 0,
                    "data_version": row["data_version"],
                }
            )


def _refresh_predictions(config: LiveDemoConfig) -> None:
    env = os.environ.copy()
    python_path = [
        str(CODE_ROOT / "simulator" / "src"),
        str(CODE_ROOT / "forecast-engine" / "src"),
    ]
    if env.get("PYTHONPATH"):
        python_path.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_path)

    predict_command = [
        sys.executable,
        "-m",
        "urbanflow_forecast.cli",
        "predict",
        "--features-path",
        str(config.data_dir / "features-v1" / "features.parquet"),
        "--observations-path",
        str(config.data_dir / "virtual-v1" / "demand_observations.csv"),
        "--baseline-metrics-path",
        str(config.data_dir / "baseline-v1" / "metrics.json"),
        "--tcn-metrics-path",
        str(config.data_dir / "tcn-v1" / "metrics.json"),
        "--output-dir",
        str(config.data_dir / "predictions-v1"),
        "--write-mysql",
    ]
    dispatch_command = [
        sys.executable,
        "-m",
        "urbanflow_forecast.cli",
        "dispatch",
        "--output-dir",
        str(config.data_dir / "dispatch-v1"),
        "--language",
        config.language,
        "--write-mysql",
    ]
    print("[live] refreshing forecast and dispatch", flush=True)
    subprocess.run(
        predict_command,
        cwd=CODE_ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        dispatch_command,
        cwd=CODE_ROOT,
        env=env,
        check=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())

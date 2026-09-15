from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from simulator.config import SimulationConfig
from simulator.locales import message


STATION_TYPES = (
    "transit",
    "business",
    "residential",
    "mixed",
    "leisure",
)

@dataclass(frozen=True)
class GenerationResult:
    output_dir: Path
    station_count: int
    inventory_snapshot_count: int
    observation_count: int
    holiday_count: int
    anomaly_count: int
    manifest_path: Path


def generate_dataset(config: SimulationConfig) -> GenerationResult:
    """Generate deterministic station, demand, weather, and manifest files."""

    config.validate()
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(config.seed)
    stations = _generate_stations(config, rng)
    holidays = _build_holiday_set(config)
    daily_weather = _generate_daily_weather(config, rng)

    stations_path = output_dir / "stations.csv"
    inventory_path = output_dir / "station_snapshots.csv"
    observations_path = output_dir / "demand_observations.csv"
    jsonl_path = output_dir / "demand_observations.jsonl"
    manifest_path = output_dir / "generation_manifest.json"

    _write_stations(stations_path, stations)
    _write_station_snapshots(
        inventory_path,
        config,
        stations,
    )
    counts = _write_observations(
        observations_path=observations_path,
        jsonl_path=jsonl_path,
        config=config,
        stations=stations,
        holidays=holidays,
        daily_weather=daily_weather,
        rng=rng,
    )

    files = {}
    for path in (
        stations_path,
        inventory_path,
        observations_path,
        jsonl_path,
    ):
        files[path.name] = {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }

    manifest = {
        "schema_version": "1.0",
        "seed": config.seed,
        "city_id": config.city_id,
        "city_name": (
            config.city_name
            or message(config.language, "city_name")
        ),
        "start_date": config.start_date.isoformat(),
        "days": config.days,
        "interval_minutes": config.interval_minutes,
        "station_count": config.station_count,
        "inventory_snapshot_count": config.station_count,
        "observation_count": config.observation_count,
        "holiday_count": len(holidays),
        "anomaly_count": counts["anomaly_count"],
        "data_version": config.data_version,
        "files": files,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return GenerationResult(
        output_dir=output_dir,
        station_count=config.station_count,
        inventory_snapshot_count=config.station_count,
        observation_count=config.observation_count,
        holiday_count=len(holidays),
        anomaly_count=counts["anomaly_count"],
        manifest_path=manifest_path,
    )


def _generate_stations(
    config: SimulationConfig,
    rng: random.Random,
) -> list[dict[str, object]]:
    stations: list[dict[str, object]] = []
    center_lon = 121.4737
    center_lat = 31.2304

    for index in range(config.station_count):
        station_type = STATION_TYPES[index % len(STATION_TYPES)]
        capacity = rng.randint(30, 90)
        base_demand = {
            "transit": 22.0,
            "business": 18.0,
            "residential": 15.0,
            "mixed": 19.0,
            "leisure": 12.0,
        }[station_type]
        base_demand *= capacity / 60.0
        base_demand *= rng.uniform(0.85, 1.15)

        stations.append(
            {
                "station_id": f"ST{index + 1:03d}",
                "city_id": config.city_id,
                "station_name": message(
                    config.language,
                    "station_template",
                    scene=message(config.language, station_type),
                    index=index + 1,
                ),
                "longitude": round(center_lon + rng.uniform(-0.08, 0.08), 6),
                "latitude": round(center_lat + rng.uniform(-0.06, 0.06), 6),
                "capacity": capacity,
                "region_id": f"R{(index % 5) + 1}",
                "station_type": station_type,
                "base_demand": round(base_demand, 4),
            }
        )

    return stations


def _build_holiday_set(config: SimulationConfig) -> set[int]:
    candidates = {8, 16, 24, 37, 52, 68, 82}
    return {day for day in candidates if day < config.days}


def _generate_daily_weather(
    config: SimulationConfig,
    rng: random.Random,
) -> list[dict[str, float | str]]:
    weather: list[dict[str, float | str]] = []
    for day_index in range(config.days):
        season = math.sin((day_index / 365.0) * 2.0 * math.pi - math.pi / 2.0)
        temperature = 18.0 + season * 12.0 + rng.uniform(-3.0, 3.0)
        precipitation = 0.0
        weather_code = "clear"

        if rng.random() < 0.18:
            weather_code = "rain"
            precipitation = round(rng.uniform(0.5, 12.0), 2)
        elif rng.random() < 0.28:
            weather_code = "cloudy"

        weather.append(
            {
                "temperature": round(temperature, 2),
                "precipitation": precipitation,
                "weather_code": weather_code,
            }
        )

    return weather


def _write_observations(
    *,
    observations_path: Path,
    jsonl_path: Path,
    config: SimulationConfig,
    stations: list[dict[str, object]],
    holidays: set[int],
    daily_weather: list[dict[str, float | str]],
    rng: random.Random,
) -> dict[str, int]:
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
    anomaly_count = 0

    with observations_path.open("w", encoding="utf-8", newline="") as csv_file, (
        jsonl_path.open("w", encoding="utf-8")
    ) as jsonl_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for row in _iter_observations(
            config=config,
            stations=stations,
            holidays=holidays,
            daily_weather=daily_weather,
            rng=rng,
        ):
            writer.writerow(row)
            jsonl_file.write(json.dumps(row, ensure_ascii=False) + "\n")
            if row["is_anomaly"]:
                anomaly_count += 1

    return {"anomaly_count": anomaly_count}


def _iter_observations(
    *,
    config: SimulationConfig,
    stations: list[dict[str, object]],
    holidays: set[int],
    daily_weather: list[dict[str, float | str]],
    rng: random.Random,
) -> Iterable[dict[str, object]]:
    for day_index in range(config.days):
        weather = daily_weather[day_index]
        event_date = config.start_date + timedelta(days=day_index)
        weekday = event_date.weekday()
        is_weekend = weekday >= 5
        is_holiday = day_index in holidays

        for step in range(config.steps_per_day):
            for station_index, station in enumerate(stations, start=1):
                station_type = str(station["station_type"])
                base_demand = float(station["base_demand"])
                event_time = event_date + timedelta(
                    minutes=step * config.interval_minutes
                )
                expected = _expected_demand(
                    base_demand=base_demand,
                    station_type=station_type,
                    event_time=event_time,
                    is_weekend=is_weekend,
                    is_holiday=is_holiday,
                    temperature=float(weather["temperature"]),
                    precipitation=float(weather["precipitation"]),
                )

                noise = max(0.35, rng.gauss(1.0, 0.13))
                is_anomaly = rng.random() < 0.0015
                if is_anomaly:
                    noise *= rng.uniform(1.8, 2.8)

                demand_count = max(0, int(round(expected * noise)))
                event_id = (
                    f"evt_{event_time.strftime('%Y%m%d%H%M')}_"
                    f"{station_index:03d}"
                )

                yield {
                    "event_id": event_id,
                    "city_id": config.city_id,
                    "station_id": station["station_id"],
                    "event_time": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "demand_count": demand_count,
                    "temperature": weather["temperature"],
                    "precipitation": weather["precipitation"],
                    "is_holiday": int(is_holiday),
                    "is_anomaly": int(is_anomaly),
                    "data_version": config.data_version,
                }


def _expected_demand(
    *,
    base_demand: float,
    station_type: str,
    event_time: datetime,
    is_weekend: bool,
    is_holiday: bool,
    temperature: float,
    precipitation: float,
) -> float:
    hour = event_time.hour + event_time.minute / 60.0
    morning_peak = _gaussian_peak(hour, 8.0, 1.25)
    evening_peak = _gaussian_peak(hour, 18.0, 1.65)
    daytime_peak = _gaussian_peak(hour, 12.5, 3.2)

    profile = {
        "transit": 0.25 + 1.05 * morning_peak + 1.15 * evening_peak,
        "business": 0.28 + 0.75 * morning_peak + 0.70 * evening_peak,
        "residential": 0.30 + 0.80 * morning_peak + 0.95 * evening_peak,
        "mixed": 0.35 + 0.70 * morning_peak + 0.80 * evening_peak + 0.25 * daytime_peak,
        "leisure": 0.25 + 0.20 * morning_peak + 0.55 * daytime_peak + 0.75 * evening_peak,
    }[station_type]

    if is_weekend:
        profile *= 0.78 if station_type in {"transit", "business"} else 1.22

    if is_holiday:
        profile *= 0.82 if station_type == "business" else 1.12

    rain_factor = min(0.25, precipitation * 0.025)
    if station_type in {"transit", "mixed"}:
        weather_factor = 1.0 + rain_factor
    elif station_type == "leisure":
        weather_factor = 1.0 - rain_factor
    else:
        weather_factor = 1.0 + rain_factor * 0.4

    if temperature < 5:
        weather_factor *= 0.92
    elif temperature > 32:
        weather_factor *= 0.95

    return max(0.0, base_demand * profile * weather_factor)


def _gaussian_peak(value: float, center: float, width: float) -> float:
    return math.exp(-((value - center) ** 2) / (2.0 * width**2))


def _write_stations(path: Path, stations: list[dict[str, object]]) -> None:
    fieldnames = [
        "station_id",
        "city_id",
        "station_name",
        "longitude",
        "latitude",
        "capacity",
        "region_id",
        "station_type",
        "base_demand",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stations)


def _write_station_snapshots(
    path: Path,
    config: SimulationConfig,
    stations: list[dict[str, object]],
) -> None:
    snapshot_time = config.start_date + timedelta(
        days=config.days - 1,
        hours=23,
        minutes=30,
    )
    availability_ratios = (0.08, 0.18, 0.35, 0.50, 0.72, 0.88)
    fieldnames = [
        "city_id",
        "station_id",
        "snapshot_time",
        "capacity",
        "available_bikes",
        "available_docks",
        "station_status",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for index, station in enumerate(stations):
            capacity = int(station["capacity"])
            ratio = availability_ratios[index % len(availability_ratios)]
            available_bikes = max(0, min(capacity, round(capacity * ratio)))
            available_docks = capacity - available_bikes
            if ratio <= 0.10:
                station_status = "empty"
            elif ratio <= 0.25:
                station_status = "low"
            elif ratio >= 0.85:
                station_status = "full"
            else:
                station_status = "normal"

            writer.writerow(
                {
                    "city_id": config.city_id,
                    "station_id": station["station_id"],
                    "snapshot_time": snapshot_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "capacity": capacity,
                    "available_bikes": available_bikes,
                    "available_docks": available_docks,
                    "station_status": station_status,
                }
            )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

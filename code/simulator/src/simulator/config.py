from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for a reproducible virtual city demand dataset."""

    station_count: int = 20
    days: int = 90
    interval_minutes: int = 30
    seed: int = 42
    start_date: datetime = datetime(2026, 1, 1, 0, 0, 0)
    city_id: str = "city-001"
    city_name: str | None = None
    language: str = "en"
    output_dir: Path = Path("data/virtual-v1")
    data_version: str = "virtual-v1"

    def validate(self) -> None:
        if self.station_count < 1:
            raise ValueError("station_count must be at least 1")
        if self.days < 1:
            raise ValueError("days must be at least 1")
        if self.interval_minutes < 1 or 1440 % self.interval_minutes != 0:
            raise ValueError("interval_minutes must divide 1440 exactly")
        if not self.city_id:
            raise ValueError("city_id cannot be empty")
        if self.language not in {"en", "zh-CN"}:
            raise ValueError("language must be en or zh-CN")

    @property
    def steps_per_day(self) -> int:
        return 1440 // self.interval_minutes

    @property
    def observation_count(self) -> int:
        return self.station_count * self.days * self.steps_per_day

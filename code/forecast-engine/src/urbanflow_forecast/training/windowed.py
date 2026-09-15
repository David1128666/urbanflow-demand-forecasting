from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "demand_count",
    "temperature",
    "precipitation",
    "is_holiday",
    "is_weekend",
    "hour_sin",
    "hour_cos",
]


@dataclass(frozen=True)
class DatasetConfig:
    input_length: int = 96
    horizon: int = 48
    train_stride: int = 2

    def validate(self) -> None:
        if self.input_length < 1:
            raise ValueError("input_length must be positive")
        if self.horizon < 1:
            raise ValueError("horizon must be positive")
        if self.train_stride < 1:
            raise ValueError("train_stride must be positive")


@dataclass(frozen=True)
class WindowedData:
    features: np.ndarray
    targets: np.ndarray
    origins: np.ndarray
    stations: np.ndarray


@dataclass(frozen=True)
class FeatureStandardizer:
    means: np.ndarray
    standard_deviations: np.ndarray
    demand_mean: float
    demand_std: float

    @classmethod
    def fit(
        cls,
        frame: pd.DataFrame,
        feature_columns: list[str],
    ) -> "FeatureStandardizer":
        train = frame[frame["split"] == "train"]
        means = train[feature_columns].mean().to_numpy(dtype=np.float32)
        standard_deviations = train[feature_columns].std().to_numpy(
            dtype=np.float32
        )
        standard_deviations = np.where(
            standard_deviations < 1e-8,
            1.0,
            standard_deviations,
        )
        demand_mean = float(train["demand_count"].mean())
        demand_std = float(train["demand_count"].std())
        if demand_std < 1e-8:
            demand_std = 1.0
        return cls(
            means=means,
            standard_deviations=standard_deviations,
            demand_mean=demand_mean,
            demand_std=demand_std,
        )

    def transform_features(self, values: np.ndarray) -> np.ndarray:
        return (values - self.means) / self.standard_deviations

    def transform_demand(self, values: np.ndarray) -> np.ndarray:
        return (values - self.demand_mean) / self.demand_std

    def inverse_demand(self, values: np.ndarray) -> np.ndarray:
        return values * self.demand_std + self.demand_mean

    def to_dict(self) -> dict[str, Any]:
        return {
            "means": self.means.tolist(),
            "standard_deviations": self.standard_deviations.tolist(),
            "demand_mean": self.demand_mean,
            "demand_std": self.demand_std,
        }


def build_windowed_datasets(
    frame: pd.DataFrame,
    config: DatasetConfig | None = None,
) -> tuple[dict[str, WindowedData], FeatureStandardizer]:
    """Build leakage-safe train, validation, and test windows."""

    config = config or DatasetConfig()
    config.validate()

    missing = sorted(set(FEATURE_COLUMNS + ["split", "event_timestamp"]) - set(frame.columns))
    if missing:
        raise ValueError(f"window input is missing columns: {missing}")

    standardizer = FeatureStandardizer.fit(frame, FEATURE_COLUMNS)
    result: dict[str, WindowedData] = {}
    interval = pd.Timedelta(minutes=30)

    for split in ("train", "validation", "test"):
        feature_batches: list[np.ndarray] = []
        target_batches: list[np.ndarray] = []
        origin_batches: list[np.datetime64] = []
        station_batches: list[str] = []
        stride = config.train_stride if split == "train" else 1

        for station_id, station_frame in frame.groupby(
            "station_id",
            sort=True,
            observed=True,
        ):
            ordered = station_frame.sort_values("event_timestamp").reset_index(
                drop=True
            )
            split_values = ordered["split"].to_numpy()
            feature_values = standardizer.transform_features(
                ordered[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
            )
            demand_values = ordered["demand_count"].to_numpy(dtype=np.float32)
            timestamps = ordered["event_timestamp"].to_numpy()

            for origin_index in range(
                config.input_length - 1,
                len(ordered) - config.horizon,
                stride,
            ):
                if split_values[origin_index] != split:
                    continue

                target_start = origin_index + 1
                target_end = origin_index + config.horizon + 1
                if not np.all(
                    split_values[target_start:target_end] == split
                ):
                    continue

                input_start = origin_index - config.input_length + 1
                input_end = origin_index + 1
                feature_batches.append(
                    feature_values[input_start:input_end]
                )
                target_batches.append(
                    standardizer.transform_demand(
                        demand_values[target_start:target_end]
                    )
                )
                origin_batches.append(timestamps[origin_index])
                station_batches.append(str(station_id))

        if not feature_batches:
            raise ValueError(f"no windows were generated for split: {split}")

        result[split] = WindowedData(
            features=np.stack(feature_batches).astype(np.float32),
            targets=np.stack(target_batches).astype(np.float32),
            origins=np.asarray(origin_batches, dtype="datetime64[ns]"),
            stations=np.asarray(station_batches, dtype=object),
        )

    return result, standardizer

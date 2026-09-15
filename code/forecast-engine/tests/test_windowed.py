import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from urbanflow_forecast.training.windowed import (  # noqa: E402
    DatasetConfig,
    build_windowed_datasets,
)


class WindowedDatasetTest(unittest.TestCase):
    def test_windows_do_not_cross_split_boundaries(self) -> None:
        rows = []
        for station_id in ("ST001", "ST002"):
            timestamps = pd.date_range(
                "2026-01-01",
                periods=230,
                freq="30min",
            )
            splits = ["train"] * 120 + ["validation"] * 50 + ["test"] * 60
            for index, timestamp in enumerate(timestamps):
                rows.append(
                    {
                        "station_id": station_id,
                        "event_timestamp": timestamp,
                        "demand_count": float(index),
                        "temperature": 20.0,
                        "precipitation": 0.0,
                        "is_holiday": 0,
                        "is_weekend": int(timestamp.weekday() >= 5),
                        "hour_sin": np.sin(index),
                        "hour_cos": np.cos(index),
                        "split": splits[index],
                    }
                )

        frame = pd.DataFrame(rows)
        datasets, standardizer = build_windowed_datasets(
            frame,
            DatasetConfig(
                input_length=20,
                horizon=6,
                train_stride=1,
            ),
        )

        self.assertEqual(datasets["train"].features.shape[1:], (20, 7))
        self.assertEqual(datasets["train"].targets.shape[1], 6)
        self.assertEqual(datasets["train"].features.shape[0], 190)
        self.assertEqual(datasets["validation"].features.shape[0], 88)
        self.assertEqual(datasets["test"].features.shape[0], 108)
        self.assertGreater(standardizer.demand_std, 0.0)


if __name__ == "__main__":
    unittest.main()

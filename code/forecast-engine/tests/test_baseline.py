import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from urbanflow_forecast.baselines import (  # noqa: E402
    add_seasonal_naive_prediction,
    build_multi_step_seasonal_naive,
)
from urbanflow_forecast.evaluation import calculate_metrics  # noqa: E402


class SeasonalNaiveTest(unittest.TestCase):
    def test_prediction_uses_target_from_previous_day(self) -> None:
        timestamps = pd.date_range("2026-01-01", periods=50, freq="30min")
        frame = pd.DataFrame(
            {
                "station_id": ["ST001"] * 50,
                "event_timestamp": timestamps,
                "target_next_30m": np.arange(50, dtype=float),
                "split": ["train"] * 50,
            }
        )

        result = add_seasonal_naive_prediction(frame, prediction_lag=48)

        self.assertEqual(result.iloc[0]["seasonal_naive_prediction"], 0.0)
        self.assertEqual(result.iloc[1]["seasonal_naive_prediction"], 1.0)
        self.assertEqual(result.iloc[0]["target_next_30m"], 48.0)

    def test_metrics(self) -> None:
        actual = pd.Series([1.0, 2.0, 3.0])
        predicted = pd.Series([1.0, 3.0, 3.0])

        metrics = calculate_metrics(actual, predicted)

        self.assertEqual(metrics["rows"], 3)
        self.assertAlmostEqual(metrics["mae"], 1.0 / 3.0)
        self.assertAlmostEqual(metrics["rmse"], (1.0 / 3.0) ** 0.5)

    def test_multi_step_prediction_uses_previous_day(self) -> None:
        timestamps = pd.date_range("2026-01-01", periods=220, freq="30min")
        frame = pd.DataFrame(
            {
                "station_id": ["ST001"] * 220,
                "event_timestamp": timestamps,
                "demand_count": np.arange(220, dtype=float),
                "split": ["train"] * 170 + ["test"] * 50,
            }
        )

        result = build_multi_step_seasonal_naive(
            frame,
            split="test",
            horizon=2,
            prediction_lag=48,
        )
        first = result[
            (result["origin_timestamp"] == timestamps[170])
            & (result["horizon_step"] == 1)
        ].iloc[0]

        self.assertEqual(first["target_next_30m"], 171.0)
        self.assertEqual(first["seasonal_naive_prediction"], 123.0)


if __name__ == "__main__":
    unittest.main()

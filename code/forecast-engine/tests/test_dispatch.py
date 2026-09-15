import sys
import unittest
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from urbanflow_forecast.dispatch import build_dispatch_plan  # noqa: E402


class DispatchTest(unittest.TestCase):
    def test_deficit_is_matched_to_nearest_surplus(self) -> None:
        stations = pd.DataFrame(
            [
                {
                    "station_id": "A",
                    "station_name": "缺车站",
                    "latitude": 31.0,
                    "longitude": 121.0,
                    "capacity": 50,
                    "available_bikes": 4,
                    "available_docks": 46,
                },
                {
                    "station_id": "B",
                    "station_name": "近盈余站",
                    "latitude": 31.01,
                    "longitude": 121.01,
                    "capacity": 50,
                    "available_bikes": 42,
                    "available_docks": 8,
                },
                {
                    "station_id": "C",
                    "station_name": "远盈余站",
                    "latitude": 31.10,
                    "longitude": 121.10,
                    "capacity": 50,
                    "available_bikes": 40,
                    "available_docks": 10,
                },
            ]
        )
        forecasts = pd.DataFrame(
            [
                {
                    "station_id": "A",
                    "target_time": pd.Timestamp("2026-04-01 00:00"),
                    "horizon_step": step,
                    "predicted_demand": 10,
                }
                for step in range(1, 5)
            ]
        )

        recommendations, summary = build_dispatch_plan(
            stations,
            forecasts,
            decision_horizon=4,
            safety_stock_ratio=0.10,
        )

        self.assertEqual(len(recommendations), 1)
        recommendation = recommendations.iloc[0]
        self.assertEqual(recommendation["from_station_id"], "B")
        self.assertEqual(recommendation["to_station_id"], "A")
        self.assertEqual(recommendation["recommended_quantity"], 40)
        self.assertIn("Expected ride orders", recommendation["reason"])
        self.assertIn("Target stock", recommendation["reason"])
        self.assertEqual(summary["total_shortage_before"], 40)
        self.assertEqual(summary["total_shortage_after"], 0)


if __name__ == "__main__":
    unittest.main()

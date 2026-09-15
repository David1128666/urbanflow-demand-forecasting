import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from app.services.dispatch_service import _priority_level
from app.services.forecast_service import _build_operation_summary


class BusinessSemanticsTest(unittest.TestCase):
    @patch(
        "app.services.forecast_service.get_latest_inventory",
        return_value=[
            {
                "station_name": "Demo · Transit Hub 001",
                "snapshot_time": datetime(2026, 3, 31, 23, 30),
                "available_bikes": 4,
                "available_docks": 46,
                "station_status": "empty",
                "station_status_label": "No bikes available",
            }
        ],
    )
    def test_forecast_operation_summary_explains_dispatch_need(
        self,
        _mock_inventory,
    ) -> None:
        points = []
        for step in range(1, 5):
            target_time = datetime(2026, 4, 1, 0, 0)
            points.append(
                {
                    "horizon_step": step,
                    "target_time": target_time,
                    "window_end": target_time,
                    "predicted_demand": Decimal("10.0"),
                }
            )

        summary = _build_operation_summary("ST001", points)

        self.assertIsNotNone(summary)
        self.assertEqual(summary["next_2h_orders"], 40.0)
        self.assertEqual(summary["safety_stock"], 4)
        self.assertEqual(summary["target_bikes"], 44)
        self.assertEqual(summary["recommended_replenishment"], 40)
        self.assertEqual(summary["operation_status"], "Dispatch now")
        self.assertIn("Move 40 bikes", summary["recommended_action"])

    def test_priority_labels_are_stable(self) -> None:
        self.assertEqual(_priority_level(30), "critical")
        self.assertEqual(_priority_level(20), "high")
        self.assertEqual(_priority_level(10), "medium")
        self.assertEqual(_priority_level(9.99), "low")


if __name__ == "__main__":
    unittest.main()

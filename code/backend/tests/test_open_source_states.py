import unittest
from unittest.mock import patch

from app.services.forecast_service import get_latest_forecasts
from app.services.model_service import get_model_metrics


class OpenSourceStateTest(unittest.TestCase):
    @patch("app.services.forecast_service.get_latest_run", return_value=None)
    def test_forecast_empty_state_has_stable_shape(self, _mock_run) -> None:
        payload = get_latest_forecasts("ST001")
        self.assertEqual(
            payload,
            {
                "run": None,
                "points": [],
                "operation_summary": None,
            },
        )

    @patch(
        "app.services.model_service._read_json",
        return_value=None,
    )
    def test_model_metrics_empty_state_has_stable_shape(
        self,
        _mock_read_json,
    ) -> None:
        payload = get_model_metrics()
        self.assertEqual(payload["models"], [])
        self.assertIsNone(payload["selection"])
        self.assertIsNone(payload["model_card"]["active_model"])


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch

from fastapi.responses import JSONResponse
from app.main import health


class HealthEndpointTest(unittest.TestCase):
    @patch(
        "app.main.get_health",
        return_value={
            "status": "ok",
            "version": "0.2.0",
            "database": {"status": "ok"},
            "data": {"status": "ready"},
        },
    )
    def test_health(self, _mock_health) -> None:
        response = health()
        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, 200)

    @patch(
        "app.main.get_health",
        return_value={
            "status": "unavailable",
            "version": "0.2.0",
            "database": {"status": "unavailable"},
            "data": {"status": "unknown"},
        },
    )
    def test_health_returns_503_when_database_is_unavailable(
        self,
        _mock_health,
    ) -> None:
        response = health()
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()

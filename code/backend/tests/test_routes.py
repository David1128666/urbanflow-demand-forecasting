import unittest
from unittest.mock import patch

from app.routers.dashboard import summary
from app.routers.demand import history
from app.routers.dispatch import dispatch_recommendations
from app.routers.forecasts import latest_forecasts
from app.routers.inventory import latest_inventory
from app.routers.models import metrics
from app.routers.stations import stations


class RouteLayerTest(unittest.TestCase):
    @patch("app.routers.stations.list_stations", return_value=[{"station_id": "ST001"}])
    def test_station_route(self, _) -> None:
        response = stations(city_id=None, limit=100, offset=0)
        self.assertEqual(response["code"], 200)
        self.assertEqual(response["data"][0]["station_id"], "ST001")

    @patch("app.routers.demand.get_demand_history", return_value=[])
    def test_demand_route(self, _) -> None:
        response = history(
            station_id="ST001",
            start_time=None,
            end_time=None,
            limit=100,
        )
        self.assertEqual(response["code"], 200)
        self.assertEqual(response["data"]["station_id"], "ST001")

    @patch(
        "app.routers.forecasts.get_latest_forecasts",
        return_value={"run": {"forecast_run_id": 1}, "points": []},
    )
    def test_forecast_route(self, _) -> None:
        response = latest_forecasts(station_id="ST001", limit=48)
        self.assertEqual(response["code"], 200)
        self.assertEqual(response["data"]["run"]["forecast_run_id"], 1)

    @patch("app.routers.models.get_model_metrics", return_value={"models": []})
    def test_model_route(self, _) -> None:
        response = metrics(include_horizons=False)
        self.assertEqual(response["code"], 200)

    @patch(
        "app.routers.dashboard.get_dashboard_summary",
        return_value={"station_count": 20},
    )
    def test_dashboard_route(self, _) -> None:
        response = summary()
        self.assertEqual(response["code"], 200)
        self.assertEqual(response["data"]["station_count"], 20)

    @patch(
        "app.routers.inventory.get_latest_inventory",
        return_value=[{"station_id": "ST001", "available_bikes": 10}],
    )
    def test_inventory_route(self, _) -> None:
        response = latest_inventory(station_id="ST001")
        self.assertEqual(response["code"], 200)
        self.assertEqual(response["data"][0]["available_bikes"], 10)

    @patch(
        "app.routers.dispatch.get_dispatch_recommendations",
        return_value=[{"recommendation_id": 1}],
    )
    def test_dispatch_route(self, _) -> None:
        response = dispatch_recommendations(limit=100)
        self.assertEqual(response["code"], 200)
        self.assertEqual(response["data"][0]["recommendation_id"], 1)


if __name__ == "__main__":
    unittest.main()

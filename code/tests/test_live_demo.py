import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "live_demo.py"
)
SPEC = importlib.util.spec_from_file_location("live_demo", SCRIPT_PATH)
LIVE_DEMO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = LIVE_DEMO
SPEC.loader.exec_module(LIVE_DEMO)


class LiveDemoTest(unittest.TestCase):
    def test_station_status_boundaries(self) -> None:
        self.assertEqual(LIVE_DEMO._station_status(5, 95, 100), "empty")
        self.assertEqual(LIVE_DEMO._station_status(20, 80, 100), "low")
        self.assertEqual(LIVE_DEMO._station_status(50, 50, 100), "normal")
        self.assertEqual(LIVE_DEMO._station_status(90, 10, 100), "full")

    def test_parser_defaults(self) -> None:
        args = LIVE_DEMO.build_parser().parse_args([])
        self.assertEqual(args.interval_seconds, 8)
        self.assertEqual(args.predict_every, 3)
        self.assertEqual(args.max_cycles, 0)


if __name__ == "__main__":
    unittest.main()

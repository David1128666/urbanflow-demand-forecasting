import sys
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from urbanflow_forecast import PREDICTION_LENGTH, __version__  # noqa: E402


class ForecastSkeletonTest(unittest.TestCase):
    def test_package_metadata(self) -> None:
        self.assertEqual(__version__, "0.1.0")
        self.assertEqual(PREDICTION_LENGTH, 48)


if __name__ == "__main__":
    unittest.main()

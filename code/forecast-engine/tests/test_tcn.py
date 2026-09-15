import importlib.util
import sys
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

TORCH_AVAILABLE = importlib.util.find_spec("torch") is not None

if TORCH_AVAILABLE:
    import torch

    from urbanflow_forecast.models import TCNRegressor  # noqa: E402


@unittest.skipUnless(TORCH_AVAILABLE, "optional torch dependency is not installed")
class TCNModelTest(unittest.TestCase):
    def test_output_shape(self) -> None:
        model = TCNRegressor(
            input_size=7,
            output_size=6,
            channels=(8, 16),
            use_seasonal_residual=False,
        )
        values = torch.randn(4, 20, 7)

        output = model(values)

        self.assertEqual(tuple(output.shape), (4, 6))


if __name__ == "__main__":
    unittest.main()

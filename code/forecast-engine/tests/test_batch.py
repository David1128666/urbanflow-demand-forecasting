import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from urbanflow_forecast.inference import (  # noqa: E402
    select_model,
)
from urbanflow_forecast.inference.batch import (  # noqa: E402
    build_seasonal_future_forecasts,
)


class BatchPredictionTest(unittest.TestCase):
    def test_seasonal_future_forecast(self) -> None:
        timestamps = pd.date_range("2026-01-01", periods=100, freq="30min")
        frame = pd.DataFrame(
            {
                "station_id": ["ST001"] * 100,
                "city_id": ["city-001"] * 100,
                "event_timestamp": timestamps,
                "demand_count": np.arange(100, dtype=float),
            }
        )

        result = build_seasonal_future_forecasts(frame)

        self.assertEqual(len(result), 48)
        self.assertEqual(result.iloc[0]["horizon_step"], 1)
        self.assertEqual(result.iloc[0]["predicted_demand"], 52.0)
        self.assertEqual(result.iloc[-1]["horizon_step"], 48)

    def test_model_selection_uses_validation_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_path = Path(temp_dir) / "baseline.json"
            tcn_path = Path(temp_dir) / "tcn.json"
            baseline_path.write_text(
                json.dumps(
                    {
                        "multi_step": {
                            "by_split": {
                                "validation": {
                                    "overall": {
                                        "mae": 2.0,
                                    }
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            tcn_path.write_text(
                json.dumps(
                    {
                        "by_split": {
                            "validation": {
                                "mae": 1.8,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            selected = select_model(
                baseline_path,
                tcn_path,
                minimum_improvement=0.05,
            )

            self.assertEqual(selected["selected_model"], "tcn")
            self.assertAlmostEqual(selected["tcn_improvement"], 0.10)

    def test_feature_loader_converts_spark_utc_time_to_local(self) -> None:
        from urbanflow_forecast.data import load_feature_dataset

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "features.parquet"
            pd.DataFrame(
                {
                    "station_id": ["ST001"],
                    "event_timestamp": [
                        pd.Timestamp("2026-01-01 00:00:00")
                    ],
                    "target_next_30m": [1.0],
                    "split": ["train"],
                }
            ).to_parquet(path, index=False)

            loaded = load_feature_dataset(path)

            self.assertEqual(
                loaded.iloc[0]["event_timestamp"],
                pd.Timestamp("2026-01-01 08:00:00"),
            )


if __name__ == "__main__":
    unittest.main()

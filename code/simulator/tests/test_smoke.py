import csv
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from simulator import SimulationConfig, __version__, generate_dataset  # noqa: E402


class SimulatorSkeletonTest(unittest.TestCase):
    def test_version(self) -> None:
        self.assertEqual(__version__, "0.1.0")

    def test_generates_expected_number_of_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = SimulationConfig(
                station_count=2,
                days=3,
                interval_minutes=30,
                seed=7,
                start_date=datetime(2026, 1, 1),
                output_dir=Path(temp_dir),
            )

            result = generate_dataset(config)

            self.assertEqual(result.station_count, 2)
            self.assertEqual(result.observation_count, 2 * 3 * 48)

            stations_path = result.output_dir / "stations.csv"
            inventory_path = result.output_dir / "station_snapshots.csv"
            observations_path = result.output_dir / "demand_observations.csv"
            manifest_path = result.manifest_path

            with stations_path.open(encoding="utf-8") as file:
                self.assertEqual(len(list(csv.DictReader(file))), 2)
            with inventory_path.open(encoding="utf-8") as file:
                self.assertEqual(len(list(csv.DictReader(file))), 2)

            with observations_path.open(encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2 * 3 * 48)
            self.assertTrue(all(int(row["demand_count"]) >= 0 for row in rows))
            self.assertEqual(len({row["event_id"] for row in rows}), len(rows))

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["observation_count"], len(rows))
            self.assertEqual(manifest["seed"], 7)

    def test_same_seed_creates_same_observation_hash(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            configs = [
                SimulationConfig(
                    station_count=2,
                    days=2,
                    seed=11,
                    start_date=datetime(2026, 1, 1),
                    output_dir=Path(first_dir),
                ),
                SimulationConfig(
                    station_count=2,
                    days=2,
                    seed=11,
                    start_date=datetime(2026, 1, 1),
                    output_dir=Path(second_dir),
                ),
            ]

            first = generate_dataset(configs[0])
            second = generate_dataset(configs[1])

            first_manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
            second_manifest = json.loads(second.manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(
                first_manifest["files"]["demand_observations.csv"]["sha256"],
                second_manifest["files"]["demand_observations.csv"]["sha256"],
            )


if __name__ == "__main__":
    unittest.main()

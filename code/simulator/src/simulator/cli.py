from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from simulator import __version__
from simulator.config import SimulationConfig
from simulator.generator import generate_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate reproducible UrbanFlow virtual city demand data."
    )
    parser.add_argument("--stations", type=int, default=20, help="Station count")
    parser.add_argument("--days", type=int, default=90, help="Number of days")
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=30,
        help="Minutes between demand observations",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--start-date",
        default="2026-01-01",
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--language",
        choices=("en", "zh-CN"),
        default="en",
        help="Language for generated demo names",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/virtual-v1"),
        help="Output directory",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = SimulationConfig(
        station_count=args.stations,
        days=args.days,
        interval_minutes=args.interval_minutes,
        seed=args.seed,
        start_date=datetime.fromisoformat(args.start_date),
        language=args.language,
        output_dir=args.output_dir,
    )
    result = generate_dataset(config)

    print(f"UrbanFlow simulator {__version__}")
    print(f"Output directory: {result.output_dir.resolve()}")
    print(f"Stations: {result.station_count}")
    print(f"Inventory snapshots: {result.inventory_snapshot_count}")
    print(f"Demand observations: {result.observation_count}")
    print(f"Holiday days: {result.holiday_count}")
    print(f"Anomalies: {result.anomaly_count}")
    print(f"Manifest: {result.manifest_path.resolve()}")
    print("Dataset generation complete")


if __name__ == "__main__":
    main()

"""Run the complete UrbanFlow demo pipeline from a checkout."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = CODE_ROOT.parent
DEFAULT_DATA_DIR = CODE_ROOT / "data"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate virtual data, build features, run baseline forecasting, "
            "persist results, and create dispatch recommendations."
        )
    )
    parser.add_argument("--stations", type=int, default=20)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start-date", default="2026-01-01")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
    )
    parser.add_argument(
        "--maven",
        default=os.getenv("MAVEN_COMMAND", "mvn"),
        help="Maven executable used for the Spark feature job.",
    )
    parser.add_argument("--train-tcn", action="store_true")
    parser.add_argument("--skip-schema", action="store_true")
    parser.add_argument("--skip-spark", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_env_file(CODE_ROOT / ".env")
    load_env_file(PROJECT_ROOT / ".env")

    data_dir = args.data_dir.resolve()
    virtual_dir = data_dir / "virtual-v1"
    feature_dir = data_dir / "features-v1"
    baseline_dir = data_dir / "baseline-v1"
    tcn_dir = data_dir / "tcn-v1"
    prediction_dir = data_dir / "predictions-v1"
    dispatch_dir = data_dir / "dispatch-v1"

    env = os.environ.copy()
    python_path = [
        str(CODE_ROOT / "simulator" / "src"),
        str(CODE_ROOT / "forecast-engine" / "src"),
    ]
    if env.get("PYTHONPATH"):
        python_path.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_path)

    mysql_args = [
        "--host",
        env.get("MYSQL_HOST", "127.0.0.1"),
        "--port",
        env.get("MYSQL_PORT", "3306"),
        "--user",
        env.get("MYSQL_USER", "urbanflow"),
        f"--password={env.get('MYSQL_PASSWORD', 'urbanflow_dev')}",
        "--database",
        env.get("MYSQL_DATABASE", "urbanflow"),
    ]

    steps: list[tuple[str, list[str]]] = []
    if not args.skip_schema:
        steps.append(
            (
                "Initialize MySQL schema",
                [
                    "mysql",
                    *mysql_args,
                    "--execute",
                    f"SOURCE {(CODE_ROOT / 'sql' / 'schema.sql').as_posix()};",
                ],
            )
        )
    steps.extend(
        [
            (
                "Generate virtual data",
                [
                    sys.executable,
                    "-m",
                    "simulator.cli",
                    "--stations",
                    str(args.stations),
                    "--days",
                    str(args.days),
                    "--seed",
                    str(args.seed),
                    "--start-date",
                    args.start_date,
                    "--language",
                    "en",
                    "--output-dir",
                    str(virtual_dir),
                ],
            ),
            (
                "Load virtual data into MySQL",
                [
                    sys.executable,
                    "-m",
                    "simulator.mysql_loader",
                    "--stations-path",
                    str(virtual_dir / "stations.csv"),
                    "--snapshots-path",
                    str(virtual_dir / "station_snapshots.csv"),
                    "--observations-path",
                    str(virtual_dir / "demand_observations.csv"),
                ],
            ),
        ]
    )
    if not args.skip_spark:
        steps.append(
            (
                "Build Spark SQL features",
                [
                    args.maven,
                    "-f",
                    str(CODE_ROOT / "offline-analysis" / "pom.xml"),
                    "exec:java",
                    (
                        "-Dexec.args="
                        f"--input-path {virtual_dir / 'demand_observations.csv'} "
                        f"--stations-path {virtual_dir / 'stations.csv'} "
                        f"--output-path {feature_dir}"
                    ),
                ],
            )
        )
    steps.append(
        (
            "Run Seasonal Naive baseline",
            [
                sys.executable,
                "-m",
                "urbanflow_forecast.cli",
                "baseline",
                "--features-path",
                str(feature_dir / "features.parquet"),
                "--output-dir",
                str(baseline_dir),
            ],
        )
    )
    if args.train_tcn:
        steps.append(
            (
                "Train TCN challenger",
                [
                    sys.executable,
                    "-m",
                    "urbanflow_forecast.cli",
                    "tcn",
                    "--features-path",
                    str(feature_dir / "features.parquet"),
                    "--baseline-metrics-path",
                    str(baseline_dir / "metrics.json"),
                    "--output-dir",
                    str(tcn_dir),
                    "--epochs",
                    "5",
                ],
            )
        )
    steps.extend(
        [
            (
                "Generate and persist forecasts",
                [
                    sys.executable,
                    "-m",
                    "urbanflow_forecast.cli",
                    "predict",
                    "--features-path",
                    str(feature_dir / "features.parquet"),
                    "--observations-path",
                    str(virtual_dir / "demand_observations.csv"),
                    "--baseline-metrics-path",
                    str(baseline_dir / "metrics.json"),
                    "--tcn-metrics-path",
                    str(tcn_dir / "metrics.json"),
                    "--output-dir",
                    str(prediction_dir),
                    "--write-mysql",
                ],
            ),
            (
                "Generate dispatch recommendations",
                [
                    sys.executable,
                    "-m",
                    "urbanflow_forecast.cli",
                    "dispatch",
                    "--output-dir",
                    str(dispatch_dir),
                    "--language",
                    "en",
                    "--write-mysql",
                ],
            ),
        ]
    )

    for index, (title, command) in enumerate(steps, start=1):
        print(f"\n[{index}/{len(steps)}] {title}")
        print(" ".join(command))
        if args.dry_run:
            continue
        subprocess.run(
            command,
            cwd=CODE_ROOT,
            env=env,
            check=True,
        )

    if args.dry_run:
        print("\nDry run complete.")
    else:
        print("\nUrbanFlow demo pipeline complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

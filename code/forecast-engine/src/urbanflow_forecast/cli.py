from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from urbanflow_forecast import PREDICTION_LENGTH, __version__
from urbanflow_forecast.baselines import run_seasonal_naive_baseline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="UrbanFlow forecast training and evaluation tools."
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("smoke", help="Show package metadata.")

    baseline = subparsers.add_parser(
        "baseline",
        help="Run the Seasonal Naive baseline.",
    )
    baseline.add_argument(
        "--features-path",
        type=Path,
        default=Path("data/features-v1/features.parquet"),
        help="Spark feature Parquet dataset.",
    )
    baseline.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/baseline-v1"),
        help="Baseline output directory.",
    )
    baseline.add_argument(
        "--prediction-lag",
        type=int,
        default=48,
        help="Seasonal lag in 30-minute steps.",
    )

    tcn = subparsers.add_parser(
        "tcn",
        help="Train and evaluate the PyTorch TCN.",
    )
    tcn.add_argument(
        "--features-path",
        type=Path,
        default=Path("data/features-v1/features.parquet"),
    )
    tcn.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/tcn-v1"),
    )
    tcn.add_argument(
        "--baseline-metrics-path",
        type=Path,
        default=Path("data/baseline-v1/metrics.json"),
    )
    tcn.add_argument("--input-length", type=int, default=96)
    tcn.add_argument("--horizon", type=int, default=48)
    tcn.add_argument("--epochs", type=int, default=5)
    tcn.add_argument("--batch-size", type=int, default=128)
    tcn.add_argument("--learning-rate", type=float, default=1e-3)
    tcn.add_argument("--train-stride", type=int, default=2)
    tcn.add_argument("--seed", type=int, default=42)

    predict = subparsers.add_parser(
        "predict",
        help="Generate future batch forecasts.",
    )
    predict.add_argument(
        "--features-path",
        type=Path,
        default=Path("data/features-v1/features.parquet"),
    )
    predict.add_argument(
        "--observations-path",
        type=Path,
        default=Path("data/virtual-v1/demand_observations.csv"),
    )
    predict.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/predictions-v1"),
    )
    predict.add_argument(
        "--baseline-metrics-path",
        type=Path,
        default=Path("data/baseline-v1/metrics.json"),
    )
    predict.add_argument(
        "--tcn-metrics-path",
        type=Path,
        default=Path("data/tcn-v1/metrics.json"),
    )
    predict.add_argument("--horizon", type=int, default=48)
    predict.add_argument("--prediction-lag", type=int, default=48)
    predict.add_argument("--minimum-improvement", type=float, default=0.05)
    predict.add_argument("--write-mysql", action="store_true")

    dispatch = subparsers.add_parser(
        "dispatch",
        help="Generate station dispatch recommendations.",
    )
    dispatch.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/dispatch-v1"),
    )
    dispatch.add_argument("--decision-horizon", type=int, default=4)
    dispatch.add_argument("--safety-stock-ratio", type=float, default=0.10)
    dispatch.add_argument(
        "--language",
        choices=("en", "zh-CN"),
        default=os.getenv("URBANFLOW_LANGUAGE", "en"),
        help="Language for generated action text.",
    )
    dispatch.add_argument("--write-mysql", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "smoke"):
        print(f"UrbanFlow forecast engine {__version__}")
        print(f"Prediction horizon: {PREDICTION_LENGTH} steps")
        print("Status: ready")
        return

    if args.command == "baseline":
        metrics = run_seasonal_naive_baseline(
            features_path=args.features_path,
            output_dir=args.output_dir,
            prediction_lag=args.prediction_lag,
        )
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return

    if args.command == "tcn":
        from urbanflow_forecast.training.tcn_trainer import (
            TCNTrainingConfig,
            train_tcn,
        )

        config = TCNTrainingConfig(
            input_length=args.input_length,
            horizon=args.horizon,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            train_stride=args.train_stride,
            seed=args.seed,
        )
        metrics = train_tcn(
            features_path=args.features_path,
            output_dir=args.output_dir,
            baseline_metrics_path=args.baseline_metrics_path,
            config=config,
        )
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return

    if args.command == "predict":
        from urbanflow_forecast.inference import (
            BatchPredictionConfig,
            run_batch_prediction,
        )

        config = BatchPredictionConfig(
            features_path=args.features_path,
            observations_path=args.observations_path,
            output_dir=args.output_dir,
            baseline_metrics_path=args.baseline_metrics_path,
            tcn_metrics_path=args.tcn_metrics_path,
            horizon=args.horizon,
            prediction_lag=args.prediction_lag,
            minimum_improvement=args.minimum_improvement,
            write_mysql=args.write_mysql,
        )
        result = run_batch_prediction(config)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "dispatch":
        from urbanflow_forecast.dispatch import (
            DispatchConfig,
            run_dispatch_recommendations,
        )

        result = run_dispatch_recommendations(
            DispatchConfig(
                output_dir=args.output_dir,
                decision_horizon=args.decision_horizon,
                safety_stock_ratio=args.safety_stock_ratio,
                language=args.language,
                write_mysql=args.write_mysql,
            )
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()

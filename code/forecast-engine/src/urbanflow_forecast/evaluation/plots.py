from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import pandas as pd


matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


def plot_seasonal_naive_results(
    one_step_predictions: pd.DataFrame,
    multi_step_metrics: dict[str, Any],
    output_dir: Path | str,
) -> tuple[Path, Path]:
    """Create prediction and horizon-error plots for the baseline."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    test_frame = one_step_predictions[
        one_step_predictions["split"] == "test"
    ].copy()
    station_id = sorted(test_frame["station_id"].unique())[0]
    station_frame = (
        test_frame[test_frame["station_id"] == station_id]
        .sort_values("event_timestamp")
        .head(200)
    )

    prediction_plot = output_path / "baseline_prediction.png"
    plt.figure(figsize=(12, 4.5))
    plt.plot(
        station_frame["event_timestamp"],
        station_frame["target_next_30m"],
        label="Actual",
        linewidth=1.8,
    )
    plt.plot(
        station_frame["event_timestamp"],
        station_frame["seasonal_naive_prediction"],
        label="Seasonal Naive",
        linewidth=1.5,
    )
    plt.title(f"Seasonal Naive Test Forecast: {station_id}")
    plt.xlabel("Time")
    plt.ylabel("Demand")
    plt.legend()
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(prediction_plot, dpi=150)
    plt.close()

    horizon_metrics = multi_step_metrics["by_horizon"]
    horizons = sorted(int(horizon) for horizon in horizon_metrics)
    mae_values = [horizon_metrics[horizon]["mae"] for horizon in horizons]

    horizon_plot = output_path / "baseline_error_by_horizon.png"
    plt.figure(figsize=(10, 4.5))
    plt.plot(horizons, mae_values, marker="o", linewidth=1.8)
    plt.title("Seasonal Naive MAE by Forecast Horizon")
    plt.xlabel("Horizon step (30 minutes)")
    plt.ylabel("MAE")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(horizon_plot, dpi=150)
    plt.close()

    return prediction_plot, horizon_plot

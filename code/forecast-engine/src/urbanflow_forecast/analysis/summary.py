from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
import pandas as pd


matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


def analyze_forecasts(
    forecasts: pd.DataFrame,
    output_dir: Path | str,
) -> dict[str, Any]:
    """Create station ranking, timeline, summary, and plots."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    station_ranking = (
        forecasts.groupby("station_id", observed=True)
        .agg(
            total_predicted_demand=("predicted_demand", "sum"),
            mean_predicted_demand=("predicted_demand", "mean"),
            peak_predicted_demand=("predicted_demand", "max"),
        )
        .reset_index()
        .sort_values("total_predicted_demand", ascending=False)
    )
    station_ranking["rank"] = range(1, len(station_ranking) + 1)
    station_ranking.to_csv(
        output_path / "station_forecast_ranking.csv",
        index=False,
    )

    timeline = (
        forecasts.groupby("target_time", observed=True)["predicted_demand"]
        .sum()
        .reset_index()
        .sort_values("target_time")
    )
    timeline.to_csv(
        output_path / "forecast_timeline.csv",
        index=False,
    )

    peak_row = timeline.loc[timeline["predicted_demand"].idxmax()]
    top_station = station_ranking.iloc[0]
    summary = {
        "station_count": int(forecasts["station_id"].nunique()),
        "forecast_horizon_steps": int(forecasts["horizon_step"].max()),
        "forecast_points": int(len(forecasts)),
        "total_predicted_demand": float(forecasts["predicted_demand"].sum()),
        "peak_target_time": pd.Timestamp(peak_row["target_time"]).isoformat(),
        "peak_aggregate_demand": float(peak_row["predicted_demand"]),
        "top_station_id": str(top_station["station_id"]),
        "top_station_total_demand": float(
            top_station["total_predicted_demand"]
        ),
    }
    (output_path / "analysis_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    top = station_ranking.head(10).sort_values("total_predicted_demand")
    plt.figure(figsize=(10, 5))
    plt.barh(top["station_id"], top["total_predicted_demand"])
    plt.title("Top Stations by Predicted 24-hour Demand")
    plt.xlabel("Predicted demand")
    plt.ylabel("Station")
    plt.tight_layout()
    plt.savefig(output_path / "station_ranking.png", dpi=150)
    plt.close()

    plt.figure(figsize=(12, 4.5))
    plt.plot(
        timeline["target_time"],
        timeline["predicted_demand"],
        linewidth=1.8,
    )
    plt.title("Aggregate Forecast Demand")
    plt.xlabel("Target time")
    plt.ylabel("Predicted demand")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output_path / "forecast_timeline.png", dpi=150)
    plt.close()

    return summary

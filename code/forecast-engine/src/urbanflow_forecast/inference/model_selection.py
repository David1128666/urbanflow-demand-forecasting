from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def select_model(
    baseline_metrics_path: Path | str,
    tcn_metrics_path: Path | str | None = None,
    minimum_improvement: float = 0.05,
) -> dict[str, Any]:
    """Select a production model using 48-step validation MAE."""

    baseline_path = Path(baseline_metrics_path)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_mae = float(
        baseline["multi_step"]["by_split"]["validation"]["overall"]["mae"]
    )

    tcn_improvement = None
    tcn_mae = None
    tcn_path = Path(tcn_metrics_path) if tcn_metrics_path else None
    if tcn_path is not None and tcn_path.is_file():
        tcn = json.loads(tcn_path.read_text(encoding="utf-8"))
        tcn_mae = float(tcn["by_split"]["validation"]["mae"])
        tcn_improvement = (baseline_mae - tcn_mae) / baseline_mae

    selected = "seasonal_naive"
    model_version = "seasonal-naive-v1"
    reason = "TCN validation metrics are unavailable"

    if tcn_improvement is not None:
        if tcn_improvement >= minimum_improvement:
            selected = "tcn"
            model_version = "tcn-v1"
            reason = (
                f"TCN validation MAE improves baseline by "
                f"{tcn_improvement * 100:.2f}%"
            )
        else:
            reason = (
                f"TCN improvement {tcn_improvement * 100:.2f}% is below "
                f"the required {minimum_improvement * 100:.2f}%"
            )

    return {
        "selected_model": selected,
        "model_version": model_version,
        "selection_split": "validation",
        "selection_metric": "multi_step_mae",
        "minimum_improvement": minimum_improvement,
        "baseline_mae": baseline_mae,
        "tcn_mae": tcn_mae,
        "tcn_improvement": tcn_improvement,
        "reason": reason,
    }

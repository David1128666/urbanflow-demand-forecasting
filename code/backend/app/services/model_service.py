import json
from datetime import datetime
from pathlib import Path

from app.config import DATA_DIR


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_model_metrics(include_horizons: bool = False) -> list[dict]:
    baseline = _read_json(DATA_DIR / "baseline-v1" / "metrics.json")
    tcn = _read_json(DATA_DIR / "tcn-v1" / "metrics.json")
    selection = _read_json(DATA_DIR / "predictions-v1" / "batch_manifest.json")

    results: list[dict] = []
    if baseline:
        results.append(
            {
                "model": "seasonal_naive",
                "version": "seasonal-naive-v1",
                "validation": baseline["multi_step"]["by_split"]["validation"][
                    "overall"
                ],
                "test": baseline["multi_step"]["by_split"]["test"]["overall"],
                "by_horizon": (
                    baseline["multi_step"]["by_split"]["test"]["by_horizon"]
                    if include_horizons
                    else None
                ),
            }
        )
    if tcn:
        results.append(
            {
                "model": "tcn",
                "version": "tcn-v1",
                "validation": tcn["by_split"]["validation"],
                "test": tcn["test_overall"],
                "by_horizon": tcn["test_by_horizon"] if include_horizons else None,
            }
        )

    selection_payload = (
        selection.get("model_selection") if selection else None
    )
    model_card = _build_model_card(
        selection=selection_payload,
        batch_manifest=selection,
        baseline_path=DATA_DIR / "baseline-v1" / "metrics.json",
        tcn_path=DATA_DIR / "tcn-v1" / "metrics.json",
    )
    return {
        "selection": selection_payload,
        "model_card": model_card,
        "models": results,
    }


def _build_model_card(
    selection: dict | None,
    batch_manifest: dict | None,
    baseline_path: Path,
    tcn_path: Path,
) -> dict:
    selected_model = selection.get("selected_model") if selection else None
    selected_version = selection.get("model_version") if selection else None
    if selected_model == "tcn":
        model_type = "Temporal Convolutional Network (deep learning)"
    elif selected_model == "seasonal_naive":
        model_type = "Seasonal Naive (statistical baseline)"
    else:
        model_type = "Unavailable"

    forecast_start = (
        batch_manifest.get("forecast_start") if batch_manifest else None
    )
    forecast_end = (
        batch_manifest.get("forecast_end") if batch_manifest else None
    )
    return {
        "active_model": selected_model,
        "model_version": selected_version,
        "model_type": model_type,
        "selection_rule": (
            "Choose the model with the lowest 48-step validation MAE. "
            "A challenger must improve the baseline by at least 5%."
        ),
        "selection_reason": selection.get("reason") if selection else None,
        "baseline_validation_mae": (
            selection.get("baseline_mae") if selection else None
        ),
        "challenger_validation_mae": (
            selection.get("tcn_mae") if selection else None
        ),
        "challenger_improvement_pct": (
            round(selection.get("tcn_improvement") * 100, 2)
            if selection and selection.get("tcn_improvement") is not None
            else None
        ),
        "minimum_improvement_pct": (
            round(selection.get("minimum_improvement") * 100, 2)
            if selection and selection.get("minimum_improvement") is not None
            else None
        ),
        "forecast_start": forecast_start,
        "forecast_end": forecast_end,
        "baseline_artifact_updated_at": _artifact_time(baseline_path),
        "challenger_artifact_updated_at": _artifact_time(tcn_path),
        "data_mode": "virtual demo data",
        "limitations": [
            "The current production model is selected from synthetic data.",
            "The TCN is a challenger and is promoted only if it passes the "
            "minimum improvement threshold.",
            "Point forecasts are shown without prediction intervals.",
        ],
    }


def _artifact_time(path: Path) -> str | None:
    if not path.is_file():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat()

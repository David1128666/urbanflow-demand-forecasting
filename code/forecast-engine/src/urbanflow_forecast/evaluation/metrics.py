from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def calculate_metrics(
    actual: pd.Series,
    predicted: pd.Series,
) -> dict[str, float | int]:
    """Calculate common point-forecast metrics."""

    actual_values = actual.to_numpy(dtype=float)
    predicted_values = predicted.to_numpy(dtype=float)

    if len(actual_values) != len(predicted_values):
        raise ValueError("actual and predicted series must have equal length")
    if len(actual_values) == 0:
        raise ValueError("metric input cannot be empty")

    errors = actual_values - predicted_values
    absolute_errors = np.abs(errors)
    denominator = np.abs(actual_values) + np.abs(predicted_values) + 1e-8
    smape_values = 2.0 * absolute_errors / denominator

    return {
        "rows": int(len(actual_values)),
        "mae": float(np.mean(absolute_errors)),
        "rmse": float(math.sqrt(np.mean(errors**2))),
        "smape": float(np.mean(smape_values) * 100.0),
        "mean_actual": float(np.mean(actual_values)),
        "mean_predicted": float(np.mean(predicted_values)),
    }


def evaluate_predictions(
    predictions: pd.DataFrame,
    actual_column: str = "target_next_30m",
    prediction_column: str = "seasonal_naive_prediction",
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Calculate metrics overall, by split, and by station."""

    if actual_column not in predictions.columns:
        raise ValueError(f"missing actual column: {actual_column}")
    if prediction_column not in predictions.columns:
        raise ValueError(f"missing prediction column: {prediction_column}")

    overall = calculate_metrics(
        predictions[actual_column],
        predictions[prediction_column],
    )

    by_split: dict[str, dict[str, float | int]] = {}
    for split, frame in predictions.groupby(
        "split",
        sort=True,
        observed=True,
    ):
        by_split[str(split)] = calculate_metrics(
            frame[actual_column],
            frame[prediction_column],
        )

    station_rows: list[dict[str, Any]] = []
    for (split, station_id), frame in predictions.groupby(
        ["split", "station_id"],
        sort=True,
        observed=True,
    ):
        row = {
            "split": split,
            "station_id": station_id,
        }
        row.update(
            calculate_metrics(
                frame[actual_column],
                frame[prediction_column],
            )
        )
        station_rows.append(row)

    by_station = pd.DataFrame(station_rows)
    return {
        "overall": overall,
        "by_split": by_split,
    }, by_station

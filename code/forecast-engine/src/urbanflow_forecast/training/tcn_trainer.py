from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from urbanflow_forecast.data import load_feature_dataset
from urbanflow_forecast.evaluation import calculate_metrics
from urbanflow_forecast.models import TCNRegressor
from urbanflow_forecast.training.windowed import (
    DatasetConfig,
    FeatureStandardizer,
    WindowedData,
    build_windowed_datasets,
)


matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402


@dataclass(frozen=True)
class TCNTrainingConfig:
    input_length: int = 96
    horizon: int = 48
    channels: tuple[int, ...] = (16, 32)
    kernel_size: int = 3
    dropout: float = 0.1
    batch_size: int = 128
    epochs: int = 5
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    early_stopping_patience: int = 2
    train_stride: int = 2
    seed: int = 42
    use_seasonal_residual: bool = True

    def dataset_config(self) -> DatasetConfig:
        return DatasetConfig(
            input_length=self.input_length,
            horizon=self.horizon,
            train_stride=self.train_stride,
        )


def train_tcn(
    features_path: Path | str,
    output_dir: Path | str,
    baseline_metrics_path: Path | str | None = None,
    config: TCNTrainingConfig | None = None,
) -> dict[str, Any]:
    """Train and evaluate the TCN on the Spark feature dataset."""

    config = config or TCNTrainingConfig()
    _set_seed(config.seed)
    _limit_torch_threads()

    frame = load_feature_dataset(features_path)
    windowed, standardizer = build_windowed_datasets(
        frame,
        config.dataset_config(),
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = TCNRegressor(
        input_size=windowed["train"].features.shape[2],
        output_size=config.horizon,
        channels=config.channels,
        kernel_size=config.kernel_size,
        dropout=config.dropout,
        use_seasonal_residual=config.use_seasonal_residual,
        seasonal_lag=config.horizon,
    ).to(device)

    train_loader = _make_loader(
        windowed["train"],
        batch_size=config.batch_size,
        shuffle=True,
    )
    validation_loader = _make_loader(
        windowed["validation"],
        batch_size=config.batch_size,
        shuffle=False,
    )
    test_loader = _make_loader(
        windowed["test"],
        batch_size=config.batch_size,
        shuffle=False,
    )

    criterion = nn.HuberLoss(delta=1.0)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=1,
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    model_path = output_path / "model.pt"

    best_validation_loss, _ = _prediction_loss(
        model,
        validation_loader,
        criterion,
        device,
    )
    best_state: dict[str, torch.Tensor] = {
        key: value.detach().cpu().clone()
        for key, value in model.state_dict().items()
    }
    epochs_without_improvement = 0
    history: list[dict[str, float | int]] = []

    for epoch in range(1, config.epochs + 1):
        train_loss = _training_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device,
        )
        validation_loss, validation_predictions = _prediction_loss(
            model,
            validation_loader,
            criterion,
            device,
        )
        validation_actual = _inverse_demand(
            windowed["validation"].targets,
            standardizer,
        )
        validation_predicted = _inverse_demand(
            validation_predictions,
            standardizer,
        )
        validation_metrics = calculate_metrics(
            pd.Series(validation_actual.reshape(-1)),
            pd.Series(validation_predicted.reshape(-1)),
        )
        scheduler.step(validation_loss)

        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "validation_loss": validation_loss,
                "validation_mae": validation_metrics["mae"],
                "validation_rmse": validation_metrics["rmse"],
                "validation_smape": validation_metrics["smape"],
                "learning_rate": optimizer.param_groups[0]["lr"],
            }
        )
        print(
            f"[TCN] epoch={epoch} train_loss={train_loss:.5f} "
            f"val_loss={validation_loss:.5f} "
            f"val_mae={validation_metrics['mae']:.5f}"
        )

        if validation_loss < best_validation_loss - 1e-6:
            best_validation_loss = validation_loss
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= config.early_stopping_patience:
                print(f"[TCN] early stopping at epoch {epoch}")
                break

    if best_state is None:
        raise RuntimeError("TCN training did not produce a best model")

    model.load_state_dict(best_state)
    torch.save(
        {
            "state_dict": best_state,
            "config": asdict(config),
            "standardizer": standardizer.to_dict(),
        },
        model_path,
    )

    validation_scaled = _predict(model, validation_loader, device)
    test_scaled = _predict(model, test_loader, device)
    predictions = pd.concat(
        [
            _prediction_frame(
                "validation",
                windowed["validation"],
                validation_scaled,
                standardizer,
            ),
            _prediction_frame(
                "test",
                windowed["test"],
                test_scaled,
                standardizer,
            ),
        ],
        ignore_index=True,
    )

    metrics, metrics_by_station = _build_metrics(predictions)
    baseline_comparison = _compare_with_baseline(
        metrics,
        baseline_metrics_path,
        predictions,
    )
    if baseline_comparison:
        metrics["baseline_comparison"] = baseline_comparison

    history_frame = pd.DataFrame(history)
    history_frame.to_csv(
        output_path / "training_history.csv",
        index=False,
    )
    predictions.to_parquet(
        output_path / "predictions.parquet",
        index=False,
    )
    predictions.to_csv(
        output_path / "predictions.csv",
        index=False,
    )
    (output_path / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_path / "config.json").write_text(
        json.dumps(
            {
                **asdict(config),
                "device": str(device),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    horizon_rows = []
    for horizon, values in metrics["by_horizon"].items():
        horizon_rows.append({"horizon_step": horizon, **values})
    pd.DataFrame(horizon_rows).to_csv(
        output_path / "metrics_by_horizon.csv",
        index=False,
    )
    metrics_by_station.to_csv(
        output_path / "metrics_by_station.csv",
        index=False,
    )

    _plot_training(
        history_frame,
        predictions,
        metrics,
        baseline_comparison,
        output_path,
    )

    return metrics


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _limit_torch_threads() -> None:
    cpu_count = os.cpu_count() or 1
    torch.set_num_threads(min(8, cpu_count))


def _make_loader(
    data: WindowedData,
    batch_size: int,
    shuffle: bool,
) -> DataLoader:
    dataset = TensorDataset(
        torch.from_numpy(data.features),
        torch.from_numpy(data.targets),
    )
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )


def _training_epoch(
    model: TCNRegressor,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    total_rows = 0

    for features, targets in loader:
        features = features.to(device)
        targets = targets.to(device)

        optimizer.zero_grad(set_to_none=True)
        predictions = model(features)
        loss = criterion(predictions, targets)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        batch_rows = len(features)
        total_loss += float(loss.item()) * batch_rows
        total_rows += batch_rows

    return total_loss / total_rows


def _prediction_loss(
    model: TCNRegressor,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, np.ndarray]:
    model.eval()
    total_loss = 0.0
    total_rows = 0
    batches: list[np.ndarray] = []

    with torch.no_grad():
        for features, targets in loader:
            features = features.to(device)
            targets = targets.to(device)
            predictions = model(features)
            loss = criterion(predictions, targets)

            batch_rows = len(features)
            total_loss += float(loss.item()) * batch_rows
            total_rows += batch_rows
            batches.append(predictions.detach().cpu().numpy())

    return total_loss / total_rows, np.concatenate(batches, axis=0)


def _predict(
    model: TCNRegressor,
    loader: DataLoader,
    device: torch.device,
) -> np.ndarray:
    model.eval()
    batches: list[np.ndarray] = []
    with torch.no_grad():
        for features, _ in loader:
            predictions = model(features.to(device))
            batches.append(predictions.detach().cpu().numpy())
    return np.concatenate(batches, axis=0)


def _inverse_demand(
    values: np.ndarray,
    standardizer: FeatureStandardizer,
) -> np.ndarray:
    return standardizer.inverse_demand(values)


def _prediction_frame(
    split: str,
    data: WindowedData,
    predictions_scaled: np.ndarray,
    standardizer: FeatureStandardizer,
) -> pd.DataFrame:
    actual = _inverse_demand(data.targets, standardizer)
    predicted = _inverse_demand(predictions_scaled, standardizer)

    sample_count, horizon = actual.shape
    origins = pd.to_datetime(data.origins)
    stations = np.repeat(data.stations, horizon)
    horizons = np.tile(np.arange(1, horizon + 1), sample_count)
    origin_values = np.repeat(origins, horizon)
    target_values = origin_values + pd.to_timedelta(
        30 * horizons,
        unit="m",
    )

    return pd.DataFrame(
        {
            "split": split,
            "station_id": stations,
            "origin_timestamp": origin_values,
            "target_timestamp": target_values,
            "horizon_step": horizons,
            "target_next_30m": actual.reshape(-1),
            "tcn_prediction": predicted.reshape(-1),
        }
    ).assign(
        absolute_error=lambda frame: (
            frame["target_next_30m"] - frame["tcn_prediction"]
        ).abs()
    )


def _build_metrics(
    predictions: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    def evaluate(frame: pd.DataFrame) -> dict[str, float | int]:
        return calculate_metrics(
            frame["target_next_30m"],
            frame["tcn_prediction"],
        )

    by_split = {}
    for split, frame in predictions.groupby(
        "split",
        sort=True,
        observed=True,
    ):
        by_split[str(split)] = evaluate(frame)

    test = predictions[predictions["split"] == "test"]
    by_horizon = {}
    for horizon, frame in test.groupby(
        "horizon_step",
        sort=True,
        observed=True,
    ):
        by_horizon[int(horizon)] = evaluate(frame)

    station_rows = []
    for (station_id, horizon), frame in test.groupby(
        ["station_id", "horizon_step"],
        sort=True,
        observed=True,
    ):
        station_rows.append(
            {
                "station_id": station_id,
                "horizon_step": int(horizon),
                **evaluate(frame),
            }
        )

    return (
        {
            "model": "tcn",
            "by_split": by_split,
            "test_overall": evaluate(test),
            "test_by_horizon": by_horizon,
            "by_horizon": by_horizon,
        },
        pd.DataFrame(station_rows),
    )


def _compare_with_baseline(
    metrics: dict[str, Any],
    baseline_metrics_path: Path | str | None,
    tcn_predictions: pd.DataFrame,
) -> dict[str, Any] | None:
    if baseline_metrics_path is None:
        default_path = Path("data/baseline-v1/metrics.json")
        baseline_metrics_path = default_path if default_path.is_file() else None
    if baseline_metrics_path is None:
        return None

    baseline = json.loads(
        Path(baseline_metrics_path).read_text(encoding="utf-8")
    )
    baseline_predictions_path = (
        Path(baseline_metrics_path).parent / "predictions_48step.parquet"
    )
    if baseline_predictions_path.is_file():
        baseline_predictions = pd.read_parquet(baseline_predictions_path)
        keys = [
            "station_id",
            "origin_timestamp",
            "target_timestamp",
            "horizon_step",
        ]
        paired = (
            tcn_predictions[tcn_predictions["split"] == "test"]
            .merge(
                baseline_predictions[
                    keys
                    + [
                        "target_next_30m",
                        "seasonal_naive_prediction",
                    ]
                ].rename(
                    columns={
                        "target_next_30m": "baseline_actual",
                        "seasonal_naive_prediction": "baseline_prediction",
                    }
                ),
                on=keys,
                how="inner",
            )
        )
        tcn_overall = calculate_metrics(
            paired["target_next_30m"],
            paired["tcn_prediction"],
        )
        baseline_overall = calculate_metrics(
            paired["baseline_actual"],
            paired["baseline_prediction"],
        )
        paired_tcn_by_horizon = {
            int(horizon): calculate_metrics(
                frame["target_next_30m"],
                frame["tcn_prediction"],
            )
            for horizon, frame in paired.groupby(
                "horizon_step",
                sort=True,
                observed=True,
            )
        }
        paired_baseline_by_horizon = {
            int(horizon): calculate_metrics(
                frame["baseline_actual"],
                frame["baseline_prediction"],
            )
            for horizon, frame in paired.groupby(
                "horizon_step",
                sort=True,
                observed=True,
            )
        }
    else:
        baseline_overall = baseline["multi_step"]["overall"]
        tcn_overall = metrics["test_overall"]
        paired_tcn_by_horizon = metrics["test_by_horizon"]
        paired_baseline_by_horizon = baseline["multi_step"]["by_horizon"]

    horizon_comparison = []
    for horizon, tcn_values in paired_tcn_by_horizon.items():
        baseline_values = paired_baseline_by_horizon[horizon]
        horizon_comparison.append(
            {
                "horizon_step": horizon,
                "tcn_mae": tcn_values["mae"],
                "baseline_mae": baseline_values["mae"],
                "mae_improvement_pct": (
                    (baseline_values["mae"] - tcn_values["mae"])
                    / baseline_values["mae"]
                    * 100.0
                ),
            }
        )

    def improvement(metric: str) -> float:
        return (
            (baseline_overall[metric] - tcn_overall[metric])
            / baseline_overall[metric]
            * 100.0
        )

    return {
        "baseline_model": baseline.get("model", "seasonal_naive"),
        "comparison_scope": (
            "paired_test_rows"
            if baseline_predictions_path.is_file()
            else "reported_test_rows"
        ),
        "tcn_test": tcn_overall,
        "baseline_test": baseline_overall,
        "mae_improvement_pct": improvement("mae"),
        "rmse_improvement_pct": improvement("rmse"),
        "smape_improvement_pct": improvement("smape"),
        "by_horizon": horizon_comparison,
    }


def _plot_training(
    history: pd.DataFrame,
    predictions: pd.DataFrame,
    metrics: dict[str, Any],
    baseline_comparison: dict[str, Any] | None,
    output_dir: Path,
) -> None:
    plt.figure(figsize=(9, 4.5))
    plt.plot(history["epoch"], history["train_loss"], label="Train")
    plt.plot(
        history["epoch"],
        history["validation_loss"],
        label="Validation",
    )
    plt.title("TCN Training Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Huber Loss")
    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "training_loss.png", dpi=150)
    plt.close()

    test = predictions[predictions["split"] == "test"].copy()
    station_id = sorted(test["station_id"].unique())[0]
    sample = (
        test[
            (test["station_id"] == station_id)
            & (test["horizon_step"] == 1)
        ]
        .sort_values("target_timestamp")
        .head(200)
    )
    plt.figure(figsize=(12, 4.5))
    plt.plot(
        sample["target_timestamp"],
        sample["target_next_30m"],
        label="Actual",
        linewidth=1.8,
    )
    plt.plot(
        sample["target_timestamp"],
        sample["tcn_prediction"],
        label="TCN",
        linewidth=1.5,
    )
    plt.title(f"TCN Test Forecast: {station_id}")
    plt.xlabel("Time")
    plt.ylabel("Demand")
    plt.legend()
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(output_dir / "tcn_prediction.png", dpi=150)
    plt.close()

    if baseline_comparison is not None:
        comparison = pd.DataFrame(baseline_comparison["by_horizon"])
        plt.figure(figsize=(10, 4.5))
        plt.plot(
            comparison["horizon_step"],
            comparison["tcn_mae"],
            marker="o",
            label="TCN",
        )
        plt.plot(
            comparison["horizon_step"],
            comparison["baseline_mae"],
            marker="o",
            label="Seasonal Naive",
        )
        plt.title("MAE by Forecast Horizon")
        plt.xlabel("Horizon step (30 minutes)")
        plt.ylabel("MAE")
        plt.grid(alpha=0.25)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "model_comparison.png", dpi=150)
        plt.close()

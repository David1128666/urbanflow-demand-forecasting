# Forecast Engine

> **中文摘要：** 本模块负责 Seasonal Naive 基线、PyTorch TCN 训练与评估、
> 48 步批量预测、模型选择，以及站点调运建议生成。

Python package for baseline models, PyTorch TCN training, evaluation, and batch
inference.

## Seasonal Naive baseline

The baseline predicts each target from the same seasonal position one day
earlier:

```text
prediction(t + 30 minutes) = demand(t + 30 minutes - 24 hours)
```

Run:

```powershell
cd code
$env:PYTHONPATH="forecast-engine\src"
python -m urbanflow_forecast.cli baseline `
  --features-path data\features-v1\features.parquet `
  --output-dir data\baseline-v1
```

Outputs:

```text
data/baseline-v1/predictions.parquet
data/baseline-v1/predictions.csv
data/baseline-v1/metrics.json
data/baseline-v1/metrics_by_split.csv
data/baseline-v1/metrics_by_station.csv
data/baseline-v1/predictions_48step.parquet
data/baseline-v1/predictions_48step.csv
data/baseline-v1/metrics_by_horizon.csv
data/baseline-v1/baseline_prediction.png
data/baseline-v1/baseline_error_by_horizon.png
```

`metrics.json` contains one-step metrics by split and 48-step rolling forecast
metrics by horizon.

## PyTorch TCN

Install the optional deep-learning dependency:

```powershell
cd code
python -m pip install -e "forecast-engine[deep]"
```

Train and evaluate the TCN:

```powershell
cd code
urbanflow-forecast tcn `
  --features-path data\features-v1\features.parquet `
  --baseline-metrics-path data\baseline-v1\metrics.json `
  --output-dir data\tcn-v1 `
  --epochs 5 `
  --input-length 96 `
  --horizon 48
```

Outputs:

```text
data/tcn-v1/model.pt
data/tcn-v1/config.json
data/tcn-v1/metrics.json
data/tcn-v1/training_history.csv
data/tcn-v1/predictions.parquet
data/tcn-v1/predictions.csv
data/tcn-v1/metrics_by_horizon.csv
data/tcn-v1/metrics_by_station.csv
data/tcn-v1/training_loss.png
data/tcn-v1/tcn_prediction.png
data/tcn-v1/model_comparison.png
```

## Future batch prediction

```powershell
cd code
urbanflow-forecast predict `
  --features-path data\features-v1\features.parquet `
  --observations-path data\virtual-v1\demand_observations.csv `
  --baseline-metrics-path data\baseline-v1\metrics.json `
  --tcn-metrics-path data\tcn-v1\metrics.json `
  --output-dir data\predictions-v1 `
  --write-mysql
```

The selection rule uses 48-step validation MAE. TCN must improve Seasonal Naive
by at least 5% before it is selected. Otherwise Seasonal Naive is used.

## Dispatch recommendations

```powershell
cd code
urbanflow-forecast dispatch --language en --write-mysql
```

The dispatch engine uses the next 2 hours of predicted orders, current station
inventory, a safety stock, and geographic distance to generate concrete
station-to-station vehicle movements and a shortage-reduction simulation.

Use `--language zh-CN` to preserve the Chinese action-text option.

# Simulator

> **中文摘要：** 本模块生成可复现的虚拟城市需求数据，包含早晚高峰、工作日、
> 周末、天气、节假日、随机噪声和异常记录，也可以把事件发送到 Kafka。

The simulator generates reproducible synthetic city demand data with station
profiles, morning and evening peaks, weekday and weekend effects, weather,
holidays, random noise, and anomalies.

Generate the default 90-day dataset:

```powershell
cd code
$env:PYTHONPATH="simulator\src"
python -m simulator.cli
```

Generated demo names are English by default. Use `--language zh-CN` to generate
the preserved Chinese demo names.

Generate a smaller dataset:

```powershell
cd code
$env:PYTHONPATH="simulator\src"
python -m simulator.cli `
  --stations 5 `
  --days 7 `
  --output-dir data\smoke-v1
```

Outputs:

```text
stations.csv
station_snapshots.csv
demand_observations.csv
demand_observations.jsonl
generation_manifest.json
```

The same seed, date range, and configuration produce the same data files.

## Send events to Kafka

Install the simulator package and its Kafka dependency:

```powershell
cd code
python -m pip install -e simulator
```

Validate the JSONL file without connecting to Kafka:

```powershell
cd code
$env:PYTHONPATH="simulator\src"
python -m simulator.producer --limit 100 --dry-run
```

Send events to Kafka:

```powershell
cd code
$env:PYTHONPATH="simulator\src"
python -m simulator.producer `
  --input data\virtual-v1\demand_observations.jsonl `
  --bootstrap-servers node1:9092 `
  --topic urbanflow-demand-events `
  --limit 1000 `
  --cycles 1 `
  --rate 100
```

The station ID is used as the Kafka message key, so events for the same station
stay in the same partition while the partition count remains unchanged.

Set `--cycles 0` to keep sending in a loop. Press `Ctrl+C` to stop and flush the
producer gracefully.

## Load generated data into MySQL

```powershell
cd code
urbanflow-load-mysql `
  --stations-path data\virtual-v1\stations.csv `
  --snapshots-path data\virtual-v1\station_snapshots.csv `
  --observations-path data\virtual-v1\demand_observations.csv `
  --batch-size 1000
```

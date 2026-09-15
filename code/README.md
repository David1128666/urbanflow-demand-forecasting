# UrbanFlow Implementation

> **中文摘要：** 本目录包含 UrbanFlow 的完整代码实现，包括虚拟数据、Kafka、
> Spark 实时与离线处理、预测模型、MySQL、FastAPI、Vue 页面和调度逻辑。

This directory contains the implementation of the UrbanFlow MVP.

The runnable MVP currently covers virtual data generation, Kafka ingestion,
Spark streaming aggregation, offline features, time-series models, batch
forecasting, MySQL persistence, FastAPI APIs, and a Vue operations dashboard.

The dashboard now includes station inventory, short-term deficits, executable
transfer recommendations, and a clearly labelled simulation of the expected
impact. All current results use virtual data and are not real operating
benefits.

## Modules

| Directory | Purpose | Current status |
|---|---|---|
| `common` | Shared Scala configuration and models | Implemented |
| `realtime-analysis` | Spark Structured Streaming application | Implemented |
| `offline-analysis` | Spark SQL feature application | Implemented |
| `forecast-engine` | Forecast, evaluation, and dispatch engine | Implemented |
| `backend` | FastAPI service for demand, models, inventory, and dispatch | Implemented |
| `simulator` | Reproducible virtual data generator | Implemented |
| `frontend` | Vue 3 operations dashboard | Implemented |
| `sql` | MySQL schema | Implemented |
| `docker` | Local MySQL and Kafka environment | Optional |
| `tests` | Cross-module documentation and smoke tests | In progress |

## Main business flow

```text
Virtual ride orders
  -> Kafka
  -> Spark 30-minute windows
  -> MySQL demand history
  -> Spark SQL features
  -> Seasonal Naive / TCN forecast
  -> station inventory and vehicle deficit
  -> transfer work orders
  -> FastAPI
  -> Vue operations dashboard
```

The key business definition is:

```text
Demand = expected ride orders in one 30-minute window.
Deficit = target bikes - currently available bikes.
```

Target bikes are based on the next two hours of forecast demand plus a safety
stock. A recommendation answers where to move bikes, how many to move, and the
deadline.

## Verify the implementation

Run the complete local demo pipeline:

```bash
python scripts/run_demo.py --dry-run
python scripts/run_demo.py
```

Use `--train-tcn` to train the optional neural challenger.

Run the continuous local live demo:

```bash
python scripts/live_demo.py --interval-seconds 10 --predict-every 3
```

The live demo keeps adding virtual demand windows and refreshes inventory,
forecasts, and dispatch recommendations without requiring Kafka.

### Scala modules

```powershell
& "E:\IDEA\IntelliJ IDEA Community Edition 2024.3.5\plugins\maven\lib\maven3\bin\mvn.cmd" -f pom.xml test
```

### Python modules

```powershell
python -m unittest discover -s backend\tests -v
python -m unittest discover -s forecast-engine\tests -v
python -m unittest discover -s simulator\tests -v
```

Generate the default virtual dataset:

```powershell
$env:PYTHONPATH="simulator\src"
python -m simulator.cli `
  --stations 20 `
  --days 90 `
  --interval-minutes 30 `
  --seed 42 `
  --start-date 2026-01-01 `
  --output-dir data\virtual-v1
```

Generated datasets are written under `data/` and are ignored by Git.

Generate offline features:

```powershell
& "E:\IDEA\IntelliJ IDEA Community Edition 2024.3.5\plugins\maven\lib\maven3\bin\mvn.cmd" `
  -f offline-analysis\pom.xml `
  exec:java `
  "-Dexec.args=--input-path data/virtual-v1/demand_observations.csv --stations-path data/virtual-v1/stations.csv --output-path data/features-v1"
```

The feature task writes Parquet partitions for `train`, `validation`, and
`test`, plus a sample CSV and feature manifest.

Generate batch forecasts and dispatch recommendations:

```powershell
urbanflow-forecast predict --write-mysql
urbanflow-forecast dispatch --write-mysql
```

### MySQL and backend

Initialize the schema:

```powershell
mysql --host=127.0.0.1 --port=3306 --user=root --password `
  --database=urbanflow `
  --execute="source sql/schema.sql"
```

Start FastAPI:

```powershell
python -m uvicorn app.main:app `
  --app-dir backend `
  --host 127.0.0.1 `
  --port 8000
```

Swagger UI is available at `http://127.0.0.1:8000/docs`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
npm run build
```

The frontend requires Node.js 20.19+ or 22.12+.

English is the default UI language. Chinese is preserved in
`frontend/src/locales/zh-CN.js` and can be selected in the navigation.

Main pages:

```text
/             Operations overview
/forecast     Station demand and replenishment recommendation
/models       Model evaluation
/dispatch     Executable transfer queue
```

### Docker infrastructure

The local machine can also use its existing MySQL and Linux virtual machine.
Docker is optional.

```powershell
docker compose -f docker\docker-compose.yml up -d
docker compose -f docker\docker-compose.yml ps
```

Do not commit `.env`, generated data, model files, logs, `node_modules`,
`target`, or Python virtual environments.

## Existing Linux VM

The current development machine uses an existing CentOS VM named
`hadoopnode1`. It provides Hadoop and Kafka.

Relevant commands inside the VM:

```bash
start-all.sh

cd /usr/local/kafka_2.13-3.3.1
nohup ./bin/kafka-server-start.sh ./config/kraft/server.properties \
  >/tmp/urbanflow-kafka.log 2>&1 &
```

The project Topic is:

```text
urbanflow-demand-events
```

Kafka listens on:

```text
node1:9092
```

This VM uses Kafka KRaft mode. ZooKeeper is not required.

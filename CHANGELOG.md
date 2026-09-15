# Changelog

> **中文摘要：** 本文件记录 UrbanFlow 的主要新增功能、修复和版本变化，
> 包括实时链路、虚拟数据、预测模型、API、前端、调度和英文开源资源。

All notable changes to UrbanFlow are documented in this file.

The format is based on Keep a Changelog. The project will follow Semantic
Versioning after the first runnable release.

## [Unreleased]

### Added

- English README and English-default API/UI for GitHub publication.
- Complete Chinese frontend, backend, simulator, and dispatch locale resources.
- Health endpoint checks MySQL, forecast freshness, inventory, and dispatch
  run consistency.
- Stable empty-state responses for forecast and model APIs.
- Model card with active model, challenger metrics, selection rule, artifact
  timestamps, and known limitations.
- One-command local demo pipeline with `--dry-run` support.
- Continuous local Live Demo mode that appends demand windows, updates
  inventory, refreshes forecasts and dispatch, and works without Kafka.
- Automatic frontend polling for overview, forecast, model, and dispatch data.
- English and Chinese dashboard screenshots.
- Forecast/dispatch batch consistency metadata.
- Structured dispatch fields for near-term demand, safety stock, and target
  bikes.
- Environment loading through `python-dotenv` and aligned MySQL defaults.
- MVP project brief and acceptance criteria.
- C4 system context, container, component, and flow diagrams.
- Detailed design specification.
- Plain-language project guide.
- MVP implementation plan with synthetic data.
- GitHub open-source guide and baseline repository files.
- Documentation and repository CI checks.
- Maven multi-module Scala skeleton.
- Python forecast engine and simulator packages.
- FastAPI health endpoint.
- Vue 3 dashboard shell.
- MySQL schema and local Docker Compose configuration.
- Frontend dependency lock file and security audit.
- Existing local MySQL database initialization.
- Hadoop and Kafka startup verification on the existing CentOS VM.
- `urbanflow-demand-events` Kafka topic and producer/consumer smoke test.
- Chinese labels and status text for the Vue dashboard.
- Chinese API title, descriptions, summaries, and tags for Swagger UI.
- Reproducible virtual data generator with 20 stations, 90 days, weather,
  holidays, demand peaks, noise, and anomalies.
- CSV, JSONL, and SHA256 generation manifest outputs.
- Kafka JSONL producer with event validation, station keys, rate limiting,
  single-cycle and loop modes, dry-run support, and delivery callbacks.
- End-to-end verification report for steps 1 through 5.
- Spark Structured Streaming window aggregation with event-time watermark,
  Kafka JSON parsing, deduplication, checkpoints, and MySQL upserts.
- Step 6 end-to-end and replay-idempotency verification report.
- Spark SQL offline feature generation with lags, rolling statistics,
  calendar encoding, weather, holiday flags, target values, and chronological
  train/validation/test splits.
- Step 7 Parquet feature dataset and verification report.
- Seasonal Naive one-step and 48-step rolling forecasts.
- MAE, RMSE, and sMAPE metrics by split, station, and horizon.
- Baseline prediction and horizon-error plots.
- PyTorch TCN model, leakage-safe window dataset, zero-initialized seasonal
  residual head, CPU training, early stopping, model persistence, and paired
  model comparison.
- Step 9 verification report with the honest result that Seasonal Naive
  remains the current best model.
- Validation-based model selection with a minimum improvement threshold.
- Future 48-step batch prediction, MySQL forecast run/result persistence,
  station ranking, aggregate timeline, and analysis plots.
- FastAPI APIs for stations, demand history, latest forecasts, model metrics,
  and dashboard summary.
- Virtual station and demand CSV loader for MySQL.
- Vue dashboard, station forecast, and model evaluation pages connected to
  real FastAPI and MySQL data.
- ECharts line and bar charts, station selection, KPI cards, forecast tables,
  loading states, and error feedback.
- Station inventory snapshots with capacity, available bikes, available docks,
  status labels, and operational notes.
- Dispatch recommendation engine that matches near-term deficits to nearby
  surplus stations and writes executable transfer work orders.
- Business-facing forecast summaries with two-hour demand, safety stock,
  target bikes, recommended replenishment, and action deadlines.
- Inventory and dispatch APIs with station names, priority labels, action text,
  lead time, shortage reduction, and simulation disclosures.
- Dispatch page with an action queue, concrete transfer instructions, and
  before/after shortage impact.
- Business terminology and simulated-benefit notes that distinguish virtual
  data results from real operating outcomes.
- Step 12.5 verification report covering the inventory and dispatch decision
  loop.

## [0.1.0] - 2026-09-10

### Added

- Initial project documentation structure.
- MIT License.
- Community, contribution, and security guidance.

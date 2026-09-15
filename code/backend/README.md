# Backend

> **中文摘要：** 本模块提供 FastAPI 后端接口，包括健康检查、站点、历史需求、
> 最新预测、模型卡片、库存、调度和看板汇总。

FastAPI service for station, demand history, forecast, model metric, and
dashboard APIs.

Main endpoints:

```text
GET /health
GET /api/v1/stations
GET /api/v1/demand/history
GET /api/v1/forecasts/latest
GET /api/v1/models/metrics
GET /api/v1/dashboard/summary
GET /api/v1/inventory/latest
GET /api/v1/dispatch/summary
GET /api/v1/dispatch/recommendations
```

Run from the repository code directory:

```powershell
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

## API

```text
GET /api/v1/stations
GET /api/v1/stations/{station_id}
GET /api/v1/demand/history
GET /api/v1/forecasts/latest
GET /api/v1/models/metrics
GET /api/v1/dashboard/summary
```

All business responses use:

```json
{
  "code": 200,
  "message": "ok",
  "data": {}
}
```

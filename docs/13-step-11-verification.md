# UrbanFlow 第 11 步验收报告

> **English summary:** This report verifies the FastAPI station, demand,
> forecast, model, and dashboard endpoints, including response structure.
>
> **中文摘要：** 本报告验收站点、需求、预测、模型和看板接口，以及统一返回
> 结构和查询结果。

## 1. 验收目标

实现 FastAPI 数据查询接口：

1. 健康检查。
2. 站点列表和站点详情。
3. 历史需求。
4. 最新预测。
5. 模型指标。
6. 看板汇总。

## 2. 数据库准备

开发数据已加载到 MySQL：

```text
station_dim：20
demand_observation：86400
forecast_run：1
forecast_result：960
```

历史时间范围：

```text
2026-01-01 00:00:00 到 2026-03-31 23:30:00
```

## 3. 接口清单

```text
GET /health
GET /api/v1/stations
GET /api/v1/stations/{station_id}
GET /api/v1/demand/history
GET /api/v1/forecasts/latest
GET /api/v1/models/metrics
GET /api/v1/dashboard/summary
```

业务接口统一响应：

```json
{
  "code": 200,
  "message": "ok",
  "data": {}
}
```

## 4. 站点接口

请求：

```text
GET /api/v1/stations
```

结果：

```text
code：200
站点数量：20
第一个站点：ST001
最后一个站点：ST020
```

## 5. 历史需求接口

请求：

```text
GET /api/v1/demand/history?station_id=ST016&limit=5
```

结果：

```text
返回行数：5
时间范围：2026-03-31 21:30 到 2026-03-31 23:30
```

示例：

| 时间 | 需求 |
|---|---:|
| 2026-03-31 21:30 | 13 |
| 2026-03-31 22:00 | 12 |
| 2026-03-31 22:30 | 7 |
| 2026-03-31 23:00 | 7 |
| 2026-03-31 23:30 | 8 |

## 6. 最新预测接口

请求：

```text
GET /api/v1/forecasts/latest?station_id=ST016&limit=48
```

结果：

```text
forecast_run_id：3
model_version：seasonal-naive-v1
预测点数：48
时间范围：2026-04-01 00:00 到 2026-04-01 23:30
预测总需求：858
峰值预测：45
```

## 7. 模型指标接口

请求：

```text
GET /api/v1/models/metrics
```

返回：

- Seasonal Naive 验证集和测试集指标。
- TCN 验证集和测试集指标。
- 模型选择理由和最低改善阈值。

模型选择结果：

```text
selected_model：seasonal_naive
model_version：seasonal-naive-v1
baseline validation MAE：2.0474
TCN validation MAE：2.0898
```

## 8. 看板汇总接口

请求：

```text
GET /api/v1/dashboard/summary
```

返回：

```text
站点数量：20
历史观测数量：86400
最新预测批次：1
预测行数：960
预测总需求：9638
最高单点预测：45
最高需求站点：ST016
```

高峰时段：

```text
2026-04-01 17:30，聚合需求 409
2026-04-01 18:00，聚合需求 405
2026-04-01 18:30，聚合需求 393
```

## 9. 自动化测试

```text
Backend 路由测试：6/6 通过
健康检查测试：通过
站点路由测试：通过
历史需求路由测试：通过
预测路由测试：通过
模型路由测试：通过
看板路由测试：通过
```

## 10. 验收结论

```text
第 11 步：通过
```

当前完成后端数据接口。下一步第 12 步将 Vue 页面连接到这些真实 API，
实现站点选择、历史曲线、预测曲线、模型指标和看板数据展示。

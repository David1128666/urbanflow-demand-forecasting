# UrbanFlow 第 10 步验收报告

> **English summary:** This report verifies batch prediction, MySQL
> persistence, station ranking, aggregate timeline output, and analysis charts.
>
> **中文摘要：** 本报告验收批量预测、MySQL 写入、站点排名、聚合时间线和
> 分析图表。

## 1. 验收目标

实现批量预测：

1. 根据验证集选择生产模型。
2. 生成每个站点未来 48 个时间点预测。
3. 保存本地 Parquet、CSV 和分析结果。
4. 写入 MySQL `forecast_run` 和 `forecast_result`。
5. 输出站点排名、峰值时段和趋势图。

## 2. 模型选择

选择指标：

```text
验证集 48 步 MAE
```

结果：

```text
Seasonal Naive：2.0474
TCN：2.0898
TCN 改善：-2.07%
最低要求改善：5.00%
```

结论：

```text
TCN 未达到最低改善要求
选择 Seasonal Naive
model_version = seasonal-naive-v1
```

## 3. 批量预测

预测起点：

```text
数据截止：2026-03-31 23:30:00
预测开始：2026-04-01 00:00:00
预测结束：2026-04-01 23:30:00
```

这里“未来”是相对于虚拟数据集的最后时间，不是相对于当前电脑日期。

规模：

```text
站点数量：20
每个站点预测步数：48
预测结果行数：960
```

## 4. MySQL 写入

预测批次：

```text
forecast_run_id：3
model_version：seasonal-naive-v1
feature_version：feature-v1
status：success
```

预测结果：

```text
forecast_result 行数：960
站点数量：20
目标时间点：48
预测总需求：9638
最小单点预测：2
最大单点预测：45
```

## 5. 分析结果

需求最高的站点：

| 排名 | 站点 | 24 小时预测总需求 | 平均需求 | 峰值需求 |
|---:|---|---:|---:|---:|
| 1 | ST016 | 858.0 | 17.9 | 45.0 |
| 2 | ST009 | 804.0 | 16.8 | 34.0 |
| 3 | ST014 | 760.0 | 15.8 | 37.0 |
| 4 | ST019 | 681.0 | 14.2 | 34.0 |
| 5 | ST001 | 641.0 | 13.4 | 34.0 |

聚合需求最高的时间点：

| 目标时间 | 聚合需求 |
|---|---:|
| 2026-04-01 17:30:00 | 409.0 |
| 2026-04-01 18:00:00 | 405.0 |
| 2026-04-01 18:30:00 | 393.0 |
| 2026-04-01 08:00:00 | 367.0 |
| 2026-04-01 17:00:00 | 365.0 |

主要结论：

```text
预测峰值出现在 2026-04-01 晚间 17:30
最高聚合需求为 409
ST016 是未来 24 小时需求最高且最需要关注的站点
```

## 6. 输出文件

```text
data/predictions-v1/forecast_results.parquet
data/predictions-v1/forecast_results.csv
data/predictions-v1/station_forecast_ranking.csv
data/predictions-v1/forecast_timeline.csv
data/predictions-v1/analysis_summary.json
data/predictions-v1/batch_manifest.json
data/predictions-v1/station_ranking.png
data/predictions-v1/forecast_timeline.png
```

## 7. 预留能力

批量写入使用事务：

- `forecast_run` 和全部 `forecast_result` 在同一事务内提交。
- 写入失败会回滚当前批次。
- 上一批已成功预测不会被删除。
- `forecast_result` 使用唯一键和 UPSERT，重复写入不会产生重复结果。

## 8. 验收结论

```text
第 10 步数据侧：通过
```

API 读取最新预测属于第 11 步。

页面展示预测生成时间属于第 12 步。

当前已完成第 1 到第 10 步的数据链路。下一步进入第 11 步：实现
站点列表、历史需求、最新预测和模型指标 FastAPI 接口。

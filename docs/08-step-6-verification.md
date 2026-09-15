# UrbanFlow 第 6 步验收报告

> **English summary:** This report verifies Kafka-to-Spark-to-MySQL window
> aggregation, replay idempotency, and checkpoint recovery.
>
> **中文摘要：** 本报告验收 Kafka 到 Spark 再到 MySQL 的窗口聚合、重复数据
> 幂等性和 checkpoint 恢复。

## 1. 验收目标

验证完整实时链路：

```text
虚拟需求数据
  -> Kafka
  -> Spark Structured Streaming
  -> 30 分钟事件时间窗口
  -> MySQL realtime_demand_metrics
```

## 2. 验收配置

```text
Kafka Topic：urbanflow-step6-20260911113823
Kafka Broker：node1:9092
窗口大小：30 分钟
Watermark：10 分钟
触发间隔：5 秒
输出模式：append
MySQL 表：realtime_demand_metrics
Checkpoint：checkpoints/step6-retry-20260911114935
```

## 3. 输入数据

第一次发送：

```text
事件数量：100
覆盖站点：20
覆盖时间点：5
时间范围：2026-01-01 00:00 到 2026-01-01 02:00
```

## 4. Spark 窗口处理

Watermark 会等待 10 分钟迟到数据。输入最后两个时间点还没有超过
Watermark 边界，因此它们的窗口尚未关闭。

Spark 最终输出：

```text
已关闭窗口数量：3
每个窗口覆盖站点：20
输出指标行数：3 * 20 = 60
```

Spark 日志：

```text
[realtime] batch=1 rows=0
[realtime] batch=2 rows=60
```

## 5. MySQL 对账

查询结果：

```text
MySQL 行数：60
站点数量：20
窗口数量：3
第一个窗口：2026-01-01 00:00:00
最后一个窗口：2026-01-01 01:00:00
MySQL 需求总量：277
MySQL 事件总量：60
```

源数据前三个已关闭窗口：

```text
源数据行数：60
源数据站点数量：20
源数据窗口数量：3
源数据需求总量：277
源数据事件总量：60
```

结论：Spark 聚合结果与源数据完全一致。

## 6. MySQL 结果示例

| city_id | station_id | window_start | window_end | demand_count | event_count |
|---|---|---|---|---:|---:|
| city-001 | ST001 | 2026-01-01 00:00:00 | 2026-01-01 00:30:00 | 5 | 1 |
| city-001 | ST001 | 2026-01-01 00:30:00 | 2026-01-01 01:00:00 | 5 | 1 |
| city-001 | ST001 | 2026-01-01 01:00:00 | 2026-01-01 01:30:00 | 5 | 1 |
| city-001 | ST002 | 2026-01-01 00:00:00 | 2026-01-01 00:30:00 | 3 | 1 |

## 7. 重复消息验收

第二次从相同 Topic 重放相同的 100 条事件。

重放后 MySQL：

```text
行数：仍然为 60
站点数量：仍然为 20
窗口数量：仍然为 3
总需求：仍然为 277
总事件：仍然为 60
```

结论：

- Spark event_id 去重有效。
- MySQL 唯一键和 UPSERT 生效。
- 重放不会重复累加业务指标。

## 8. 修复记录

首次运行时出现 Jackson 组件版本混用：

```text
jackson-module-scala：2.17.2
jackson-databind：2.15.2
```

统一为 Spark 3.5.1 对应的 Jackson 2.15.2 后，Spark
`SparkThrowableHelper` 初始化正常，实时任务成功运行。

## 9. 验收结论

```text
第 6 步：通过
```

当前已完成第 1 到第 6 步，下一步进入第 7 步：使用 Spark SQL 生成
滞后、滑动窗口、日历和虚拟天气特征，为 Seasonal Naive 和 TCN 准备训练数据。

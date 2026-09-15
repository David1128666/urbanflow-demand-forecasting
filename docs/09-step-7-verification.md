# UrbanFlow 第 7 步验收报告

> **English summary:** This report verifies lag, rolling, calendar, weather,
> and holiday features, plus chronological train, validation, and test splits.
>
> **中文摘要：** 本报告验收滞后、滑动、日历、天气和节假日特征，以及按时间
> 顺序划分训练集、验证集和测试集。

## 1. 验收目标

验证 Spark SQL 离线特征工程可以：

1. 读取虚拟历史需求。
2. 按站点构造历史滞后和滑动统计。
3. 生成日历、天气和节假日特征。
4. 生成未来 30 分钟目标。
5. 按时间切分训练、验证和测试集。
6. 输出 Parquet 数据集。

## 2. 输入数据

```text
需求观测文件：data/virtual-v1/demand_observations.csv
站点文件：data/virtual-v1/stations.csv
原始观测数量：86400
站点数量：20
时间范围：2026-01-01 到 2026-03-31
时间粒度：30 分钟
```

## 3. 生成特征

### 历史滞后

```text
demand_lag_1
demand_lag_2
demand_lag_48
demand_lag_336
```

### 滑动统计

```text
rolling_mean_1h
rolling_std_1h
rolling_mean_6h
rolling_std_6h
rolling_mean_24h
rolling_std_24h
rolling_mean_7d
rolling_std_7d
```

### 日历特征

```text
hour_of_day
minute_of_day
day_of_week
day_of_month
week_of_year
is_weekend
hour_sin
hour_cos
week_sin
week_cos
```

### 其他特征

```text
is_holiday
temperature
precipitation
capacity
region_id
station_type
base_demand
target_next_30m
```

## 4. 数据完整性

每条序列需要至少 336 个历史时间点才能计算 7 天滞后和 7 天滑动统计。
每个站点的最后一条记录没有下一时间点，因此不能计算目标值。

结果：

```text
原始观测：86400
完整特征：79660
被排除：6740
```

被排除的数据包括：

```text
每个站点前 336 条尚不完整的记录：336 * 20 = 6720
每个站点最后 1 条无目标值的记录：20
合计：6740
```

## 5. 时间切分

采用严格时间顺序，不进行随机切分：

```text
训练集：55760
验证集：11940
测试集：11960
总计：79660
```

切分时间边界：

```text
训练结束：2026-03-06T17:42:00Z
验证结束：2026-03-19T04:21:00Z
测试集：验证结束之后
```

## 6. 特征正确性抽样

选择 `ST003` 在 `2026-01-08 00:00:00` 的记录进行核对。

特征结果：

```text
demand_lag_1 = 3
demand_lag_48 = 3
demand_lag_336 = 2
rolling_mean_1h = 2.5
target_next_30m = 2
```

源数据核对：

```text
2026-01-07 23:30:00 需求 = 3
2026-01-07 00:00:00 需求 = 3
2026-01-01 00:00:00 需求 = 2
2026-01-07 23:00:00 需求 = 2
2026-01-08 00:30:00 需求 = 2
```

计算验证：

```text
lag_1：3，匹配
lag_48：3，匹配
lag_336：2，匹配
rolling_mean_1h：(2 + 3) / 2 = 2.5，匹配
target_next_30m：2，匹配
```

## 7. 输出文件

```text
data/features-v1/features.parquet/
  split=train/
  split=validation/
  split=test/

data/features-v1/sample.csv/
data/features-v1/feature_manifest.json
```

完整 Parquet 数据集包含 40 列，并带有 `split` 分区列。

## 8. 防泄漏说明

- 所有滞后特征只引用当前时间点之前的数据。
- 所有滑动窗口使用 `rowsBetween(-N, -1)`，不包含当前值。
- 目标列使用下一时间点，只在训练标签中使用。
- 数据按时间顺序切分，不做随机划分。
- 标准化和缺失值拟合将在模型训练时只使用训练集统计量。

## 9. 验收结论

```text
第 7 步：通过
```

当前已完成第 1 到第 7 步。下一步进入第 8 步：使用这些特征实现
Seasonal Naive 基线，并计算 MAE、RMSE 和 sMAPE。

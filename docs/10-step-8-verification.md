# UrbanFlow 第 8 步验收报告

> **English summary:** This report verifies the Seasonal Naive one-step and
> 48-step rolling forecasts, metric calculations, and evaluation plots.
>
> **中文摘要：** 本报告验收 Seasonal Naive 一步预测、48 步滚动预测、指标计算
> 和评估图表。

## 1. 验收目标

实现并验证 Seasonal Naive 基线：

1. 使用目标时间前一天同一时间作为预测。
2. 计算一步预测指标。
3. 从测试集每个起点预测未来 48 个时间点。
4. 按 horizon 计算误差。
5. 生成预测和误差图。

## 2. 预测公式

对于目标时间 `t`：

```text
prediction(t) = demand(t - 24 hours)
```

时间粒度为 30 分钟，因此 24 小时等于 48 个时间点。

## 3. 一步预测结果

### 测试集

```text
预测行数：11960
MAE：1.9552675585
RMSE：3.1167231527
sMAPE：18.8291719481%
实际需求均值：10.4331939799
预测需求均值：10.4379598662
```

### 验证集

```text
预测行数：11940
MAE：2.1205192630
RMSE：3.4553747612
sMAPE：19.5638071334%
```

### 训练集

```text
预测行数：54800
MAE：2.0762956204
RMSE：3.3208504099
sMAPE：19.7901753990%
```

训练集前 48 个目标点因为缺少前一天历史，被自然排除。

## 4. 未来 48 步预测

对测试集每个时间起点执行 48 步滚动预测：

```text
预测行数：550560
MAE：1.9777244987
RMSE：3.1488784024
sMAPE：19.0352642713%
```

部分 horizon 结果：

| Horizon | 时间范围 | MAE |
|---:|---:|---:|
| 1 | 30 分钟 | 1.9571189280 |
| 24 | 12 小时 | 1.9764808362 |
| 48 | 24 小时 | 1.9958181818 |

结果符合预期：预测越远，MAE 总体略有增加。

## 5. 预测对齐检查

重新从原始特征中计算：

```text
expected = demand(target_timestamp - 24 hours)
```

与基线预测逐条比较：

```text
比较行数：550560
最大绝对差：0.0
不一致数量：0
缺失参考值：0
```

说明 48 步预测正确使用了目标时间前一天的数据，没有时间错位。

## 6. 输出文件

```text
data/baseline-v1/predictions.parquet
data/baseline-v1/predictions.csv
data/baseline-v1/predictions_48step.parquet
data/baseline-v1/predictions_48step.csv
data/baseline-v1/metrics.json
data/baseline-v1/metrics_by_split.csv
data/baseline-v1/metrics_by_station.csv
data/baseline-v1/metrics_by_horizon.csv
```

图表：

```text
data/baseline-v1/baseline_prediction.png
data/baseline-v1/baseline_error_by_horizon.png
```

## 7. 基线用途

后续模型必须使用相同测试集进行比较，并至少达到以下基线要求：

```text
测试集 MAE < 1.9552675585
测试集 RMSE < 3.1167231527
测试集 sMAPE < 18.8291719481%
```

如果复杂模型没有明显优于这些指标，就说明增加模型复杂度不值得。

## 8. 验收结论

```text
第 8 步：通过
```

当前已完成第 1 到第 8 步。下一步进入第 9 步：训练 PyTorch TCN，
并在完全相同的测试集上与 Seasonal Naive 比较。

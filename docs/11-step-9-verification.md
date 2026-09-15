# UrbanFlow 第 9 步验收报告

> **English summary:** This report verifies TCN training, test metrics,
> paired comparison with the baseline, and the resulting model-selection
> decision.
>
> **中文摘要：** 本报告验收 TCN 训练、测试指标、与基线的配对比较，以及最终
> 模型选择结论。

## 1. 验收目标

实现并验证 PyTorch TCN：

1. 构造不跨 split 的滑窗训练样本。
2. 使用过去 96 个时间点预测未来 48 个时间点。
3. 在 CPU 上完成训练。
4. 使用验证集早停。
5. 保存最佳模型和完整预测。
6. 在相同测试样本上与 Seasonal Naive 公平比较。

## 2. 模型与数据

```text
输入长度：96 个 30 分钟时间点，约 48 小时
输出长度：48 个 30 分钟时间点，约 24 小时
输入通道：7
TCN 通道：16、32
卷积核：3
Dropout：0.1
Batch size：128
训练轮数：5
优化器：AdamW
损失：Huber Loss
设备：CPU
随机种子：42
```

输入特征：

```text
demand_count
temperature
precipitation
is_holiday
is_weekend
hour_sin
hour_cos
```

模型采用 Seasonal Naive 残差结构：

```text
prediction = seasonal_naive_baseline + tcn_residual
```

残差输出头初始化为 0，因此训练开始时预测严格等于 Seasonal Naive。

## 3. 训练结果

| Epoch | Train Loss | Validation Loss | Validation MAE |
|---:|---:|---:|---:|
| 1 | 0.08115 | 0.08440 | 2.12366 |
| 2 | 0.07833 | 0.08271 | 2.09572 |
| 3 | 0.07683 | 0.08238 | 2.08984 |
| 4 | 0.07570 | 0.08276 | 2.09003 |
| 5 | 0.07516 | 0.08273 | 2.09247 |

最佳验证轮次为第 3 轮。训练损失持续下降，验证损失从第 3 轮后没有继续改善。

## 4. 配对测试比较

TCN 与 Seasonal Naive 使用完全相同的：

```text
测试站点
预测起点
目标时间
horizon
```

配对样本：

```text
528000 条预测
11000 条 / 每个 horizon
```

结果：

| 指标 | TCN | Seasonal Naive | TCN 改善 |
|---|---:|---:|---:|
| MAE | 2.0737 | 1.9928 | -4.06% |
| RMSE | 3.1919 | 3.1768 | -0.48% |
| sMAPE | 20.2797% | 19.2156% | -5.54% |

48 个 horizon 中，TCN 当前均没有稳定优于 Seasonal Naive。

## 5. 原因分析

1. 虚拟需求具有较强的日周期，Seasonal Naive 与数据生成规律高度匹配。
2. TCN 训练样本只有 3 个月，深度模型容易学习到局部波动。
3. 当前 TCN 使用小型 CPU 模型，训练轮数和参数规模有限。
4. 中期 horizon 的残差修正没有稳定泛化到测试阶段。
5. 验证损失下降不能保证测试阶段同方向改善，说明存在一定过拟合或分布变化。

## 6. 输出文件

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

## 7. 模型选择结论

模型选择不能根据测试集反复调参。当前结论：

```text
TCN 实现完成
TCN 可训练、可保存、可推理
TCN 当前不优于 Seasonal Naive
生产候选模型：Seasonal Naive
TCN 保留为实验模型
```

这是一个有效的负结果，说明复杂模型没有天然优势。

## 8. 后续改善方向

- 增加训练数据到 1 年以上。
- 引入跨站点共享信息。
- 使用更长时间历史和多尺度 TCN。
- 对新数据重新调参并固定验证协议。
- 在 TCN 中显式加入未来日历和天气预报。
- 使用概率预测或分位数损失。

## 9. 验收结论

```text
第 9 步：通过
```

第 9 步要求的是完成 TCN 训练和比较，不要求 TCN 必须获胜。当前已完成第 1 到
第 9 步。下一步进入第 10 步：建立批量预测任务，并按照验证集选择结果生成未来
48 步预测。

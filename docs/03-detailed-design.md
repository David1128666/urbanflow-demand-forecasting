# UrbanFlow 详细设计说明书

> **English summary:** This document covers the data model, Kafka and Spark
> flow, feature engineering, MySQL schema, forecasting models, API contracts,
> frontend design, testing, and failure handling.
>
> **中文摘要：** 本文覆盖数据模型、Kafka 与 Spark 链路、特征工程、MySQL
> 结构、预测模型、API 设计、前端、测试和异常处理。

## 1. 文档说明

本文基于《UrbanFlow 项目文档》和《UrbanFlow C4 架构说明》，描述系统的数据、模块、接口、模型、前端、部署、测试和运维设计。本文面向后续实际编码，不把尚未实现的指标或实验结果写成既定事实。

| 项目 | 内容 |
|---|---|
| 文档版本 | v0.2 |
| 文档日期 | 2026-09-10 |
| 上游文档 | `01-project-brief.md`、`02-c4-architecture.md`、`05-mvp-implementation-plan.md` |
| 设计范围 | MVP 必做范围 + 后期目标设计 |
| 核心架构 | Lambda 架构 + 离线模型训练 + 服务化预测 |

### 1.1 当前实施边界

当前编码只实现以下闭环：

```text
Python 虚拟数据
  -> Kafka
  -> Spark Structured Streaming
  -> MySQL + 本地 Parquet
  -> Spark SQL 特征
  -> Seasonal Naive + PyTorch TCN
  -> FastAPI
  -> Vue 3 + ECharts
```

当前不实现：

- 真实城市数据接入。
- Flume 文件采集。
- MLflow 服务。
- PatchTST 和大型 Transformer。
- 概率预测和 WQL。
- 登录、权限和复杂管理后台。
- MinIO、Airflow、Redis、Prometheus、Grafana 和 Kubernetes。

本文后续出现这些技术时，均视为后期目标设计，不纳入当前 MVP 验收。

### 1.2 设计裁剪原则

1. 先实现点预测，再实现概率预测。
2. 先使用虚拟数据，再替换为真实数据适配器。
3. 先使用 Kafka 直连，再增加 Flume。
4. 先使用本地 CSV/Parquet，再增加对象存储。
5. 先实现 TCN，再评估 PatchTST。
6. 先使用文件保存模型和指标，再引入 MLflow。
7. 先实现核心页面，再增加监控和管理后台。

## 2. 设计目标

1. MVP 复用原项目的 Kafka、Scala、Spark、MySQL、FastAPI、Vue 和 ECharts，Flume 后置。
2. 把时序预测做成数据产品，而不是一次性 Notebook。
3. 统一实时指标和离线特征的时间口径。
4. 用严格时间回测评价模型，防止数据泄漏。
5. 支持点预测、基础误差分析和简单模型版本记录，概率区间后置。
6. 为后续扩展到多城市、多业务和更复杂模型保留接口。

## 3. 总体设计

### 3.1 分层

| 层 | 主要模块 | 职责 |
|---|---|---|
| 数据源层 | simulator | 产生有规律的虚拟历史和增量需求 |
| 接入层 | Kafka；Flume 后期 | MVP 直接写 Kafka，后期增加文件采集 |
| 处理层 | realtime-analysis、offline-analysis | 实时聚合、离线特征和统计 |
| 存储层 | MySQL、本地 CSV/Parquet | MVP 服务数据、特征、训练集和回测集 |
| 模型层 | forecast-engine；MLflow 后期 | 训练、评估、TCN 和批量推理 |
| 服务层 | FastAPI | MVP 提供历史和预测 API，认证后置 |
| 展示层 | Vue 3、Pinia、ECharts | 总览、预测和模型指标页面 |
| 工程层 | Maven、Docker、pytest | MVP 构建、本地运行和核心测试 |

### 3.2 运行模式

| 模式 | 触发方式 | 频率 | 主要任务 |
|---|---|---|---|
| 实时模式 | Spark Streaming 常驻 | 持续 | 清洗事件、窗口聚合、质量检查 |
| 离线特征 | 定时任务 | 每小时或每天 | 生成滞后、滑动、日历和天气特征 |
| 训练模式 | 手工触发 | 数据版本更新后 | 训练、验证和评估模型 |
| 批量预测 | 定时任务 | 每 30 分钟或每小时 | 生成未来 24 小时预测 |
| 在线查询 | 用户请求 | 按需 | 查询预测、统计和监控结果 |

### 3.3 推荐目录

```text
urbanflow-forecast/
├── common/
│   ├── src/main/scala/.../config/
│   ├── src/main/scala/.../model/
│   └── src/main/scala/.../util/
├── realtime-analysis/
│   └── src/main/scala/.../processor/
├── offline-analysis/
│   └── src/main/scala/.../analysis/
├── forecast-engine/
│   ├── configs/
│   ├── src/urbanflow_forecast/
│   │   ├── data/
│   │   ├── features/
│   │   ├── models/
│   │   ├── evaluation/
│   │   ├── training/
│   │   └── inference/
│   └── tests/
├── backend/
│   ├── routers/
│   ├── services/
│   ├── repositories/
│   ├── schemas/
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── router/
│       ├── stores/
│       └── views/
├── simulator/
├── sql/
├── docker/
└── docs/
```

## 4. 数据设计

### 4.1 时间口径

时间序列项目首先要统一时间语义：

- 事件时间：需求实际发生的时间，所有聚合和标签都以该时间为准。
- 处理时间：Spark 或后端处理数据的当前时间，只用于监控，不参与标签构造。
- 数据截止时间：生成某个特征或预测时允许使用的最新数据时间。
- 目标时间：预测结果对应的未来时间点。
- 发布时间：预测写入服务数据库的时间。

统一时区建议使用 UTC 存储，页面按城市本地时区展示。如果只在单城市运行，也可以统一使用城市本地时区，但必须有明确文档。

### 4.2 数据分层

| 层级 | 存储 | 内容 | 生命周期 |
|---|---|---|---|
| Raw | Kafka、Parquet | 原始事件、来源和接收时间 | 长期或按数据许可保存 |
| Standardized | Parquet、MySQL 汇总表 | 字段标准化后的事件 | 中期 |
| Realtime | MySQL | 5 分钟或 30 分钟实时指标 | 90 到 365 天 |
| Feature | Parquet | 训练、验证和预测特征 | 按特征版本保留 |
| Serving | MySQL | 预测结果、模型指标和任务状态 | 长期 |
| Model | MLflow、本地文件或 MinIO | 模型参数、指标和产物 | 按模型版本保留 |

### 4.3 核心领域对象

#### 站点维度

```text
station_id          站点唯一标识
city_id             城市标识
station_name        站点名称
longitude           经度
latitude            纬度
capacity            容量或运力上限
region_id           所属区域
station_type        站点类型
is_active           是否运营
valid_from          生效时间
valid_to            失效时间
```

#### 需求观测

```text
observation_id      观测唯一标识
city_id             城市
station_id          站点
window_start        30 分钟窗口开始时间
window_end          30 分钟窗口结束时间
demand_count        需求数量
source_type         数据来源
data_version        数据版本
quality_flag        数据质量标记
created_at          写入时间
```

#### 天气观测

```text
weather_id          天气记录标识
city_id             城市
weather_time        天气时间
temperature         温度
precipitation       降水量
wind_speed          风速
humidity            湿度
weather_code        天气类型编码
is_forecast         是否为预报值
data_version        数据版本
```

#### 预测任务

```text
forecast_run_id     预测批次标识
model_version       模型版本
feature_version     特征版本
data_cutoff         数据截止时间
forecast_start      预测开始时间
horizon_steps       预测步数
status              运行状态
generated_at        生成时间
```

#### 预测结果

```text
forecast_result_id  结果标识
forecast_run_id     所属预测批次
station_id          站点
target_time         目标时间
horizon_step        第几个未来步
predicted_q10       10% 分位预测
predicted_q50       50% 分位预测，也就是中位数
predicted_q90       90% 分位预测
confidence_level    置信水平
created_at          写入时间
```

MVP 只使用 `predicted_demand` 点预测字段。`predicted_q10`、`predicted_q50`、`predicted_q90` 属于后期概率预测设计。

## 5. MySQL 物理设计

### 5.1 需求观测表

```sql
CREATE TABLE demand_observation (
    observation_id BIGINT NOT NULL AUTO_INCREMENT,
    city_id VARCHAR(32) NOT NULL,
    station_id VARCHAR(64) NOT NULL,
    window_start DATETIME NOT NULL,
    window_end DATETIME NOT NULL,
    demand_count INT NOT NULL DEFAULT 0,
    source_type VARCHAR(32) NOT NULL,
    data_version VARCHAR(64) NOT NULL,
    quality_flag TINYINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (observation_id),
    UNIQUE KEY uk_demand_window (
        city_id, station_id, window_start, data_version
    ),
    KEY idx_demand_station_time (station_id, window_start),
    KEY idx_demand_city_time (city_id, window_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5.2 预测批次表

```sql
CREATE TABLE forecast_run (
    forecast_run_id BIGINT NOT NULL AUTO_INCREMENT,
    city_id VARCHAR(32) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    feature_version VARCHAR(64) NOT NULL,
    data_cutoff DATETIME NOT NULL,
    forecast_start DATETIME NOT NULL,
    horizon_steps INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message VARCHAR(500) NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (forecast_run_id),
    KEY idx_run_city_time (city_id, data_cutoff),
    KEY idx_run_model (model_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5.3 预测结果表

```sql
CREATE TABLE forecast_result (
    forecast_result_id BIGINT NOT NULL AUTO_INCREMENT,
    forecast_run_id BIGINT NOT NULL,
    city_id VARCHAR(32) NOT NULL,
    station_id VARCHAR(64) NOT NULL,
    target_time DATETIME NOT NULL,
    horizon_step INT NOT NULL,
    predicted_demand DECIMAL(12,4) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (forecast_result_id),
    UNIQUE KEY uk_forecast_point (
        forecast_run_id, station_id, horizon_step
    ),
    KEY idx_forecast_query (
        city_id, station_id, target_time, forecast_run_id
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

概率预测阶段可以在该表增加 `predicted_q10`、`predicted_q50` 和 `predicted_q90` 字段，或单独建立分位数结果表。

### 5.4 模型指标表

```sql
CREATE TABLE model_metric (
    metric_id BIGINT NOT NULL AUTO_INCREMENT,
    model_version VARCHAR(64) NOT NULL,
    feature_version VARCHAR(64) NOT NULL,
    split_name VARCHAR(20) NOT NULL,
    horizon_step INT NULL,
    metric_name VARCHAR(32) NOT NULL,
    metric_value DECIMAL(16,6) NOT NULL,
    segment_type VARCHAR(32) NULL,
    segment_value VARCHAR(100) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (metric_id),
    KEY idx_metric_model (model_version, metric_name),
    KEY idx_metric_segment (segment_type, segment_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5.5 索引与保留策略

- 预测查询以 `city_id + station_id + target_time` 为主，必须建立联合索引。
- 高频率写入表按日期分区或定期归档。
- 原始事件保存在 Parquet，MySQL 只保留常用汇总和结果。
- 预测结果至少保留 180 天，训练特征按版本保留。
- 软删除字段仅用于维度表，事实表默认追加写入。

## 6. 数据质量设计

### 6.1 校验规则

| 检查 | 规则 | 处理 |
|---|---|---|
| 主键完整性 | 事件 ID 或窗口键不能为空 | 拒绝写入并计数 |
| 时间合法性 | 事件时间不能超出合理范围 | 标记异常 |
| 重复数据 | 唯一键重复 | Kafka 键去重或 MySQL UPSERT |
| 站点存在性 | station_id 必须存在 | 进入待处理维度表 |
| 数值范围 | 需求数量不能为负 | 标记或置零并告警 |
| 天气缺失 | 关键天气字段为空 | 保留空值并新增缺失标记 |
| 数据延迟 | 数据截止时间超过阈值 | 页面显示数据过期 |
| 分布漂移 | 与训练窗口差异过大 | 触发模型监控告警 |

### 6.2 数据质量分数

可以定义 0 到 100 的质量分数：

```text
quality_score =
    40 * 时间完整性 +
    25 * 字段完整性 +
    20 * 数值合法性 +
    15 * 新鲜度
```

每个子项归一化到 0 到 1。质量分数小于 80 时页面提示，小于 60 时停止自动发布预测。

## 7. 实时计算设计

### 7.1 Kafka Topic

| Topic | 内容 | Key | 分区建议 |
|---|---|---|---|
| `urbanflow-demand-events` | 标准需求事件 | `station_id` | 3 到 6 |
| `urbanflow-weather-events` | 天气观测和预报 | `city_id` | 1 到 3 |
| `urbanflow-data-quality` | 数据质量事件 | `station_id` | 1 到 3 |
| `urbanflow-alerts` | 模型或业务告警 | `alert_key` | 1 到 3 |

### 7.2 Structured Streaming 流程

1. 从 Kafka 读取 JSON 值。
2. 使用显式 Schema 解析，禁止完全依赖自动推断。
3. 校验事件时间、站点、需求数量和来源字段。
4. 使用 watermark 处理迟到数据。
5. 按 30 分钟事件时间窗口聚合需求。
6. 使用 `foreachBatch` 写入 MySQL，写入采用 UPSERT。
7. 同时将标准化事件写入 Parquet。
8. 写入批次日志、延迟指标和异常计数。

推荐参数：

```text
trigger interval = 30 seconds
watermark = 2 hours
maxOffsetsPerTrigger = 5000
checkpoint = ./checkpoint/<topic>
write mode = append/update according to sink
```

### 7.3 幂等设计

- Kafka 消息包含 `event_id`。
- MySQL 使用 `ON DUPLICATE KEY UPDATE` 或唯一键保证幂等。
- Parquet 按 `event_date` 和批次分区，避免重复覆盖历史数据。
- 所有结果记录 `batch_id`、`source_offset` 和处理时间。

## 8. 离线特征设计

### 8.1 特征分类

| 特征类别 | 示例 | 作用 |
|---|---|---|
| 历史需求 | lag_1、lag_2、lag_48 | 捕捉短期和日周期 |
| 滑动统计 | 1h mean、24h mean、7d std | 捕捉趋势和波动 |
| 时间特征 | hour sin/cos、weekday、is_weekend | 捕捉周期模式 |
| 节假日 | is_holiday、day_before_holiday | 捕捉特殊日期 |
| 天气 | temperature、precipitation、wind_speed | 捕捉外部影响 |
| 空间特征 | capacity、neighbor_mean、region_mean | 捕捉区域联动 |
| 事件特征 | event_count、event_type、distance | 捕捉突发需求 |
| 质量特征 | missing_ratio、delay_minutes | 表达数据可信度 |

### 8.2 时间窗口步长

时间粒度为 30 分钟时：

```text
1 小时 = 2 步
1 天 = 48 步
7 天 = 336 步
14 天 = 672 步
```

### 8.3 特征公式示例

为了避免目标泄漏，所有历史需求特征必须先 shift 一个时间步：

```text
lag_1(t) = demand(t - 1)
lag_2(t) = demand(t - 2)
rolling_mean_2(t) = mean(demand(t - 2), demand(t - 1))
rolling_mean_48(t) = mean(demand(t - 48), ..., demand(t - 1))
rolling_std_48(t) = std(demand(t - 48), ..., demand(t - 1))
```

周期编码：

```text
hour_sin = sin(2 * pi * minute_of_day / 1440)
hour_cos = cos(2 * pi * minute_of_day / 1440)
weekday_sin = sin(2 * pi * weekday / 7)
weekday_cos = cos(2 * pi * weekday / 7)
```

### 8.4 特征版本

特征版本格式建议：

```text
feature-v<major>.<minor>.<patch>
```

以下情况必须升级版本：

- 改变特征定义或窗口长度。
- 改变缺失值填充方式。
- 改变站点筛选规则。
- 改变训练标签口径。
- 引入新的外部数据源。

## 9. 预测模型设计

### 9.1 问题形式

对每个站点 `s` 和截止时间 `t`：

```text
X[s, t-L+1:t] -> Y[s, t+1:t+H]
```

- `L`：输入历史长度，建议 336 到 672 步。
- `H`：输出步数，MVP 为 48 步。
- `X`：需求历史、日历、天气、站点和空间特征。
- `Y`：未来 48 个 30 分钟需求值。
- MVP 输出：每个未来时间点的点预测。
- 后期输出：每个未来时间点的 q10、q50、q90。

### 9.2 模型梯队

#### 模型 M0：Seasonal Naive

```text
prediction(t + h) = demand(t + h - 48)
```

这是最低基线。任何复杂模型至少应在这个基线上进行公平比较。

#### 模型 M1：Spark MLlib 梯度提升（后期）

- 使用直接多步预测，每个 horizon 训练一个模型或在模型中增加 horizon 特征。
- 使用 Spark MLlib 的 `GBTRegressor`。
- 适合处理表格特征，训练成本低，可解释性较好。

#### 模型 M2：TCN

- 使用一维膨胀卷积。
- 训练速度快，适合作为深度模型的第一版。
- 可与残差连接和因果卷积结合。

#### 模型 M3：PatchTST（后期）

- 将时间序列切片成 patch。
- 使用 Transformer Encoder 学习长距离依赖。
- 输出多步预测。
- 增加分位数预测头，输出 q10、q50、q90。

### 9.3 PatchTST 参考配置（后期）

```yaml
model:
  name: patchtst
  input_length: 672
  prediction_length: 48
  patch_length: 16
  patch_stride: 8
  d_model: 128
  n_heads: 8
  n_layers: 3
  dropout: 0.1
  quantiles: [0.1, 0.5, 0.9]

training:
  batch_size: 64
  learning_rate: 0.001
  max_epochs: 100
  early_stopping_patience: 10
  weight_decay: 0.0001
  gradient_clip: 1.0
  seed: 42
```

具体参数必须根据数据量和显存调整，不应机械照搬。

### 9.4 损失函数

点预测可以使用 Huber Loss，减少异常值影响。概率预测使用分位数损失：

```text
Lq(y, y_hat, q) = max(q * (y - y_hat), (q - 1) * (y - y_hat))
```

总损失：

```text
Loss = L0.1 + L0.5 + L0.9
```

也可以为 50% 分位数增加权重，但要保持验证集评价一致。

### 9.5 数据切分

禁止随机切分。推荐时间顺序：

```text
训练集：最早 70% 时间
验证集：随后 15% 时间
测试集：最后 15% 时间
```

更严格的评估采用滚动回测：

```text
窗口 1：训练 1 到 28 天，验证第 29 到 30 天
窗口 2：训练 2 到 29 天，验证第 30 到 31 天
窗口 3：训练 3 到 30 天，验证第 31 到 32 天
```

每次窗口都必须重新拟合缺失值处理和标准化参数，不能使用全量数据先计算均值和方差。

### 9.6 评估指标

```text
MAE = mean(abs(y - y_hat))
RMSE = sqrt(mean((y - y_hat)^2))
sMAPE = mean(2 * abs(y - y_hat) / (abs(y) + abs(y_hat) + epsilon))
WQL = Weighted Quantile Loss
```

除了总体指标，还要按以下维度分组：

- 预测步长。
- 站点和区域。
- 工作日和周末。
- 早晚高峰和低峰。
- 晴天、雨天和极端天气。
- 节假日和非节假日。
- 高需求站和低需求站。

### 9.7 模型选择

模型选择不能只看测试集最低 MAE。推荐综合：

1. 验证集 WQL。
2. 验证集 MAE。
3. 训练和推理成本。
4. 高峰时段误差。
5. 结果稳定性和漂移风险。
6. 可解释性。

### 9.8 模型回退

预测引擎在任何阶段失败时执行以下回退顺序：

1. 使用当前已发布深度模型。
2. 深度模型失败时使用 Spark MLlib 模型。
3. 机器学习模型失败时使用 Seasonal Naive。
4. 全部失败时返回最近一次有效预测，并明确标记数据截止时间。

## 10. 模型训练流程

```text
1. 读取 feature-vX 数据
2. 执行 Schema 和缺失质量检查
3. 构造训练、验证和测试窗口
4. 拟合只在训练集范围内的预处理参数
5. 训练 M0、M1、M2、M3
6. 在相同验证集上评估
7. 记录 MLflow 参数、指标和模型
8. 生成误差切片和残差图
9. 选出候选模型
10. 人工确认后发布模型版本
11. 批量生成预测并写入 MySQL
```

模型版本格式：

```text
urbanflow-demand-v1.0.0
urbanflow-demand-v1.0.1
urbanflow-demand-v1.1.0
```

## 11. 模型推理设计

### 11.1 批量推理

MVP 优先使用批量推理：

- 每 30 分钟触发一次。
- 读取每个站点最新 672 个时间步。
- 生成未来 48 步 q10、q50、q90。
- 写入 `forecast_run` 和 `forecast_result`。
- 发布成功后更新当前活动预测版本。

### 11.2 在线推理

只有在用户需要即时模拟参数或个性化场景时才增加在线推理。在线推理需要：

- 模型常驻内存。
- 特征实时可用。
- 请求超时和降级策略。
- 批量预测优先，避免重复计算。

## 12. 后端设计

### 12.1 后端分层

```text
Router       HTTP 参数、认证、响应格式
Service      业务规则、权限判断、缓存
Repository   SQL 查询和数据库映射
Schema       Pydantic 请求与响应模型
Core         配置、日志、异常和依赖
```

### 12.2 核心 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/stations` | 站点列表和筛选 |
| GET | `/api/v1/stations/{id}` | 站点详情 |
| GET | `/api/v1/forecasts` | 按站点和时间范围查询预测 |
| GET | `/api/v1/forecasts/latest` | 查询最新预测批次 |
| GET | `/api/v1/dashboard/overview` | 看板总览 |
| GET | `/api/v1/dashboard/rankings` | 高峰和缺口排行 |
| GET | `/api/v1/models` | 模型版本和当前发布状态 |
| GET | `/api/v1/models/{version}/metrics` | 模型评估指标 |
| GET | `/api/v1/data-quality` | 数据质量与新鲜度 |
| GET | `/api/v1/alerts` | 数据、模型和业务告警 |
| POST | `/api/v1/admin/forecast-runs` | 触发批量预测 |
| POST | `/api/v1/admin/model-releases` | 发布模型 |
| POST | `/api/v1/auth/login` | 用户登录 |

### 12.3 统一响应

```json
{
  "code": 200,
  "message": "ok",
  "data": {},
  "request_id": "req_xxx"
}
```

错误响应：

```json
{
  "code": 400,
  "message": "invalid station_id",
  "data": null,
  "request_id": "req_xxx"
}
```

### 12.4 查询接口示例

```http
GET /api/v1/forecasts?city_id=chicago&station_id=123&start=2026-09-10T00:00:00Z&end=2026-09-11T00:00:00Z
```

返回：

```json
{
  "code": 200,
  "message": "ok",
  "data": {
    "model_version": "urbanflow-demand-v1.0.0",
    "data_cutoff": "2026-09-10T00:00:00Z",
    "points": [
      {
        "target_time": "2026-09-10T00:30:00Z",
        "q10": 8.2,
        "q50": 11.5,
        "q90": 15.1
      }
    ]
  }
}
```

### 12.5 缓存策略

- 最新预测结果缓存 30 到 60 秒。
- 站点维度和模型指标缓存 5 分钟。
- 历史预测按站点和时间键缓存。
- 缓存必须在模型发布和数据刷新后失效。
- MVP 可以继续使用进程内 TTL 缓存，规模增加后再引入 Redis。

### 12.6 安全和认证

- 使用 PyJWT 生成和验证 JWT。
- 密码使用 bcrypt 或 Argon2。
- 管理员接口执行角色校验。
- CORS 仅允许配置的前端域名。
- 不向客户端返回堆栈和数据库错误。
- 所有写操作记录操作人和请求 ID。

## 13. 前端设计

### 13.1 页面

| 页面 | 主要内容 |
|---|---|
| `/dashboard` | 总览指标、未来高峰、区域热力、数据状态 |
| `/forecast` | 站点选择、历史与预测曲线、预测区间 |
| `/stations/:id` | 单站点详情、天气和事件影响 |
| `/models` | 模型版本、指标、训练时间和发布状态 |
| `/quality` | 数据新鲜度、缺失率和异常记录 |
| `/alerts` | 数据、模型和业务告警 |
| `/admin` | 任务触发、模型发布和用户管理 |

### 13.2 核心组件

```text
ForecastChart        历史曲线、预测曲线和区间
StationSelector      城市、区域和站点筛选
MetricCard           指标卡
ErrorByHorizon       按预测步长的误差图
WeatherImpact        天气影响分析
QualityIndicator     数据质量状态
ModelVersionBadge    当前模型版本
AlertTable           告警列表
```

### 13.3 图表设计

- 主图使用折线图展示历史需求、q50 预测和 q10-q90 区间。
- 使用按钮切换 6 小时、24 小时和 7 天视图。
- 使用柱状图展示站点缺口排名。
- 使用热力图展示区域时空需求。
- 使用散点图比较观测值和预测值。
- 所有图表显示数据截止时间和模型版本。
- 当数据过期或模型未发布时显示明确状态，不用空白图误导用户。

## 14. 调度与任务设计

MVP 可以先使用 cron 或 Shell：

```text
每 30 分钟：批量预测
每小时：更新实时数据质量
每天 02:00：生成离线特征和日报
每周日 03:00：重训候选模型
每天 04:00：计算漂移和滚动误差
```

当任务数量增加后，再评估 Airflow。不要在 MVP 一开始就引入复杂调度平台。

## 15. 部署设计

### 15.1 开发环境

```text
Flume 本地进程
Kafka Docker
MySQL Docker
Spark 本地模式
MLflow 本地服务
FastAPI 本地进程
Vue Vite 开发服务器
```

### 15.2 Docker Compose 服务

```text
mysql
kafka
zookeeper 或 KRaft
mlflow
backend
frontend
```

Spark、Flume 和模型训练可以按需要挂载到容器中运行。Windows 开发环境需要特别关注路径、权限和 Hadoop 兼容问题。

### 15.3 配置管理

Scala 模块：

```text
application.conf
环境变量覆盖
```

Python 后端和预测引擎：

```text
.env
configs/train.yaml
环境变量覆盖
```

禁止把数据库密码、JWT SECRET 和云存储密钥提交到 Git。

## 16. 测试设计

### 16.1 数据测试

- Schema 字段和类型测试。
- 时间窗口唯一性测试。
- 迟到和重复事件测试。
- 缺失值和异常值处理测试。
- 特征 shift 和无泄漏测试。

### 16.2 模型测试

- 数据切分严格按时间顺序。
- 训练集统计量不能泄漏到验证集。
- 相同种子可以复现结果。
- 输出形状必须为 `[batch, 48, 3]`。
- q10、q50、q90 的排序正确。
- 基线、机器学习和深度模型使用同一测试集。
- 模型发布失败时保留上一版本。

### 16.3 后端测试

- 认证和权限测试。
- 查询参数校验。
- SQL 分页和时间范围测试。
- 缓存失效测试。
- 错误响应不暴露堆栈。

### 16.4 前端测试

- 路由和登录状态。
- 图表无数据状态。
- API 错误状态。
- 模型版本和数据截止时间展示。
- 移动端和桌面端基本布局。

### 16.5 集成测试

```text
模拟事件 -> Kafka -> Spark -> MySQL -> FastAPI -> Vue
```

集成测试不要求使用真实模型，可以先使用固定预测结果验证链路。

## 17. 监控与告警

### 17.1 数据监控

- 最新事件时间。
- 每分钟事件数量。
- 重复率和缺失率。
- 迟到数据比例。
- 站点覆盖比例。

### 17.2 模型监控

- 最近 7 天 MAE、RMSE 和 WQL。
- 预测均值和真实均值偏差。
- 分位数覆盖率。
- 特征分布漂移。
- 不同站点和时段的误差。
- 模型推理耗时。

### 17.3 服务监控

- API 请求量和 P95 延迟。
- 错误率。
- 数据库连接和慢查询。
- 缓存命中率。
- 任务成功率和失败原因。

## 18. 性能设计

- Spark 使用 30 秒微批，避免过小批次造成调度开销。
- 预测结果按批次批量写入 MySQL。
- 历史特征使用 Parquet 列式读取。
- 站点序列按 `station_id` 分区，减少随机访问。
- API 只查询当前活动预测批次。
- 大范围热力图使用预聚合区域指标，不在前端临时计算。
- 深度模型训练先使用小窗口和 TCN 验证流程，再启用 PatchTST。

## 19. 故障处理

| 故障 | 影响 | 降级策略 |
|---|---|---|
| Kafka 暂时不可用 | 实时数据延迟 | 保留文件，恢复后重放 |
| Spark 任务失败 | 实时指标停止 | 从 checkpoint 重启 |
| 天气数据缺失 | 特征不完整 | 缺失标记和最近值 |
| 模型训练失败 | 无法更新模型 | 保留当前发布模型 |
| 模型批量预测失败 | 预测过期 | 使用上一批次并显示过期 |
| MySQL 查询慢 | 页面响应慢 | 缓存、索引和查询限制 |
| 前端 API 失败 | 页面无数据 | 显示错误和最后更新时间 |

## 20. 可解释性设计

- 展示 Seasonal Naive 与最终模型的对比。
- 展示不同特征或特征组移除后的性能变化。
- 对树模型使用特征重要性。
- 对深度模型展示按时间步和站点聚合的误差。
- 对重点预测展示邻近站点、天气和日历影响。
- 不只展示单个“高分案例”，也要展示失败案例。

## 21. 开源工程要求

### 21.1 必备文件

```text
README.md
LICENSE
.gitignore
.env.example
docker-compose.yml
pom.xml
requirements.txt
pyproject.toml
sql/schema.sql
docs/
tests/
```

### 21.2 CI 流程

```text
Python lint + unit test
Scala compile + test
Frontend build + unit test
SQL schema validation
Mermaid documentation build
```

### 21.3 Definition of Done

一个功能完成必须同时满足：

1. 代码和配置已提交。
2. 单元测试或集成测试通过。
3. 文档和接口示例已更新。
4. 不包含明文密钥。
5. 不引入未记录的数据泄漏。
6. 错误和降级行为明确。
7. 可以在干净环境复现。

## 22. 实施顺序

```text
第一步：数据字典、MySQL Schema、虚拟数据生成器
第二步：Kafka、Spark Streaming、MySQL 实时链路
第三步：本地 Parquet 标准化数据和 Spark SQL 离线特征
第四步：Seasonal Naive 与基础时间回测框架
第五步：PyTorch TCN
第六步：FastAPI 与 Vue 看板
第七步：测试、README 和演示
第八步（后期）：Flume 和 Parquet 服务化
第九步（后期）：Spark MLlib 与 PatchTST
第十步（后期）：MLflow、监控和模型发布
```

## 23. 需要避免的设计问题

1. 不把原始事件长期堆积在 MySQL。
2. 不用随机切分评估时间序列。
3. 不先计算全量数据的均值、方差和分位数。
4. 不把未来天气或未来需求错误地作为历史特征。
5. 不在 API 请求中同步训练模型。
6. 不让前端依赖未发布模型。
7. 不把 MLflow 本地实验目录提交到 Git。
8. 不用准确率描述连续需求预测。
9. 不伪造项目指标或业务收益。
10. 不为了“技术栈更多”引入与当前问题无关的组件。

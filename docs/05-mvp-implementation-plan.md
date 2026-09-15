# UrbanFlow MVP 实施清单

> **English summary:** This document defines the MVP scope, implementation
> order, quality gates, deliverables, and explicitly excluded features.
>
> **中文摘要：** 本文定义 MVP 范围、实施顺序、质量门槛、交付物和明确不做
> 的功能。

## 1. MVP 目标

MVP 不追求真实城市数据、复杂模型和完整生产架构。它需要证明一条完整链路可以工作，同时满足 GitHub 开源项目的最低要求：

```text
虚拟需求数据
  -> Kafka
  -> Spark Structured Streaming
  -> MySQL
  -> 离线特征
  -> Seasonal Naive + PyTorch TCN
  -> FastAPI
  -> Vue 3 + ECharts
```

项目规模可以缩小，但 README、许可证、忽略文件、环境模板、测试、贡献说明和复现步骤不能省略。

完成这条链路后，再逐步考虑真实数据、Flume、PatchTST、MLflow、监控和更复杂的调度决策。

## 2. MVP 范围

### 2.1 数据规模

建议第一版只使用：

- 1 个虚拟城市。
- 20 个站点。
- 90 天历史数据。
- 30 分钟聚合粒度。
- 每天 48 个时间点。
- 约 86,400 条站点需求观测。
- 实时模拟每秒或每两秒发送少量事件。

这个规模足以训练时序模型，也可以在普通电脑上运行。

### 2.2 数据生成规则

虚拟数据不能完全随机，否则模型没有规律可以学习。生成器应包含：

- 早晚高峰。
- 工作日与周末差异。
- 站点基础需求差异。
- 随机噪声。
- 雨天需求扰动。
- 节假日扰动。
- 少量异常高峰。

建议生成公式：

```text
demand =
    站点基础需求
    * 日内模式
    * 星期模式
    * 节假日系数
    * 天气系数
    + 随机噪声
    + 异常扰动
```

例如：

```text
工作日早上 8 点需求高
工作日凌晨 3 点需求低
周末中午需求相对更高
下雨时部分交通接驳站点需求上升
节假日部分商业区站点需求变化明显
```

### 2.3 初期不做的内容

- 不接入真实城市数据。
- 不采集网络天气，先使用虚拟天气字段。
- 不引入 Flume，直接由 Python 生成器写入 Kafka。
- 不引入 MLflow，训练结果先写 JSON 和 MySQL。
- 不训练 PatchTST 或大型 Transformer。
- 不做用户注册、复杂权限和管理后台。
- 不做实时在线推理，先做定时批量预测。
- 不做复杂调度优化，只输出站点优先级。
- 不做 Kubernetes、集群和云部署。

### 2.4 开源基础能力属于 P0

以下内容不能推迟到后期：

- README 和项目状态。
- MIT License。
- `.gitignore` 和 `.env.example`。
- 虚拟数据生成和固定随机种子。
- 基础测试。
- 依赖版本和启动命令。
- 贡献指南和安全政策。
- Issue 和 Pull Request 模板。
- GitHub Actions 基础校验。
- 数据来源和许可证说明。

## 3. MVP 技术栈

| 层级 | 技术 | MVP 用途 |
|---|---|---|
| 虚拟数据 | Python | 生成站点需求和天气字段 |
| 消息队列 | Kafka | 优先使用现有 Linux 虚拟机，Docker 为备用方案 |
| 实时计算 | Scala + Spark Structured Streaming | 清洗和窗口聚合 |
| 离线特征 | Spark SQL | 生成滞后、滑动和日历特征 |
| 存储 | MySQL | 优先复用本机 MySQL 8.0，Docker 容器使用 3307 端口 |
| 预测模型 | Python + PyTorch | 实现一个小型 TCN |
| 基线模型 | Python/Spark MLlib | Seasonal Naive 和简单机器学习基线 |
| 后端 | FastAPI | 提供历史、预测和模型状态 API |
| 前端 | Vue 3 + Pinia + ECharts | 展示趋势和预测 |
| 构建 | Maven、npm | 后端编译和前端构建 |

MVP 新增技术只有 PyTorch。Kafka、Spark、MySQL、FastAPI 和 Vue 都沿用原项目技术栈。

## 4. MVP 项目结构

```text
urbanflow-forecast/
├── common/
├── realtime-analysis/
├── offline-analysis/
├── forecast-engine/
│   ├── configs/
│   ├── src/urbanflow_forecast/
│   │   ├── data/
│   │   ├── features/
│   │   ├── models/
│   │   ├── evaluation/
│   │   └── inference/
│   └── tests/
├── backend/
├── frontend/
├── simulator/
├── sql/
├── docker/
└── docs/
```

为了减少第一版复杂度，可以暂时省略：

```text
MLflow 服务
MinIO
Airflow
Prometheus
Grafana
Redis
```

## 5. MVP 数据表

第一版只需要以下表：

| 表 | 用途 |
|---|---|
| `station_dim` | 站点基础信息 |
| `demand_observation` | 30 分钟需求观测 |
| `realtime_demand_metrics` | Spark 实时聚合结果 |
| `forecast_result` | 最新预测结果 |
| `model_metric` | 基线模型和 TCN 指标 |
| `job_run_log` | 数据生成、训练和预测任务状态 |

`forecast_result` 第一版可以简化：

```sql
CREATE TABLE forecast_result (
    id BIGINT NOT NULL AUTO_INCREMENT,
    station_id VARCHAR(64) NOT NULL,
    target_time DATETIME NOT NULL,
    horizon_step INT NOT NULL,
    predicted_demand DECIMAL(12,4) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_forecast_point (
        station_id, target_time, model_version
    ),
    KEY idx_forecast_query (station_id, target_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

在完成点预测后，再增加 `predicted_q10` 和 `predicted_q90`。

## 6. MVP 模型

### 6.1 Seasonal Naive

```text
预测当前时间 = 前一天同一时间需求
```

作用：

- 验证数据管道。
- 提供最低对照基线。
- 发现数据时间口径错误。

### 6.2 PyTorch TCN

选择 TCN 而不是 PatchTST 的原因：

- 模型小，训练速度快。
- 对普通笔记本或单 GPU 更友好。
- 可以处理多变量输入和多步输出。
- 仍然能够展示 PyTorch、滑动窗口、深度时序建模和回测能力。

第一版参考参数：

```yaml
input_length: 336
prediction_length: 48
channels: [32, 64]
kernel_size: 3
dropout: 0.1
batch_size: 64
learning_rate: 0.001
max_epochs: 50
early_stopping_patience: 8
```

### 6.3 MVP 评价

第一版计算：

- MAE。
- RMSE。
- sMAPE。
- 相对 Seasonal Naive 的改善比例。

概率预测、WQL、PatchTST 和模型注册放到下一阶段。

## 7. MVP API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 服务状态 |
| GET | `/api/v1/stations` | 站点列表 |
| GET | `/api/v1/demand/history` | 查询历史需求 |
| GET | `/api/v1/forecasts/latest` | 查询最新预测 |
| GET | `/api/v1/models/metrics` | 查询模型指标 |
| GET | `/api/v1/dashboard/summary` | 查询首页汇总 |
| POST | `/api/v1/jobs/simulate` | 可选，启动模拟数据 |
| POST | `/api/v1/jobs/forecast` | 可选，触发批量预测 |

第一版不实现登录和权限，等核心链路稳定后再补充。

## 8. MVP 页面

第一版只需要三个页面：

### 总览页

- 当前总需求。
- 未来高峰站点。
- 最近模型 MAE。
- 数据最新时间。

### 预测页

- 选择站点。
- 展示过去 7 天历史需求。
- 展示未来 24 小时预测。
- 展示模型版本和生成时间。

### 模型页

- Seasonal Naive 与 TCN 指标。
- 不同预测步长误差。
- 最近一次训练和预测状态。

站点详情、告警、数据质量、管理后台和调度建议可以后续增加。

## 9. MVP 开发顺序

### 第 1 阶段：数据与存储

- 创建根 Maven POM。
- 检查 Git 忽略规则，避免提交数据、模型和虚拟环境。
- 创建 `sql/schema.sql`。
- 编写虚拟数据生成器。
- 生成 90 天历史数据。
- 将数据写入本地文件和 MySQL。

验收：

```text
可以生成 20 个站点、90 天、30 分钟粒度的数据
数据包含高峰、周末、节假日和天气变化
```

### 第 2 阶段：实时链路

- 复用本机 MySQL，并在现有 Linux 虚拟机中启动 Kafka。
- 如果没有现成环境，再用 Docker Compose 作为备用方案。
- Python 模拟器持续发送 JSON 到 Kafka。
- Spark Structured Streaming 读取 Kafka。
- 按 30 分钟窗口聚合并写入 MySQL。

验收：

```text
Kafka 可收到事件
Spark 可以稳定写入 realtime_demand_metrics
页面或 SQL 可以查看最近聚合结果
```

### 第 3 阶段：特征与基线

- Spark SQL 读取历史观测。
- 生成 lag、rolling、日历和站点特征。
- 按时间切分训练集、验证集和测试集。
- 实现 Seasonal Naive。
- 输出基线和第一版指标。

验收：

```text
不存在随机切分
不使用未来需求特征
基线可以生成未来 48 步预测
```

### 第 4 阶段：TCN

- 构造滑窗数据集。
- 实现 PyTorch TCN。
- 训练、早停和保存模型。
- 在同一测试集上与基线比较。
- 生成未来 48 步预测并写入 MySQL。

验收：

```text
模型可以复现训练
输出形状与 48 个预测步一致
能够展示 MAE、RMSE 和 sMAPE
```

### 第 5 阶段：API

- 搭建 FastAPI。
- 实现历史和预测查询。
- 实现模型指标查询。
- 增加统一错误处理。

验收：

```text
可以通过 HTTP 查询站点需求
可以查询指定站点未来 24 小时预测
接口返回模型版本和生成时间
```

### 第 6 阶段：Vue 页面

- 创建 Vue 3 + Vite 工程。
- 使用 Pinia 管理页面状态。
- 使用 ECharts 绘制历史与预测曲线。
- 使用 Vite 代理访问 FastAPI。

验收：

```text
选择站点后可以看到历史曲线和预测曲线
页面显示模型指标和数据更新时间
没有数据或接口失败时有明确提示
```

### 第 7 阶段：开源发布

- 补齐 README 的安装、运行、测试和截图。
- 校验 `.gitignore`、`.env.example` 和许可证。
- 增加 GitHub Actions。
- 执行无缓存或干净环境验证。
- 创建 `v0.1.0` Release。

验收：

```text
新用户可以按照 README 生成虚拟数据并启动核心链路
仓库不包含密钥、真实数据、依赖目录和大型模型文件
CI 至少可以执行并通过一项核心检查
```

## 10. MVP 验收清单

- [ ] 可以一键生成虚拟数据。
- [ ] 虚拟数据可以通过 Kafka 进入 Spark。
- [ ] Spark 可以聚合并写入 MySQL。
- [ ] 可以生成时间顺序正确的训练和测试数据。
- [ ] Seasonal Naive 可以工作。
- [ ] PyTorch TCN 可以训练、保存和加载。
- [ ] 可以批量生成未来 48 步预测。
- [ ] FastAPI 可以查询历史和预测。
- [ ] Vue 页面可以展示趋势。
- [ ] 代码可以在干净环境按 README 启动。
- [ ] 文档明确说明当前使用虚拟数据。
- [ ] MIT License、贡献指南、安全政策和 Issue/PR 模板存在。
- [ ] `.gitignore` 可以阻止密钥、数据和模型进入 Git。
- [ ] 虚拟数据可以通过固定随机种子重建。
- [ ] 核心链路至少有一条自动化测试。
- [ ] GitHub Actions 可以执行基础检查。

## 11. 后期扩展

完成 MVP 后再按优先级增加：

1. 真实城市数据适配器。
2. Flume 文件采集链路。
3. Parquet 特征存储。
4. MLflow 实验追踪。
5. 概率预测 q10、q50、q90。
6. PatchTST 或 Temporal Fusion Transformer。
7. 模型漂移和误差监控。
8. 调度建议和简单优化。
9. 用户认证和管理后台。
10. Docker Compose 和云端部署。

## 12. 最小成功标准

只要做到以下三件事，MVP 就算成功：

1. 虚拟数据可以自动生成并进入完整数据管道。
2. 系统可以训练模型并输出未来 24 小时预测。
3. 用户可以在页面上看到历史需求、预测结果和模型指标。

真实数据、复杂模型和高级架构不阻塞 MVP 完成。

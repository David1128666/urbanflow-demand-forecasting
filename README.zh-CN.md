# UrbanFlow：城市需求时序预测与调度支持平台

[English README](README.md)

> **English summary:** UrbanFlow is an AI-assisted urban bike-demand
> forecasting and dispatch decision-support platform built with Kafka, Spark,
> PyTorch TCN, FastAPI, Vue, and MySQL. See [README.md](README.md) for the full
> English guide.

> GitHub 默认英文界面。项目保留完整中文资源，可通过前端右上角语言按钮切换，
> 也可以使用后端 `APP_LANGUAGE=zh-CN` 和引擎 `URBANFLOW_LANGUAGE=zh-CN`
> 生成中文 API 与调度文案。

UrbanFlow 是一个面向城市出行需求的开源时序预测项目。项目采用“MVP 优先、真实数据后置”的策略：先使用可控的虚拟数据完成需求预测、模型训练、预测服务和可视化闭环，后期再接入真实城市数据并完善工程能力。

## MVP 实施原则

1. 功能优先：先跑通预测全流程，不追求一步到位的大而全架构。
2. 虚拟数据优先：真实数据暂时获取困难，先用模拟数据验证业务和模型。
3. 单机优先：优先保证一台普通开发电脑可以运行。
4. 可替换优先：数据源、模型和存储都通过清晰接口隔离，后期可以替换。
5. 渐进增强：Flume、Parquet、MLflow、复杂深度模型和高级监控后置。

## MVP 主链路

```text
Python 虚拟数据生成器
        |
        v
      Kafka
        |
        v
Spark Structured Streaming
        |
        v
      MySQL
        |
        +--> Spark SQL 离线特征
        |          |
        |          v
        |    Python/PyTorch 预测模型
        |          |
        +----------+
        |
        v
   FastAPI -> Vue 3 + ECharts
```

## 分阶段范围

| 阶段 | 目标 | 技术 |
|---|---|---|
| MVP 0 | 跑通虚拟数据、实时聚合、API 和页面 | Python、Kafka、Spark、MySQL、FastAPI、Vue |
| MVP 1 | 完成特征、回测和时序预测 | Spark SQL、Seasonal Naive、PyTorch/TCN |
| MVP 2 | 增强模型与工程能力 | PatchTST、Flume、Parquet、MLflow |
| 后期 | 接入真实数据和业务决策 | 真实数据适配器、调度建议、监控和部署 |

## 文档索引

| 文档 | 内容 |
|---|---|
| [05 MVP 实施清单](docs/05-mvp-implementation-plan.md) | 当前开发的唯一范围基线、最小功能清单和实施顺序 |
| [01 项目文档](docs/01-project-brief.md) | MVP 范围、功能需求、验收标准和分阶段计划 |
| [02 C4 架构图](docs/02-c4-architecture.md) | MVP 容器图、后期目标架构和数据流 |
| [03 详细设计说明书](docs/03-detailed-design.md) | MVP 必做设计、后期目标设计和完整参考 |
| [04 通俗讲解文档](docs/04-plain-language-guide.md) | 用非技术语言解释项目价值和演示方式 |
| [06 GitHub 开源指南](docs/06-open-source-guide.md) | 开源必备文件、复现要求、测试和首次发布清单 |
| [07 第 1 到第 5 步验收报告](docs/07-step-1-5-verification.md) | 当前阶段的编译、数据库、虚拟数据和 Kafka 验收结果 |
| [08 第 6 步验收报告](docs/08-step-6-verification.md) | Kafka 到 Spark 到 MySQL 的实时窗口聚合验收结果 |
| [09 第 7 步验收报告](docs/09-step-7-verification.md) | 滞后、滑动、日历、天气特征和时间切分验收结果 |
| [10 第 8 步验收报告](docs/10-step-8-verification.md) | Seasonal Naive 一步与 48 步预测指标及图表 |
| [11 第 9 步验收报告](docs/11-step-9-verification.md) | TCN 训练、测试及与 Seasonal Naive 的配对比较 |
| [12 第 10 步验收报告](docs/12-step-10-verification.md) | 批量预测、MySQL 写入和需求分析结果 |
| [13 第 11 步验收报告](docs/13-step-11-verification.md) | 站点、历史需求、预测、模型和看板 API 验收 |
| [14 第 12 步验收报告](docs/14-step-12-verification.md) | Vue 完整功能页面和真实数据展示验收 |
| [15 业务语义与调度闭环验收](docs/15-business-value-dispatch-verification.md) | 库存、缺口、调运工单和模拟影响验收 |
| [代码制作任务计划](code/CODE_TASK_PLAN.md) | 用通俗语言列出代码制作的顺序和完成标准 |
| [CHANGELOG](CHANGELOG.md) | 项目版本变化记录 |

当前开发以 `05-mvp-implementation-plan.md` 为范围基线。`01` 到 `04` 中标记为后期的内容，不作为 MVP 验收条件。

## GitHub 开源基线

项目虽然先做小型 MVP，但会保留开源项目的基础要求：

- 清晰的 README、当前状态和快速开始。
- MIT License。
- `.gitignore` 和 `.env.example`。
- 贡献指南、安全政策和行为准则。
- Issue、Bug 和 Pull Request 模板。
- 固定随机种子和可重新生成的虚拟数据。
- 可执行的数据、模型、后端和前端测试。
- GitHub Actions 持续集成。
- 真实数据接入前的许可证和隐私检查。

## 项目状态

- 当前阶段：基础预测闭环和调度决策页面已完成，进入测试、CI 和发布收尾
- 当前版本：v0.1.0
- 目标预测粒度：30 分钟
- MVP 预测范围：未来 24 小时，共 48 个预测点
- MVP 数据源：可配置的虚拟城市需求数据
- 后期数据源：城市开放数据、天气数据、日历数据
- 开源许可证：MIT

## 当前能回答的业务问题

UrbanFlow 不把预测值只当作一条曲线，而是继续转换成运营动作：

```text
未来 30 分钟有多少骑行订单
  -> 未来 2 小时累计需要多少辆可借车
  -> 当前库存还缺多少辆
  -> 从哪个盈余站点调多少辆
  -> 最晚何时完成
  -> 模拟执行后还能剩多少缺口
```

当前 100% 缺口改善是虚拟数据下的模拟结果，不是真实经营收益。项目文档明确区分预测值、风险暴露量和模拟改善，避免把演示数字当成实际业务成果。

## 核心目标

1. 使用虚拟数据建立从事件产生、实时处理、特征、模型、API 到可视化的完整闭环。
2. 使用严格的时间序列回测方法，量化模型相对基线的提升。
3. 先实现 24 小时点预测，再增加预测区间和误差分析。
4. 将预测结果转化为简单的站点优先级建议。
5. 保持代码可扩展，后期可以接入真实数据和更复杂模型。

## 建议仓库结构

```text
urbanflow-forecast/
├── common/                  # Scala 公共模型、配置和工具
├── realtime-analysis/       # Spark Structured Streaming 实时处理
├── offline-analysis/        # Spark SQL 离线特征和统计
├── forecast-engine/         # Python 预测、训练、回测和批量推理
├── backend/                 # FastAPI 业务后端
├── frontend/                # Vue 3 + Pinia + ECharts
├── simulator/               # 虚拟数据生成与发送
├── sql/                     # MySQL DDL、视图和初始化数据
├── docker/                  # 本地基础设施编排
├── .github/                 # Issue、PR 和 CI 配置
├── tests/                   # 单元、集成和模型测试
└── docs/                    # 项目文档
```

## 下一步

1. 完成第 13 步的回归测试和 GitHub Actions 扩展。
2. 补充页面截图、启动顺序和已知限制。
3. 完成第 14 步的 README、CHANGELOG 和 `v0.1.0` 发布检查。
4. 首版发布后，再接入真实城市数据、车辆归还预测和工单执行回写。

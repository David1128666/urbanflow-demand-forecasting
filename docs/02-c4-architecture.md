# UrbanFlow C4 架构说明

> **English summary:** This document presents the C4 context, container,
> component, deployment, and data-flow views, together with the target
> architecture and evolution path.
>
> **中文摘要：** 本文展示 C4 系统上下文、容器、组件、部署和数据流视图，
> 并说明目标架构与后续演进路径。

## 1. 文档目的

本文使用 C4 模型描述 UrbanFlow 的系统边界、容器、核心组件和关键数据流。C4 图使用 Mermaid 编写，可直接在支持 Mermaid 的 Markdown 渲染器中查看。

本文同时描述两个层次：

- 当前 MVP：只实现虚拟数据到预测页面的最小闭环。
- 目标架构：后期增加 Flume、MLflow、概率预测、复杂模型和真实数据。

本文包含：

- MVP 容器图。
- 目标系统上下文图。
- 目标容器图。
- 目标预测引擎组件图。
- 目标数据管线流程图。
- 预测查询与模型训练时序图。

## 2. 架构原则

1. MVP 先使用虚拟数据，真实数据通过适配器后期接入。
2. MVP 不引入 Flume、MLflow、Parquet 服务和复杂部署。
3. Kafka、Spark、MySQL、FastAPI 和 Vue 保持原项目技术栈。
4. PyTorch 只负责深度时序模型训练和推理，不替代 Spark。
5. MySQL 保存 MVP 的观测、实时指标、预测和任务状态。
6. 当前先实现点预测，概率区间和复杂模型后期增加。
7. 前端不直接访问数据库，也不包含模型逻辑。

## 3. MVP 容器图

这张图表示当前真正需要实现的最小功能。图中的所有组件都属于 MVP，不包含 Flume、MLflow 和 PatchTST。

```mermaid
C4Container
    title UrbanFlow MVP 容器图

    Person(analyst, "运营分析师", "查看历史需求和未来 24 小时预测")
    Person(scientist, "数据科学家", "使用虚拟数据训练和评估模型")

    System_Boundary(urbanflow, "UrbanFlow MVP") {
        Container(simulator, "虚拟数据生成器", "Python", "生成有周期、天气和异常规律的需求事件")
        ContainerQueue(kafka, "消息队列", "Apache Kafka", "接收模拟实时事件")
        Container(streaming, "实时分析模块", "Scala + Spark Structured Streaming", "清洗事件并按 30 分钟聚合")
        Container(batch, "离线分析模块", "Scala + Spark SQL", "生成滞后、滑动、日历和天气特征")
        Container(forecast, "预测引擎", "Python + PyTorch", "训练 Seasonal Naive 和 TCN，生成 48 步预测")
        ContainerDb(datasets, "本地数据集", "CSV/Parquet", "保存历史观测、特征和模型文件")
        ContainerDb(mysql, "服务数据库", "MySQL 8", "保存观测、实时指标、预测结果和任务状态")
        Container(api, "业务后端", "Python + FastAPI", "提供历史、预测和模型指标 API")
        Container(spa, "可视化前端", "Vue 3 + Pinia + Vite", "展示趋势、预测和模型指标")
    }

    Rel(simulator, kafka, "发送虚拟需求事件", "Kafka Protocol")
    Rel(kafka, streaming, "消费实时事件", "Kafka Protocol")
    Rel(streaming, mysql, "写入 30 分钟实时指标", "JDBC")
    Rel(streaming, datasets, "写入标准化历史数据", "File/Parquet")
    Rel(datasets, batch, "读取历史数据", "Spark SQL")
    Rel(mysql, batch, "读取站点维度", "JDBC")
    Rel(batch, datasets, "写出版本化特征", "Parquet")
    Rel(datasets, forecast, "读取训练和回测数据", "Python/PyArrow")
    Rel(forecast, mysql, "写入预测和模型指标", "PyMySQL")
    Rel(api, mysql, "查询历史和预测", "PyMySQL")
    Rel(spa, api, "调用 REST API", "JSON/HTTPS")
    Rel(analyst, spa, "查看预测", "HTTPS")
    Rel(scientist, forecast, "执行训练和批量预测", "CLI")
```

## 4. 目标系统上下文图

系统上下文关注“谁使用 UrbanFlow”和“UrbanFlow 依赖哪些外部系统”。

```mermaid
C4Context
    title UrbanFlow 系统上下文图

    Person(analyst, "运营分析师", "查看未来需求、误差和调度优先级")
    Person(operator, "调度人员", "根据短期预测安排车辆或运力")
    Person(admin, "系统管理员", "维护数据、模型、任务和用户")
    Person(scientist, "数据科学家", "训练、回测、比较和发布模型")

    System(urbanflow, "UrbanFlow", "城市时空需求预测与调度支持平台")

    System_Ext(citydata, "城市开放数据平台", "提供历史出行和增量需求数据")
    System_Ext(weather, "天气数据服务", "提供历史天气和未来天气预报")
    System_Ext(calendar, "日历与节假日服务", "提供日期、周末、节假日和调休信息")
    System_Ext(eventdata, "城市事件数据源", "可选的演唱会、赛事、封路等活动信息")

    Rel(analyst, urbanflow, "查看预测、误差和站点排名", "HTTPS")
    Rel(operator, urbanflow, "查看短期缺口和调度建议", "HTTPS")
    Rel(admin, urbanflow, "监控数据质量、任务和模型状态", "HTTPS")
    Rel(scientist, urbanflow, "执行训练、回测和模型发布", "CLI/HTTPS")

    Rel(urbanflow, citydata, "读取历史与增量需求数据", "HTTPS/文件")
    Rel(urbanflow, weather, "读取天气特征", "HTTPS")
    Rel(urbanflow, calendar, "读取日历特征", "HTTPS/文件")
    Rel(urbanflow, eventdata, "读取事件特征", "HTTPS，可选")
```

## 5. 目标容器图

这张图表示后期完整目标，不代表 MVP 首批实现范围。

```mermaid
C4Container
    title UrbanFlow 容器图

    Person(analyst, "运营分析师", "查看预测和调度建议")
    Person(scientist, "数据科学家", "训练和发布模型")

    System_Ext(citydata, "城市开放数据平台", "提供出行需求数据")
    System_Ext(weather, "天气数据服务", "提供天气特征")

    System_Boundary(urbanflow, "UrbanFlow") {
        Container(simulator, "数据模拟器", "Python + Shell", "生成和发送模拟需求事件")
        Container(flume, "文件采集代理", "Apache Flume", "监控数据文件并发送到 Kafka")
        ContainerQueue(kafka, "事件消息队列", "Apache Kafka", "缓存和分发需求、天气和状态事件")
        Container(streaming, "实时分析模块", "Scala + Spark Structured Streaming", "清洗事件、窗口聚合和实时质量检查")
        Container(batch, "离线分析模块", "Scala + Spark SQL", "生成离线特征、统计和回测数据集")
        Container(forecast, "预测引擎", "Python + PyTorch", "训练、评估和批量生成时序预测")
        Container(mlflow, "实验与模型注册", "MLflow", "记录参数、指标、模型和版本")
        ContainerDb(features, "特征与数据集存储", "Parquet", "保存版本化特征、训练集和回测集")
        ContainerDb(mysql, "服务数据库", "MySQL 8", "保存事件、实时指标、预测结果和任务状态")
        Container(api, "业务后端", "Python + FastAPI", "认证、查询、聚合和预测接口")
        Container(spa, "可视化前端", "Vue 3 + Pinia + Vite", "预测看板、误差分析和管理页面")
    }

    Rel(citydata, simulator, "提供原始公开数据", "文件/HTTPS")
    Rel(weather, batch, "提供天气特征数据", "HTTPS")
    Rel(simulator, flume, "写入增量 JSON 文件", "文件系统")
    Rel(flume, kafka, "发布标准事件", "Kafka Protocol")
    Rel(kafka, streaming, "消费实时事件", "Kafka Protocol")
    Rel(streaming, mysql, "写入实时指标和数据质量结果", "JDBC")
    Rel(streaming, features, "写入标准化事件", "Parquet")
    Rel(features, batch, "读取历史和标准化事件", "File")
    Rel(mysql, batch, "读取维度与业务数据", "JDBC")
    Rel(batch, features, "写出版本化特征", "Parquet")
    Rel(forecast, features, "读取训练和回测特征", "Python/PyArrow")
    Rel(forecast, mlflow, "记录实验与注册模型", "MLflow API")
    Rel(forecast, mysql, "写入预测、评估和漂移结果", "PyMySQL")
    Rel(api, mysql, "查询预测和业务数据", "PyMySQL")
    Rel(spa, api, "调用 REST API", "JSON/HTTPS")
    Rel(analyst, spa, "查看预测和调度建议", "HTTPS")
    Rel(scientist, forecast, "配置并执行训练", "CLI")
```

## 6. 目标预测引擎组件图

预测引擎是新增的核心 AI 模块。MVP 只需要其中的读取器、校验器、数据集构建器、切分器、Seasonal Naive、TCN、评估器和推理器。MLflow、PatchTST 和复杂解释器属于后期。

```mermaid
C4Component
    title UrbanFlow 预测引擎组件图

    ContainerDb(features, "特征存储", "Parquet", "训练、验证和回测特征")
    ContainerDb(mysql, "服务数据库", "MySQL 8", "预测结果与评估指标")
    Container(mlflow, "实验与模型注册", "MLflow", "参数、指标和模型版本")
    Container(scheduler, "任务调度器", "Cron/Shell", "定时触发训练和批量预测")

    Container_Boundary(forecast, "Forecast Engine") {
        Component(reader, "特征读取器", "Python + PyArrow", "读取指定版本的特征数据")
        Component(validator, "特征校验器", "Pydantic + Pandas", "检查字段、时间范围和缺失情况")
        Component(transformer, "特征变换器", "NumPy + Pandas", "缩放、编码、时间与天气特征变换")
        Component(builder, "数据集构建器", "PyTorch Dataset", "构造滑窗样本和多步预测标签")
        Component(splitter, "时间回测切分器", "Python", "生成训练、验证、测试和滚动窗口")
        Component(baselines, "基线模型", "统计方法 + Spark MLlib", "Seasonal Naive、移动平均、梯度提升")
        Component(deepmodel, "深度预测模型", "PyTorch + PatchTST/TCN", "学习多变量、多步时序依赖")
        Component(trainer, "训练与调参器", "PyTorch", "训练循环、早停、学习率调度和随机种子")
        Component(evaluator, "模型评估器", "NumPy + Pandas", "计算 MAE、RMSE、sMAPE 和 WQL")
        Component(explainer, "误差解释器", "Pandas + SHAP/注意力", "分析特征、时段和场景误差")
        Component(registry, "模型登记器", "MLflow SDK", "记录指标并注册最佳模型")
        Component(inference, "批量推理器", "PyTorch", "生成未来 48 步点预测和分位数")
        Component(writer, "结果写回器", "PyMySQL", "将预测和状态写入 MySQL")
    }

    Rel(scheduler, trainer, "触发训练", "CLI")
    Rel(scheduler, inference, "触发批量预测", "CLI")
    Rel(features, reader, "提供特征文件", "File")
    Rel(reader, validator, "传递原始特征", "DataFrame")
    Rel(validator, transformer, "传递合法特征", "DataFrame")
    Rel(transformer, builder, "传递处理后的特征", "Array/DataFrame")
    Rel(splitter, builder, "提供时间窗口索引", "Python")
    Rel(builder, baselines, "提供训练和验证数据", "Dataset")
    Rel(builder, deepmodel, "提供滑窗张量", "Tensor")
    Rel(baselines, trainer, "提供基线预测", "Array")
    Rel(deepmodel, trainer, "提供模型输出", "Tensor")
    Rel(trainer, evaluator, "提供验证结果", "Array")
    Rel(evaluator, explainer, "提供指标和残差", "DataFrame")
    Rel(evaluator, registry, "提供最佳指标", "Metrics")
    Rel(registry, mlflow, "保存实验和模型", "MLflow API")
    Rel(mlflow, inference, "提供已发布模型", "Model URI")
    Rel(inference, writer, "提供预测结果", "DataFrame")
    Rel(writer, mysql, "写入预测和状态", "PyMySQL")
```

## 7. 目标数据管线流程图

这张图包含完整的后期数据管线。MVP 不经过 Flume，也不使用 MLflow，直接由虚拟数据生成器写入 Kafka。

```mermaid
flowchart LR
    A["公开城市数据"] --> B["标准化与数据版本"]
    S["模拟增量数据"] --> C["Flume"]
    B --> C
    C --> D["Kafka"]
    D --> E["Spark Structured Streaming"]
    E --> F["实时指标"]
    E --> G["标准化事件"]
    F --> H["MySQL 服务库"]
    G --> I["Parquet 特征存储"]
    I --> J["Spark SQL 离线特征"]
    J --> K["版本化训练与回测集"]
    K --> L["Seasonal Naive 基线"]
    K --> M["Spark MLlib 基线"]
    K --> N["PyTorch 时序模型"]
    L --> O["统一评估与滚动回测"]
    M --> O
    N --> O
    O --> P["MLflow 实验与模型注册"]
    P --> Q["批量预测"]
    Q --> H
    H --> R["FastAPI"]
    R --> T["Vue 3 + ECharts"]
```

## 8. 预测查询时序图

```mermaid
sequenceDiagram
    autonumber
    actor User as 运营分析师
    participant UI as Vue 前端
    participant API as FastAPI 后端
    participant Cache as 进程内缓存
    participant DB as MySQL

    User->>UI: 选择城市、站点和时间范围
    UI->>API: GET /api/v1/forecasts
    API->>API: 校验参数与用户身份
    API->>Cache: 查询缓存
    alt 缓存命中
        Cache-->>API: 返回预测结果
    else 缓存未命中
        API->>DB: 查询 forecast_result
        DB-->>API: 返回 48 步预测
        API->>Cache: 写入短期缓存
    end
    API-->>UI: 返回预测、区间和模型版本
    UI-->>User: 绘制历史曲线、预测曲线和告警
```

## 9. 模型训练与发布时序图

```mermaid
sequenceDiagram
    autonumber
    actor Scientist as 数据科学家
    participant Scheduler as 调度器
    participant Spark as Spark 离线分析
    participant Store as Parquet 特征存储
    participant Engine as Forecast Engine
    participant MLflow as MLflow
    participant DB as MySQL
    participant API as FastAPI

    Scientist->>Engine: 配置模型与特征版本
    Scheduler->>Spark: 触发特征生成
    Spark->>Store: 写出版本化特征
    Scheduler->>Engine: 触发训练
    Engine->>Store: 读取训练与回测集
    Engine->>Engine: 时间切分、训练和评估
    Engine->>MLflow: 记录参数、指标和模型
    Engine->>DB: 写入评估结果
    Scientist->>MLflow: 检查并发布最佳模型
    Scheduler->>Engine: 使用已发布模型批量预测
    Engine->>DB: 写入 forecast_result
    API->>DB: 查询最新已发布预测
```

## 10. 部署拓扑

MVP 可以在单机 Docker Compose 中运行：

| 服务 | 端口示例 | 说明 |
|---|---:|---|
| Vue/Vite | 5173 | 开发环境前端 |
| FastAPI | 8000 | 业务 API |
| MySQL | 3306 | 服务数据库 |
| Kafka | 9092 | 消息队列 |
| Spark UI | 4040 | Spark 任务监控 |
| MLflow | 5000 | 实验和模型查看 |
| Flume | 无固定端口 | 本地文件采集 |

生产扩展可以拆分为：

- Nginx 托管 Vue 构建产物。
- FastAPI 和预测服务独立部署。
- Kafka 使用至少三节点集群。
- Spark 使用 YARN、Kubernetes 或 Standalone 集群。
- MySQL 使用主从复制和定期备份。
- Parquet 和模型文件迁移到 MinIO、HDFS 或云对象存储。
- MLflow 后端数据库与对象存储独立配置。

## 11. 关键架构决策

| 决策 | 选择 | 原因 |
|---|---|---|
| 数据架构 | Lambda | 保留原项目能力，同时支持实时指标和离线训练 |
| 实时计算 | Spark Structured Streaming | 与现有 Scala 和 Spark 技术栈一致 |
| 深度模型 | PyTorch | Spark MLlib 不适合复杂深度时序结构 |
| 特征存储 | Parquet | 适合时间序列列存储、版本化和高效读取 |
| 服务存储 | MySQL | 延续现有项目，适合结果和元数据查询 |
| 模型追踪 | MLflow | 解决实验不可复现和模型版本混乱 |
| API | FastAPI | 沿用现有后端技术栈 |
| 前端 | Vue 3 + ECharts | 沿用现有技术栈，适合趋势和误差可视化 |

## 12. 架构约束

1. 所有预测必须记录模型版本和特征版本。
2. 训练集、验证集和测试集必须按时间顺序切分。
3. API 不能直接触发昂贵的在线训练。
4. MySQL 不保存大规模训练样本，训练数据放在 Parquet。
5. 实时链路必须支持重复消息的幂等写入。
6. 模型发布失败时不能覆盖当前可用版本。
7. 预测结果必须包含生成时间、数据截止时间和有效期。
8. 模型缺失天气等外部特征时，必须有明确的缺失标记。

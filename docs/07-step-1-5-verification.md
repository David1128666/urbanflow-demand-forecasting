# UrbanFlow 第 1 到第 5 步整体验收报告

> **English summary:** This report verifies the development environment,
> MySQL, virtual data generation, Kafka, and the prerequisites for steps 1-5.
>
> **中文摘要：** 本报告验收开发环境、MySQL、虚拟数据生成、Kafka，以及第
> 1 到第 5 步的基础链路。

## 1. 验收信息

| 项目 | 内容 |
|---|---|
| 验收日期 | 2026-09-11 |
| 验收范围 | 第 1 步到第 5 步 |
| 验收方式 | 编译、单元测试、构建、数据库查询、文件哈希、真实 Kafka 生产消费 |
| 最终结论 | 通过 |

## 2. 总体结果

| 步骤 | 内容 | 结果 |
|---|---|---|
| 第 1 步 | 项目骨架 | 通过 |
| 第 2 步 | MySQL、Linux 虚拟机、Hadoop、Kafka | 通过 |
| 第 3 步 | MySQL 数据库与表 | 通过 |
| 第 4 步 | 虚拟数据生成器 | 通过 |
| 第 5 步 | Kafka 数据生产者 | 通过 |

## 3. 第 1 步验收

### Scala

```text
common：编译通过
realtime-analysis：编译通过
offline-analysis：编译通过
Maven test：通过
```

### Python

```text
Backend 测试：1 项通过
Forecast Engine 测试：1 项通过
Simulator 测试：8 项通过
总计：10 项通过
```

### 前端

```text
Vite 版本：7.3.6
转换模块：86
生产构建：通过
```

### 页面与接口

```text
前端：http://127.0.0.1:5173，HTTP 200
后端：http://127.0.0.1:8000，HTTP 200
健康检查：{"status":"ok","version":"0.1.0"}
根接口状态：运行中
```

### 仓库检查

```text
文档链接：通过
Mermaid 代码块：通过
必备开源文件：通过
Git 工作区：干净
```

## 4. 第 2 步验收

### 宿主机

```text
MySQL：127.0.0.1:3306，连通
FastAPI：127.0.0.1:8000，连通
Vue：127.0.0.1:5173，连通
```

### Linux 虚拟机

```text
虚拟机：hadoopnode1
SSH：node1:22，连通
Kafka：node1:9092，连通
HDFS UI：node1:9870，连通
YARN UI：node1:8088，连通
```

### Hadoop 进程

```text
NameNode
DataNode
SecondaryNameNode
ResourceManager
NodeManager
```

### Kafka

```text
版本：3.3.1
模式：KRaft
Broker：node1:9092
Controller：node1:9093
ZooKeeper：不需要
```

## 5. 第 3 步验收

```text
MySQL 版本：8.0.41
数据库：urbanflow
表数量：7
```

数据表：

```text
demand_observation
forecast_result
forecast_run
job_run_log
model_metric
realtime_demand_metrics
station_dim
```

## 6. 第 4 步验收

### 数据规模

```text
随机种子：42
站点数量：20
观测数量：86400
唯一事件数：86400
最小需求：1
最大需求：102
节假日记录：6720
异常记录：122
```

### 输出文件

```text
stations.csv                    1600 字节
demand_observations.csv      7258872 字节
demand_observations.jsonl   21428358 字节
generation_manifest.json        785 字节
```

### 文件完整性

manifest 中记录的 SHA256 与实际文件重新计算结果完全一致：

```text
stations.csv：匹配
demand_observations.csv：匹配
demand_observations.jsonl：匹配
```

### 复现性

```text
相同种子重复生成测试：通过
生成器测试：通过
```

## 7. 第 5 步验收

### 最终验收 Topic

```text
Topic：urbanflow-verification-20260911112337
分区数：3
副本数：1
```

### 生产结果

```text
读取事件：100
成功发送：100
完成轮数：1
Dry run：False
```

### 消费结果

```text
消费数量：100
结果：与发送数量一致
```

### 消息示例

```json
{
  "event_id": "evt_202601010000_001",
  "city_id": "city-001",
  "station_id": "ST001",
  "event_time": "2026-01-01 00:00:00",
  "demand_count": 5,
  "temperature": 4.27,
  "precipitation": 0.0,
  "is_holiday": 0,
  "is_anomaly": 0,
  "data_version": "virtual-v1"
}
```

其他已验证模式：

```text
Dry-run：通过
单轮发送：通过
循环发送：通过
station_id 作为消息 Key：通过
速率限制：通过
发送回调与 flush：通过
```

## 8. 当前风险

1. Linux 虚拟机需要手动运行 `start-all.sh` 和 Kafka 启动命令。
2. 虚拟机曾出现过一次正常关机，Kafka 不会在宿主机重启后自动保证运行。
3. 当前只验证了 100 条 Kafka 消息，没有把全部 86,400 条一次发送完成。
4. Docker Desktop 不可用，但项目已经切换为现有 MySQL 和 VMware 环境。

## 9. 当前进度

```text
已完成：第 1、2、3、4、5 步
下一步：第 6 步，Spark Structured Streaming 消费 Kafka 并写入 MySQL
```

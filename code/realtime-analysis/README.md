# Realtime Analysis

> **中文摘要：** 本模块使用 Spark Structured Streaming 读取 Kafka 事件，
> 按 30 分钟事件时间窗口聚合需求，并把关闭窗口结果写入 MySQL。

Spark Structured Streaming job that:

1. Reads demand events from Kafka.
2. Parses the JSON event schema.
3. Removes invalid and duplicate events.
4. Groups events into 30-minute event-time windows.
5. Uses a 10-minute watermark for late data.
6. Upserts closed-window metrics into `realtime_demand_metrics`.

## Run

Install the parent and common module first:

```powershell
cd code
& "E:\IDEA\IntelliJ IDEA Community Edition 2024.3.5\plugins\maven\lib\maven3\bin\mvn.cmd" install -DskipTests
```

Start the streaming job:

```powershell
cd code
& "E:\IDEA\IntelliJ IDEA Community Edition 2024.3.5\plugins\maven\lib\maven3\bin\mvn.cmd" `
  -f realtime-analysis\pom.xml `
  exec:java `
  "-Dexec.args=--bootstrap-servers node1:9092 --topic urbanflow-demand-events --starting-offsets latest"
```

For a focused acceptance run, use a unique topic, `--starting-offsets earliest`,
and `--run-seconds 90`. The checkpoint directory must also be unique for a new
topic.

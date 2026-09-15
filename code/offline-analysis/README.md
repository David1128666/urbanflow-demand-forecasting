# Offline Analysis

> **中文摘要：** 本模块使用 Spark SQL 根据历史需求生成滞后、滑动统计、
> 日历、天气、节假日和目标值特征，并按时间顺序划分训练、验证和测试集。

Spark SQL feature engineering job for the UrbanFlow MVP.

It reads generated demand observations and station metadata, then creates:

- Demand lags for 30 minutes, 1 hour, 24 hours, and 7 days.
- Rolling mean and standard deviation for 1 hour, 6 hours, 24 hours, and 7 days.
- Calendar features such as hour, weekday, weekend, sine, and cosine encoding.
- Weather and holiday features.
- The next 30-minute demand target.
- Chronological train, validation, and test splits.

## Run

```powershell
cd code
& "E:\IDEA\IntelliJ IDEA Community Edition 2024.3.5\plugins\maven\lib\maven3\bin\mvn.cmd" `
  -f offline-analysis\pom.xml `
  exec:java `
  "-Dexec.args=--input-path data/virtual-v1/demand_observations.csv --stations-path data/virtual-v1/stations.csv --output-path data/features-v1"
```

Outputs:

```text
data/features-v1/features.parquet
data/features-v1/sample.csv
data/features-v1/feature_manifest.json
```

The Parquet dataset is partitioned by `split`.

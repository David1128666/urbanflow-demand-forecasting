# Local Infrastructure

> **中文摘要：** 本目录提供可选的本地 MySQL 和 Kafka 环境，适合没有现成
> MySQL 或 Kafka 的开发者使用。

This directory is an optional setup for developers who do not already have
MySQL or Kafka available.

It starts:

- MySQL 8.4
- Kafka in KRaft mode

The optional MySQL container uses host port `3307` so it does not conflict with
an existing MySQL service on port `3306`.

```powershell
docker compose -f docker\docker-compose.yml up -d
docker compose -f docker\docker-compose.yml ps
```

MySQL initialization uses `../sql/schema.sql`. Connect to the optional
container with `MYSQL_PORT=3307`.

Stop services:

```powershell
docker compose -f docker\docker-compose.yml down
```

Add `-v` only when you intentionally want to delete the local database and
Kafka volumes.

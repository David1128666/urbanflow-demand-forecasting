# Cross-module Tests

> **中文摘要：** 本目录用于跨模块测试，例如实时事件、Spark 聚合、特征、
> 模型预测、API 和前端之间的完整链路。

This directory is reserved for tests that verify more than one module.

Planned integration tests:

- Virtual event to Kafka.
- Kafka to Spark to MySQL.
- MySQL to feature dataset.
- Model prediction to FastAPI.
- FastAPI response to the Vue client.

The first skeleton milestone verifies each module independently. End-to-end
tests are added after the real data path is implemented.

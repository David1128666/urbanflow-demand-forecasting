# Contributing to UrbanFlow

> **English:** The English contribution guide is available at
> [CONTRIBUTING.md](CONTRIBUTING.md).

感谢你关注 UrbanFlow。项目当前处于 MVP 阶段，重点是先完成虚拟数据到预测页面的最小闭环。

## 开发原则

1. 功能正确优先于模型复杂度。
2. 默认使用虚拟数据，不提交真实用户数据。
3. 所有时间序列评估必须按时间切分，禁止随机切分训练集和测试集。
4. 新增功能必须同步更新文档、测试和示例配置。
5. 不提交密码、密钥、大型数据文件、模型文件或运行日志。

## 开发环境

项目计划使用：

- JDK 11+
- Maven 3.8+
- Scala 2.13.14
- Python 3.11+
- Node.js 20.19+ or 22.12+
- Docker Desktop，用于 Kafka 和 MySQL

具体启动方式在代码完成和依赖锁定后补充到 README。

## 分支与提交

- 默认开发分支：`main`
- 功能分支：`feat/<short-description>`
- 修复分支：`fix/<short-description>`
- 文档分支：`docs/<short-description>`

提交信息建议使用：

```text
feat: add virtual demand generator
fix: handle duplicate kafka events
docs: update mvp deployment steps
test: add temporal split validation
```

## Pull Request 要求

- 说明变更目的和影响范围。
- 关联对应 Issue。
- 提供本地验证命令和结果。
- 数据、模型或接口变化必须更新文档。
- 不包含无关格式化或大规模重构。

## 测试要求

- Python：`pytest`
- Scala：`mvn test`
- Frontend：构建和基础组件测试
- 数据：Schema、时间窗口和特征泄漏测试
- 模型：输出形状、随机种子和回退逻辑测试

## 数据与模型

- `data/`、`models/`、`mlruns/` 默认不进入 Git。
- 示例数据必须由脚本生成。
- 如果接入真实数据，必须记录数据来源、许可证、字段口径和下载日期。
- 模型产物通过 Release、对象存储或 Git LFS 管理，不直接提交到普通 Git 历史。

## 许可证

提交代码即表示你同意代码按照本项目的 MIT License 发布。第三方代码、数据或模型必须保留原始许可证和署名。

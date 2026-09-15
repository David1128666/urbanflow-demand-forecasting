# UrbanFlow GitHub 开源指南

> **English summary:** This guide covers repository files, reproducibility,
> testing, licensing, screenshots, release preparation, and contribution
> basics.
>
> **中文摘要：** 本文说明仓库文件、复现要求、测试、许可证、截图、发布准备
> 和贡献规范。

## 1. 目标

UrbanFlow 虽然采用小型 MVP，但必须满足开源项目的最低可理解、可运行、可复现和可维护要求。项目规模可以小，工程规范不能缺。

开源项目至少要做到：

1. 别人能快速知道项目解决什么问题。
2. 别人能知道当前完成到哪里。
3. 别人能根据 README 运行项目。
4. 别人能区分虚拟数据和真实数据。
5. 别人能确认项目许可证。
6. 别人能安全提交问题和 Pull Request。
7. 核心行为有测试。
8. 依赖、配置和随机种子可以复现。
9. 不包含密码、隐私数据、大型文件或生成产物。

## 2. 首次公开前的 P0 文件

| 文件 | 用途 | 当前状态 |
|---|---|---|
| `README.md` | 项目介绍、状态、快速开始和文档入口 | 已具备 |
| `LICENSE` | 明确开源许可 | 已具备，MIT |
| `.gitignore` | 阻止依赖、数据、模型和密钥进入 Git | 已具备 |
| `.editorconfig` | 统一缩进、换行和编码 | 已具备 |
| `.env.example` | 提供无密钥的配置模板 | 已具备 |
| `CONTRIBUTING.md` | 说明开发、分支、提交和测试要求 | 已具备 |
| `CODE_OF_CONDUCT.md` | 社区行为规范 | 已具备 |
| `SECURITY.md` | 安全问题报告和密钥处理规则 | 已具备 |
| `CITATION.cff` | 提供学术引用信息 | 已具备，上传后替换仓库地址 |
| `CHANGELOG.md` | 记录版本变化 | 已具备 |
| `docs/` | 提供架构和设计说明 | 已具备 |
| `.github/ISSUE_TEMPLATE/` | 规范 Bug 和功能请求 | 已具备 |
| `.github/pull_request_template.md` | 规范 PR 检查项 | 已具备 |
| `.github/workflows/ci.yml` | 检查仓库和文档基础质量 | 已具备 |
| `.github/dependabot.yml` | 定期检查依赖更新 | 已具备 |

代码完成后还必须增加：

- 根 `pom.xml`。
- Python 依赖清单和锁定文件。
- 前端 `package.json` 和 `package-lock.json`。
- `sql/schema.sql`。
- 虚拟数据生成脚本。
- 测试目录。
- 扩展 GitHub Actions，增加 Python、Scala 和前端测试。
- 首个 Release 说明。

## 3. README 最低标准

公开仓库的 README 应包含：

1. 项目一句话介绍。
2. 当前状态和 MVP 边界。
3. 架构或数据流图。
4. 技术栈。
5. 目录结构。
6. 环境要求。
7. 安装和启动步骤。
8. 虚拟数据生成步骤。
9. 训练和预测步骤。
10. 测试命令。
11. API 或页面截图。
12. 数据来源和许可证说明。
13. 已知限制。
14. 后续计划。
15. 贡献和许可证入口。

在没有真实数据时，README 必须明确写：

> The current MVP uses synthetic data. Real public datasets will be integrated in a later stage.

不要让访问者误以为预测结果来自真实城市运营数据。

## 4. 数据与隐私规则

### 4.1 当前政策

- MVP 只使用脚本生成的虚拟数据。
- `data/`、`datasets/` 和生成结果不提交到 Git。
- 示例数据必须能够通过固定随机种子重新生成。
- 不提交真实用户、车辆、订单、手机号、位置轨迹或隐私数据。

### 4.2 后期接入真实数据

接入公开数据前必须记录：

- 数据名称和来源 URL。
- 许可证和再分发要求。
- 下载日期和版本。
- 时间范围和空间范围。
- 字段含义和预处理方式。
- 是否允许商业或二次分发。

如果许可证不允许重新分发原始数据，仓库只提供下载脚本和字段说明。

## 5. 可复现性要求

开源项目不能只在作者电脑上运行。必须做到：

- 固定 Python、Scala、Node.js 和核心库版本。
- 固定模型随机种子。
- 固定虚拟数据生成种子。
- 配置由 `.env.example` 和示例配置文件提供。
- 命令可以在 Windows 和常见 Linux 环境中理解。
- 数据版本、特征版本和模型版本互相记录。
- 模型指标由脚本生成，不允许手工修改结果。

## 6. 测试最低标准

### 6.1 数据测试

- 虚拟数据字段和类型正确。
- 30 分钟窗口没有重复主键。
- 时间范围和触发规则正确。
- 特征只使用预测时间点之前的数据。

### 6.2 模型测试

- 训练集、验证集和测试集按时间切分。
- TCN 输出形状为 48 个预测步。
- 固定种子可以复现。
- 模型失败时不会覆盖上一个可用结果。
- Seasonal Naive 和 TCN 使用相同测试集。

### 6.3 后端测试

- 历史查询和预测查询正常。
- 参数错误返回明确状态。
- 没有预测数据时返回可理解的结果。
- API 不泄露数据库错误或堆栈。

### 6.4 前端测试

- 核心路由可以打开。
- 无数据和接口错误状态可见。
- 图表能区分历史值和预测值。
- 页面展示模型版本和数据生成时间。

## 7. GitHub Actions 最低标准

当前 `.github/workflows/ci.yml` 会检查文档、链接和开源基线。代码完成后扩展为：

```text
Python syntax/lint + pytest
Scala compile + mvn test
Frontend npm ci + build
Markdown link and structure check
```

前期如果部分工程尚未完成，可以把对应检查设为 Optional，但公开仓库前必须至少有一条可执行的 CI。

## 8. GitHub 仓库设置

建议在 GitHub 页面完成：

- Repository description：使用项目一句话介绍。
- Topics：`time-series-forecasting`、`spark`、`kafka`、`pytorch`、`fastapi`、`vue`、`data-science`。
- Social preview：使用预测看板截图。
- Default branch：`main`。
- Branch protection：禁止直接向 `main` 强推。
- Release：首个可运行版本发布 `v0.1.0`。
- Discussions：问题多时再启用。
- Security advisories：启用私密漏洞报告。
- Dependabot：启用依赖更新。

## 9. 模型和数据文件策略

不要直接把大型训练数据和模型提交到普通 Git 历史。

可选方案：

| 内容 | 推荐方式 |
|---|---|
| 小型示例数据 | 由脚本生成 |
| 大型公开数据 | 下载脚本或外部存储 |
| 模型权重 | GitHub Releases、对象存储或 Git LFS |
| 实验指标 | JSON、CSV 或 MLflow |
| 页面截图 | `docs/images/`，控制文件大小 |

如果使用 Git LFS，必须在 README 中说明安装步骤。

## 10. 首次上传检查清单

- [ ] 仓库中不存在 `.env`、密码、Token 和私钥。
- [ ] 不存在 `node_modules`、`.venv`、`target`、`data` 和 `models`。
- [ ] README 可以独立说明项目。
- [ ] LICENSE 和 CITATION 信息正确。
- [ ] 仓库地址占位符已经替换。
- [ ] 虚拟数据可以重新生成。
- [ ] 安装和启动步骤已经亲自验证。
- [ ] 测试命令已经执行。
- [ ] 当前限制和未实现内容写清楚。
- [ ] 没有声称使用了尚不存在的真实数据。
- [ ] 没有伪造模型提升数字。

## 11. 发布流程

```text
1. 完成一个可运行 MVP
2. 执行测试和干净环境验证
3. 更新 README、CHANGELOG 和截图
4. 创建 v0.1.0 Tag 和 GitHub Release
5. 在 Release 中说明支持范围和已知限制
6. 后续功能通过小版本逐步添加
```

## 12. 开源与作品集的平衡

项目不需要一次完成所有高级能力，但首次公开版本必须：

- 能运行。
- 能解释。
- 能复现。
- 能判断哪些已经完成，哪些尚未完成。

满足这些条件的小项目，比不能运行的大型架构更适合 GitHub、PS 和 CV。

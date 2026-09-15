# Contributing to UrbanFlow

> **中文说明：** 中文版本保存在
> [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)。

Thanks for your interest in UrbanFlow. The project is an open-source,
MVP-focused AI forecasting and dispatch decision-support system.

The Chinese version is preserved at [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md).

## Development Principles

1. Correctness is more important than model complexity.
2. Use synthetic data by default and never commit private user data.
3. Split time-series data chronologically; never use a random train/test split.
4. Update documentation, tests, and examples when behavior changes.
5. Never commit passwords, API keys, large datasets, model files, or runtime
   logs.

## Development Environment

- JDK 11+
- Maven 3.8+
- Scala 2.13.14
- Python 3.11+
- Node.js 20.19+ or 22.12+
- MySQL 8
- Kafka or Docker Compose

See [README.md](README.md) for the complete local setup.

## Branches and Commits

- Default branch: `main`
- Feature branches: `feat/<short-description>`
- Fix branches: `fix/<short-description>`
- Documentation branches: `docs/<short-description>`

Recommended commit prefixes:

```text
feat: add virtual demand generator
fix: handle duplicate kafka events
docs: update deployment steps
test: add temporal split validation
```

## Pull Request Requirements

- Explain the problem and the change.
- Link the relevant issue when one exists.
- Provide local verification commands and results.
- Update documentation when data, models, or APIs change.
- Avoid unrelated formatting or large refactors.
- Mention any external risk or migration requirement.

## Testing Requirements

- Python backend: `python -m unittest discover -s code/backend/tests -v`
- Forecast engine: `python -m unittest discover -s code/forecast-engine/tests -v`
- Simulator: `python -m unittest discover -s code/simulator/tests -v`
- Scala: `mvn -f code/pom.xml test`
- Frontend: `npm run build`
- Documentation: `python scripts/check_docs.py`

## Data and Models

- `data/`, `models/`, `mlruns/`, and generated artifacts are ignored by Git.
- Example datasets must be generated from a script.
- Public data must include its source, license, field definitions, and download
  date.
- Model artifacts should be managed through a Release, object storage, or Git
  LFS when they become large.

## License

By contributing, you agree that your contribution is released under the
project's MIT License. Third-party code, data, and models must retain their
original license and attribution.

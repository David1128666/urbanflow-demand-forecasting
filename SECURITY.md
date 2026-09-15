# Security Policy

> **中文说明：** 不要在公开 Issue 中提交密码、密钥、数据库连接信息或安全
> 漏洞。若发现敏感安全问题，请通过仓库主页公布的私下联系方式报告。

## Supported Versions

UrbanFlow is currently in the design and MVP stage. Security fixes are applied
to the `main` branch.

## Reporting a Vulnerability

Do not create a public GitHub Issue for secrets, authentication bypasses,
database exposure, remote code execution, or other sensitive vulnerabilities.

Please contact the maintainers privately through the security contact published
on the GitHub repository. Include:

- Affected component and version.
- Reproduction steps.
- Expected and actual behavior.
- Potential impact.
- Suggested fix, if available.

## Secret Handling

- Never commit `.env`, credentials, access tokens, private keys, or database
  dumps.
- Use `.env.example` for public configuration templates.
- Rotate any credential immediately if it is accidentally committed.
- Production deployments must use environment variables or a secret manager.

## Data Handling

- The MVP uses synthetic data only.
- Real user, customer, or location data requires explicit permission, privacy
  review, and a documented retention policy.
- Public datasets must be checked for redistribution and commercial-use terms.

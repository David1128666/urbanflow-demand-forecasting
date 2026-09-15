from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".env.example",
    "CONTRIBUTING.md",
    "CONTRIBUTING.zh-CN.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "docs/README.md",
    "docs/images/overview.png",
    "docs/images/forecast.png",
    "docs/images/models.png",
    "docs/images/dispatch.png",
    "docs/01-project-brief.md",
    "docs/02-c4-architecture.md",
    "docs/03-detailed-design.md",
    "docs/04-plain-language-guide.md",
    "docs/05-mvp-implementation-plan.md",
    "docs/06-open-source-guide.md",
    "docs/07-step-1-5-verification.md",
    "docs/08-step-6-verification.md",
    "docs/09-step-7-verification.md",
    "docs/10-step-8-verification.md",
    "docs/11-step-9-verification.md",
    "docs/12-step-10-verification.md",
    "docs/13-step-11-verification.md",
    "docs/14-step-12-verification.md",
    "docs/15-business-value-dispatch-verification.md",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/workflows/ci.yml",
    "code/README.md",
    "code/CODE_TASK_PLAN.md",
    "code/pom.xml",
    "code/common/pom.xml",
    "code/realtime-analysis/pom.xml",
    "code/offline-analysis/pom.xml",
    "code/forecast-engine/pyproject.toml",
    "code/forecast-engine/src/urbanflow_forecast/locales.py",
    "code/backend/pyproject.toml",
    "code/backend/app/main.py",
    "code/backend/app/locales/en.py",
    "code/backend/app/locales/zh_CN.py",
    "code/simulator/pyproject.toml",
    "code/scripts/run_demo.py",
    "code/scripts/live_demo.py",
    "code/tests/test_live_demo.py",
    "code/frontend/package.json",
    "code/frontend/package-lock.json",
    "code/frontend/src/locales/en.js",
    "code/frontend/src/locales/zh-CN.js",
    "code/frontend/scripts/check-locales.mjs",
    "code/sql/schema.sql",
    "code/docker/docker-compose.yml",
)

ALLOWED_MERMAID_TYPES = (
    "C4Context",
    "C4Container",
    "C4Component",
    "flowchart ",
    "sequenceDiagram",
)

EXCLUDED_DIRECTORIES = {
    ".git",
    ".venv",
    "dist",
    "node_modules",
    "target",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def check_required_files(errors: list[str]) -> None:
    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).is_file():
            fail(errors, f"missing required file: {relative_path}")


def check_markdown(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.md")):
        if any(part in EXCLUDED_DIRECTORIES for part in path.parts):
            continue

        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)

        if text.count("```") % 2:
            fail(errors, f"{relative}: unbalanced code fences")

        for target in re.findall(r"\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean_target = target.split("#", 1)[0]
            resolved = (path.parent / clean_target).resolve()
            if not resolved.exists():
                fail(errors, f"{relative}: broken link: {target}")

        for block in re.findall(r"```mermaid\s*(.*?)```", text, flags=re.DOTALL):
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                fail(errors, f"{relative}: empty mermaid block")
                continue
            if not lines[0].startswith(ALLOWED_MERMAID_TYPES):
                fail(errors, f"{relative}: unsupported mermaid type: {lines[0]}")


def main() -> int:
    errors: list[str] = []
    check_required_files(errors)
    check_markdown(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Repository baseline check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

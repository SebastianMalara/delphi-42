from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_METADATA = (
    "Purpose:",
    "Audience:",
    "Owner:",
    "Status:",
    "Last Updated:",
    "Dependencies:",
    "Exit Criteria:",
)

LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def collect_issues(root: Path) -> list[str]:
    issues: list[str] = []
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        issues.extend(check_metadata(path, text))
        issues.extend(check_links(path, text))
        issues.extend(check_mermaid_fences(path, text))
    return issues


def check_metadata(path: Path, text: str) -> list[str]:
    header_lines = text.splitlines()[:12]
    issues: list[str] = []
    for field in REQUIRED_METADATA:
        expected_prefix = f"- {field}"
        if not any(line.startswith(expected_prefix) for line in header_lines):
            issues.append(f"{path}: missing metadata field `{field}`")
    return issues


def check_links(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    for raw_target in LINK_PATTERN.findall(text):
        target = raw_target.strip()
        if "://" in target or target.startswith("mailto:") or target.startswith("#"):
            continue
        target_path = target.split("#", maxsplit=1)[0]
        if not target_path:
            continue
        resolved = (path.parent / target_path).resolve()
        if not resolved.exists():
            issues.append(f"{path}: broken link `{target}`")
    return issues


def check_mermaid_fences(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    in_mermaid = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "```mermaid":
            if in_mermaid:
                issues.append(f"{path}: nested mermaid fence")
            in_mermaid = True
            continue
        if stripped == "```" and in_mermaid:
            in_mermaid = False
    if in_mermaid:
        issues.append(f"{path}: unclosed mermaid fence")
    return issues


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "docs"
    issues = collect_issues(root)
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("Documentation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

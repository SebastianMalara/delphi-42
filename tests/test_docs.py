from pathlib import Path

from scripts.check_docs import collect_issues


def test_docs_pass_repo_checks() -> None:
    issues = collect_issues(Path("docs"))
    assert issues == []

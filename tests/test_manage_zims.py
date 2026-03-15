from __future__ import annotations

from pathlib import Path

from scripts.manage_zims import (
    add_file_archive,
    answer_enabled_aliases,
    load_registry,
    set_answer_enabled,
)


def test_add_file_archive_registers_alias_and_allowlist(tmp_path: Path) -> None:
    source = tmp_path / "source.zim"
    source.write_bytes(b"zim")

    archive = add_file_archive(
        tmp_path,
        alias="field-guide.zim",
        source_path=source,
        answer_enabled=True,
    )

    assert archive.alias == "field-guide.zim"
    assert (tmp_path / "library/zim/field-guide.zim").is_symlink()
    assert answer_enabled_aliases(tmp_path) == ("field-guide.zim",)


def test_set_answer_enabled_updates_registry(tmp_path: Path) -> None:
    source = tmp_path / "source.zim"
    source.write_bytes(b"zim")
    add_file_archive(
        tmp_path,
        alias="browse-only.zim",
        source_path=source,
        answer_enabled=False,
    )

    updated = set_answer_enabled(tmp_path, alias="browse-only.zim", enabled=True)

    assert updated.answer_enabled is True
    assert answer_enabled_aliases(tmp_path) == ("browse-only.zim",)
    assert load_registry(tmp_path)[0].answer_enabled is True

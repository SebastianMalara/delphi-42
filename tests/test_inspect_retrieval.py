from __future__ import annotations

from pathlib import Path
import sys

from ingest.build_index import SQLiteIndexBuilder, build_chunks
from ingest.zim_extract import ExtractedDocument
from scripts.inspect_retrieval import main


def test_inspect_retrieval_reports_selected_context(tmp_path: Path, capsys) -> None:
    index_path = tmp_path / "data/index/oracle.db"
    SQLiteIndexBuilder(index_path).build(
        build_chunks(
            [
                ExtractedDocument(
                    title="Water Purification",
                    source_id="water.txt",
                    text="Boil water for one minute before drinking.",
                )
            ]
        )
    )

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    argv = sys.argv
    sys.argv = [
        "inspect_retrieval.py",
        "--config",
        str(config_path),
        "--question",
        "how to purify water",
    ]
    try:
        main()
    finally:
        sys.argv = argv

    output = capsys.readouterr().out
    assert "anchor_terms: purify, water" in output
    assert "confidence: strong" in output
    assert "source: sqlite" in output
    assert "Water Purification" in output

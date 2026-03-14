from __future__ import annotations

from pathlib import Path
import sys

from core.retriever import KeywordRetriever, RetrievalChunk
from scripts.inspect_retrieval import main


def test_inspect_retrieval_reports_selected_context(tmp_path: Path, capsys, monkeypatch) -> None:
    zim_dir = tmp_path / "data/library/zim"
    zim_dir.mkdir(parents=True)
    (zim_dir / "medicine.zim").write_bytes(b"zim")

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  zim_dir: {zim_dir}
  zim_allowlist:
    - medicine.zim
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "scripts.inspect_retrieval.KiwixRetriever",
        lambda *args, **kwargs: KeywordRetriever(
            [
                RetrievalChunk(
                    title="Water Purification",
                    source="medicine.zim:A/WaterPurification.html",
                    snippet="Boil water for one minute before drinking.",
                    matched_terms=2,
                )
            ]
        ),
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
    assert "source: kiwix" in output
    assert "Water Purification" in output

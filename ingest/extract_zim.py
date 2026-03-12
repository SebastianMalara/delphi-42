from __future__ import annotations

import argparse
from pathlib import Path
import shutil

from .zim_extract import ExtractedDocument, ZimExtractor


def export_zim_to_plaintext(
    zim_dir: Path,
    output_dir: Path,
    allowlist: tuple[str, ...],
    *,
    extractor: ZimExtractor | None = None,
) -> int:
    extractor = extractor or ZimExtractor()
    output_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for filename in allowlist:
        source_path = zim_dir / filename
        if not source_path.exists():
            raise FileNotFoundError(f"ZIM file not found: {source_path}")

        target_root = output_dir / filename
        shutil.rmtree(target_root, ignore_errors=True)

        documents = extractor.extract(source_path)
        for document in documents:
            destination = _destination_path(output_dir, document)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(document.text + "\n", encoding="utf-8")
            written += 1

    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract allowlisted ZIM archives into staged plaintext."
    )
    parser.add_argument("--zim-dir", type=Path, required=True, help="Directory of .zim files.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where plaintext should be written.",
    )
    parser.add_argument(
        "--allowlist",
        nargs="+",
        required=True,
        help="One or more ZIM filenames to extract.",
    )
    args = parser.parse_args()

    total = export_zim_to_plaintext(
        args.zim_dir,
        args.output_dir,
        tuple(args.allowlist),
    )
    print(f"Extracted {total} documents from {len(args.allowlist)} ZIM files to {args.output_dir}")


def _destination_path(output_dir: Path, document: ExtractedDocument) -> Path:
    zim_name, article_path = document.source_id.split(":", 1)
    return output_dir / zim_name / f"{article_path}.txt"


if __name__ == "__main__":
    main()

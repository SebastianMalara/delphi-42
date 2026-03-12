from pathlib import Path

from ingest.extract_zim import export_zim_to_plaintext
from ingest.zim_extract import ZimExtractor


class FakeItem:
    def __init__(self, title: str, path: str, content: str, mimetype: str = "text/html") -> None:
        self.title = title
        self.path = path
        self.content = content.encode("utf-8")
        self.mimetype = mimetype


class FakeEntry:
    def __init__(self, item: FakeItem, *, is_redirect: bool = False) -> None:
        self._item = item
        self.is_redirect = is_redirect

    def get_item(self) -> FakeItem:
        return self._item


class FakeArchive:
    def __init__(self, entries) -> None:
        self.entries = entries
        self.all_entry_count = len(entries)

    def _get_entry_by_id(self, index: int) -> FakeEntry:
        return self.entries[index]


def test_zim_extractor_extracts_normalized_documents() -> None:
    archive = FakeArchive(
        [
            FakeEntry(
                FakeItem(
                    "Water Purification",
                    "A/Water.html",
                    "<html><body><h1>Water</h1><p>Boil for one minute.</p></body></html>",
                )
            ),
            FakeEntry(
                FakeItem(
                    "Ignored",
                    "I/image.png",
                    "binary",
                    mimetype="image/png",
                )
            ),
        ]
    )
    extractor = ZimExtractor(archive_opener=lambda _: archive)

    documents = extractor.extract(Path("medical.zim"))

    assert len(documents) == 1
    assert documents[0].title == "Water Purification"
    assert documents[0].source_id == "medical.zim:A/Water.html"
    assert "Boil for one minute." in documents[0].text


def test_export_zim_to_plaintext_writes_allowlisted_output(tmp_path: Path) -> None:
    archive = FakeArchive(
        [
            FakeEntry(
                FakeItem(
                    "Shelter",
                    "A/Shelter.html",
                    "<html><body><p>Use dry insulation.</p></body></html>",
                )
            )
        ]
    )
    zim_dir = tmp_path / "zim"
    zim_dir.mkdir()
    (zim_dir / "survival.zim").write_bytes(b"zim")
    output_dir = tmp_path / "plaintext"

    written = export_zim_to_plaintext(
        zim_dir,
        output_dir,
        ("survival.zim",),
        extractor=ZimExtractor(archive_opener=lambda _: archive),
    )

    destination = output_dir / "survival.zim" / "A/Shelter.html.txt"
    assert written == 1
    assert destination.exists()
    assert "Use dry insulation." in destination.read_text(encoding="utf-8")

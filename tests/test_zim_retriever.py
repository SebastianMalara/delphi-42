from pathlib import Path

from core.zim_retriever import RuntimeZimRetriever


class FakeArchive:
    def __init__(self, articles) -> None:
        self.articles = articles
        self.search_calls = 0

    def search_paths(self, question: str, limit: int):
        self.search_calls += 1
        haystack_tokens = set(question.lower().split())
        matches = []
        for path, article in self.articles.items():
            content = f"{article['title']} {article['content']}".lower()
            if any(token in content for token in haystack_tokens):
                matches.append(path)
        return matches[:limit]

    def read_article(self, article_path: str):
        return self.articles[article_path]


def test_runtime_zim_retriever_returns_bounded_chunks_from_allowlist() -> None:
    archive = FakeArchive(
        {
            "A/Water.html": {
                "title": "Water Purification",
                "content": "<html><body><p>Boil water for one minute before drinking.</p></body></html>",
            }
        }
    )
    retriever = RuntimeZimRetriever(
        Path("/unused"),
        ("medical.zim",),
        archive_opener=lambda _: archive,
    )

    results = retriever.search("how do i purify water", limit=3)

    assert len(results) == 1
    assert results[0].title == "Water Purification"
    assert results[0].source == "medical.zim:A/Water.html"
    assert "Boil water" in results[0].snippet
    assert results[0].matched_terms >= 1


def test_runtime_zim_retriever_stops_after_budget_is_filled() -> None:
    first_archive = FakeArchive(
        {
            "A/WaterStorage.html": {
                "title": "Water Storage",
                "content": "<html><body><p>Store water safely after treatment.</p></body></html>",
            }
        }
    )
    second_archive = FakeArchive(
        {
            "A/WaterPurification.html": {
                "title": "Water Purification",
                "content": "<html><body><p>Boil water for one minute before drinking.</p></body></html>",
            }
        }
    )
    archive_map = {
        "weak.zim": first_archive,
        "medical.zim": second_archive,
    }
    retriever = RuntimeZimRetriever(
        Path("/unused"),
        ("weak.zim", "medical.zim"),
        archive_opener=lambda source_path: archive_map[source_path.name],
    )

    results = retriever.search("how do i purify water", limit=1)

    assert len(results) == 1
    assert results[0].source == "medical.zim:A/WaterPurification.html"
    assert first_archive.search_calls == 1
    assert second_archive.search_calls == 1

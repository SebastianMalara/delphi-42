from pathlib import Path

from core.retriever import KiwixRetriever, RetrievalConfidence, assess_retrieval


def test_kiwix_retriever_reads_allowlisted_articles() -> None:
    article_map = {
        ("medical.zim", "A/WaterPurification.html"): (
            "Boil water for one minute before drinking. "
            "Let it cool in a clean container."
        ),
    }

    def search_fn(zim_file_path: str, search_string: str):
        assert "medical.zim" in zim_file_path
        assert "purify water" in search_string
        return 1, ["A/WaterPurification.html"]

    def read_fn(zim_file_path: str, article_path: str):
        return article_map[(Path(zim_file_path).name, article_path)]

    results = KiwixRetriever(
        Path("/unused"),
        ("medical.zim",),
        search_fn=search_fn,
        read_fn=read_fn,
    ).search("how do i purify water", limit=3)

    assert results
    assert results[0].source == "medical.zim:A/WaterPurification.html"
    assert "Boil water" in results[0].snippet


def test_assess_retrieval_rejects_ambiguous_wound_query() -> None:
    retriever = KiwixRetriever(
        Path("/unused"),
        ("medical.zim",),
        search_fn=lambda *_: (2, ["A/WoundClosure.html", "A/CompartmentSyndrome.html"]),
        read_fn=lambda _, article_path: {
            "A/WoundClosure.html": (
                "Negative-pressure wound therapy may support wound closure in supervised settings."
            ),
            "A/CompartmentSyndrome.html": (
                "Compartment syndrome requires urgent evaluation and pressure relief."
            ),
        }[article_path],
    )

    assessment = assess_retrieval(
        "how to treat a wound it's not closing, I'm alone in the woods",
        retriever.search("how to treat a wound it's not closing, I'm alone in the woods", limit=6),
    )

    assert assessment.confidence is RetrievalConfidence.WEAK
    assert assessment.context == ()

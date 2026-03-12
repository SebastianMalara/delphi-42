from ingest.chunker import chunk_text


def test_chunk_text_splits_long_input() -> None:
    text = " ".join(["water"] * 200)
    chunks = chunk_text("guide", text, max_chars=80, title="Guide")

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 80 for chunk in chunks)
    assert all(chunk.title == "Guide" for chunk in chunks)

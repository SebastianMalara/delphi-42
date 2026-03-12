from ingest.html_normalizer import normalize_html_to_text


def test_normalize_html_to_text_removes_markup_and_scripts() -> None:
    text = normalize_html_to_text(
        """
<html>
  <head><script>ignore()</script></head>
  <body><h1>Water</h1><p>Boil for one minute.</p></body>
</html>
""".strip()
    )

    assert "Water" in text
    assert "Boil for one minute." in text
    assert "ignore()" not in text

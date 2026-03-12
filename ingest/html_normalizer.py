from __future__ import annotations

from html import unescape
import re


_SCRIPT_STYLE_RE = re.compile(r"(?is)<(script|style)\b.*?>.*?</\1>")
_TAG_RE = re.compile(r"(?s)<[^>]+>")


def normalize_html_to_text(raw_content: str) -> str:
    """Convert ZIM HTML content into compact plain text."""
    if not raw_content:
        return ""

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return _normalize_with_regex(raw_content)

    soup = BeautifulSoup(raw_content, "html.parser")
    for node in soup(["script", "style"]):
        node.decompose()

    lines = [line.strip() for line in soup.get_text("\n").splitlines()]
    return "\n".join(line for line in lines if line)


def _normalize_with_regex(raw_content: str) -> str:
    cleaned = _SCRIPT_STYLE_RE.sub(" ", raw_content)
    cleaned = _TAG_RE.sub(" ", cleaned)
    cleaned = unescape(cleaned)
    lines = [" ".join(line.split()) for line in cleaned.splitlines()]
    return "\n".join(line for line in lines if line)

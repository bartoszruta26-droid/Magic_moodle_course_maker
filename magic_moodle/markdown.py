"""Wspólne renderowanie Markdown do HTML dla wszystkich adapterów Moodle."""
from __future__ import annotations

from markdown_it import MarkdownIt


def _renderer() -> MarkdownIt:
    """Create a deterministic renderer with raw HTML disabled."""
    return MarkdownIt(
        "gfm-like",
        {
            "html": False,
            "linkify": False,
            "typographer": False,
            "breaks": False,
        },
    )


def render_markdown(source: str) -> str:
    """Convert Markdown to an HTML fragment suitable for Moodle HTML fields."""
    if not isinstance(source, str):
        raise TypeError("Treść Markdown musi być tekstem.")
    if not source:
        return ""
    return _renderer().render(source)

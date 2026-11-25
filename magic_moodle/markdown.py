"""Wspólne renderowanie Markdown do HTML dla wszystkich adapterów Moodle."""
from __future__ import annotations

from markdown_it import MarkdownIt


def _renderer() -> MarkdownIt:
    """Create a deterministic renderer with raw HTML disabled."""
    return MarkdownIt(
        "default",
        {
            "html": False,
            "linkify": False,
            "typographer": False,
            "breaks": False,
        },
    )


def render_markdown(source: str, *, heading_offset: int = 0) -> str:
    """Render Markdown as an HTML fragment.

    heading_offset can adapt document heading levels to a host platform's
    semantic hierarchy. Standard Markdown rendering uses the default value 0.
    """
    if not isinstance(source, str):
        raise TypeError("Treść Markdown musi być tekstem.")
    if not isinstance(heading_offset, int) or not 0 <= heading_offset <= 5:
        raise ValueError("Przesunięcie nagłówków musi być liczbą całkowitą od 0 do 5.")
    if not source:
        return ""

    parser = _renderer()
    tokens = parser.parse(source)
    if heading_offset:
        for token in tokens:
            if token.type in {"heading_open", "heading_close"}:
                level = int(token.tag[1:])
                token.tag = f"h{min(6, level + heading_offset)}"
    return parser.renderer.render(tokens, parser.options, {})

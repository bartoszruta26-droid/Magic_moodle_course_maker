"""Wspólny, bezpieczny renderer Markdown do treści HTML Moodle.

Renderer zachowuje semantyczną hierarchię nagłówków i obsługuje rozszerzenia
Markdown używane w materiałach dydaktycznych. Wynik jest oczyszczany z HTML,
który mógłby wykonywać skrypt lub używać niebezpiecznych adresów URL.
"""
from __future__ import annotations

from markdown import Markdown
import nh3


_ALLOWED_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "caption", "code", "col", "colgroup",
    "dd", "del", "details", "div", "dl", "dt", "em", "figcaption", "figure",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "ins", "kbd",
    "li", "ol", "p", "pre", "s", "small", "span", "strong", "sub", "summary",
    "sup", "table", "tbody", "td", "th", "thead", "tr", "u", "ul",
}

_ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "abbr": {"title"},
    "img": {"src", "alt", "title", "width", "height"},
    "ol": {"start", "type"},
    "td": {"colspan", "rowspan", "align"},
    "th": {"colspan", "rowspan", "scope", "align"},
    "code": {"class"},
    "pre": {"class"},
    "span": {"class"},
    "div": {"class"},
    "p": {"class"},
    "h1": {"id", "class"},
    "h2": {"id", "class"},
    "h3": {"id", "class"},
    "h4": {"id", "class"},
    "h5": {"id", "class"},
    "h6": {"id", "class"},
}

_EXTENSIONS = (
    "fenced_code",
    "tables",
    "sane_lists",
    "footnotes",
    "attr_list",
    "md_in_html",
    "toc",
)


def markdown_to_html(source: str) -> str:
    """Render Markdown to sanitized HTML5 suitable for Moodle content fields.

    Raw HTML is permitted as Markdown input but is sanitized before return.
    Script elements, event-handler attributes, unsafe URL schemes and unknown
    elements are removed. Relative links and image paths remain relative so
    that a later Moodle file-area resolver can rewrite them.
    """
    if not isinstance(source, str):
        raise TypeError("Treść Markdown musi być tekstem.")
    if len(source.encode("utf-8")) > 10 * 1024 * 1024:
        raise ValueError("Treść Markdown przekracza limit 10 MiB.")

    parser = Markdown(
        extensions=list(_EXTENSIONS),
        output_format="html5",
    )
    rendered = parser.convert(source)
    return nh3.clean(
        rendered,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto", "tel"},
        strip_comments=True,
    )

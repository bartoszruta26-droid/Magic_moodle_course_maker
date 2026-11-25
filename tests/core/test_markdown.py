from __future__ import annotations

import pytest

from magic_moodle.markdown import render_markdown


def test_renders_heading_levels_without_collapsing_them() -> None:
    rendered = render_markdown("# Tytuł\n\n## Rozdział\n\n### Podrozdział")
    assert "<h1>Tytuł</h1>" in rendered
    assert "<h2>Rozdział</h2>" in rendered
    assert "<h3>Podrozdział</h3>" in rendered


def test_renders_ordered_and_nested_lists() -> None:
    rendered = render_markdown("1. Pierwszy\n2. Drugi\n   - Podpunkt")
    assert "<ol>" in rendered
    assert "<li>Drugi" in rendered
    assert "<ul>" in rendered


def test_renders_tables_and_strikethrough() -> None:
    rendered = render_markdown(
        "| Pojęcie | Opis |\n| --- | --- |\n| Nerw | **błędny** |\n\n~~stare~~"
    )
    assert "<table>" in rendered
    assert "<th>Pojęcie</th>" in rendered
    assert "<strong>błędny</strong>" in rendered
    assert "<s>stare</s>" in rendered


def test_renders_links_images_quotes_and_fenced_code() -> None:
    rendered = render_markdown(
        "> Cytat\n\n[Dokument](https://example.org)\n\n"
        "![Schemat](https://example.org/image.png)\n\n"
        "```python\nprint('ok')\n```"
    )
    assert "<blockquote>" in rendered
    assert 'href="https://example.org"' in rendered
    assert '<img src="https://example.org/image.png"' in rendered
    assert "<pre><code" in rendered


def test_escapes_raw_html_and_rejects_unsafe_link_protocols() -> None:
    rendered = render_markdown(
        '<script>alert("x")</script>\n\n[klik](javascript:alert(1))'
    )
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert 'href="javascript:' not in rendered


def test_preserves_polish_characters_and_math_source() -> None:
    rendered = render_markdown("Żółć, ęśąźż oraz wzór $x^2 + y^2$")
    assert "Żółć, ęśąźż" in rendered
    assert "$x^2 + y^2$" in rendered


def test_requires_text_input() -> None:
    with pytest.raises(TypeError):
        render_markdown(None)  # type: ignore[arg-type]


def test_heading_offset_is_explicit_and_bounded() -> None:
    rendered = render_markdown("# Tytuł\\n\\n###### Najniższy")
    shifted = render_markdown("# Tytuł\\n\\n###### Najniższy", heading_offset=1)
    assert "<h1>Tytuł</h1>" in rendered
    assert "<h2>Tytuł</h2>" in shifted
    assert "<h6>Najniższy</h6>" in shifted


def test_rejects_invalid_heading_offset() -> None:
    with pytest.raises(ValueError):
        render_markdown("# Tytuł", heading_offset=6)

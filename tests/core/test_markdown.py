from __future__ import annotations

import pytest

from magic_moodle.markdown import markdown_to_html


def test_renders_semantic_heading_levels_and_paragraphs():
    html = markdown_to_html("# Tytuł\n\n## Rozdział\n\n### Podrozdział\n\nTekst akapitu.")
    assert "<h1>Tytuł</h1>" in html
    assert "id=" not in html
    assert "<h2>Rozdział</h2>" in html
    assert "<h3>Podrozdział</h3>" in html
    assert "<p>Tekst akapitu.</p>" in html


def test_renders_tables_and_ordered_lists():
    html = markdown_to_html(
        "| Pojęcie | Definicja |\n|---|---|\n| Neuron | Komórka nerwowa |\n\n"
        "1. Pierwszy etap\n2. Drugi etap"
    )
    assert "<table>" in html
    assert "<th>Pojęcie</th>" in html
    assert "<td>Neuron</td>" in html
    assert "<ol>" in html
    assert "<li>Pierwszy etap</li>" in html


def test_renders_fenced_code_block_and_inline_code():
    html = markdown_to_html("Przykład `print(1)`.\n\n```python\nprint('ok')\n```")
    assert "<code>print(1)</code>" in html
    assert "<pre>" in html
    assert "print(&#x27;ok&#x27;)" in html or "print('ok')" in html


def test_preserves_safe_links_images_and_relative_paths():
    html = markdown_to_html("[Dokument](https://example.org/doc) ![Schemat](media/schemat.png)")
    assert 'href="https://example.org/doc"' in html
    assert 'src="media/schemat.png"' in html
    assert 'alt="Schemat"' in html


def test_sanitizes_script_elements_event_handlers_and_javascript_urls():
    html = markdown_to_html(
        '<script>alert("x")</script>\n\n'
        '<img src="x" onerror="alert(1)">\n\n'
        '[zły](javascript:alert%281%29)'
    )
    assert "<script" not in html.lower()
    assert "onerror" not in html.lower()
    assert "javascript:" not in html.lower()
    assert "alert" not in html


def test_rejects_non_text_input():
    with pytest.raises(TypeError, match="musi być tekstem"):
        markdown_to_html(None)  # type: ignore[arg-type]


def test_rejects_oversized_markdown():
    with pytest.raises(ValueError, match="10 MiB"):
        markdown_to_html("x" * (10 * 1024 * 1024 + 1))

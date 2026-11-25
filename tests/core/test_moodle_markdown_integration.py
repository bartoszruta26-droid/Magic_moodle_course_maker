from magic_moodle.moodle_publish import _markdown_to_html


def test_moodle_publisher_uses_shared_markdown_renderer():
    html = _markdown_to_html("# Nagłówek\n\n| A | B |\n|---|---|\n| 1 | 2 |")
    assert "<h1>Nagłówek</h1>" in html
    assert "id=" not in html
    assert "<table>" in html
    assert "<td>1</td>" in html


def test_moodle_publisher_sanitizes_unsafe_raw_html():
    html = _markdown_to_html('<img src="x" onerror="alert(1)">')
    assert "onerror" not in html.lower()

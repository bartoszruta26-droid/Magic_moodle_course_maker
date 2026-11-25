from pathlib import Path

import pytest
import yaml

from magic_moodle.loader import load_course
from magic_moodle.markdown_import import (
    MarkdownImportError, import_markdown_course, parse_outline, split_markdown_chapters,
)


def _source_tree(tmp_path: Path) -> Path:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "course.md").write_text(
        "# Kurs testowy\n\n## Moduł 1. Wstęp\n\n"
        "### 1.1. Anatomia\n- punkt\n\n### 1.2. Fizjologia\n",
        encoding="utf-8",
    )
    (source_dir / "1_1_anatomia.md").write_text("# Anatomia\n\nTreść.\n", encoding="utf-8")
    return source_dir / "course.md"


def test_parse_outline_matches_only_explicit_topic_files(tmp_path):
    source = _source_tree(tmp_path)
    modules = parse_outline(source)
    assert len(modules) == 1
    assert [topic.number for topic in modules[0].topics] == ["1.1", "1.2"]
    assert modules[0].topics[0].source.name == "1_1_anatomia.md"
    assert modules[0].topics[1].source is None


def test_import_creates_loader_compatible_book_and_missing_report(tmp_path):
    source = _source_tree(tmp_path)
    destination = tmp_path / "generated"
    report = import_markdown_course(source, destination, title="Kurs testowy", short_name="TEST")

    course = load_course(destination)
    assert course.full_name == "Kurs testowy"
    assert course.section_count == 1
    assert course.activity_count == 1
    assert course.activity_types == {"book": 1}
    assert report["topics_in_outline"] == 2
    assert report["activities_created"] == 1
    assert report["missing_topics"][0]["topic"] == "1.2"
    assert (destination / "import-report.json").is_file()


def test_import_refuses_nonempty_destination(tmp_path):
    source = _source_tree(tmp_path)
    destination = tmp_path / "generated"
    destination.mkdir()
    (destination / "keep.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(MarkdownImportError, match="nie jest pusty"):
        import_markdown_course(source, destination)


def test_import_rejects_source_inside_destination(tmp_path):
    source = _source_tree(tmp_path)
    with pytest.raises(MarkdownImportError, match="wewnątrz źródeł"):
        import_markdown_course(source, source.parent / "out")


def test_generated_yaml_is_safe_and_explicit(tmp_path):
    source = _source_tree(tmp_path)
    destination = tmp_path / "generated"
    import_markdown_course(source, destination)
    data = yaml.safe_load((destination / "course.yaml").read_text(encoding="utf-8"))
    assert data["course"]["lang"] == "pl"
    section_file = next((destination / "sections").glob("*/section.yaml"))
    section = yaml.safe_load(section_file.read_text(encoding="utf-8"))
    assert [item["type"] for item in section["modules"]] == ["book"]

def test_import_real_neurology_course_outline(tmp_path):
    repository_root = Path(__file__).resolve().parents[2]
    source = repository_root / "courses/05-badanie-neurologiczne/course.md"
    destination = tmp_path / "neurology-import"

    report = import_markdown_course(source, destination)
    course = load_course(destination)

    assert report["modules"] == 16
    assert report["topics_in_outline"] == 155
    assert report["activities_created"] == 5
    assert len(report["missing_topics"]) == 150
    assert course.section_count == 16
    assert course.activity_count == 5
    assert course.activity_types == {"book": 5}


def test_split_markdown_chapters_preserves_content_and_order():
    source = (
        "# Temat główny\n\nWprowadzenie.\n\n"
        "## Pierwszy podrozdział\n\nTreść pierwsza.\n\n"
        "### Szczegół niższego poziomu\n\nTreść szczegółowa.\n\n"
        "## Drugi podrozdział\n\nTreść druga.\n"
    )
    chapters = split_markdown_chapters(source, "1.1. Temat główny")
    assert [item[0] for item in chapters] == [
        "1.1. Temat główny", "Pierwszy podrozdział", "Drugi podrozdział"
    ]
    assert [item[2] for item in chapters] == [False, True, True]
    assert "".join(item[1] for item in chapters) == source
    assert "### Szczegół niższego poziomu" in chapters[1][1]


def test_split_markdown_chapters_ignores_headings_inside_fenced_code():
    source = (
        "# Temat\n\nPrzed.\n\n"
        "```markdown\n## To nie jest podrozdział\n```\n\n"
        "## Rzeczywisty podrozdział\n\nTreść.\n"
    )
    chapters = split_markdown_chapters(source, "Temat")
    assert len(chapters) == 2
    assert chapters[1][0] == "Rzeczywisty podrozdział"
    assert "".join(item[1] for item in chapters) == source


def test_split_markdown_chapters_handles_empty_root_and_empty_subchapter():
    source = "## Pusty pierwszy\n## Wypełniony\nTreść\n## Pusty ostatni\n"
    chapters = split_markdown_chapters(source, "Temat")
    assert len(chapters) == 4
    assert chapters[0][1] == ""
    assert chapters[1][1] == "## Pusty pierwszy\n"
    assert chapters[3][1] == "## Pusty ostatni\n"


def test_import_creates_book_subchapters_from_source_headings(tmp_path):
    source = _source_tree(tmp_path)
    topic_file = source.parent / "1_1_anatomia.md"
    original = (
        "# Anatomia\n\nWprowadzenie.\n\n"
        "## Anatomia funkcjonalna\n\nTreść A.\n\n"
        "## Znaczenie kliniczne\n\nTreść B.\n"
    )
    topic_file.write_text(original, encoding="utf-8")
    destination = tmp_path / "generated"
    import_markdown_course(source, destination)
    course = load_course(destination)
    activity = course.sections[0].activities[0]
    chapters = activity.resource["chapters"]
    assert [item["subchapter"] for item in chapters] == [False, True, True]
    assert len(activity.content) == 3
    assert "".join(activity.content[item["content_file"]] for item in chapters) == original

def test_import_real_neurology_book_chapters_round_trip(tmp_path):
    """Sprawdza wszystkie rzeczywiste pliki: strukturę Book i bezstratność importu."""
    repository_root = Path(__file__).resolve().parents[2]
    source_dir = repository_root / "courses/05-badanie-neurologiczne"
    source = source_dir / "course.md"
    destination = tmp_path / "neurology-book-import"

    report = import_markdown_course(source, destination)
    course = load_course(destination)

    activities_by_ref = {
        activity.ref: activity
        for section in course.sections
        for activity in section.activities
    }
    assert len(activities_by_ref) == 5
    assert set(activities_by_ref) == {item["activity_ref"] for item in report["activities"]}

    for imported in report["activities"]:
        source_text = (source_dir / imported["source_file"]).read_text(encoding="utf-8")
        activity = activities_by_ref[imported["activity_ref"]]
        chapters = activity.resource["chapters"]

        expected = split_markdown_chapters(source_text, activity.name)
        assert len(chapters) == len(expected), imported["source_file"]
        assert [chapter["title"] for chapter in chapters] == [
            title for title, _, _ in expected
        ], imported["source_file"]
        assert [chapter["subchapter"] for chapter in chapters] == [
            is_subchapter for _, _, is_subchapter in expected
        ], imported["source_file"]

        reconstructed = "".join(
            activity.content[chapter["content_file"]]
            for chapter in chapters
        )
        assert reconstructed == source_text, imported["source_file"]

    assert course.section_count == 16
    assert course.activity_count == 5
    assert course.activity_types == {"book": 5}

def test_import_copies_and_rewrites_nested_local_assets(tmp_path):
    source = _source_tree(tmp_path)
    source_dir = source.parent
    (source_dir / "media").mkdir()
    (source_dir / "docs").mkdir()
    (source_dir / "media" / "zdjęcie test.png").write_bytes(b"PNG-DATA")
    (source_dir / "media" / "inline.png").write_bytes(b"INLINE-DATA")
    (source_dir / "docs" / "załącznik.pdf").write_bytes(b"PDF-DATA")
    original = (
        "# Anatomia\n\n"
        "![Zdjęcie](media/zdjęcie%20test.png?download=1#podpis)\n\n"
        "[Dokument](docs/załącznik.pdf)\n\n"
        '<img src="media/inline.png" alt="ilustracja">\n\n'
        "[Zewnętrzny](https://example.org/obraz.png)\n\n"
        "[Brakujący](missing.png)\n\n"
        "[Poza katalogiem](../../outside.txt)\n\n"
        "```markdown\n![Przykład kodu](not-an-asset.png)\n```\n"
    )
    (source_dir / "1_1_anatomia.md").write_text(original, encoding="utf-8")

    destination = tmp_path / "generated-assets"
    report = import_markdown_course(source, destination)
    activity = load_course(destination).sections[0].activities[0]
    chapters = activity.resource["chapters"]
    content = "".join(activity.content[item["content_file"]] for item in chapters)

    assert "assets/media/zdj%C4%99cie%20test.png?download=1#podpis" in content
    assert "[Dokument](assets/docs/za%C5%82%C4%85cznik.pdf)" in content
    assert 'src="assets/media/inline.png"' in content
    assert "https://example.org/obraz.png" in content
    assert "[Brakujący](missing.png)" in content
    assert "[Poza katalogiem](../../outside.txt)" in content
    assert "![Przykład kodu](not-an-asset.png)" in content

    asset_root = destination / "sections" / "01-modul-wstep" / activity.ref / "chapters" / "assets"
    assert (asset_root / "media" / "zdjęcie test.png").read_bytes() == b"PNG-DATA"
    assert (asset_root / "media" / "inline.png").read_bytes() == b"INLINE-DATA"
    assert (asset_root / "docs" / "załącznik.pdf").read_bytes() == b"PDF-DATA"
    assert report["assets"]["copied"] == 3
    assert len(report["assets"]["missing"]) == 1
    assert report["assets"]["rejected"][0]["reason"] == "path_traversal"


def test_import_rejects_symlinked_local_assets(tmp_path):
    source = _source_tree(tmp_path)
    source_dir = source.parent
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("not for import", encoding="utf-8")
    (source_dir / "linked.txt").symlink_to(outside)
    (source_dir / "1_1_anatomia.md").write_text(
        "[Link](linked.txt)\n", encoding="utf-8"
    )

    report = import_markdown_course(source, tmp_path / "generated-symlink")
    assert report["assets"]["copied"] == 0
    assert report["assets"]["rejected"] == [
        {"topic": "1.1", "url": "linked.txt", "reason": "symlink"}
    ]


def test_import_rejects_backslashes_and_empty_normalized_asset_paths(tmp_path):
    source = _source_tree(tmp_path)
    (source.parent / "1_1_anatomia.md").write_text(
        "[Backslash](folder\\file.txt)\n"
        "[Encoded backslash](folder%5Cfile.txt)\n"
        "[Current directory](.)\n",
        encoding="utf-8",
    )

    report = import_markdown_course(source, tmp_path / "generated-invalid-paths")

    assert report["assets"]["copied"] == 0
    assert report["assets"]["missing"] == []
    assert report["assets"]["rejected"] == [
        {"topic": "1.1", "url": "folder\\file.txt", "reason": "absolute_or_backslash_path"},
        {"topic": "1.1", "url": "folder%5Cfile.txt", "reason": "invalid_path"},
        {"topic": "1.1", "url": ".", "reason": "invalid_path"},
    ]


def test_import_rewrites_srcset_css_and_reference_markdown_assets(tmp_path):
    source = _source_tree(tmp_path)
    source_dir = source.parent
    (source_dir / "media").mkdir()
    (source_dir / "media" / "small.png").write_bytes(b"SMALL")
    (source_dir / "media" / "large.png").write_bytes(b"LARGE")
    (source_dir / "media" / "background image.png").write_bytes(b"BACKGROUND")
    (source_dir / "media" / "reference.pdf").write_bytes(b"REFERENCE")
    original = (
        "![Responsywne](placeholder.png)\n"
        '<img srcset="media/small.png 1x, media/large.png 2x" alt="warianty">\n'
        '<div style="background-image: url(\'media/background%20image.png\')"></div>\n'
        "<style> .hero { background: url(media/large.png); } </style>\n"
        "[dokument]: <media/reference.pdf> \"Opis\"\n"
        "[Dokument][dokument]\n"
        '<img srcset="https://cdn.example.org/a.png 1x, media/small.png 2x">\n'
        '<img srcset="data:image/png;base64,AAAA 1x, media/large.png 2x">\n'
    )
    (source_dir / "1_1_anatomia.md").write_text(original, encoding="utf-8")

    destination = tmp_path / "generated-rich-assets"
    report = import_markdown_course(source, destination)
    activity = load_course(destination).sections[0].activities[0]
    content = "".join(
        activity.content[item["content_file"]]
        for item in activity.resource["chapters"]
    )

    assert 'srcset="assets/media/small.png 1x, assets/media/large.png 2x"' in content
    assert "url('assets/media/background%20image.png')" in content
    assert "url(assets/media/large.png)" in content
    assert "[dokument]: <assets/media/reference.pdf> \"Opis\"" in content
    assert "[Dokument][dokument]" in content
    assert "https://cdn.example.org/a.png 1x, assets/media/small.png 2x" in content
    assert "data:image/png;base64,AAAA 1x, assets/media/large.png 2x" in content
    assert report["assets"]["copied"] == 4

    assets = (
        destination / "sections" / "01-modul-wstep"
        / activity.ref / "chapters" / "assets" / "media"
    )
    assert (assets / "small.png").read_bytes() == b"SMALL"
    assert (assets / "large.png").read_bytes() == b"LARGE"
    assert (assets / "background image.png").read_bytes() == b"BACKGROUND"
    assert (assets / "reference.pdf").read_bytes() == b"REFERENCE"

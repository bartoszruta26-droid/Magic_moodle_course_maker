from pathlib import Path

import pytest

from magic_moodle.loader import load_course
from magic_moodle.markdown_import import (
    MarkdownImportError,
    import_markdown_course,
    parse_outline,
    split_markdown_chapters,
)


def _source_tree(tmp_path: Path) -> Path:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "course.md").write_text(
        "# Kurs testowy\n\n## Moduł 1. Wstęp\n\n"
        "### 1.1. Anatomia\n\n### 1.2. Fizjologia\n",
        encoding="utf-8",
    )
    (source_dir / "1_1_anatomia.md").write_text(
        "# Anatomia\n\nTreść.\n", encoding="utf-8"
    )
    return source_dir / "course.md"


def test_parse_outline_maps_only_matching_source_files(tmp_path):
    source = _source_tree(tmp_path)
    topics = parse_outline(source)[0].topics
    assert [topic.number for topic in topics] == ["1.1", "1.2"]
    assert topics[0].source.name == "1_1_anatomia.md"
    assert topics[1].source is None


def test_import_generates_loader_compatible_book_and_report(tmp_path):
    source = _source_tree(tmp_path)
    destination = tmp_path / "generated"
    report = import_markdown_course(source, destination, title="Kurs testowy", short_name="TEST")
    course = load_course(destination)

    assert course.full_name == "Kurs testowy"
    assert course.section_count == 1
    assert course.activity_count == report["activities_created"] == 1
    assert course.activity_types == {"book": 1}
    assert report["missing_topics"][0]["topic"] == "1.2"
    assert report["mbz_status"] == "not_generated"
    assert (destination / "import-report.json").is_file()


def test_import_refuses_nonempty_destination_and_source_inside_destination(tmp_path):
    source = _source_tree(tmp_path)
    destination = tmp_path / "occupied"
    destination.mkdir()
    (destination / "keep.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(MarkdownImportError, match="nie jest pusty"):
        import_markdown_course(source, destination)
    with pytest.raises(MarkdownImportError, match="wewnątrz źródeł"):
        import_markdown_course(source, source.parent / "nested")


def test_split_markdown_chapters_preserves_content_and_fenced_headings():
    markdown = (
        "# Temat główny\n\nWprowadzenie.\n\n"
        "## Pierwszy podrozdział\n\nTreść pierwsza.\n\n"
        "```md\n## Nagłówek w kodzie\n```\n\n"
        "### Szczegół\nTreść szczegółowa.\n\n"
        "## Drugi podrozdział\nTreść druga.\n"
    )
    chapters = split_markdown_chapters(markdown, "1.1. Temat główny")
    assert [chapter[0] for chapter in chapters] == [
        "1.1. Temat główny", "Pierwszy podrozdział", "Drugi podrozdział"
    ]
    assert [chapter[2] for chapter in chapters] == [False, True, True]
    assert "".join(chapter[1] for chapter in chapters) == markdown


def test_import_copies_local_assets_and_rewrites_references(tmp_path):
    source = _source_tree(tmp_path)
    source_dir = source.parent
    (source_dir / "media").mkdir()
    (source_dir / "media" / "diagram.png").write_bytes(b"PNGDATA")
    (source_dir / "1_1_anatomia.md").write_text(
        "![Schemat](media/diagram.png)\n", encoding="utf-8"
    )

    destination = tmp_path / "generated-assets"
    report = import_markdown_course(source, destination)
    activity = load_course(destination).sections[0].activities[0]
    chapter_content = "".join(
        activity.content[chapter["content_file"]]
        for chapter in activity.resource["chapters"]
    )
    assert "assets/media/diagram.png" in chapter_content
    asset = (
        destination / "sections" / "01-modul-wstep" / activity.ref
        / "chapters" / "assets" / "media" / "diagram.png"
    )
    assert asset.read_bytes() == b"PNGDATA"
    assert report["assets"]["copied"] == 1

from pathlib import Path

import pytest
import yaml

from magic_moodle.loader import load_course
from magic_moodle.markdown_import import MarkdownImportError, import_markdown_course, parse_outline


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

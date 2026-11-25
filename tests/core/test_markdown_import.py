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

from pathlib import Path

from magic_moodle.loader import load_course
from magic_moodle.validation import validate_course


def make_course(root: Path) -> Path:
    section = root / "sections" / "01-intro"
    section.mkdir(parents=True)
    (root / "course.yaml").write_text(
        "course:\n  full_name: Kurs testowy\n  short_name: TEST\n"
        "description:\n  markdown_file: course.md\n", encoding="utf-8"
    )
    (root / "course.md").write_text("# Witaj", encoding="utf-8")
    (section / "section.yaml").write_text(
        "id: 1\nname: Wprowadzenie\nmodules:\n"
        "  - type: page\n    ref: page-01.md\n    name: Start\n", encoding="utf-8"
    )
    (section / "page-01.md").write_text("# Start", encoding="utf-8")
    (section / "section.md").write_text("Opis sekcji", encoding="utf-8")
    return root


def test_loads_repository_course_shape(tmp_path: Path) -> None:
    course = load_course(make_course(tmp_path))
    assert course.full_name == "Kurs testowy"
    assert course.section_count == 1
    assert course.activity_count == 1
    assert course.description == "# Witaj"


def test_validator_detects_missing_activity_reference(tmp_path: Path) -> None:
    root = make_course(tmp_path)
    (root / "sections" / "01-intro" / "section.yaml").write_text(
        "id: 1\nname: Wprowadzenie\nmodules:\n"
        "  - type: page\n    ref: missing.md\n    name: Brak\n", encoding="utf-8"
    )
    report = validate_course(load_course(root))
    assert not report.ok
    assert any(item.code == "ACTIVITY_REF_MISSING" for item in report.errors)


def test_validator_accepts_valid_minimal_course(tmp_path: Path) -> None:
    report = validate_course(load_course(make_course(tmp_path)))
    assert report.ok
    assert not report.errors

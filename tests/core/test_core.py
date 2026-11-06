from pathlib import Path

import pytest

from magic_moodle.loader import CourseLoadError, load_course
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
    assert course.activity_types == {"page": 1}


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


def test_loads_book_chapters_and_assignment_instructions(tmp_path: Path) -> None:
    root = make_course(tmp_path)
    section = root / "sections" / "01-intro"
    book = section / "book-01"
    (book / "chapters").mkdir(parents=True)
    (book / "book.yaml").write_text(
        "book:\n  name: Podręcznik\n  chapters:\n"
        "    - title: Rozdział 1\n      content_file: chapters/01.md\n",
        encoding="utf-8",
    )
    (book / "chapters" / "01.md").write_text("# Treść rozdziału", encoding="utf-8")
    assignment = section / "assignment-01"
    assignment.mkdir()
    (assignment / "assignment.yaml").write_text(
        "name: Zadanie\nmarkdown_file: instructions.md\nsubmission_types: [onlinetext]\n",
        encoding="utf-8",
    )
    (assignment / "instructions.md").write_text("Wykonaj zadanie.", encoding="utf-8")
    (section / "section.yaml").write_text(
        "id: 1\nname: Wprowadzenie\nmodules:\n"
        "  - type: book\n    ref: book-01\n    name: Podręcznik\n"
        "  - type: assignment\n    ref: assignment-01\n    name: Zadanie\n",
        encoding="utf-8",
    )

    course = load_course(root)
    book_activity, assignment_activity = course.sections[0].activities
    assert book_activity.resource["name"] == "Podręcznik"
    assert book_activity.content["chapters/01.md"] == "# Treść rozdziału"
    assert assignment_activity.resource["submission_types"] == ["onlinetext"]
    assert assignment_activity.content["instructions.md"] == "Wykonaj zadanie."
    assert validate_course(course).ok


def test_rejects_description_path_traversal(tmp_path: Path) -> None:
    root = make_course(tmp_path)
    (root / "course.yaml").write_text(
        "course:\n  full_name: Test\n  short_name: TEST\n"
        "description:\n  markdown_file: ../outside.md\n", encoding="utf-8"
    )
    with pytest.raises(CourseLoadError, match="poza dozwolony katalog"):
        load_course(root)


def test_rejects_book_chapter_path_traversal(tmp_path: Path) -> None:
    root = make_course(tmp_path)
    section = root / "sections" / "01-intro"
    book = section / "book-01"
    book.mkdir()
    (book / "book.yaml").write_text(
        "book:\n  chapters:\n    - title: Zły\n      content_file: ../../outside.md\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: 1\nname: Wprowadzenie\nmodules:\n"
        "  - type: book\n    ref: book-01\n    name: Podręcznik\n",
        encoding="utf-8",
    )
    with pytest.raises(CourseLoadError, match="poza dozwolony katalog"):
        load_course(root)


def test_glossary_requires_terms_and_definitions(tmp_path: Path) -> None:
    root = make_course(tmp_path)
    section = root / "sections" / "01-intro"
    glossary = section / "glossary-01"
    glossary.mkdir()
    (glossary / "glossary.yaml").write_text(
        "glossary:\n  name: Słownik\n  entries:\n    - term: Pojęcie\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: 1\nname: Wprowadzenie\nmodules:\n"
        "  - type: glossary\n    ref: glossary-01\n    name: Słownik\n",
        encoding="utf-8",
    )
    report = validate_course(load_course(root))
    assert any(item.code == "GLOSSARY_ENTRY_INVALID" for item in report.errors)


def test_loads_quiz_configuration_with_repository_schema(tmp_path: Path) -> None:
    root = make_course(tmp_path)
    section = root / "sections" / "01-intro"
    quiz = section / "quiz-01"
    quiz.mkdir()
    (quiz / "quiz.yaml").write_text(
        "name: Test wiedzy\nquestions_file: questions.gift\ntime_limit: 600\nattempts: 2\n",
        encoding="utf-8",
    )
    (quiz / "questions.gift").write_text("::Pytanie:: 2+2? {=4}", encoding="utf-8")
    (section / "section.yaml").write_text(
        "id: 1\nname: Wprowadzenie\nmodules:\n"
        "  - type: quiz\n    ref: quiz-01\n    name: Test wiedzy\n",
        encoding="utf-8",
    )
    activity = load_course(root).sections[0].activities[0]
    assert activity.resource["name"] == "Test wiedzy"
    assert activity.resource["questions_file"] == "questions.gift"
    assert activity.content["questions.gift"] == "::Pytanie:: 2+2? {=4}"
    assert validate_course(load_course(root)).ok



def test_rejects_symlinked_activity_config_outside_course(tmp_path: Path) -> None:
    root = make_course(tmp_path / "course")
    section = root / "sections" / "01-intro"
    activity_dir = section / "book-01"
    activity_dir.mkdir()
    outside = tmp_path / "outside.yaml"
    outside.write_text("book:" + chr(10) + "  chapters: []" + chr(10), encoding="utf-8")
    try:
        (activity_dir / "book.yaml").symlink_to(outside)
    except OSError:
        pytest.skip("System plików nie pozwala tworzyć dowiązań symbolicznych.")
    (section / "section.yaml").write_text(
        "id: 1" + chr(10) + "name: Wprowadzenie" + chr(10) + "modules:" + chr(10)
        + "  - type: book" + chr(10) + "    ref: book-01" + chr(10) + "    name: Podręcznik" + chr(10),
        encoding="utf-8",
    )
    with pytest.raises(CourseLoadError, match="poza dozwolony katalog"):
        load_course(root)


def test_rejects_section_symlink_outside_course(tmp_path: Path) -> None:
    root = make_course(tmp_path / "course")
    outside = tmp_path / "outside-section"
    outside.mkdir()
    (outside / "section.yaml").write_text("id: 9" + chr(10) + "name: Obca" + chr(10) + "modules: []" + chr(10), encoding="utf-8")
    try:
        (root / "sections" / "external").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("System plików nie pozwala tworzyć dowiązań symbolicznych.")
    with pytest.raises(CourseLoadError, match="dowiązanie symboliczne"):
        load_course(root)


def test_rejects_oversized_yaml_file(tmp_path: Path) -> None:
    root = make_course(tmp_path)
    (root / "course.yaml").write_text("x: " + ("a" * (2 * 1024 * 1024)), encoding="utf-8")
    with pytest.raises(CourseLoadError, match="przekracza limit"):
        load_course(root)



def test_rejects_symlinked_section_config_outside_course(tmp_path: Path) -> None:
    root = make_course(tmp_path / "course")
    section = root / "sections" / "01-intro"
    outside = tmp_path / "external-section.yaml"
    outside.write_text("id: 9\\nname: Obca\\nmodules: []\\n", encoding="utf-8")
    (section / "section.yaml").unlink()
    try:
        (section / "section.yaml").symlink_to(outside)
    except OSError:
        pytest.skip("System plików nie pozwala tworzyć dowiązań symbolicznych.")
    with pytest.raises(CourseLoadError, match="poza dozwolony katalog"):
        load_course(root)


def test_rejects_symlinked_course_config_outside_root(tmp_path: Path) -> None:
    root = make_course(tmp_path / "course")
    outside = tmp_path / "external-course.yaml"
    outside.write_text(
        "course:" + chr(10) + "  full_name: Zewnętrzny" + chr(10) + "  short_name: EXT" + chr(10),
        encoding="utf-8",
    )
    (root / "course.yaml").unlink()
    try:
        (root / "course.yaml").symlink_to(outside)
    except OSError:
        pytest.skip("System plików nie pozwala tworzyć dowiązań symbolicznych.")
    with pytest.raises(CourseLoadError, match="poza dozwolony katalog"):
        load_course(root)

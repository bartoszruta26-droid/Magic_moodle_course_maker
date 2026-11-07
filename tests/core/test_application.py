from pathlib import Path

import pytest

from magic_moodle.application import CourseApplicationService, CourseNotFoundError


def make_course(root: Path, *, name: str = "Kurs testowy") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "course.yaml").write_text(
        f"course:\n  full_name: {name}\n  short_name: TEST\n",
        encoding="utf-8",
    )
    section = root / "sections" / "01-intro"
    section.mkdir(parents=True)
    (section / "section.yaml").write_text(
        "id: intro\nname: Wprowadzenie\nmodules: []\n",
        encoding="utf-8",
    )
    return root


def test_list_courses_returns_presentation_neutral_summaries(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")

    result = CourseApplicationService(courses).list_courses()

    assert len(result) == 1
    assert result[0].id == "sample"
    assert result[0].name == "Kurs testowy"
    assert result[0].short_name == "TEST"
    assert result[0].sections == 1
    assert result[0].activities == 0
    assert result[0].load_error is False


def test_list_courses_keeps_malformed_course_visible(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    broken = courses / "broken"
    broken.mkdir(parents=True)
    (broken / "course.yaml").write_text("[]", encoding="utf-8")

    result = CourseApplicationService(courses).list_courses()

    assert len(result) == 1
    assert result[0].id == "broken"
    assert result[0].load_error is True
    assert result[0].sections is None


def test_list_courses_returns_empty_for_missing_root(tmp_path: Path) -> None:
    result = CourseApplicationService(tmp_path / "missing").list_courses()
    assert result == []


def test_get_course_and_validate_share_core_models(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")
    service = CourseApplicationService(courses)

    course = service.get_course("sample")
    validated_course, report = service.validate("sample")

    assert course.full_name == "Kurs testowy"
    assert validated_course.short_name == course.short_name
    assert report.ok is True


@pytest.mark.parametrize("course_id", ["", ".", "..", "../outside", "a/b", r"a\\b"])
def test_get_course_rejects_invalid_identifiers(
    tmp_path: Path, course_id: str
) -> None:
    service = CourseApplicationService(tmp_path / "courses")
    with pytest.raises(CourseNotFoundError):
        service.get_course(course_id)


def test_get_course_rejects_symlink_escape(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    outside = make_course(tmp_path / "outside")
    courses.mkdir()
    try:
        (courses / "escape").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("System plików nie pozwala tworzyć dowiązań symbolicznych.")

    with pytest.raises(CourseNotFoundError):
        CourseApplicationService(courses).get_course("escape")


def test_export_json_uses_canonical_course_manifest(tmp_path: Path) -> None:
    import json

    courses = tmp_path / "courses"
    make_course(courses / "sample")
    destination = tmp_path / "exports" / "sample.manifest.json"

    result = CourseApplicationService(courses).export_json("sample", destination)

    assert result == destination
    manifest = json.loads(destination.read_text(encoding="utf-8"))
    assert manifest["course"]["full_name"] == "Kurs testowy"
    assert manifest["format"] == "magic-moodle-course-manifest"
    assert str(courses) not in destination.read_text(encoding="utf-8")


def test_export_json_rejects_invalid_course_identifier(tmp_path: Path) -> None:
    service = CourseApplicationService(tmp_path / "courses")
    with pytest.raises(CourseNotFoundError):
        service.export_json("../outside", tmp_path / "manifest.json")


def test_question_bank_load_and_xml_export(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    course = make_course(courses / "sample")
    bank_dir = course / "question-bank" / "multichoice"
    bank_dir.mkdir(parents=True)
    (bank_dir / "set-01.gift").write_text(
        "::q1::Która odpowiedź jest prawidłowa? {=Poprawna ~Błędna}\n",
        encoding="utf-8",
    )
    service = CourseApplicationService(courses)

    bank = service.get_question_bank("sample")
    destination = tmp_path / "exports" / "sample.questions.xml"
    output = service.export_question_bank_xml("sample", destination)

    assert len(bank.questions) == 1
    assert bank.by_type() == {"multichoice": 1}
    assert output == destination
    assert 'type="category"' in destination.read_text(encoding="utf-8")
    assert "Która odpowiedź jest prawidłowa?" in destination.read_text(encoding="utf-8")


def test_question_bank_requires_existing_course_bank(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")
    with pytest.raises(FileNotFoundError):
        CourseApplicationService(courses).get_question_bank("sample")


def test_question_bank_rejects_symlink_escape(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    course = make_course(courses / "sample")
    outside = tmp_path / "outside-bank"
    outside.mkdir()
    (outside / "set.gift").write_text(
        "::q1::Pytanie? {=Tak ~Nie}\\n",
        encoding="utf-8",
    )
    try:
        (course / "question-bank").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("System plików nie pozwala tworzyć dowiązań symbolicznych.")

    with pytest.raises(ValueError, match="poza katalogiem kursu"):
        CourseApplicationService(courses).get_question_bank("sample")

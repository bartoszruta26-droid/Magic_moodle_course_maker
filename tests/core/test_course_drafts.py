from __future__ import annotations

import json
from pathlib import Path

import pytest

from magic_moodle.application import (
    CourseDraftConflictError,
    CourseDraftNotFoundError,
    CourseDraftService,
    CourseDraftValidationError,
)


def make_course(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "course.yaml").write_text(
        "course:\n  full_name: Kurs bazowy\n  short_name: BASE\n"
        "description:\n  markdown_file: description.md\n",
        encoding="utf-8",
    )
    (root / "description.md").write_text("Opis bazowy", encoding="utf-8")
    section = root / "sections" / "01-intro"
    section.mkdir(parents=True)
    (section / "section.yaml").write_text(
        "id: intro\nname: Wprowadzenie\nmodules:\n"
        "  - type: page\n    ref: page.md\n    name: Strona bazowa\n",
        encoding="utf-8",
    )
    (section / "page.md").write_text("# Treść strony", encoding="utf-8")
    return root


def test_create_and_preview_draft_without_modifying_source(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    course_path = make_course(courses / "sample")
    original = (course_path / "course.yaml").read_text(encoding="utf-8")
    service = CourseDraftService(courses)

    draft = service.create("sample")
    updated = service.update(
        draft.draft_id,
        expected_revision=1,
        changes={
            "full_name": "Kurs po zmianie",
            "short_name": "UPDATED",
            "description": "Nowy opis",
            "section_names": {"intro": "Podstawy"},
            "activity_names": {"intro|page.md": "Strona po zmianie"},
        },
    )
    preview = service.preview(draft.draft_id)

    assert updated.revision == 2
    assert preview["draft"]["revision"] == 2
    assert preview["course"]["course"]["full_name"] == "Kurs po zmianie"
    assert preview["course"]["course"]["short_name"] == "UPDATED"
    assert preview["course"]["course"]["description"] == "Nowy opis"
    assert preview["course"]["sections"][0]["name"] == "Podstawy"
    assert preview["course"]["sections"][0]["activities"][0]["name"] == "Strona po zmianie"
    assert preview["validation"]["ok"] is True
    assert preview["source_modified"] is False
    assert (course_path / "course.yaml").read_text(encoding="utf-8") == original
    assert (course_path / "description.md").read_text(encoding="utf-8") == "Opis bazowy"


def test_draft_update_requires_current_revision(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")
    service = CourseDraftService(courses)
    draft = service.create("sample")
    service.update(
        draft.draft_id,
        expected_revision=1,
        changes={"full_name": "Pierwsza zmiana"},
    )

    with pytest.raises(CourseDraftConflictError, match="Bieżąca rewizja: 2"):
        service.update(
            draft.draft_id,
            expected_revision=1,
            changes={"full_name": "Nadpisanie"},
        )


def test_preview_detects_source_course_change(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    course = make_course(courses / "sample")
    service = CourseDraftService(courses)
    draft = service.create("sample")
    (course / "description.md").write_text("Zmiana poza wersją roboczą", encoding="utf-8")

    with pytest.raises(CourseDraftConflictError, match="Kurs źródłowy zmienił się"):
        service.preview(draft.draft_id)


@pytest.mark.parametrize(
    "changes",
    [
        {"unknown_field": "value"},
        {"full_name": ""},
        {"short_name": 123},
        {"section_names": ["not", "a", "mapping"]},
        {"activity_names": {"intro|missing.md": "Brak"}},
    ],
)
def test_draft_rejects_invalid_changes(tmp_path: Path, changes: dict) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")
    service = CourseDraftService(courses)
    draft = service.create("sample")

    if "activity_names" in changes:
        with pytest.raises(CourseDraftValidationError, match="Nie znaleziono aktywności"):
            service.update(draft.draft_id, expected_revision=1, changes=changes)
    else:
        with pytest.raises(CourseDraftValidationError):
            service.update(draft.draft_id, expected_revision=1, changes=changes)


def test_draft_storage_is_json_and_does_not_write_course_files(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    course = make_course(courses / "sample")
    service = CourseDraftService(courses)
    draft = service.create("sample")
    draft_file = courses / ".magic_moodle" / "drafts" / f"{draft.draft_id}.json"

    payload = json.loads(draft_file.read_text(encoding="utf-8"))
    assert payload["format"] == "magic-moodle-course-draft"
    assert payload["format_version"] == 1
    assert payload["course_id"] == "sample"
    assert (course / "course.yaml").is_file()


def test_get_rejects_unknown_or_malformed_draft_id(tmp_path: Path) -> None:
    service = CourseDraftService(tmp_path / "courses")
    with pytest.raises(CourseDraftNotFoundError):
        service.get("../outside")
    with pytest.raises(CourseDraftNotFoundError):
        service.get("00000000-0000-0000-0000-000000000000")

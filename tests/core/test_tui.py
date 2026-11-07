import asyncio
from pathlib import Path

from textual.widgets import DataTable

from tui.app import _build_app


def test_tui_app_uses_shared_application_service() -> None:
    app = _build_app()
    assert app.title == "Magic Moodle Course Maker"
    assert app.service.__class__.__name__ == "CourseApplicationService"
    assert app._selected_id is None


def test_tui_mounts_and_lists_courses(tmp_path: Path, monkeypatch) -> None:
    courses = tmp_path / "courses"
    course = courses / "sample"
    course.mkdir(parents=True)
    (course / "course.yaml").write_text(
        "course:\n  full_name: Kurs TUI\n  short_name: TUI\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MAGIC_MOODLE_COURSES", str(courses))
    app = _build_app()

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            table = app.query_one("#course-table", DataTable)
            assert table.row_count == 1

    asyncio.run(exercise())


def test_tui_export_button_writes_manifest(tmp_path: Path, monkeypatch) -> None:
    import asyncio
    import json

    from textual.widgets import DataTable

    courses = tmp_path / "courses"
    course = courses / "sample"
    course.mkdir(parents=True)
    (course / "course.yaml").write_text(
        "course:\n  full_name: Kurs eksportowy\n  short_name: EXP\n",
        encoding="utf-8",
    )
    exports = tmp_path / "exports"
    monkeypatch.setenv("MAGIC_MOODLE_COURSES", str(courses))
    monkeypatch.setenv("MAGIC_MOODLE_EXPORTS", str(exports))
    app = _build_app()

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            table = app.query_one("#course-table", DataTable)
            app._selected_id = "sample"
            await pilot.click("#export")
            await pilot.pause()
            manifest = exports / "sample.manifest.json"
            assert manifest.is_file()
            assert json.loads(manifest.read_text(encoding="utf-8"))["course"]["full_name"] == "Kurs eksportowy"

    asyncio.run(exercise())


def test_tui_question_bank_actions_validate_and_export(tmp_path: Path, monkeypatch) -> None:
    import asyncio
    import xml.etree.ElementTree as ET

    courses = tmp_path / "courses"
    course = courses / "sample"
    course.mkdir(parents=True)
    (course / "course.yaml").write_text(
        "course:\n  full_name: Kurs z bankiem\n  short_name: BANK\n",
        encoding="utf-8",
    )
    bank_dir = course / "question-bank"
    bank_dir.mkdir()
    (bank_dir / "set-01.gift").write_text(
        "::q1::Pytanie testowe? {=Tak ~Nie}\n",
        encoding="utf-8",
    )
    exports = tmp_path / "exports"
    monkeypatch.setenv("MAGIC_MOODLE_COURSES", str(courses))
    monkeypatch.setenv("MAGIC_MOODLE_EXPORTS", str(exports))
    app = _build_app()

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            app._selected_id = "sample"
            await pilot.click("#bank-export")
            await pilot.pause()
            xml_file = exports / "sample.questions.xml"
            assert xml_file.is_file()
            assert ET.parse(xml_file).getroot().tag == "quiz"

    asyncio.run(exercise())


def test_tui_draft_editor_saves_course_metadata_and_sections(tmp_path: Path, monkeypatch) -> None:
    from textual.widgets import Button, Input, Static, TextArea

    courses = tmp_path / "courses"
    course = courses / "sample"
    course.mkdir(parents=True)
    (course / "course.yaml").write_text(
        "course:\n  full_name: Kurs TUI\n  short_name: TUI\n",
        encoding="utf-8",
    )
    section = course / "sections" / "intro"
    section.mkdir(parents=True)
    (section / "section.yaml").write_text(
        "id: intro\nname: Wprowadzenie\nmodules: []\n",
        encoding="utf-8",
    )
    original = (course / "course.yaml").read_text(encoding="utf-8")
    monkeypatch.setenv("MAGIC_MOODLE_COURSES", str(courses))
    app = _build_app()

    async def exercise() -> None:
        async with app.run_test() as pilot:
            await pilot.pause()
            app._selected_id = "sample"
            await pilot.click("#draft-edit")
            await pilot.pause()

            editor = app.screen
            assert editor.query_one("#draft-full-name", Input).value == "Kurs TUI"
            editor.query_one("#draft-full-name", Input).value = "Kurs TUI po zmianie"
            editor.query_one("#draft-section-0", Input).value = "Podstawy TUI"
            editor.query_one("#draft-description", TextArea).text = "Opis wersji roboczej"
            await pilot.click("#draft-save")
            await pilot.pause()

            assert app._draft.revision == 2
            preview = app.draft_service.preview(app._draft.draft_id)
            assert preview["course"]["course"]["full_name"] == "Kurs TUI po zmianie"
            assert preview["course"]["course"]["description"] == "Opis wersji roboczej"
            assert preview["course"]["sections"][0]["name"] == "Podstawy TUI"
            assert (course / "course.yaml").read_text(encoding="utf-8") == original
            detail = app.query_one("#detail", Static)
            assert "WERSJA ROBOCZA ZAPISANA" in str(detail.render())

    asyncio.run(exercise())

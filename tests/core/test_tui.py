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

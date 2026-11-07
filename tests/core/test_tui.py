from tui.app import _build_app


def test_tui_app_uses_shared_application_service() -> None:
    app = _build_app()
    assert app.title == "Magic Moodle Course Maker"
    assert app.service.__class__.__name__ == "CourseApplicationService"
    assert app._selected_id is None

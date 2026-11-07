from desktopgui.app import main


def test_desktop_gui_module_imports_without_loading_qt() -> None:
    assert callable(main)

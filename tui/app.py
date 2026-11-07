"""Interactive terminal interface built on the shared application service."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _build_app():
    """Build Textual lazily so the core remains independent of UI packages."""
    try:
        from textual.app import App
        from textual.containers import Horizontal, Vertical, VerticalScroll
        from textual.screen import ModalScreen
        from textual.widgets import Button, DataTable, Footer, Header, Input, Static, TextArea
    except ImportError as exc:
        raise RuntimeError(
            "Interfejs TUI wymaga dodatku Textual. Zainstaluj: "
            "python -m pip install '.[tui]'"
        ) from exc

    from magic_moodle.application import (
        CourseApplicationService,
        CourseDraftConflictError,
        CourseDraftService,
        CourseDraftValidationError,
        CourseNotFoundError,
    )
    from magic_moodle.loader import CourseLoadError

    class DraftEditorScreen(ModalScreen[dict | None]):
        """Small form for editing course metadata and section titles."""

        def __init__(self, preview: dict) -> None:
            super().__init__()
            self.preview = preview

        def compose(self):
            course = self.preview["course"]["course"]
            sections = self.preview["course"]["sections"]
            with Vertical(id="draft-dialog"):
                yield Static("EDYTOR WERSJI ROBOCZEJ")
                with VerticalScroll(id="draft-scroll"):
                    yield Static("Nazwa kursu")
                    yield Input(value=course["full_name"], id="draft-full-name")
                    yield Static("Nazwa skrócona")
                    yield Input(value=course["short_name"], id="draft-short-name")
                    yield Static("Opis kursu")
                    yield TextArea(text=course.get("description", ""), id="draft-description")
                    yield Static("Nazwy sekcji")
                    for index, section in enumerate(sections):
                        yield Static(f"Sekcja: {section['id']}")
                        yield Input(value=section["name"], id=f"draft-section-{index}")
                with Horizontal(id="draft-actions"):
                    yield Button("Anuluj", id="draft-cancel")
                    yield Button("Zapisz wersję roboczą", id="draft-save", variant="primary")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "draft-cancel":
                self.dismiss(None)
                return
            if event.button.id != "draft-save":
                return
            sections = self.preview["course"]["sections"]
            changes = {
                "full_name": self.query_one("#draft-full-name", Input).value,
                "short_name": self.query_one("#draft-short-name", Input).value,
                "description": self.query_one("#draft-description", TextArea).text,
                "section_names": {
                    section["id"]: self.query_one(f"#draft-section-{index}", Input).value
                    for index, section in enumerate(sections)
                },
            }
            self.dismiss(changes)

    class MagicMoodleTui(App):
        """Course browser and validator; business operations use app services."""

        TITLE = "Magic Moodle Course Maker"
        SUB_TITLE = "Pracownia kursów · TUI"
        CSS = """
        #workspace { height: 1fr; }
        #sidebar { width: 42%; min-width: 32; border-right: solid $primary; padding: 1; }
        #main { width: 1fr; padding: 1; }
        #course-table { height: 1fr; }
        #detail { height: 1fr; border: round $secondary; padding: 1; }
        #validate, #draft-edit, #export, #bank-validate, #bank-export { width: 100%; }
        DraftEditorScreen { align: center middle; }
        #draft-dialog { width: 84%; height: 90%; border: round $primary; background: $surface; padding: 1; }
        #draft-scroll { height: 1fr; }
        #draft-description { height: 8; }
        #draft-actions { height: auto; align-horizontal: right; }
        """
        BINDINGS = [
            ("q", "quit", "Wyjście"),
            ("r", "refresh", "Odśwież"),
            ("v", "validate_selected", "Waliduj"),
            ("e", "edit_draft", "Edytuj wersję roboczą"),
        ]

        def __init__(self) -> None:
            super().__init__()
            root = Path(os.environ.get("MAGIC_MOODLE_COURSES", "courses"))
            self.service = CourseApplicationService(root)
            self.draft_service = CourseDraftService(self.service.courses_root)
            self._draft = None
            self._summaries = []
            self._selected_id: str | None = None

        def compose(self):
            yield Header()
            with Horizontal(id="workspace"):
                with Vertical(id="sidebar"):
                    yield Static("KURSY")
                    yield Input(placeholder="Szukaj kursu…", id="search")
                    yield DataTable(id="course-table", cursor_type="row")
                with Vertical(id="main"):
                    yield Static("SZCZEGÓŁY I WALIDACJA")
                    yield Static(
                        "Wybierz kurs z listy, aby zobaczyć szczegóły.",
                        id="detail",
                        markup=False,
                    )
                    yield Button("Waliduj wybrany kurs", id="validate", variant="primary")
                    yield Button("Edytuj wersję roboczą", id="draft-edit")
                    yield Button("Eksportuj manifest JSON", id="export")
                    yield Button("Waliduj bank pytań", id="bank-validate")
                    yield Button("Eksportuj bank do Moodle XML", id="bank-export")
            yield Footer()

        def on_mount(self) -> None:
            table = self.query_one("#course-table", DataTable)
            table.add_columns("Kurs", "Sekcje", "Aktywności")
            self.refresh_courses()

        def refresh_courses(self) -> None:
            self._summaries = self.service.list_courses()
            query = self.query_one("#search", Input).value.strip().casefold()
            table = self.query_one("#course-table", DataTable)
            table.clear(columns=False)
            visible = [
                item for item in self._summaries
                if query in f"{item.name} {item.short_name}".casefold()
            ]
            for item in visible:
                table.add_row(
                    item.name,
                    str(item.sections) if item.sections is not None else "—",
                    str(item.activities) if item.activities is not None else "—",
                    key=item.id,
                )
            if not visible:
                self._selected_id = None
                self.query_one("#detail", Static).update(
                    "Brak kursów pasujących do wyszukiwania."
                )

        def on_input_changed(self, event: Input.Changed) -> None:
            if event.input.id == "search":
                self.refresh_courses()

        def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
            self._selected_id = str(event.row_key.value)
            self.show_selected_course()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "validate":
                self.action_validate_selected()
            elif event.button.id == "draft-edit":
                self.action_edit_draft()
            elif event.button.id == "export":
                self.action_export_selected()
            elif event.button.id == "bank-validate":
                self.action_validate_bank()
            elif event.button.id == "bank-export":
                self.action_export_bank()

        def show_selected_course(self) -> None:
            if not self._selected_id:
                return
            try:
                course, report = self.service.validate(self._selected_id)
            except CourseNotFoundError:
                self.query_one("#detail", Static).update(
                    "Nie znaleziono wybranego kursu."
                )
                return
            except (CourseLoadError, OSError, ValueError):
                self.query_one("#detail", Static).update(
                    "Nie udało się wczytać lub zwalidować kursu."
                )
                return

            lines = [
                course.full_name,
                f"Nazwa skrócona: {course.short_name}",
                f"Sekcje: {course.section_count} | Aktywności: {course.activity_count}",
                f"Typy aktywności: {course.activity_types or 'brak'}",
                "",
                f"Wynik: {'POPRAWNY' if report.ok else 'BŁĘDY'}",
                f"Błędy: {len(report.errors)} | Ostrzeżenia: {len(report.warnings)}",
            ]
            for finding in report.findings:
                lines.append(
                    f"[{finding.severity.upper()}] {finding.code}: "
                    f"{finding.path}: {finding.message}"
                )
            self.query_one("#detail", Static).update("\n".join(lines))

        def action_edit_draft(self) -> None:
            if not self._selected_id:
                self.query_one("#detail", Static).update(
                    "Najpierw wybierz kurs do edycji."
                )
                return
            try:
                if self._draft is None or self._draft.course_id != self._selected_id:
                    self._draft = self.draft_service.create(self._selected_id)
                preview = self.draft_service.preview(self._draft.draft_id)
            except CourseDraftConflictError as exc:
                self._draft = None
                self.query_one("#detail", Static).update(
                    f"Konflikt wersji roboczej: {exc} Utwórz nową wersję."
                )
                return
            except (CourseDraftValidationError, CourseNotFoundError, CourseLoadError, OSError, ValueError) as exc:
                self.query_one("#detail", Static).update(
                    f"Nie udało się otworzyć wersji roboczej: {exc}"
                )
                return
            self.push_screen(DraftEditorScreen(preview), self._save_draft_changes)

        def _save_draft_changes(self, changes: dict | None) -> None:
            if changes is None or self._draft is None:
                return
            try:
                self._draft = self.draft_service.update(
                    self._draft.draft_id,
                    expected_revision=self._draft.revision,
                    changes=changes,
                )
                preview = self.draft_service.preview(self._draft.draft_id)
            except CourseDraftConflictError as exc:
                self._draft = None
                self.query_one("#detail", Static).update(
                    f"Konflikt wersji roboczej: {exc}"
                )
                return
            except (CourseDraftValidationError, CourseNotFoundError, CourseLoadError, OSError, ValueError) as exc:
                self.query_one("#detail", Static).update(
                    f"Nie zapisano wersji roboczej: {exc}"
                )
                return

            validation = preview["validation"]
            self.query_one("#detail", Static).update(
                "\\n".join(
                    [
                        "WERSJA ROBOCZA ZAPISANA",
                        f"ID: {self._draft.draft_id}",
                        f"Rewizja: {self._draft.revision}",
                        f"Kurs: {preview['course']['course']['full_name']}",
                        f"Sekcje: {len(preview['course']['sections'])}",
                        f"Walidacja: {'POPRAWNA' if validation['ok'] else 'BŁĘDY'}",
                        f"Błędy: {len(validation['errors'])}",
                        f"Ostrzeżenia: {len(validation['warnings'])}",
                        "",
                        "Pliki źródłowe kursu pozostają bez zmian.",
                    ]
                )
            )

        def action_refresh(self) -> None:
            self.refresh_courses()

        def action_validate_selected(self) -> None:
            self.show_selected_course()

        def action_validate_bank(self) -> None:
            if not self._selected_id:
                self.query_one("#detail", Static).update(
                    "Najpierw wybierz kurs, którego bank pytań chcesz sprawdzić."
                )
                return
            try:
                bank = self.service.get_question_bank(self._selected_id)
            except (CourseNotFoundError, FileNotFoundError, OSError, ValueError):
                self.query_one("#detail", Static).update(
                    "Walidacja banku nie powiodła się. Sprawdź pliki GIFT i ich składnię."
                )
                return
            lines = [
                f"Bank pytań: {len(bank.questions)} pytań",
                "Rozkład typów:",
            ]
            lines.extend(f"  {kind}: {count}" for kind, count in bank.by_type().items())
            self.query_one("#detail", Static).update("\n".join(lines))

        def action_export_bank(self) -> None:
            if not self._selected_id:
                self.query_one("#detail", Static).update(
                    "Najpierw wybierz kurs, którego bank pytań chcesz eksportować."
                )
                return
            export_root = Path(
                os.environ.get(
                    "MAGIC_MOODLE_EXPORTS",
                    str(self.service.courses_root.parent / "exports"),
                )
            ).expanduser()
            destination = export_root / f"{self._selected_id}.questions.xml"
            try:
                output = self.service.export_question_bank_xml(
                    self._selected_id, destination
                )
            except (CourseNotFoundError, FileNotFoundError, OSError, ValueError):
                self.query_one("#detail", Static).update(
                    "Eksport Moodle XML nie powiódł się. Sprawdź bank pytań i kategorię."
                )
                return
            self.query_one("#detail", Static).update(
                f"Bank pytań wyeksportowany do Moodle XML:\n{output}"
            )

        def action_export_selected(self) -> None:
            if not self._selected_id:
                self.query_one("#detail", Static).update(
                    "Najpierw wybierz kurs do eksportu."
                )
                return
            export_root = Path(
                os.environ.get(
                    "MAGIC_MOODLE_EXPORTS",
                    str(self.service.courses_root.parent / "exports"),
                )
            ).expanduser()
            destination = export_root / f"{self._selected_id}.manifest.json"
            try:
                output = self.service.export_json(self._selected_id, destination)
            except (CourseNotFoundError, CourseLoadError, OSError, TypeError, ValueError):
                self.query_one("#detail", Static).update(
                    "Eksport nie powiódł się. Sprawdź kurs i uprawnienia katalogu eksportowego.",
                )
                return
            self.query_one("#detail", Static).update(
                f"Manifest JSON zapisany pomyślnie:\n{output}",
            )

    return MagicMoodleTui()


def main() -> int:
    try:
        app = _build_app()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

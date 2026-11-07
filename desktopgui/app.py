"""PySide6 desktop client using the shared application service."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _build_window():
    """Create the desktop window; import Qt only when the desktop client is used."""
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QFileDialog,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QScrollArea,
            QSplitter,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Interfejs DesktopGUI wymaga PySide6. Zainstaluj: "
            "python -m pip install '.[desktop]'"
        ) from exc

    from magic_moodle.application import (
        CourseApplicationService,
        CourseDraftConflictError,
        CourseDraftService,
        CourseDraftValidationError,
        CourseNotFoundError,
    )
    from magic_moodle.loader import CourseLoadError

    class MagicMoodleDesktop(QMainWindow):
        """Desktop workspace for course inspection, validation and exports."""

        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Magic Moodle Course Maker")
            self.resize(1180, 760)
            courses_root = Path(os.environ.get("MAGIC_MOODLE_COURSES", "courses"))
            self.service = CourseApplicationService(courses_root)
            self.draft_service = CourseDraftService(self.service.courses_root)
            self._draft = None
            self._selected_id: str | None = None

            splitter = QSplitter(Qt.Orientation.Horizontal)
            sidebar = QWidget()
            sidebar_layout = QVBoxLayout(sidebar)
            sidebar_layout.addWidget(QLabel("KURSY"))
            self.course_list = QListWidget()
            self.course_list.currentItemChanged.connect(self._on_course_selected)
            sidebar_layout.addWidget(self.course_list)
            refresh_button = QPushButton("Odśwież listę")
            refresh_button.clicked.connect(self.refresh_courses)
            sidebar_layout.addWidget(refresh_button)
            splitter.addWidget(sidebar)

            workspace = QWidget()
            workspace_layout = QVBoxLayout(workspace)
            workspace_layout.addWidget(QLabel("SZCZEGÓŁY KURSU"))
            self.details = QTextEdit()
            self.details.setReadOnly(True)
            self.details.setPlaceholderText("Wybierz kurs z listy.")
            workspace_layout.addWidget(self.details)

            actions = QHBoxLayout()
            validate_button = QPushButton("Waliduj kurs")
            validate_button.clicked.connect(self.show_selected_course)
            actions.addWidget(validate_button)
            draft_button = QPushButton("Edytuj wersję roboczą")
            draft_button.clicked.connect(self.edit_course_draft)
            actions.addWidget(draft_button)
            export_button = QPushButton("Eksportuj manifest JSON")
            export_button.clicked.connect(self.export_manifest)
            actions.addWidget(export_button)
            bank_validate_button = QPushButton("Waliduj bank GIFT")
            bank_validate_button.clicked.connect(self.validate_question_bank)
            actions.addWidget(bank_validate_button)
            bank_export_button = QPushButton("Eksportuj Moodle XML")
            bank_export_button.clicked.connect(self.export_question_bank)
            actions.addWidget(bank_export_button)
            workspace_layout.addLayout(actions)
            splitter.addWidget(workspace)
            splitter.setStretchFactor(0, 1)
            splitter.setStretchFactor(1, 3)

            self.setCentralWidget(splitter)
            self.statusBar().showMessage("Gotowy")
            self.refresh_courses()

        def refresh_courses(self) -> None:
            selected = self._selected_id
            self.course_list.clear()
            summaries = self.service.list_courses()
            for summary in summaries:
                label = summary.name
                if summary.short_name:
                    label += f" ({summary.short_name})"
                if summary.load_error:
                    label += " — BŁĄD ODCZYTU"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, summary.id)
                self.course_list.addItem(item)
                if summary.id == selected:
                    self.course_list.setCurrentItem(item)
            if self.course_list.count() == 0:
                self._selected_id = None
                self.details.setPlainText("Nie znaleziono kursów w skonfigurowanym katalogu.")
            self.statusBar().showMessage(f"Znaleziono kursów: {len(summaries)}")

        def _on_course_selected(self, current, previous) -> None:
            self._selected_id = (
                str(current.data(Qt.ItemDataRole.UserRole)) if current is not None else None
            )
            if self._selected_id:
                self.show_selected_course()

        def _require_selection(self) -> str | None:
            if self._selected_id:
                return self._selected_id
            QMessageBox.information(self, "Wybór kursu", "Najpierw wybierz kurs z listy.")
            return None

        def show_selected_course(self) -> None:
            course_id = self._require_selection()
            if not course_id:
                return
            try:
                course, report = self.service.validate(course_id)
            except CourseNotFoundError:
                QMessageBox.warning(self, "Kurs", "Nie znaleziono wybranego kursu.")
                return
            except (CourseLoadError, OSError, ValueError) as exc:
                QMessageBox.critical(self, "Błąd odczytu", str(exc))
                return

            lines = [
                course.full_name,
                f"Nazwa skrócona: {course.short_name}",
                f"Sekcje: {course.section_count}",
                f"Aktywności: {course.activity_count}",
                f"Typy aktywności: {course.activity_types or 'brak'}",
                "",
                f"Wynik walidacji: {'POPRAWNY' if report.ok else 'BŁĘDY'}",
                f"Błędy: {len(report.errors)} | Ostrzeżenia: {len(report.warnings)}",
            ]
            for finding in report.findings:
                lines.append(
                    f"[{finding.severity.upper()}] {finding.code}: "
                    f"{finding.path}: {finding.message}"
                )
            self.details.setPlainText("\n".join(lines))
            self.statusBar().showMessage(f"Zweryfikowano kurs: {course.short_name}")

        def edit_course_draft(self) -> None:
            course_id = self._require_selection()
            if not course_id:
                return
            try:
                if self._draft is None or self._draft.course_id != course_id:
                    self._draft = self.draft_service.create(course_id)
                preview = self.draft_service.preview(self._draft.draft_id)
            except CourseDraftConflictError as exc:
                self._draft = None
                QMessageBox.warning(
                    self,
                    "Konflikt wersji roboczej",
                    f"{exc} Utwórz nową wersję roboczą, aby kontynuować.",
                )
                return
            except (CourseNotFoundError, CourseDraftValidationError, CourseLoadError, OSError, ValueError) as exc:
                QMessageBox.critical(self, "Wersja robocza", str(exc))
                return

            course_data = preview["course"]["course"]
            dialog = QDialog(self)
            dialog.setWindowTitle("Edytor wersji roboczej kursu")
            dialog.resize(760, 680)
            outer = QVBoxLayout(dialog)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            form = QFormLayout(content)

            full_name = QLineEdit(course_data["full_name"])
            short_name = QLineEdit(course_data["short_name"])
            description = QTextEdit()
            description.setPlainText(course_data.get("description", ""))
            description.setMinimumHeight(110)
            form.addRow("Nazwa kursu", full_name)
            form.addRow("Nazwa skrócona", short_name)
            form.addRow("Opis kursu", description)

            section_fields = {}
            for section in preview["course"]["sections"]:
                field = QLineEdit(section["name"])
                section_fields[section["id"]] = field
                form.addRow(f"Sekcja: {section['id']}", field)

            note = QLabel(
                "Zmiany są zapisywane wyłącznie w wersji roboczej. "
                "Pliki źródłowe kursu pozostają bez zmian. "
                "Nazwy aktywności można edytować w WebUI."
            )
            note.setWordWrap(True)
            form.addRow(note)
            scroll.setWidget(content)
            outer.addWidget(scroll)

            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            outer.addWidget(buttons)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            changes = {
                "full_name": full_name.text(),
                "short_name": short_name.text(),
                "description": description.toPlainText(),
                "section_names": {
                    section_id: field.text() for section_id, field in section_fields.items()
                },
            }
            try:
                self._draft = self.draft_service.update(
                    self._draft.draft_id,
                    expected_revision=self._draft.revision,
                    changes=changes,
                )
                updated_preview = self.draft_service.preview(self._draft.draft_id)
            except CourseDraftConflictError as exc:
                self._draft = None
                QMessageBox.warning(self, "Konflikt wersji roboczej", str(exc))
                return
            except (CourseDraftValidationError, CourseNotFoundError, CourseLoadError, OSError, ValueError) as exc:
                QMessageBox.critical(self, "Nie zapisano wersji roboczej", str(exc))
                return

            validation = updated_preview["validation"]
            self.details.setPlainText(
                "\\n".join(
                    [
                        f"Wersja robocza: {self._draft.draft_id}",
                        f"Rewizja: {self._draft.revision}",
                        f"Nazwa: {updated_preview['course']['course']['full_name']}",
                        f"Sekcje: {len(updated_preview['course']['sections'])}",
                        f"Walidacja: {'POPRAWNA' if validation['ok'] else 'BŁĘDY'}",
                        f"Błędy: {len(validation['errors'])}",
                        f"Ostrzeżenia: {len(validation['warnings'])}",
                        "",
                        "Pliki źródłowe nie zostały zmienione.",
                    ]
                )
            )
            QMessageBox.information(
                self,
                "Zapisano wersję roboczą",
                f"Zapisano rewizję {self._draft.revision}. "
                f"Błędy walidacji: {len(validation['errors'])}; "
                f"ostrzeżenia: {len(validation['warnings'])}.",
            )

        def _export_root(self) -> Path:
            return Path(
                os.environ.get(
                    "MAGIC_MOODLE_EXPORTS",
                    str(self.service.courses_root.parent / "exports"),
                )
            ).expanduser()

        def export_manifest(self) -> None:
            course_id = self._require_selection()
            if not course_id:
                return
            default_path = self._export_root() / f"{course_id}.manifest.json"
            destination, _ = QFileDialog.getSaveFileName(
                self, "Eksport manifestu kursu", str(default_path), "Manifest JSON (*.json)"
            )
            if not destination:
                return
            try:
                output = self.service.export_json(course_id, destination)
            except (CourseNotFoundError, CourseLoadError, OSError, TypeError, ValueError) as exc:
                QMessageBox.critical(self, "Błąd eksportu", str(exc))
                return
            self.statusBar().showMessage(f"Manifest zapisany: {output}")

        def validate_question_bank(self) -> None:
            course_id = self._require_selection()
            if not course_id:
                return
            try:
                bank = self.service.get_question_bank(course_id)
            except (CourseNotFoundError, FileNotFoundError, OSError, ValueError) as exc:
                QMessageBox.critical(self, "Błąd banku pytań", str(exc))
                return
            summary = "\n".join(
                [f"Liczba pytań: {len(bank.questions)}"]
                + [f"{kind}: {count}" for kind, count in bank.by_type().items()]
            )
            QMessageBox.information(self, "Walidacja banku GIFT", summary)

        def export_question_bank(self) -> None:
            course_id = self._require_selection()
            if not course_id:
                return
            default_path = self._export_root() / f"{course_id}.questions.xml"
            destination, _ = QFileDialog.getSaveFileName(
                self, "Eksport banku pytań", str(default_path), "Moodle XML (*.xml)"
            )
            if not destination:
                return
            try:
                output = self.service.export_question_bank_xml(course_id, destination)
            except (CourseNotFoundError, FileNotFoundError, OSError, ValueError) as exc:
                QMessageBox.critical(self, "Błąd eksportu Moodle XML", str(exc))
                return
            self.statusBar().showMessage(f"Bank pytań wyeksportowany: {output}")

    return MagicMoodleDesktop()


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "Interfejs DesktopGUI wymaga PySide6. Zainstaluj: "
            "python -m pip install '.[desktop]'",
            file=sys.stderr,
        )
        return 2

    application = QApplication(sys.argv)
    window = _build_window()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())

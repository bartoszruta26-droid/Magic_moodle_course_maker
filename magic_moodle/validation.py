"""Walidacja niezależna od specyficznych wymagań pojedynczego kursu."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .models import Course


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class ValidationReport:
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, severity: str, code: str, path: Path | str, message: str) -> None:
        self.findings.append(Finding(severity, code, str(path), message))


def validate_course(course: Course) -> ValidationReport:
    report = ValidationReport()
    root = course.root.resolve()

    if not (root / "course.yaml").is_file():
        report.add("error", "COURSE_CONFIG_MISSING", root, "Brak course.yaml.")

    if not course.sections:
        report.add("warning", "NO_SECTIONS", root, "Kurs nie zawiera wykrytych sekcji.")

    seen_ids: set[str] = set()
    for section in course.sections:
        config = section.path / "section.yaml"
        if section.id in seen_ids:
            report.add("error", "DUPLICATE_SECTION_ID", config,
                       f"Powtórzony identyfikator sekcji: {section.id}.")
        seen_ids.add(section.id)

        summary = section.path / "section.md"
        if not summary.is_file():
            report.add("warning", "SECTION_SUMMARY_MISSING", section.path,
                       "Brak opcjonalnego pliku section.md.")

        for activity in section.activities:
            target = (section.path / activity.ref).resolve()
            if not target.exists():
                report.add("error", "ACTIVITY_REF_MISSING", config,
                           f"Aktywność '{activity.name}' wskazuje nieistniejący zasób: {activity.ref}.")
                continue
            if not target.is_relative_to(section.path.resolve()):
                report.add("error", "ACTIVITY_REF_OUTSIDE_SECTION", config,
                           f"Odwołanie '{activity.ref}' wychodzi poza katalog sekcji.")
                continue

            if activity.kind == "book":
                if not activity.resource:
                    report.add("warning", "BOOK_CONFIG_MISSING", target,
                               "Nie wczytano konfiguracji book.yaml.")
                chapters = activity.resource.get("chapters", [])
                for index, chapter in enumerate(chapters if isinstance(chapters, list) else []):
                    chapter_file = chapter.get("content_file") if isinstance(chapter, dict) else None
                    if not isinstance(chapter_file, str) or chapter_file not in activity.content:
                        report.add("error", "BOOK_CHAPTER_CONTENT_MISSING", target,
                                   f"Brak treści rozdziału nr {index + 1} ({chapter_file!r}).")

            elif activity.kind == "assignment":
                if not activity.resource:
                    report.add("warning", "ASSIGNMENT_CONFIG_MISSING", target,
                               "Nie wczytano konfiguracji assignment.yaml.")
                if not activity.content:
                    report.add("warning", "ASSIGNMENT_INSTRUCTIONS_MISSING", target,
                               "Brak pliku instrukcji wskazanego przez markdown_file.")

            elif activity.kind == "glossary":
                entries = activity.resource.get("entries")
                if not isinstance(entries, list) or not entries:
                    report.add("error", "GLOSSARY_ENTRIES_MISSING", target,
                               "Słownik musi zawierać niepustą listę entries.")
                else:
                    for index, entry in enumerate(entries):
                        if not isinstance(entry, dict) or not all(
                            isinstance(entry.get(key), str) and entry[key].strip()
                            for key in ("term", "definition")
                        ):
                            report.add("error", "GLOSSARY_ENTRY_INVALID", target,
                                       f"Niepoprawny wpis słownika nr {index + 1}; wymagane są term i definition.")

            elif activity.kind == "quiz" and not activity.resource:
                report.add("warning", "QUIZ_CONFIG_MISSING", target,
                           "Nie wczytano konfiguracji quiz.yaml.")

    # Sprawdź składnię wszystkich plików YAML w kursie, z pominięciem kopii zapasowych.
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml"}:
            continue
        if any(part.endswith((".bak", ".bak-v1", ".bak-gen")) for part in path.parts):
            continue
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            report.add("error", "YAML_INVALID", path, str(exc))

    return report

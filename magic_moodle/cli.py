"""Interfejs wiersza poleceń rdzenia."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .loader import CourseLoadError, load_course
from .validation import validate_course


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="magic-moodle", description="Rdzeń Magic Moodle Course Maker")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "validate"):
        cmd = commands.add_parser(name, help=f"{'Pokaż' if name == 'inspect' else 'Zweryfikuj'} strukturę kursu")
        cmd.add_argument("course", type=Path, help="Katalog zawierający course.yaml")
        cmd.add_argument("--json", action="store_true", help="Wynik w formacie JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        course = load_course(args.course)
    except CourseLoadError as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    if args.command == "inspect":
        result = {
            "name": course.full_name, "short_name": course.short_name,
            "sections": course.section_count, "activities": course.activity_count,
            "activity_types": course.activity_types,
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Kurs: {course.full_name}\nNazwa skrócona: {course.short_name}")
            print(f"Sekcje: {course.section_count}\nAktywności: {course.activity_count}")
            for kind, count in course.activity_types.items():
                print(f"  - {kind}: {count}")
        return 0

    report = validate_course(course)
    if args.json:
        print(json.dumps({
            "ok": report.ok,
            "errors": [item.__dict__ for item in report.errors],
            "warnings": [item.__dict__ for item in report.warnings],
        }, ensure_ascii=False, indent=2))
    else:
        for item in report.findings:
            print(f"{item.severity.upper():7} {item.code}: {item.path}: {item.message}")
        print(f"\nWynik: {'POPRAWNY' if report.ok else 'BŁĘDY'}; "
              f"błędy: {len(report.errors)}, ostrzeżenia: {len(report.warnings)}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

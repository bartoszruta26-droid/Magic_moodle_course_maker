"""Interfejs wiersza poleceń rdzenia."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .course_export import export_course_json
from .gift import GiftParseError, parse_gift, validate_question_bank
from .loader import CourseLoadError, load_course
from .moodle_api import MoodleAPIError, MoodleClient, MoodleConfig
from .moodle_publish import build_publish_plan, publish_course
from .moodle_xml import export_moodle_xml
from .question_bank import load_question_bank
from .validation import validate_course


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="magic-moodle", description="Rdzeń Magic Moodle Course Maker")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "validate"):
        cmd = commands.add_parser(name, help=f"{'Pokaż' if name == 'inspect' else 'Zweryfikuj'} strukturę kursu")
        cmd.add_argument("course", type=Path, help="Katalog zawierający course.yaml")
        cmd.add_argument("--json", action="store_true", help="Wynik w formacie JSON")

    course_export = commands.add_parser(
        "course-export-json",
        help="Eksportuj strukturę i treści kursu do manifestu JSON (nie jest to plik MBZ)",
    )
    course_export.add_argument("course", type=Path, help="Katalog zawierający course.yaml")
    course_export.add_argument("destination", type=Path, help="Docelowy plik JSON")

    moodle_publish = commands.add_parser(
        "moodle-publish", help="Utwórz kurs i opublikuj obsługiwane aktywności przez Moodle REST API"
    )
    moodle_publish.add_argument("course", type=Path, help="Katalog zawierający course.yaml")
    moodle_publish.add_argument("--category-id", type=int, default=None, help="Id kategorii Moodle")
    moodle_publish.add_argument("--dry-run", action="store_true", help="Pokaż plan bez połączenia z Moodle")
    moodle_publish.add_argument("--state-file", type=Path, default=None,
                                help="Zapisuj postęp publikacji do bezpiecznego manifestu JSON (bez tokenu)")
    moodle_publish.add_argument("--json", action="store_true", help="Wynik w formacie JSON")

    gift_validate = commands.add_parser("gift-validate", help="Sprawdź składnię i typy pytań GIFT")
    gift_validate.add_argument("source", type=Path, help="Plik GIFT")
    gift_validate.add_argument("--json", action="store_true")

    gift_export = commands.add_parser("gift-to-xml", help="Konwertuj pojedynczy plik GIFT do Moodle XML")
    gift_export.add_argument("source", type=Path, help="Wejściowy plik GIFT")
    gift_export.add_argument("destination", type=Path, help="Wyjściowy plik XML")
    gift_export.add_argument("--category", default="$course$/top", help="Kategoria banku pytań Moodle")

    bank_validate = commands.add_parser("bank-validate", help="Zweryfikuj wszystkie pliki GIFT w banku")
    bank_validate.add_argument("source", type=Path, help="Plik GIFT lub katalog question-bank")
    bank_validate.add_argument("--json", action="store_true")

    bank_export = commands.add_parser("bank-to-xml", help="Eksportuj cały bank GIFT do Moodle XML")
    bank_export.add_argument("source", type=Path, help="Katalog question-bank lub plik GIFT")
    bank_export.add_argument("destination", type=Path, help="Wyjściowy plik XML")
    bank_export.add_argument("--category", default="$course$/top", help="Kategoria banku pytań Moodle")
    return parser


def _load_bank(path: Path):
    source = path.read_text(encoding="utf-8-sig")
    bank = parse_gift(source, source_name=str(path))
    return bank, validate_question_bank(bank)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "moodle-publish":
        try:
            course = load_course(args.course)
            category_id = args.category_id or int(os.environ.get("MOODLE_CATEGORY_ID", "0"))
            plan = build_publish_plan(course, category_id)
            if args.dry_run:
                result = publish_course(None, course, category_id, dry_run=True)
            else:
                client = MoodleClient(MoodleConfig.from_env())
                result = publish_course(client, course, category_id, state_file=args.state_file)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                if plan.warnings:
                    for warning in plan.warnings:
                        print(f"OSTRZEŻENIE: {warning}", file=sys.stderr)
            return 0
        except (CourseLoadError, MoodleAPIError, OSError, ValueError) as exc:
            print(f"BŁĄD publikacji Moodle: {exc}", file=sys.stderr)
            return 2

    if args.command in {"gift-validate", "gift-to-xml", "bank-validate", "bank-to-xml"}:
        try:
            if args.command.startswith("bank-"):
                bank = load_question_bank(args.source)
                errors = []
            else:
                bank, errors = _load_bank(args.source)
        except (OSError, UnicodeError, GiftParseError) as exc:
            print(f"BŁĄD GIFT: {exc}", file=sys.stderr)
            return 2
        if errors:
            for error in errors:
                print(f"BŁĄD: {error}", file=sys.stderr)
            return 1
        if args.command in {"gift-validate", "bank-validate"}:
            result = {"ok": True, "questions": len(bank.questions), "types": bank.by_type()}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Poprawny bank: {len(bank.questions)} pytań")
                for kind, count in bank.by_type().items():
                    print(f"  - {kind}: {count}")
            return 0
        try:
            output = export_moodle_xml(bank, args.destination, category=args.category)
        except (OSError, ValueError) as exc:
            print(f"BŁĄD eksportu: {exc}", file=sys.stderr)
            return 2
        print(f"Wyeksportowano {len(bank.questions)} pytań do: {output}")
        return 0

    try:
        course = load_course(args.course)
    except CourseLoadError as exc:
        print(f"BŁĄD: {exc}", file=sys.stderr)
        return 2

    if args.command == "course-export-json":
        try:
            output = export_course_json(course, args.destination)
        except (OSError, TypeError, ValueError) as exc:
            print(f"BŁĄD eksportu kursu: {exc}", file=sys.stderr)
            return 2
        print(
            f"Wyeksportowano manifest kursu: {output} "
            f"({course.section_count} sekcji, {course.activity_count} aktywności). "
            "To format pośredni, nie pakiet Moodle MBZ."
        )
        return 0

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

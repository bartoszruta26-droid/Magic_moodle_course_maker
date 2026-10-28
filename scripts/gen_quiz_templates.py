#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generator szablonow quizow i zadan na podstawie spisu tresci kursu.

Dla kazdego tematu tworzy (tylko jesli plik jest pusty / nie istnieje):
  * quiz-NN/questions.yaml  - szkielet kolekcji pytan (metadane + szablony
    wielokrotnego wyboru per podtemat, do uzupelnienia przez autora/AI),
  * quiz-NN/questions.gift  - ten sam zestaw w formacie GIFT,
  * assignment-NN/instructions.md - tresc zadania praktycznego wg tematu.

Nigdy nie nadpisuje plikow z istniejaca trescia.

Uzycie:
    python3 scripts/gen_quiz_templates.py --toc kurs_masazu.txt \
        --base courses/03-kurs-masazysta-med10 [--dry-run] [--per-topic 3]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import default_source, parse_course  # noqa: E402


def gift_escape(s: str) -> str:
    """Escapowanie znakow specjalnych GIFT (~ # { } \\ : = < > |)."""
    return re.sub(r"([~#{}\\:=<>|])", r"\\\1", s)


def yaml_questions(topic, limit: int) -> str:
    lines = [
        "# Szablon pytan quizu - wypelniac zgodnie z templates/schemas/question.schema.json",
        f'quiz: "{topic.num} {topic.clean_title}"',
        "category: masaz",
        "questions:",
    ]
    for sub in topic.subtopics[:limit]:
        st = f"{sub.num} {sub.title}"
        lines += [
            "  - type: multichoice",
            f'    name: "{st[:60]}"',
            f"    text: \"Z podtematu '{st}' - sformuluj polecenie...?\"",
            "    answers:",
            '      - text: "ODPOWIEDZ PRAWIDLOWA <- uzupelnic"  fraction: 100',
            '      - text: "dystraktor 1"  fraction: 0',
            '      - text: "dystraktor 2"  fraction: 0',
        ]
    return "\n".join(lines) + "\n"


def gift_questions(topic, limit: int) -> str:
    out = [f"// Quiz: {topic.num} {topic.clean_title}",
           "// Skladnia GIFT - patrz docs/03-QUESTION-FORMATS.md", ""]
    for sub in topic.subtopics[:limit]:
        st = f"{sub.num} {sub.title}"
        out += [
            f"::{gift_escape(st)}::Z podtematu '{gift_escape(st)}' "
            "- sformuluj polecenie...?~",
            "    ~ODPOWIEDZ PRAWIDLOWA <- uzupelnic%100%#",
            "    ~dystraktor 1%0%#",
            "    ~dystraktor 2%0%#",
            "",
        ]
    return "\n".join(out) + "\n"


def assignment_md(topic) -> str:
    checklist = "".join(f"- [ ] {sub.num} {sub.title}\n" for sub in topic.subtopics)
    return (
        f"# Zadanie: {topic.num} {topic.clean_title}\n\n"
        "## Cel ksztalcenia (efekt kursu)\n\n"
        "<!-- TODO: powiaz z efektem ksztalcenia ze spisu tresci -->\n\n"
        "## Przebieg zadania\n\n"
        f"{checklist}\n"
        "## Kryteria oceny\n\n<!-- TODO -->\n"
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--toc", type=Path, default=default_source())
    ap.add_argument("--base", type=Path, required=True,
                    help="katalog kursu utworzony wczesniej przez scaffold_course.py")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--per-topic", type=int, default=3,
                    help="ile szablonow pytan na temat (max = liczba podtematow)")
    args = ap.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    base = args.base if args.base.is_absolute() else root / args.base
    course = parse_course(args.toc)
    written = skipped = 0

    def put(path: Path, content: str):
        nonlocal written, skipped
        if path.exists() and path.stat().st_size > 0:
            skipped += 1
            return
        written += 1
        if not args.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    for mod in course.modules:
        sec = base / "sections" / mod.dir_name
        if not sec.is_dir():
            continue
        for t in mod.topics:
            qz = sec / f"quiz-{t.order:02d}"
            put(qz / "questions.yaml", yaml_questions(t, args.per_topic))
            put(qz / "questions.gift", gift_questions(t, args.per_topic))
            asm = sec / f"assignment-{t.order:02d}"
            put(asm / "instructions.md", assignment_md(t))

    print(f"Zapisano szablonow: {written}, pominięto (mają treść): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

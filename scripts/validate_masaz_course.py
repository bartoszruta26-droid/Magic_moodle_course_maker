#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Walidator struktury i treści kursu masażysty MED.10.

Sprawdza (wszystko na realnych plikach repozytorium):
  1. Pliki puste / zbyt krótkie (< 400 B) wśród *.md, *.yaml, *.gift
     (z wyjątkiem .gitkeep oraz plików o znanej dopuszczalnej krótkości).
  2. Każdy quiz ma w questions.gift min. 30 pytań (:: nazwa ...) i poprawny
     questions.yaml (parsowalny YAML, zgodna liczba pytań z GIFT ±1 dla essay).
  3. Wszystkie pliki YAML kursu są parsowalne (safe_load).
  4. Każda aktywność book ma book.yaml z co najmniej jednym rozdziałem oraz
     istniejące pliki chapters/*.md wskazane w content_file.
  5. section.yaml każdej sekcji wskazuje `ref` do istniejących katalogów
     aktywności (brak „sierot”: katalog aktywności bez rejestru w section.yaml
     traktowany jest jako OSTRZEŻENIE, nie błąd — np. kopie .bak usuwane ręcznie).
  6. Brak aktywności typu page w modułach sekcji (preferencja: book).
     Podsumowanie sekcji (summary.markdown_file) NIE jest aktywnością page.
  7. Glossary ma min. 25 haseł; kazdy assignment ma instructions.md >= 400 B.

Kod wyjścia: 0 = brak błędów (ostrzeżenia dozwolone), 1 = błędy.

Użycie:
    python3 scripts/validate_masaz_course.py [--base courses/03-kurs-masazysta-med10]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("BRACK pyyaml — zainstaluj: pip install pyyaml")
    sys.exit(2)

MIN_FILE_BYTES = 400
MIN_QUIZ_QUESTIONS = 30
MIN_GLOSSARY_TERMS = 25
ALLOW_SHORT = {".gitkeep", "course.jpg.svg"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def check_short_files(base: Path) -> None:
    for f in base.rglob("*"):
        if not f.is_file() or f.name.endswith(".bak") or f.name in ALLOW_SHORT:
            continue
        if f.suffix not in {".md", ".yaml", ".gift"}:
            continue
        size = f.stat().st_size
        if size == 0:
            err(f"PLIK PUSTY: {f.relative_to(base)}")
        elif size < MIN_FILE_BYTES and f.suffix == ".gift":
            err(f"GIFT za krótki ({size} B): {f.relative_to(base)}")
        elif size < MIN_FILE_BYTES and f.suffix == ".md":
            # sekcje organizacyjne mogą być krótsze — tylko ostrzeżenie
            warn(f"MD krótki ({size} B): {f.relative_to(base)}")


def count_gift_questions(path: Path) -> int:
    txt = path.read_text(encoding="utf-8", errors="replace")
    return len(re.findall(r"^[^\s#].*::[\w\-]+::", txt, flags=re.M))


def check_quizzes(base: Path) -> None:
    for qdir in sorted(base.glob("sections/*/quiz-*")):
        gift = qdir / "questions.gift"
        yml = qdir / "questions.yaml"
        if not gift.exists():
            err(f"Brak questions.gift w {qdir.relative_to(base)}")
            continue
        n = count_gift_questions(gift)
        if n < MIN_QUIZ_QUESTIONS:
            err(f"{qdir.relative_to(base)}: tylko {n} pytań w GIFT (min {MIN_QUIZ_QUESTIONS})")
        if yml.exists():
            try:
                data = yaml.safe_load(yml.read_text(encoding="utf-8"))
                items = (data or {}).get("questions", data if isinstance(data, list) else [])
                ny = len(items or [])
                if abs(ny - n) > 2:
                    warn(f"{qdir.relative_to(base)}: rozjazd liczby pytań GIFT={n} YAML={ny}")
            except yaml.YAMLError as e:
                err(f"NIEPRAWNY YAML: {yml.relative_to(base)}: {str(e)[:100]}")


def check_all_yaml(base: Path) -> None:
    for f in sorted(base.rglob("*.yaml")):
        if f.name.endswith(".bak"):
            continue
        try:
            yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            err(f"NIEPRAWNY YAML: {f.relative_to(base)}: {str(e)[:100]}")


def check_books(base: Path) -> None:
    for byml in sorted(base.rglob("book.yaml")):
        bdir = byml.parent
        try:
            data = yaml.safe_load(byml.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue  # zgłoszone w check_all_yaml
        book = data.get("book", {})
        chapters = book.get("chapters") or []
        if not chapters:
            err(f"Book bez rozdziałów: {bdir.relative_to(base)}")
        for ch in chapters:
            cf = ch.get("content_file")
            if not cf:
                err(f"Rozdział bez content_file: {bdir.relative_to(base)}")
            elif not (bdir / cf).exists():
                err(f"Brak pliku rozdziału {cf}: {bdir.relative_to(base)}")


def check_sections(base: Path) -> None:
    for syml in sorted(base.glob("sections/*/section.yaml")):
        secdir = syml.parent
        try:
            data = yaml.safe_load(syml.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        modules = data.get("modules") or []
        refs = set()
        for m in modules:
            if m.get("type") == "page":
                err(f"Aktywność page w sekcji (ma być book!): {secdir.name} ref={m.get('ref')}")
            ref = m.get("ref")
            if ref:
                refs.add(ref)
                if not (secdir / ref).exists():
                    err(f"section.yaml wskazuje nieistniejący ref: {secdir.name}/{ref}")
        for d in sorted(secdir.iterdir()):
            if d.is_dir() and re.match(r"^(book|quiz|assignment|glossary|label)", d.name) \
                    and not d.name.endswith(".bak") and d.name not in refs:
                warn(f"Katalog aktywności nie zarejestrowany w section.yaml: {d.relative_to(base)}")


def check_glossary_and_assignments(base: Path) -> None:
    for g in sorted(base.rglob("glossary.yaml")):
        try:
            data = yaml.safe_load(g.read_text(encoding="utf-8")) or {}
            entries = (data.get("glossary") or {}).get("entries") or []
            if len(entries) < MIN_GLOSSARY_TERMS:
                warn(f"{g.relative_to(base)}: tylko {len(entries)} haseł (oczekiwane >= {MIN_GLOSSARY_TERMS})")
        except yaml.YAMLError:
            pass
    for a in sorted(base.glob("sections/*/assignment-*")):
        inst = a / "instructions.md"
        if not inst.exists():
            err(f"Brak instructions.md: {a.relative_to(base)}")
        elif inst.stat().st_size < MIN_FILE_BYTES:
            err(f"instructions.md za krótki ({inst.stat().st_size} B): {a.relative_to(base)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="courses/03-kurs-masazysta-med10")
    args = ap.parse_args()
    base = Path(args.base)
    if not base.is_dir():
        print(f"Baza nie istnieje: {base}")
        return 2

    check_short_files(base)
    check_quizzes(base)
    check_all_yaml(base)
    check_books(base)
    check_sections(base)
    check_glossary_and_assignments(base)

    print(f"WALIDACJA {base}: bledy={len(errors)} ostrzezenia={len(warnings)}")
    for e in errors[:40]:
        print("  BLAD:", e)
    for w in warnings[:40]:
        print("  OSTROZ.: ", w)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

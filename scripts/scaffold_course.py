#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uniwersalny generator szkicu (szkieletu) kursu Moodle na podstawie spisu tresci.

Nastepca jednorazowego skryptu scripts/scaffold-kurs-masazu.py: strukture kursu
odczytuje z biblioteki scripts/course_toc.py, wiec dziala dla KAZDEGO spisu tresci
w formacie markdown-like (kurs_masazu.txt i podobnych), nie tylko dla masazu.

DomySlnie tworzy WYLACZNIE puste pliki (0 bajtow) - sam szkic struktury, bez treści.
Konwencja nazewnicza zgodna z courses/01-* i courses/02-*:

    <baza>/
      course.yaml course.md settings.yaml tags.yaml completion.yaml
      grades.yaml changelog.md course.jpg
      media/{images,videos,audio,documents}/.gitkeep
      question-bank/categories.yaml  +  <typ>/set-01.gift (x5 typow)
      sections/00-ogloszenia/{section.yaml,page.md}
      sections/NN-<slug-modulu>/
          section.yaml section.md
          page-NN-<slug-tematu>.md              (1 temat = 1 strona)
          quiz-NN/{quiz.yaml,questions.gift,questions.yaml,feedback.md}
          assignment-NN/{assignment.yaml,instructions.md}
      sections/NN-zalaczniki/label-NN-<slug>.md (+ ewentualnie podkatalogi)

Uzycie:
    python3 scripts/scaffold_course.py --list                     # co umiem
    python3 scripts/scaffold_course.py --toc kurs_masazu.txt \
        --base courses/03-kurs-masazysta-med10 [--dry-run] [--no-attachments]
    python3 scripts/scaffold_course.py --toc inny_kurs.txt --base courses/04-x \
        --front --attachments=subdirs --force-titles

Bez --base katalog docelowy jest wyliczany z tytulow: courses/NN-<slug-frazy-tytulowej>
(licznik NN = kolejny wolny numer w courses/).

Idempotentnosc: istniejacych plikow NIGDY nie nadpisujemy; usuwamy jedynie puste
duplikaty stron przy normalizacji nazewnictwa (--normalize, wlaczone domyslne).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import (  # noqa: E402
    ACTIVITY_KINDS, MEDIA_SUBDIRS, QKINDS, TOP_FILES, Course,
    parse_course, slugify,
)

ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------ plan plikow
class Plan:
    """Zbior operacji dotknij-plik z pelna idempotentnoscia."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.created: list[Path] = []
        self.existed: list[Path] = []

    def touch(self, path: Path):
        if path.exists():
            self.existed.append(path)
            return
        self.created.append(path)
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

    def report(self, mode: str):
        print(f"{mode}: nowe pliki = {len(self.created)}, "
              f"istniejace = {len(self.existed)}, "
              f"razem = {len(self.created) + len(self.existed)}")


def topic_stem(order: int, title: str) -> str:
    """Czlon 'NN-slug' wspolny dla strony / quizu / zadania danego tematu."""
    return f"{order:02d}-{slugify(title)}"


def scaffold_modules(course: Course, base: Path, plan: Plan,
                     first_section: int = 1):
    for k, mod in enumerate(sorted(course.modules, key=lambda m: m.index),
                            start=first_section):
        sec = base / "sections" / mod.dir_name
        plan.touch(sec / "section.yaml")
        plan.touch(sec / "section.md")
        for order, topic in enumerate(mod.topics, start=1):
            stem = topic_stem(order, topic.title)
            plan.touch(sec / f"page-{stem}.md")
            qz = sec / f"quiz-{order:02d}"
            for f in ("quiz.yaml", "questions.gift", "questions.yaml", "feedback.md"):
                plan.touch(qz / f)
            ap = sec / f"assignment-{order:02d}"
            plan.touch(ap / "assignment.yaml")
            plan.touch(ap / "instructions.md")


def scaffold_attachments(course: Course, base: Path, plan: Plan,
                         mode: str = "labels", first_section: int = 12):
    """Tryb 'labels': jedna sekcja, label per zalacznik (jak w kursie masazu).

    Tryb 'subdirs': sekcja per zalacznik, a w niej strona per pozycja zalacznika.
    """
    if mode == "subdirs":
        for att in course.attachments:
            name = f"{att.order + first_section - 1:02d}-zalacznik-{slugify(att.letter + '--' + att.title)}"
            sec = base / "sections" / name
            plan.touch(sec / "section.yaml")
            plan.touch(sec / "section.md")
            for i, (num, title) in enumerate(att.items, start=1):
                plan.touch(sec / f"page-{i:02d}-{slugify(num + ' ' + title)}.md")
        return
    sec = base / "sections" / f"{first_section:02d}-zalaczniki"
    plan.touch(sec / "section.yaml")
    plan.touch(sec / "section.md")
    for att in course.attachments:
        plan.touch(sec / f"label-{att.order:02d}-{slugify(att.title)}.md")


def scaffold_front(course: Course, base: Path, plan: Plan,
                   first_section: int = 0):
    """Sekcje czesci wstepnej: 1 sekcja per podrozdzial, 1 strona per punkt."""
    for fs in course.front:
        num = re.match(r"^(?:Czesc|Cz\.)\s+(\d+)", fs.title)
        idx = int(num.group(1)) if num else None
        name = f"{idx:02d}-{slugify(fs.title)}" if idx is not None else slugify(fs.title)
        sec = base / "sections" / name
        plan.touch(sec / "section.yaml")
        plan.touch(sec / "section.md")
        for i, (num2, title) in enumerate(fs.items, start=1):
            plan.touch(sec / f"page-{i:02d}-{slugify(title)}.md")


def normalize_page_names(course: Course, base: Path) -> dict:
    """Przechowuje puste strony page-NN-*.md do wlasciwych slugow ze spisu tresci.

    * pusty plik o tym samym numerze -> zmiana nazwy,
    * puste duplikaty tego samego numeru -> usuniecie,
    * brakujace -> utworzenie jako pustych,
    * plikow z trescia (rozmiar > 0) NIE dotykamy.
    """
    stats = {"renamed": 0, "removed_dupes": 0, "created": 0, "skipped_nonempty": 0}
    for mod in sorted(course.modules, key=lambda m: m.index):
        sec = base / "sections" / mod.dir_name
        if not sec.is_dir():
            continue
        for order, topic in enumerate(mod.topics, start=1):
            want = sec / f"page-{topic_stem(order, topic.title)}.md"
            olds = list(sec.glob(f"page-{order:02d}-*.md"))
            empties = [p for p in olds if p.stat().st_size == 0]
            nonempty = [p for p in olds if p.stat().st_size > 0]
            if want.exists():
                for dup in empties:
                    if dup != want:
                        dup.unlink()
                        stats["removed_dupes"] += 1
                continue
            if nonempty:
                stats["skipped_nonempty"] += 1
                continue
            if len(empties) == 1:
                empties[0].rename(want)
                stats["renamed"] += 1
            else:
                for e in empties:
                    e.unlink()
                    stats["removed_dupes"] += 1
                want.parent.mkdir(parents=True, exist_ok=True)
                want.touch()
                stats["created"] += 1
    return stats


# ------------------------------------------------------------------ adresowanie
def default_base(toc_path: Path) -> Path:
    """courses/NN-<slug> gdzie NN to pierwszy wolny licznik w courses/."""
    title = ""
    try:
        course = parse_course(toc_path)
        title = course.name or toc_path.stem
    except Exception:
        title = toc_path.stem
    slug = slugify(title)[:40]
    existing = {p.name for p in (ROOT / "courses").iterdir() if p.is_dir()}
    for n in range(1, 100):
        cand = f"{n:02d}-{slug}"
        if cand not in existing:
            return ROOT / "courses" / cand
    raise RuntimeError("Brak wolnego licznika sekcji w courses/")


# ------------------------------------------------------------------ CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Schematyczne tworzenie struktury plikow kursu ze spisu tresci.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Uzycie:")[1] if "Uzycie:" in __doc__ else "")
    ap.add_argument("--toc", type=Path, default=ROOT / "kurs_masazu.txt",
                    help="plik spisu tresci (markdown-like); domyslnie kurs_masazu.txt")
    ap.add_argument("--base", type=Path, default=None,
                    help="katalog kursu; domyslnie wyliczony z tytulu: courses/NN-slug")
    ap.add_argument("--dry-run", action="store_true",
                    help="pokaz plan bez tworzenia plikow")
    ap.add_argument("--no-modules", action="store_true",
                    help="pomin sekcje modulow (tylko pliki glowne/media/question-bank)")
    ap.add_argument("--attachments", choices=["labels", "subdirs", "none"],
                    default="labels", help="sposob rozlozenia zalacznikow")
    ap.add_argument("--front", action="store_true",
                    help="utworz takze sekcje czesci wstepnej (jezeli parser ja wykryl)")
    ap.add_argument("--first-module-section", type=int, default=1,
                    help="numer pierwszej sekcji modulu (dla --front ustaw np. na 2)")
    ap.add_argument("--no-normalize", action="store_true",
                    help="wlacz tylko tworzenie, bez normalizacji nazw stron")
    args = ap.parse_args(argv)

    if not args.toc.exists():
        ap.error(f"brak pliku spisu tresci: {args.toc}")
    base = args.base or default_base(args.toc)
    if not base.is_absolute():
        base = ROOT / base

    course = parse_course(args.toc)
    print(f"Zrodlo   : {args.toc}")
    print(f"Tytul    : {course.name}")
    print(f"Kurs     : {base.relative_to(ROOT)}")
    print(f"Struktura: {len(course.modules)} modulow, {course.topic_count} tematom, "
          f"{course.subtopic_count} podtematom, {len(course.attachments)} zalacznikow, "
          f"{len(course.front)} sekcji wstepnych\n")

    plan = Plan(dry_run=args.dry_run)

    for f in TOP_FILES:
        plan.touch(base / f)
    for sub in MEDIA_SUBDIRS:
        plan.touch(base / "media" / sub / ".gitkeep")

    qb = base / "question-bank"
    plan.touch(qb / "categories.yaml")
    for kind in QKINDS:
        plan.touch(qb / kind / "set-01.gift")
    plan.touch(qb / "multichoice" / "set-01.yaml")

    ann = base / "sections" / "00-ogloszenia"
    plan.touch(ann / "section.yaml")
    plan.touch(ann / "page.md")

    if args.front and course.front:
        scaffold_front(course, base, plan)
    if not args.no_modules:
        scaffold_modules(course, base, plan, first_section=args.first_module_section)
    if args.attachments != "none" and course.attachments:
        att_first = args.first_module_section + len(course.modules)
        scaffold_attachments(course, base, plan, mode=args.attachments,
                             first_section=att_first)

    plan.report("DRY-RUN" if args.dry_run else "UTWORZONO")

    if not args.dry_run and not args.no_normalize and not args.no_modules:
        stats = normalize_page_names(course, base)
        print("Normalizacja nazw stron:", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

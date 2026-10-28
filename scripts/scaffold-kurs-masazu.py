#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schematyczne tworzenie struktury plikow kursu
"Kwalifikacyjny kurs zawodowy masazysty certyfikowanego" (MED.10).

Zrodlo struktury : /workspace/kurs_masazu.txt  (spis tresci: MODUL 1..11 + Zalaczniki A-M)
Cel              : /workspace/courses/03-kurs-masazysta-med10

Zalozenia:
 * tworzy WYLACZNIE puste pliki (0 bajtow) - zadnej tresci, sam szkic struktury,
 * konwencja nazewnicza zgodna z kursami courses/01-* i courses/02-*:
     course.yaml|md, settings.yaml, tags.yaml, completion.yaml, grades.yaml,
     changelog.md, course.jpg, media/{images,videos,audio,documents},
     question-bank/{categories.yaml,multichoice,truefalse,shortanswer,essay,matching},
     sections/NN-nazwa/{section.yaml,section.md,page-NN-tytul.md,
                        quiz-NN/{quiz.yaml,questions.gift,questions.yaml,feedback.md},
                        assignment-NN/{assignment.yaml,instructions.md},label-NN-tytul.md}
 * 1 temat spisu tresci = 1 strona + 1 quiz + 1 zadanie,
 * idempotentnosc: istniejace pliki nie sa nadpisywane ani usuwane.

Uruchomienie:  python3 scripts/scaffold-kurs-masazu.py [--dry-run]
"""
import re
import sys
import unicodedata
from pathlib import Path

TXT = Path("/workspace/kurs_masazu.txt")
BASE = Path("/workspace/courses/03-kurs-masazysta-med10")
SECTIONS_DIR = BASE / "sections"
MAX_SLUG = 55            # dlugosc slugu jak w istniejacych sekcjach kursu

TOP_FILES = ["course.yaml", "course.md", "settings.yaml", "tags.yaml",
             "completion.yaml", "grades.yaml", "changelog.md", "course.jpg"]
MEDIA_SUBDIRS = ["images", "videos", "audio", "documents"]
QKINDS = ["multichoice", "truefalse", "shortanswer", "essay", "matching"]

DIRNAMES = {
    1: "med-10-1-bezpieczenstwo-i-higiena-pracy",
    2: "med-10-2-podstawy-masazu",
    3: "med-10-3-podstawy-masazu-w-medycynie",
    4: "med-10-4-wykonywanie-masazu-w-medycynie",
    5: "med-10-5-wykonywanie-masazu-w-sporcie",
    6: "med-10-6-wykonywanie-masazu-prozdrowotnego",
    7: "med-10-7-jezyk-obcego-zawodowy",
    8: "med-10-8-kompetencje-personalne-i-spoleczne",
    9: "med-10-9-organizacja-pracy-malych-zespolow",
    10: "praktyka-zawodowa",
    11: "przygotowanie-do-egzaminu-potwierdzajacego-kw",
}


def fold(text: str) -> str:
    """Usuwa diakrytyki (ł->l, ż->z, ę->e ...) bez zmian wielkosci liter."""
    s = text.replace("ł", "l").replace("Ł", "L")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", fold(text).lower()).strip("-")
    if len(s) > MAX_SLUG:                      # ciecie na granicy wyrazow
        cut = ""
        for part in s.split("-"):
            if not cut:
                cut = part
            elif len(cut) + 1 + len(part) <= MAX_SLUG:
                cut += "-" + part
            else:
                break
        s = cut.strip("-")
    return s


def parse_toc(lines):
    """{modul: [(nr_tematu, tytul), ...]} z naglowkow '### N.M. Tytul'.

    Naglowki porownujemy po uproszczeniu diakrytykow (fold), ale tytul zachowujemy
    w brzmieniu oryginalnym - slug i tak jest tworzony bez polskich znakow.
    """
    modules, current = {}, None
    for raw in lines:
        line = raw.strip()
        m = re.match(r"^##\s*MODU[L\u0141]\s+(\d+)\s*$", fold(line), re.I)
        if m:
            current = int(m.group(1))
            modules.setdefault(current, [])
            continue
        if line.startswith("# "):                       # nowy rozdzial glowny
            current = None
            continue
        if current is None:
            continue
        t = re.match(r"^###\s+%d\.(\d{1,2})\.\s+(.+?)\s*$" % current, line)
        if t:
            modules[current].append((int(t.group(1)), t.group(2)))
    return modules


def attachments(lines):
    return [re.sub(r"^##\s+", "", l.strip()) for l in lines
            if re.match(r"^##\s*Zala?cznik\s+[A-M]\.", fold(l.strip()))]


class Plan:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.created, self.existed = [], []

    def touch(self, path: Path):
        if path.exists():
            self.existed.append(path)
            return
        self.created.append(path)
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()


def normalize_page_names(modules):
    """Uporzadkowuje nazwy stron page-NN-*.md do slugu z spisu tresci.

        * zamienia istniejacy EMPTY plik o tym samym numerze na wlasciwa nazwe,
        * usuwa puste duplikaty tego samego numeru,
        * tworzy brakujace (jako puste) strony.
    Zwraca dict z licznikami operacji. Plikow z trescia nie dotyka.
    """
    stats = {"renamed": 0, "removed_dupes": 0, "created": 0, "skipped_nonempty": 0}
    for mod, topics in sorted(modules.items()):
        name = DIRNAMES.get(mod) or slugify(f"modul-{mod}")
        sec = SECTIONS_DIR / f"{mod:02d}-{name}"
        if not sec.is_dir():
            continue
        for order, (_num, title) in enumerate(topics, start=1):
            want = sec / f"page-{order:02d}-{slugify(title)}.md"
            if want.exists():
                for dup in sec.glob(f"page-{order:02d}-*.md"):
                    if dup != want and dup.stat().st_size == 0:
                        dup.unlink(); stats["removed_dupes"] += 1
                continue
            olds = [p for p in sec.glob(f"page-{order:02d}-*.md")]
            empties = [p for p in olds if p.stat().st_size == 0]
            nonempty = [p for p in olds if p.stat().st_size > 0]
            if nonempty:
                stats["skipped_nonempty"] += 1     # nie niszczyma realnej tresci
            if len(empties) == 1:
                empties[0].rename(want); stats["renamed"] += 1
            else:
                for e in empties:
                    e.unlink(); stats["removed_dupes"] += 1
                want.touch(); stats["created"] += 1
    return stats


def build(dry_run=False):
    lines = TXT.read_text(encoding="utf-8").splitlines()
    modules = parse_toc(lines)
    plan = Plan(dry_run)

    print("Rozpoznana struktura spisu tresci (kurs_masazu.txt):")
    for mod in sorted(modules):
        print(f"  MODUL {mod:>2} ({DIRNAMES.get(mod, '?')}): {len(modules[mod]):>2} tematow")
    total = sum(len(v) for v in modules.values())
    print(f"  RAZEM tematom: {total}\n")

    for f in TOP_FILES:
        plan.touch(BASE / f)
    for sub in MEDIA_SUBDIRS:
        plan.touch(BASE / "media" / sub / ".gitkeep")

    qb = BASE / "question-bank"
    plan.touch(qb / "categories.yaml")
    for kind in QKINDS:
        plan.touch(qb / kind / "set-01.gift")
    plan.touch(qb / "multichoice" / "set-01.yaml")

    ann = SECTIONS_DIR / "00-ogloszenia"
    plan.touch(ann / "section.yaml")
    plan.touch(ann / "page.md")

    for mod in sorted(modules):
        name = DIRNAMES.get(mod) or slugify(f"modul-{mod}")
        sec = SECTIONS_DIR / f"{mod:02d}-{name}"
        plan.touch(sec / "section.yaml")
        plan.touch(sec / "section.md")
        for order, (_num, title) in enumerate(modules[mod], start=1):
            stem = f"{order:02d}-{slugify(title)}"
            plan.touch(sec / f"page-{stem}.md")
            qz = sec / f"quiz-{order:02d}"
            for f in ["quiz.yaml", "questions.gift", "questions.yaml", "feedback.md"]:
                plan.touch(qz / f)
            ap = sec / f"assignment-{order:02d}"
            plan.touch(ap / "assignment.yaml")
            plan.touch(ap / "instructions.md")

    att = SECTIONS_DIR / "12-zalaczniki"
    for i, title in enumerate(attachments(lines), start=1):
        plan.touch(att / f"label-{i:02d}-{slugify(title)}.md")
    plan.touch(att / "section.yaml")
    plan.touch(att / "section.md")

    if not dry_run:
        stats = normalize_page_names(modules)
        print("Normalizacja nazw stron:", stats, "\n")

    mode = "DRY-RUN" if dry_run else "UTWORZONO"
    print(f"{mode}: nowe pliki = {len(plan.created)}, "
          f"istniejace = {len(plan.existed)}, razem = {len(plan.created) + len(plan.existed)}")
    if not dry_run:
        validate(modules)
    return plan


def validate(modules):
    """Sprawdza strukture kursu ze spisem tresci (kurs_masazu.txt)."""
    problems = []
    for mod, topics in sorted(modules.items()):
        name = DIRNAMES.get(mod) or slugify(f"modul-{mod}")
        sec = SECTIONS_DIR / f"{mod:02d}-{name}"
        if not sec.is_dir():
            problems.append(f"brak sekcji {sec.name}"); continue
        expected = {f"page-{o:02d}-{slugify(t)}.md" for o, (_n, t) in enumerate(topics, 1)}
        present = {p.name for p in sec.glob("page-*.md")}
        for miss in sorted(expected - present):
            problems.append(f"{sec.name}: brak strony {miss}")
        for extra in sorted(present - expected):
            problems.append(f"{sec.name}: dodatkowa strona {extra}")
        for order in range(1, len(topics) + 1):
            qz, ap = sec / f"quiz-{order:02d}", sec / f"assignment-{order:02d}"
            for f in ["quiz.yaml", "questions.gift", "questions.yaml", "feedback.md"]:
                if not (qz / f).exists():
                    problems.append(f"{sec.name}: brak {qz.name}/{f}")
            for f in ["assignment.yaml", "instructions.md"]:
                if not (ap / f).exists():
                    problems.append(f"{sec.name}: brak {ap.name}/{f}")
        for f in ["section.yaml", "section.md"]:
            if not (sec / f).exists():
                problems.append(f"{sec.name}: brak {f}")
    nfiles = sum(1 for _ in BASE.rglob("*") if _.is_file())
    npages = len(list(BASE.rglob("page-*.md")))
    print("\nWALIDACJA:")
    print(f"  sekcje aktywnosciowe : {len(modules)} + 00-ogloszenia + 12-zalaczniki")
    print(f"  strony (page-*.md)   : {npages} / oczekiwane {sum(len(v) for v in modules.values())}")
    print(f"  pliki w kursie        : {nfiles}")
    print(f"  bledy struktury      : {len(problems)}")
    for pr in problems[:25]:
        print("   -", pr)
    return not problems


if __name__ == "__main__":
    build(dry_run="--dry-run" in sys.argv[1:])

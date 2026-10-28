#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Konwersja aktywności „page” kursu masażysty MED.10 na preferowaną „book”.

Stan wejściowy (po gen_masaz_content.py / fix_masaz_gaps.py):
    sections/NN-*/page-XX-temat.md            — strona tematyczna (pełna treść)
    sections/NN-*/book-01/chapters/XX-*.md    — rozdział podręcznika modułu
    sections/NN-*/section.yaml                — moduły Moodle: type: page + book-01

Operacje (idempotentne, z kopią .bak przy zmianie pliku istniejącego):

A) Uzupełnianie luk — jeśli plik strony lub rozdziału jest szkicem bez
   zagadnień („realizuje 0 …”) albo w ogóle nie istnieje, a temat ma
   podtematy w spisie treści — generujemy pełną treść (GGC.page_md).

B) Zamiana page -> book (żądanie użytkownika: unikać aktywności page):
   dla KAŻDEGO tematu tworzymy SAMODZIELNĄ aktywność typu book:
       sections/NN-*/book-XX-temat/book.yaml      (1 rozdział = pełny temat)
       sections/NN-*/book-XX-temat/chapters/01-temat.md
   Następnie w section.yaml wpis „type: page / ref: page-XX-*.md” zastępowany
   jest wpisem „type: book / ref: book-XX-temat”. Plik page-XX-*.md zostaje
   usunięty (jego treść żyje teraz w rozdziale książki; wcześniejsza kopia
   .bak pozostaje do wglądu).

C) Kwestia merytoryczna (prawda): gdy rozdział book-01 był szkicem
   „0 zagadnień”, a strona miała już prawdziwą treść (naprawioną np. po
   korekcie numeracji w kurs_masazu.txt), kopiujemy treść do rozdziału,
   aby podręcznik modułu nigdy nie przeczył stanowi spisu treści.

Idempotentność:
    * powtórne uruchomienie nie dubluje wpisów (sprawdzenie, czy sekcja
      zawiera już ref do danego booka);
    * istniejące książki book-XX są pomijane, chyba że ich jedyny rozdział
      jest szkicem — wtedy jest on uzupełniany;
    * --dry-run przedstawia plan bez zapisu.

Użycie:
    python3 scripts/page_to_book.py [--toc kurs_masazu.txt]
        [--base courses/03-kurs-masazysta-med10] [--dry-run] [--no-backup]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import parse_course, default_source, slugify  # noqa: E402
import gen_masaz_content as GGC  # noqa: E402


# --------------------------------------------------------------------------
# rozpoznawanie szkiców i pomocnicze zapisy
# --------------------------------------------------------------------------


def is_stub(text: str) -> bool:
    """Szkic = tekst wygenerowany, gdy parser widział 0 podtematów."""
    if re.search(r"realizuje\s+0\b", text):
        return True
    if "## Zagadnienia szczegółowe" in text and "### " not in text:
        return True
    return False


def backup_file(path: Path, backup: bool) -> None:
    if backup and path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            bak.write_bytes(path.read_bytes())


class Stats:
    def __init__(self):
        self.written = 0
        self.skipped = 0
        self.removed = 0

    def log(self, tag: str, path: Path, dry_run: bool):
        self.written += 1
        print(f"[{tag}] {'PLAN:' if dry_run else 'OK:  '} {path}")


# --------------------------------------------------------------------------
# B) generator pojedynczej książki tematycznej
# --------------------------------------------------------------------------


def topic_book_yaml(mod, t) -> str:
    """book.yaml jednej książki = jeden rozdział = pełny temat ze spisu."""
    name = f"{t.num}. {t.clean_title}"
    L = [
        "# Aktywność typu book — materiał tematyczny (preferowana aktywność)",
        "# Konwersja aktywności page -> book wykonana przez scripts/page_to_book.py",
        "book:",
        f"  name: {GGC.yaml_q(name)}",
        "  intro: |",
        f"    Materiał dydaktyczny tematu {t.num} — {t.clean_title}.",
        f"    {GGC.MOD_INTRO.get(mod.index, '')}",
        "  intro_format: markdown",
        "  numbering: 1",
        "  customtitles: 0",
        "  revision: 1",
        "  chapters:",
        f"    - title: {GGC.yaml_q(GGC.topic_heading(t))}",
        "      subchapter: false",
        f"      content_file: {GGC.yaml_q('chapters/01-' + slugify(t.clean_title) + '.md')}",
        "      hidden: false",
        "  completion:",
        "    enabled: true",
        "    type: view",
    ]
    return "\n".join(L) + "\n"


def topic_chapter_name(t) -> str:
    return f"chapters/01-{slugify(t.clean_title)}.md"


# --------------------------------------------------------------------------
# C) podmiana wpisu page -> book w section.yaml
# --------------------------------------------------------------------------


PAGE_ENTRY_RE = re.compile(
    r"^  - type: page\n"
    r"    ref: (?P<ref>\"?)(?P<file>page-(?P<num>\d{2})-[^\"\n]+\.md)(?P=ref)\n"
    r"    name: (?P<q>\"?)(?P<name>[^\"\n]+)(?P=q)\n",
    re.M,
)


def swap_section_yaml(sec_yaml_text: str, book_ref: str, num: int) -> tuple[str, int]:
    """Zamienia WPISY type: page wskazujące na plik page-NN-*.md na type: book.

    Zwraca (nowy_tekst, liczba_zmienionych_wpisow). Wpis o numerze NN
    otrzymuje ref = book_ref (np. "book-07-wykonywanie-masazu...").
    """

    def repl(m: re.Match) -> str:
        n = int(m.group("num"))
        if n != num:
            return m.group(0)
        q = m.group("q")
        return (
            "  - type: book\n"
            f"    ref: {book_ref}\n"
            f"    name: {q}{m.group('name')}{q}\n"
        )

    new_text = PAGE_ENTRY_RE.sub(repl, sec_yaml_text)
    changed = 1 if new_text != sec_yaml_text else 0
    return new_text, changed


# --------------------------------------------------------------------------
# główna pętla konwersji
# --------------------------------------------------------------------------


def convert(course, base: Path, dry_run: bool, backup: bool) -> Stats:
    st = Stats()
    for mod in course.modules:
        sec = base / "sections" / mod.dir_name
        if not sec.is_dir():
            continue
        for t in mod.topics:
            full_content = GGC.page_md(mod, t)  # prawda źródłowa: spis treści

            # --- A) rozdział podręcznika modułu (book-01) ------------------
            ch01 = sec / "book-01" / "chapters" / f"{t.order:02d}-{slugify(t.clean_title)}.md"
            if ch01.exists() and ch01.stat().st_size > 0:
                old = ch01.read_text(encoding="utf-8", errors="replace")
                if is_stub(old) and t.subtopics:
                    if not dry_run:
                        backup_file(ch01, backup)
                        ch01.write_text(full_content, encoding="utf-8")
                    st.log("BK01", ch01, dry_run)
                else:
                    st.skipped += 1
            elif t.subtopics:
                if not dry_run:
                    ch01.parent.mkdir(parents=True, exist_ok=True)
                    ch01.write_text(full_content, encoding="utf-8")
                st.log("BK01", ch01, dry_run)

            # --- B) samodzielna książka tematyczna book-NN ------------------
            bookdir = sec / f"book-{t.order:02d}-{slugify(t.clean_title)}"
            byaml = bookdir / "book.yaml"
            chap = bookdir / topic_chapter_name(t)
            pages = sorted(sec.glob(f"page-{t.order:02d}-*.md"))

            already_book = byaml.exists() and byaml.stat().st_size > 0
            if not already_book:
                if not dry_run:
                    bookdir.mkdir(parents=True, exist_ok=True)
                    byaml.write_text(topic_book_yaml(mod, t), encoding="utf-8")
                st.log("BOOK", byaml, dry_run)

            # treść rozdziału książki: priorytet ma prawdziwa treść strony (jeśli
            # była lepsza niż szkic), potem pełna generacja, potem istniejący plik
            chapter_src = full_content
            if pages:
                pg = pages[0]
                ptxt = pg.read_text(encoding="utf-8", errors="replace")
                if not is_stub(ptxt) and len(ptxt) >= len(full_content):
                    chapter_src = ptxt
            if chap.exists() and chap.stat().st_size > 0 and not is_stub(
                    chap.read_text(encoding="utf-8", errors="replace")):
                st.skipped += 1
            else:
                if not dry_run:
                    if chap.exists():
                        backup_file(chap, backup)
                    chap.parent.mkdir(parents=True, exist_ok=True)
                    chap.write_text(chapter_src, encoding="utf-8")
                st.log("CHAP", chap, dry_run)

            # --- section.yaml: page -> book ---------------------------------
            syml = sec / "section.yaml"
            if syml.exists():
                txt = syml.read_text(encoding="utf-8", errors="replace")
                if f"ref: {bookdir.name}" in txt or f'ref: "{bookdir.name}"' in txt:
                    st.skipped += 1  # już przekonwertowane
                else:
                    new_txt, changed = swap_section_yaml(txt, bookdir.name, t.order)
                    if changed:
                        if not dry_run:
                            backup_file(syml, backup)
                            syml.write_text(new_txt, encoding="utf-8")
                        st.log("SECT", syml, dry_run)
                    else:
                        st.skipped += 1

            # --- usunięcie pliku strony (jego treść jest w książce) ---------
            for pg in pages:
                if not dry_run:
                    backup_file(pg, backup)
                    pg.unlink()
                st.log("DEL ", pg, dry_run)
                st.removed += 1
                st.written -= 1  # usunięcie nie jest "zapisem"

        # --- D) section.md: prawda — tabela nie może wskazywać na page-XX,
        #     skoro aktywność page została zastąpiona książką book-XX -------
        smd = sec / "section.md"
        if smd.exists():
            txt = smd.read_text(encoding="utf-8", errors="replace")
            if re.search(r"\|\s*Strona\s*\|", txt) or "page-" in txt:
                new_txt = txt.replace("| Strona |", "| Książka (book) |")
                new_txt = re.sub(r"\bpage-(\d{2})\b", r"book-\1", new_txt)
                if new_txt != txt:
                    if not dry_run:
                        backup_file(smd, backup)
                        smd.write_text(new_txt, encoding="utf-8")
                    st.log("SMDF", smd, dry_run)
    return st


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="page -> book dla kursu MED.10")
    ap.add_argument("--toc", type=Path, default=default_source())
    ap.add_argument("--base", type=Path,
                    default=Path("courses/03-kurs-masazysta-med10"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args(argv)

    course = parse_course(args.toc)
    GGC.BASE = str(args.base)
    st = convert(course, args.base, args.dry_run, not args.no_backup)
    print(f"RAZEM: utworzonych/zmienionych {st.written}, "
          f"usuniętych stron {st.removed}, pominiętych {st.skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

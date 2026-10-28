#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pages_to_books.py — konwersja aktywności typu `page` na preferowaną `book`.

Motywacja
---------
Kursy w repozytorium (np. Kwalifikacyjny Kurs Zawodowy – Naturopata) zawierały
setki stron tematycznych jako moduły Moodle typu `page`. Zgodnie z wymaganiami
preferowaną aktywnością treściową jest **book**, a aktywności `page` należy
unikać. Niniejszy skrypt przekształca każdy katalog sekcji kursu tak, aby:

1. Strony `page-X-Y-*.md` (oraz ewentualne `page.md`) sekcji zostały przeniesione
   do istniejącej książki `book-01/chapters/NN-*.md` jako kolejne rozdziały
   (zachowując numerację i tytuły). Treść rozdziałów pochodzi 1:1 ze stron —
   nic nie jest tracone; strony oznaczone komentarzem konwersji są usuwane.
2. Wpisy `- type: page` w `section.yaml` zostają usunięte (pozostaje `book`,
   quiz, assignment itd.). Jeżeli sekcja nie ma żadnej książki, tworzona jest
   książka `book-01` z przeniesionymi rozdziałami.
3. W `section.md` słowa „page” w tabeli struktury zastępowane są na „book”.

Bezpieczeństwo / idempotentność
-------------------------------
* Skrypt działa tylko tam, gdzie w sekcji istnieją pliki `page*.md`; powtórne
  uruchomienie nic nie robi (brak stron = brak zmian).
* Rozdział o tej samej docelowej ścieżce NIE jest nadpisywany, jeśli już
  istnieje i ma treść inną niż pusta — wtedy strona źródłowa jest zachowywana
  przy boku, a operacja raportowana (nic nie ginie).
* Tryb `--dry-run` pokazuje plan bez zapisów.

Użycie
------
    python3 scripts/pages_to_books.py [--base courses/03-kwalifikacyjny-kurs-zawodowy-naturopaty] [--dry-run] [--keep-pages]

Flagi
-----
    --base PATH   katalog kursu (domyślnie kurs naturopaty)
    --dry-run     tylko wypisz plan zmian
    --keep-pages  przenieś treść do book, ale nie usuwaj plików page-*.md
                  (przydatne, gdy zewnętrzny build oczekuje jeszcze starych ścieżek)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    print("BLAD: wymagany pakiet pyyaml (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

DEFAULT_BASE = Path("courses/03-kwalifikacyjny-kurs-zawodowy-naturopaty")

PAGE_RE = re.compile(r"^page(?:-[0-9]+-[0-9]+)?(?:-.*)?\.md$")


def natural_key(p: Path):
    """Sortowanie naturalne: page-1-2 przed page-1-10."""
    parts = re.split(r"(\d+)", p.name)
    return [int(x) if x.isdigit() else x for x in parts]


def chapter_slug(src: Path) -> str:
    """Slug rozdziału ze strony: page-9-1-choroby...md -> 9-1-choroby; page.md -> strona-sekcji."""
    stem = src.stem
    if stem == "page":
        return "strona-sekcji"
    rest = stem[len("page") :].lstrip("-")
    return rest or "strona-sekcji"


def slugify_title(title: str) -> str:
    """Slug z tytułu (do dopasowania istniejących rozdziałów)."""
    tr = str.maketrans({
        "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
        "ó": "o", "ś": "s", "ź": "z", "ż": "z",
        "Ą": "a", "Ć": "c", "Ę": "e", "Ł": "l", "Ń": "n",
        "Ó": "o", "Ś": "s", "Ź": "z", "Ż": "z",
    })
    s = title.translate(tr).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60]


def find_existing_chapter(chapters, title: str, slug: str):
    """Czy istnieje już rozdział o tym samym tytule/slugu (wygenerowany wcześniej przez
    gen_naturopata_books.py)? Zwraca wpis lub None."""
    tslug = slugify_title(title)
    for c in chapters:
        cf = str(c.get("content_file", ""))
        cst = str(c.get("title", ""))
        if slugify_title(cst) == tslug and tslug:
            return c
        base = Path(cf).stem
        # format wcześniejszego generatora: NN-<slug>, gdzie slug pochodzi od tematu
        m = re.match(r"^\d+-(.+)$", base)
        core = m.group(1) if m else base
        if core and (core == slug or core.rstrip("-") in slug or slug in core):
            return c
    return None


def title_from_md(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def ensure_trailing_newline(s: str) -> str:
    return s if s.endswith("\n") else s + "\n"


def convert_section(sec: Path, dry_run: bool, keep_pages: bool, stats: dict) -> None:
    pages = sorted((p for p in sec.iterdir() if p.is_file() and PAGE_RE.match(p.name)), key=natural_key)
    if not pages:
        return
    stats["sections"] += 1
    book_dir = sec / "book-01"
    chapters_dir = book_dir / "chapters"
    book_yaml = book_dir / "book.yaml"

    # 1) wczytaj lub utwórz book.yaml
    if book_yaml.exists():
        data = yaml.safe_load(book_yaml.read_text(encoding="utf-8")) or {}
    else:
        data = {}
    book = data.get("book") or {}
    chapters = book.get("chapters") or []
    existing_files = {c.get("content_file") for c in chapters}

    # nazwa książki, jeśli nowa
    if not book.get("name"):
        sy = sec / "section.yaml"
        name = sec.name
        if sy.exists():
            sd = yaml.safe_load(sy.read_text(encoding="utf-8")) or {}
            name = sd.get("name", sec.name)
        book["name"] = f"Podręcznik: {name}"
        book.setdefault("intro", "")
        book["intro_format"] = "markdown"
        book["numbering"] = 1
        book["customtitles"] = 0
        book["revision"] = 1
        book["completion"] = {"enabled": True, "type": "view"}

    idx = len(chapters)
    moved = []
    merged = 0
    for src in pages:
        text = src.read_text(encoding="utf-8")
        body = re.sub(r"^<!--.*?-->\s*", "", text, count=1, flags=re.DOTALL)
        title = title_from_md(body, src.stem)
        slug = chapter_slug(src)

        match = find_existing_chapter(chapters, title, slug)
        if match is not None:
            # rozdział o tej samej tematyce już istnieje (book był równoległym
            # odbiciem stron) — scal treść: dopisz brakujące fragmenty strony.
            cf = str(match.get("content_file", ""))
            dst = chapters_dir / Path(cf).name
            cur = dst.read_text(encoding="utf-8") if dst.exists() else ""
            marker = "\n\n---\n\n## Materiały uzupełniające ze strony tematycznej\n\n"
            extra = body.strip()
            # usuń H1 z dopisanej treści (tytuł ma rozdział)
            extra = re.sub(r"^#\s+.*\n+", "", extra)
            if "Materiały uzupełniające ze strony tematycznej" not in cur and extra:
                if not dry_run:
                    dst.write_text(ensure_trailing_newline(cur.rstrip() + marker + extra + "\n"), encoding="utf-8")
                stats["chapters"] += 1
                moved.append(src)
                merged += 1
            continue

        idx += 1
        cf = f"chapters/{idx:02d}-{slug}.md"
        dst = chapters_dir / Path(cf).name
        if cf in existing_files or dst.exists():
            print(f"  POMINIETO (kolizja rozdziału): {src.name} -> {cf}")
            stats["skipped"] += 1
            continue

        header = (
            f"<!--\nPlik: {Path(cf).name}\nTyp pliku: Rozdział książki (book chapter)\n"
            f"Konwersja: Markdown → HTML\nSekcja: {sec.name}\n"
            f"Kurs: Kwalifikacyjny Kurs Zawodowy – Naturopata\n"
            f"Pochodzenie: przekształcono aktywność page ({src.name}) w rozdział book.\n-->\n\n"
        )
        content = ensure_trailing_newline(header + body.rstrip() + "\n")

        if not dry_run:
            chapters_dir.mkdir(parents=True, exist_ok=True)
            dst.write_text(content, encoding="utf-8")
        chapters.append({"title": title, "subchapter": False, "content_file": cf, "hidden": False})
        existing_files.add(cf)
        moved.append(src)
        stats["chapters"] += 1

    # 2) zapis book.yaml
    book["chapters"] = chapters
    data["book"] = book
    if not dry_run:
        book_dir.mkdir(parents=True, exist_ok=True)
        book_yaml.write_text(
            "# Aktywność typu book — podręcznik sekcji (preferowana aktywność kursu)\n"
            + yaml.dump(data, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )

    # 3) aktualizacja section.yaml — usuń wpisy page wskazujące na przeniesione pliki
    sy = sec / "section.yaml"
    if sy.exists():
        sd = yaml.safe_load(sy.read_text(encoding="utf-8")) or {}
        mods = sd.get("modules") or []
        moved_names = {p.name for p in moved}
        new_mods = [m for m in mods if not (m.get("type") == "page" and str(m.get("ref", "")).split("/")[-1] in moved_names)]
        removed = len(mods) - len(new_mods)
        if new_mods and not any(m.get("type") == "book" for m in new_mods):
            new_mods.insert(0, {"type": "book", "ref": "book-01", "name": book.get("name", "Podręcznik sekcji")})
        sd["modules"] = new_mods
        if not dry_run:
            sy.write_text(
                "# Metadane sekcji\n" + yaml.dump(sd, allow_unicode=True, sort_keys=False, width=100),
                encoding="utf-8",
            )
        stats["page_entries_removed"] += removed

    # 4) usunięcie plików page (chyba że --keep-pages)
    if not keep_pages:
        for p in moved:
            if not dry_run:
                p.unlink()
        stats["pages_deleted"] += len(moved)

    # 5) section.md — zamiana etykiety page na book w tabeli struktury
    smd = sec / "section.md"
    if smd.exists():
        t = smd.read_text(encoding="utf-8")
        t2 = re.sub(r"\|\s*page\s*\|", "| book |", t)
        t2 = t2.replace("stron tematycznych (page)", "rozdziałów podręcznika (book)")
        if t2 != t and not dry_run:
            smd.write_text(t2, encoding="utf-8")
            stats["section_md_updated"] += 1

    print(f"  SEKCJA {sec.name}: przeniesiono/scalono {len(moved)} stron do book-01 (nowe rozdziały: {len(moved) - merged}, scalenia: {merged})"
          + (" [dry-run]" if dry_run else ""))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--base", type=Path, default=DEFAULT_BASE, help="katalog kursu")
    ap.add_argument("--dry-run", action="store_true", help="tylko plan, bez zapisów")
    ap.add_argument("--keep-pages", action="store_true", help="nie usuwaj plików page-*.md po konwersji")
    args = ap.parse_args()

    root = args.base
    if not root.is_absolute():
        root = Path.cwd() / root if not root.exists() else root
    sections_dir = root / "sections"
    if not sections_dir.is_dir():
        print(f"BLAD: brak katalogu {sections_dir}", file=sys.stderr)
        return 2

    stats = dict(sections=0, chapters=0, pages_deleted=0, page_entries_removed=0, skipped=0, section_md_updated=0)
    for sec in sorted(sections_dir.iterdir()):
        if sec.is_dir():
            convert_section(sec, args.dry_run, args.keep_pages, stats)

    print(
        f"\nPODSUMOWANIE{' [DRY-RUN]' if args.dry_run else ''}: sekcji={stats['sections']}, "
        f"rozdziałów dodanych={stats['chapters']}, wpisów page usuniętych z section.yaml={stats['page_entries_removed']}, "
        f"plików page usuniętych={stats['pages_deleted']}, kolizje={stats['skipped']}, "
        f"section.md zaktualizowane={stats['section_md_updated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

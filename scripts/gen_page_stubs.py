#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wypelnienie SZKIELETU kursu minimalnymi stubami stron (bez merytoryki).

Dla kazdej pustej strony `page-NN-*.md` tworzy naglowek + liste podtematow
ze spisu tresci jako podrozedzia `##`, dzieki czemu:
  * od razu widac, ktora strona jest pusta szkicowo, a ktora ma tresc,
  * agent AI / autor dostaje gotowy szkielet redakcyjny tematu,
  * sekcje otrzymuja `section.md` z lista stron i linkami do nich.

Nigdy nie nadpisuje plikow z istniejaca trescia (uzupelnia tylko pliki
0-bajtowe utworzone wczesniej przez scaffold_course.py).

Uzycie:
    python3 scripts/gen_page_stubs.py --toc kurs_masazu.txt \
        --base courses/03-kurs-masazysta-med10 [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import default_source, parse_course  # noqa: E402

PAGE_RE = re.compile(r"^page-(\d+)-.*\.md$")


def fill_file(path: Path, content: str, dry_run: bool, stats: dict) -> None:
    if path.exists() and path.stat().st_size > 0:
        stats["skipped_nonempty"] += 1
        return
    stats["written"] += 1
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--toc", type=Path, default=default_source())
    ap.add_argument("--base", type=Path, required=True,
                    help="katalog kursu utworzony wczesniej przez scaffold_course.py")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    base = args.base if args.base.is_absolute() else root / args.base
    course = parse_course(args.toc)
    stats = {"written": 0, "skipped_nonempty": 0}

    sections_dir = base / "sections"
    sec_dirs = sorted(p for p in sections_dir.iterdir() if p.is_dir()) \
        if sections_dir.is_dir() else []
    by_dir = {m.dir_name: m for m in course.modules}

    for sec in sec_dirs:
        mod = by_dir.get(sec.name)
        pages = sorted(p for p in sec.glob("page-*.md"))

        # section.md - przeglad sekcji z linkami do stron
        lines = [f"# {sec.name.split('-', 1)[1].replace('-', ' ').capitalize()}", ""]
        if mod is not None:
            if mod.hours:
                lines.append(f"Wymiar godzinowy: {mod.hours}")
                lines.append("")
            for t in mod.topics:
                link = next((p.name for p in pages
                             if PAGE_RE.match(p.name)
                             and PAGE_RE.match(p.name).group(1) == f"{t.order:02d}"),
                            None)
                arrow = f" -> [{link}](./{link})" if link else ""
                lines.append(f"- {t.num} {t.clean_title}{arrow}")
            lines.append("")
        fill_file(sec / "section.md", "\n".join(lines), args.dry_run, stats)

        # strony tematow - naglowek + podtematy jako H2 + placeholder TODO
        if mod is not None:
            for t in mod.topics:
                page = next((p for p in pages
                             if PAGE_RE.match(p.name)
                             and PAGE_RE.match(p.name).group(1) == f"{t.order:02d}"),
                            None)
                if page is None:
                    continue
                body = [f"# {t.num} {t.clean_title}", ""]
                for sub in t.subtopics:
                    body += [f"## {sub.num} {sub.title}", "",
                             "<!-- TODO: tresc podtematu -->", ""]
                fill_file(page, "\n".join(body), args.dry_run, stats)

    print(f"Stuby zapisane: {stats['written']}, "
          f"pominiete (maja tresc): {stats['skipped_nonempty']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

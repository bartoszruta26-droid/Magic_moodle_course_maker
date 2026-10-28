#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generator promptow AI do wypelniania trescia szkicu kursu (temat po temacie).

Na podstawie spisu tresci tworzy katalog z gotowymi promptami markdown -
po jednym na kazdy temat kursu (+ zbiorczy index.md). Prompt zawiera:
tytul i numer tematu, liste podtematow ze spisu, docelowa sciezke pliku
strony w kursie oraz reguly stylistyczne repozytorium. Wystepuje jako
kontekst dla agenta AI (Qwen Code / Qwen Coder) podczas generowania tresci.

Uzycie:
    python3 scripts/toc_prompts.py --toc kurs_masazu.txt \
        --base courses/03-kurs-masazysta-med10 --out prompts-masaz [--limit 5]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import default_source, parse_course, slugify  # noqa: E402

RULES = """Zasady tworzenia tresci:
- jezyk: polski, formowy, zgodny z terminologia MED.10;
- naglowek H1 = numer i tytul tematu, nastepnie H2 per podtemat;
- treść merytoryczna, ale zwinla (ok. 150-400 slow na podtemat);
- bez wymyslonych danych medycznych - ogolne zasady, wskazowki praktyczne;
- zgodnosc etyczna z docs/04-AUTOMATION-AND-ETHICS.md (prawda, godnosc osoby,
  rowne traktowanie); dostepnosc WCAG 2.1 AA (alt-y obrazkow, hierarchia naglowkow);
- output: TYLKO cala tresc pliku markdown, bez komentarzy o generowaniu."""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--toc", type=Path, default=default_source())
    ap.add_argument("--base", type=Path, required=True,
                    help="katalog kursu (do wpisywania docelowych sciezek plikow)")
    ap.add_argument("--out", type=Path, default=Path("prompts-course"),
                    help="katalog wyjsciowy na prompty")
    ap.add_argument("--limit", type=int, default=0,
                    help="wygeneruj tylko pierwsze N promptow (0 = wszystkie)")
    args = ap.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    base = args.base if args.base.is_absolute() else root / args.base
    out = args.out if args.out.is_absolute() else root / args.out
    course = parse_course(args.toc)

    made = 0
    index_lines = [f"# Prompty AI: {course.name}", ""]
    for mod, topic in course.all_topics():
        page_name = f"page-{topic.order:02d}-{slugify(topic.clean_title)}.md"
        target = base / "sections" / mod.dir_name / page_name
        fname = f"{mod.index:02d}-{topic.order:02d}-{slugify(topic.clean_title, 40)}.md"
        body = (
            f"# Prompt: {topic.num} {topic.clean_title}\n\n"
            f"Kurs: {course.name}\n"
            f"Modul {mod.index}: {mod.title}\n"
            f"Plik docelowy: {target.relative_to(root)}\n\n"
            "## Podtematy do opracowania (ze spisu tresci):\n\n"
            + "".join(f"- {s.num} {s.title}\n" for s in topic.subtopics)
            + "\n" + RULES + "\n"
        )
        out.mkdir(parents=True, exist_ok=True)
        (out / fname).write_text(body, encoding="utf-8")
        index_lines.append(f"- [{topic.num} {topic.clean_title}](./{fname})")
        made += 1
        if args.limit and made >= args.limit:
            break
    (out / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"Wygenerowano promptow: {made} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

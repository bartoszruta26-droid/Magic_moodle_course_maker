#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Eksport struktury spisu tresci kursu do JSON / YAML / Markdown.

Dziala na kazdym spisie tresci obslugiwanym przez scripts/course_toc.py,
dzieki czemu latwo:
  * przejrzec przeanalizowana strukture przed szkicowaniem kursu,
  * podac ja agentowi AI jako kontekst generowania tresci stron/quizow,
  * zintegrowac ja z pipeline'm CI (diff JSON miedzy wersjami spisu).

Uzycie:
    python3 scripts/toc_outline.py --toc kurs_masazu.txt --format markdown
    python3 scripts/toc_outline.py --toc kurs_masazu.txt --format json --output outline.json
    python3 scripts/toc_outline.py                     # domyslny spis (kurs masazu), JSON
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import default_source, parse_course  # noqa: E402


def course_to_dict(c) -> dict:
    return {
        "source": str(c.source),
        "name": c.name,
        "qualification": c.qualification,
        "front": [{"title": s.title, "items": [f"{n} {t}" for n, t in s.items]}
                  for s in c.front],
        "modules": [
            {
                "order": m.index,
                "number": f"MODUL {m.index}",
                "code": m.code,
                "title": m.title,
                "dir_name": m.dir_name,
                "hours": m.hours,
                "meta": m.meta,
                "topics": [
                    {
                        "order": t.order,
                        "number": t.num,
                        "title": t.clean_title,
                        "stem": t.stem,
                        "subtopics": [f"{s.num} {s.title}" for s in t.subtopics],
                    }
                    for t in sorted(m.topics, key=lambda t: t.order)
                ],
            }
            for m in sorted(c.modules, key=lambda m: m.index)
        ],
        "attachments": [
            {"letter": a.letter, "order": a.order, "title": a.title,
             "items": [f"{n} {t}" for n, t in a.items]}
            for a in c.attachments
        ],
        "stats": {
            "modules": len(c.modules),
            "topics": c.topic_count,
            "subtopics": c.subtopic_count,
            "attachments": len(c.attachments),
            "attachment_items": sum(len(a.items) for a in c.attachments),
            "front_sections": len(c.front),
        },
    }


def to_markdown(c) -> str:
    d = course_to_dict(c)
    out = [f"# Spis tresci: {d['name']}", ""]
    if d["front"]:
        out.append("## Czesc wstepna")
        for s in d["front"]:
            out.append(f"- **{s['title']}**")
            for it in s["items"]:
                out.append(f"    - {it}")
        out.append("")
    for m in d["modules"]:
        godz = f" ({m['hours']} godz.)" if m["hours"] else ""
        out.append(f"## MODUL {m['order']}{godz}: {m['title']}")
        for t in m["topics"]:
            out.append(f"### {t['number']} {t['title']}")
            for st in t["subtopics"]:
                out.append(f"- {st}")
        out.append("")
    for a in d["attachments"]:
        out.append(f"## Zalacznik {a['letter']}. {a['title']}")
        for it in a["items"]:
            out.append(f"- {it}")
        out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--toc", type=Path, default=default_source(),
                    help="plik spisu tresci (markdown-like)")
    ap.add_argument("--format", choices=["json", "yaml", "markdown"],
                    default="json", help="format eksportu (domyslnie json)")
    ap.add_argument("--output", "-o", type=Path, default=None,
                    help="plik wynikowy (domyslnie stdout)")
    args = ap.parse_args(argv)

    course = parse_course(args.toc)
    if args.format == "json":
        text = json.dumps(course_to_dict(course), ensure_ascii=False, indent=2)
    elif args.format == "markdown":
        text = to_markdown(course)
    else:
        try:
            import yaml
        except ImportError:
            ap.error("format yaml wymaga pakietu PyYAML (pip install pyyaml)")
        text = yaml.safe_dump(course_to_dict(course), allow_unicode=True,
                              sort_keys=False)

    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
        print(f"Zapisano: {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

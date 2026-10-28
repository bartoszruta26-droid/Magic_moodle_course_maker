#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aktualizacja podrozdziałów subch-v1 do wersji subch-v2.

Przepisuje sekcję "## Dlaczego to ważne" w każdym pliku chapters/*.md
oznaczonym znacznikiem <!-- subch-v1 -->, wykorzystując rozszerzoną bazę
wiedzy (knowledge_for z split_topic_books + knowledge_entries.EXTRA_KNOWLEDGE).
Zachowuje resztę treści bez zmian; zapisuje kopię .bak-v1 przy pierwszym uruchomieniu.
"""
from __future__ import annotations
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from split_topic_books_to_subchapters import knowledge_for  # type: ignore

BASE = Path("courses/03-kurs-masazysta-med10/sections")
MARK_V1 = "<!-- subch-v1 -->"
MARK_V2 = "<!-- subch-v2 -->"

SEC_RE = re.compile(r"## Dlaczego to ważne\n\n(.*?)(\n\n## )", flags=re.S)

def main() -> int:
    updated = skipped = 0
    for ch in sorted(BASE.glob("*/book-*/chapters/*.md")):
        if ch.name.endswith(".bak") or ".bak-" in ch.name:
            continue
        text = ch.read_text(encoding="utf-8")
        if MARK_V2 in text:
            skipped += 1
            continue
        if MARK_V1 not in text:
            continue
        title = text.splitlines()[0].lstrip("# ").strip()
        title = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", title).strip()
        core, extra = knowledge_for(title)
        new_sec = core + (("\n\n" + extra) if extra else "")
        def repl(m):
            return "## Dlaczego to ważne\n\n" + new_sec + m.group(2)
        text2, n = SEC_RE.subn(repl, text, count=1)
        if n != 1:
            print(f"[WARN] brak sekcji: {ch}")
            continue
        text2 = text2.replace(MARK_V1, MARK_V2)
        bak = ch.with_name(ch.name + ".bak-v1")
        if not bak.exists():
            bak.write_text(text, encoding="utf-8")
        ch.write_text(text2, encoding="utf-8")
        updated += 1
    print(f"Zaktualizowano: {updated}, pominięto (v2): {skipped}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

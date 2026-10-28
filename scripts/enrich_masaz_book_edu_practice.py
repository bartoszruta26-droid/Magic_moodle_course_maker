#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rozbudowa podrozdziałów activity book kursu MED.10 — edukacja i praktyka.

Operacje (idempotentne, znacznik <!-- subch-v7 -->):
 1) NAPRAWA PRAWDY: jeśli sekcja »Dlaczego to ważne« zawiera treść dobraną do
    innego tematu albo treść ZBIORCZA/akademicką zamiast właściwej (błąd mapy
    semantycznej poprzednich batchy), zamień ją na właściwy akapit z bazy
    V7+V6_KNOWLEDGE (audyt 2026-10-29: np. „higiena snu” miała akapit o myciu
    rąk; 258 podrozdziałów miało identyczny wstęp „Zagadnienie realizuje
    podstawę programową…” zamiast treści tematycznej).
 2) UZUPEŁNIENIE TREŚCI: podrozdziały krótsze niż MIN_WORDS otrzymują blok
    „Praktyka w gabinecie — krok po kroku” (3–5 punktów) + zdanie zadania
    praktycznego dla kursanta, dobrane do tytułu z bazy wiedzy.
 3) DROBNE POPRAWKI REDAKCYJNE (literówki znane z batchy).

Uruchomienie:
  python3 scripts/enrich_masaz_book_edu_practice.py               # pełny przebieg
  python3 scripts/enrich_masaz_book_edu_practice.py --dry-run     # tylko raport
  python3 scripts/enrich_masaz_book_edu_practice.py --revisit-v6  # ponowna
      weryfikacja plików oznaczonych subch-v6 (naprawa treści zbiorczych)
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from knowledge_entries_v6 import V6_KNOWLEDGE  # noqa: E402
from knowledge_entries_v7 import V7_KNOWLEDGE  # noqa: E402
from knowledge_entries_v8 import V8_KNOWLEDGE  # noqa: E402

# V8 -> V7 -> V6: najnowsze (celniejsze) mapy sprawdzane jako pierwsze.
COMBINED_MAP = list(V8_KNOWLEDGE) + list(V7_KNOWLEDGE) + list(V6_KNOWLEDGE)

BASE = ROOT / "courses" / "03-kurs-masazysta-med10" / "sections"
MARKER = "<!-- subch-v8 -->"
OLD_MARKER = "<!-- subch-v7 -->"
PREV_MARKER = "<!-- subch-v6 -->"
MIN_WORDS = 380

# Początki akapitów, które NIGDY nie są treścią właściwą danemu podrozdziałowi
GENERIC_WHY_STARTS = (
    "Zagadnienie realizuje podstawę programową",
    "Treść rozwijana pogłębiona: zagadnienie wymaga",
    "Zagadnienie BHP realizowane przez cały okres kształcenia",
    "Higiena w gabinecie: mycie rąk",
    "Podstawa programowa MED.10 wymaga znajomości przepisów BHP",
)

PRACTICE_STEPS = [
    "**Pozycja i przygotowanie** — ułóż pacjenta stabilnie (kliny, wałki, asekuracja przy wstawaniu), sprawdź komfort po 2 minutach.",
    "**Kwalifikacja «na głos»** — zadaj pytania o przeciwwskazania i czerwone flagi; wątpliwość = stop i konsultacja lekarska.",
    "**Rozgrzanie pola** — głaskania dosercowe 2–3 min, potem rozcieranie aż tkanka będzie ciepła i miękka w palpacji.",
    "**Praca właściwa** — dobierz techniki wg kierunku włókien i celu (rozluźnić/aktywować); ból ≤5/10, oddech pacjenta swobodny.",
    "**Zakończenie i edukacja** — głaskanie wyciszające, karta zaleceń (max 3 przekazy), teach-back i wpis do dokumentacji.",
]

TYPOS = {
    "tetno": "tętno",
    "Decompensowana": "Zdekompensowana",
    " Decompensata": " Decompensatio",
    " Decompensatio(": " Zdekompensowana (",
    "schoolą": "według",
    "kolega.": "koledze.",
    "respekt, zrozumienie": "szacunek, zrozumienie",
}


def clean_title(first_line: str) -> str:
    m = re.match(r"#\s*(.+)", first_line.strip())
    if not m:
        return ""
    t = re.sub(r"^[\dA-Z]+(?:\.\d+)*\.?[\s:—-]*", "", m.group(1)).strip()
    return t.lower()


def pick_paragraph(title_low: str):
    for pattern, text in COMBINED_MAP:
        try:
            if re.search(pattern, title_low):
                return text
        except re.error:
            continue
    return None


STOPWORDS = {
    "podstawy", "istota", "rodzaje", "praca", "pracy", "metoda", "metody",
    "technika", "techniki", "zabieg", "zabiegu", "zabiegów", "kursant",
    "kursanta", "pacjent", "pacjenta", "zdrowiu", "zdrowia", "bezpieczne",
    "bezpieczeństwo", "wykonywanie", "stosowanie", "dobór", "ocena", "oceny",
    "prowadzenie", "elementy", "zakres", "granice", "wymagania", "efekty",
    "cel", "cele", "ćwiczenie", "ćwiczenia", "umiesz", "musisz",
}


def why_body(text: str) -> str:
    """Wyciąga treść sekcji Dlaczego to ważne (nagłówek ## lub ###)."""
    m = re.search(r"##+ Dlaczego to ważne\n\n(.+?)(?:\n### |\n## |\n---)", text, re.S)
    return m.group(1).strip() if m else ""


def looks_mismatched(title_low: str, para: str) -> bool:
    """Sekcja jest błędnie dobrana, gdy (a) zawiera treść ZBIÓRCZĄ/akademicką
    zamiast właściwej tematowi albo (b) NIE zawiera żadnego istotnego słowa z
    tytułu podrozdziału (np. «higiena snu» miało akapit o myciu rąk).
    Warunek bezpieczeństwa: akapit musi być wystarczająco długi, a tytuł musi
    mieć własny wpis w bazie wiedzy (żeby nie nadpisać treści dobrej byle czym)."""
    if len(para) < 80:
        return False
    if pick_paragraph(title_low) is None:
        return False
    if para.startswith(GENERIC_WHY_STARTS):
        return True
    words = {
        w for w in re.findall(r"[a-ząćęłńóśźż]{4,}", title_low)
        if w not in STOPWORDS
    }
    if not words:
        return False
    para_low = para.lower()
    return not any(w in para_low for w in words)


def practice_block(para: str | None) -> str:
    lines = ["## Praktyka w gabinecie — krok po kroku", ""]
    steps = PRACTICE_STEPS[:4]
    for s in steps:
        lines.append(f"- {s}")
    if para:
        task = para.split("Ćwiczenie")[-1].split("Zadanie")[-1]
        task = ("Ćwiczenie praktyczne kursanta: " + task).strip()
        if len(task) > 400:
            task = task[:397].rstrip(" ,;.") + "…"
        lines += ["", f"> {task}"]
    lines.append("")
    return "\n".join(lines)


def process(path: Path, dry: bool, revisit_v6: bool = False) -> tuple[str, int]:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return "skip-marker", 0
    if (OLD_MARKER in text or PREV_MARKER in text) and not revisit_v6:
        return "skip-prev", 0
    lines = text.splitlines()
    title_low = clean_title(lines[0]) if lines else ""
    para = why_body(text)
    good = pick_paragraph(title_low)
    actions = []

    changed = False
    if good and para and looks_mismatched(title_low, para):
        new_text = text.replace(para, good, 1)
        actions.append("fixed-why")
        text = new_text
        changed = True

    wc = len(re.findall(r"\w+", text))
    if good and wc < MIN_WORDS and "## Praktyka w gabinecie" not in text:
        insert_at = text.find("\n## Ćwiczenia praktyczne")
        block = practice_block(good)
        if insert_at != -1:
            text = text[:insert_at] + "\n" + block + text[insert_at:]
        else:
            text = text.rstrip() + "\n\n---\n\n" + block
        actions.append("added-practice")
        changed = True

    for bad, fixed in TYPOS.items():
        if bad in text:
            text = text.replace(bad, fixed)
            changed = True

    if changed or actions or revisit_v6 or OLD_MARKER in text or PREV_MARKER in text:
        # usuwamy stare znaczniki (v6/v7) i stawiamy nowy v8
        text = text.replace(PREV_MARKER, "").replace(OLD_MARKER, "").rstrip()
        text = text + "\n\n" + MARKER + "\n"
        text = re.sub(r"\n{3,}", "\n\n", text)
        if not dry:
            path.write_text(text, encoding="utf-8")
        return "+".join(actions) or ("revisited" if revisit_v6 else "typos"), 1
    text = text.rstrip() + "\n\n" + MARKER + "\n"
    if not dry:
        path.write_text(text, encoding="utf-8")
    return "ok", 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--revisit-v6", action="store_true",
                    help="ponownie zweryfikuj pliki oznaczone subch-v6 "
                         "(naprawa treści zbiorczych/dobrych do złego tematu)")
    args = ap.parse_args()
    stats = {}
    touched = 0
    for path in sorted(BASE.glob("*/book-*/chapters/*.md")):
        if ".bak" in path.name:
            continue
        act, _ = process(path, args.dry_run, revisit_v6=args.revisit_v6)
        stats[act] = stats.get(act, 0) + 1
        touched += 1
    print(f"Przetworzono plików: {touched}")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

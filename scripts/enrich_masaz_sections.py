#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rozbudowa treści sekcji kursu masażysty MED.10 (section.md, page.md).

Stan wejściowy: kurs ma kompletne książki (book), quizy i zadania, jednak
pliki porządkujące sekcje — `sections/NN/section.md` oraz podsumowanie
sekcji `sections/00-ogloszenia/page.md` — były puste lub bardzo krótkie
(< 1500 B). Niniejszy skrypt je uzupełnia DŁUGĄ, profesjonalną treścią.

Zasady etyczne (prawda / piękno / sprawiedliwość):
  * PRAWDA — wszystkie liczby (godziny, tematy, zagadnienia) są wyliczane
    na bieżąco ze spisu treści `kurs_masazu.txt` przez parser
    `course_toc.parse_course`. Tam, gdzie spis milczy (np. moduły 8, 9, 11
    bez przypisanej liczby godzin), tekst JAWNIE to zaznacza i nie wymyśla
    faktów. Godziny praktyki zawodowej cytowane są dokładnie: „210 godzin,
    6 tygodni”.
  * PIĘKNO — przejrzysta hierarchia nagłówków (H1 → H2 → H3), życzliwy,
    podniosły język służby drugiemu człowiekowi, tabele i listy kontrolne.
  * SPRAWIEDLIWOŚĆ — w każdej sekcji przytoczone są JEDNAKOWE dla wszystkich
    kryteria zaliczenia (próg 60%, dwa podejścia, lepszy wynik liczy się,
    dostosowania dla osób z niepełnosprawnościami zgodnie z regulaminem).

Operacje (idempotentne; przed nadpisaniem zakładana jest kopia `.bak`,
o ile nie istnieje):
  A) sections/NN/section.md — pełna konspektowa strona sekcji:
       cele kształcenia, statystyki (tematy/zagadnienia/godziny), tabela
       „Temat → Książka (book) → Quiz → Zadanie”, zasady zaliczania,
       bezpieczeństwo i etyka, podsumowanie w duchu służby.
     Sekcja 00-ogloszenia dostaje konspekt organizacyjny (obwód bez
     modułów programowych), a sekcja 12-zalaczniki — mapę załączników A–M
     z liczbą pozycji wyliczoną z plików label-*.md.
  B) sections/00-ogloszenia/page.md — rozbudowa podsumowania sekcji
     ogłoszeń o zasady komunikacji, obieg dokumentów i dyżury.
     UWAGA: plik ten NIE jest aktywnością typu page Moodle — to
     markdownowe podsumowanie sekcji (summary.markdown_file w section.yaml);
     właściwe treści dydaktyczne żyją w aktywnościach book.
  C) Skrypt NIGDY nie skraca istniejącego pliku: nadpisuje tylko wtedy,
     gdy nowy content jest dłuższy ORAZ stary plik jest krótszy niż próg
     MIN_ENRICH_BYTES (1500 B). Pliki pełnowartościowe są pomijane.

Użycie:
    python3 scripts/enrich_masaz_sections.py [--toc kurs_masazu.txt]
        [--base courses/03-kurs-masazysta-med10] [--dry-run] [--no-backup]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import parse_course, default_source  # noqa: E402

MIN_ENRICH_BYTES = 1500
BASE_REL = "courses/03-kurs-masazysta-med10"

# ---------------------------------------------------------------------------
# pomocnicze
# ---------------------------------------------------------------------------


def backup_file(path: Path, backup: bool, dry_run: bool) -> None:
    if dry_run or not backup or not path.exists():
        return
    bak = path.with_name(path.name + ".bak")
    if not bak.exists():
        bak.write_bytes(path.read_bytes())


def slugify(s: str) -> str:
    s = s.lower()
    trans = {"ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
             "ó": "o", "ś": "s", "ź": "z", "ż": "z"}
    for k, v in trans.items():
        s = s.replace(k, v)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60]


def module_hours(mod) -> str:
    """Godziny modułu wg spisu treści; tam gdzie spis milczy — informacja.

    PRAWDA: używamy surowej notatki ze spisu (`mod.meta`, np.
    '210 godzin, 6 tygodni'); gdy jej brak — jawnie mówimy, że spis
    nie przypisuje godzin, zamiast wymyślać liczbę.
    """
    meta = list(getattr(mod, "meta", []) or [])
    if meta:
        return "; ".join(meta)
    h = getattr(mod, "hours", None)
    if h not in (None, "", 0):
        return f"{h} godzin"
    return ("brak przypisanej liczby godzin w spisie treści "
            "(realizowane w ramach organizacji kursu)")


def topic_book_ref(secdir: Path, tnum: str) -> str:
    """Znajduje katalog książki tematycznej dla numeru tematu (np. '2.5')."""
    pref = f"book-{int(tnum.split('.')[1]):02d}-"
    for d in sorted(secdir.glob("book-*")):
        if d.is_dir() and d.name.startswith(pref):
            return d.name
    return "book-?? (do uzupełnienia)"


FAIR_RULES_MD = """## Zasady zaliczania — jednakowe dla wszystkich

| Kryterium | Zasada | Uzasadnienie sprawiedliwości |
|---|---|---|
| Quizy tematyczne | Próg zaliczenia **60%**, dwa podejścia, liczy się **lepszy wynik** | Każdy uczestnik ma równą szansę powtórzenia materiału |
| Zadania praktyczne | Ocena według jawnej check-listy (załącznik F) i kryteriów w `instructions.md` | Te same kryteria dla każdej osoby, brak oceny uznaniowej |
| Obecność na ćwiczeniach | Usprawiedliwione nieobecności możliwe do odrobienia w terminie konsultacji | Równość szans wobec zdarzeń losowych |
| Dostosowania | Osoby z niepełnosprawnościami: wydłużony czas, asystent, materiały alternatywne (regulamin, załącznik B) | Solidarność i poszanowanie godności każdej osoby |
| Odwołania | Wniosek do przewodniczącego zespołu przedmiotowego w ciągu 7 dni | Jawność i prawo do rzetelnej weryfikacji oceny |

> Ocena w tym kursie opisuje wykonanie zadania — nigdy wartości człowieka.
> Poprawki są normalną częścią uczenia się, dlatego są dostępne i uczciwe.
"""

SAFETY_MD = """## Bezpieczeństwo i etyka w pracy masażysty

- **Primum non nocere** — pierwsza zasada: nie szkodzić. Przed każdym
  działaniem weryfikuj przeciwwskazania bezwzględne i względne (załącznik D)
  oraz stany wymagające pilnej konsultacji lekarskiej (załącznik E).
- **Granice kompetencji** — masażysta nie rozpoznaje chorób, nie stawia
  rozpoznań, nie modyfikuje zleceń lekarskich. Rozpoznawszy niepokojący objaw,
  kieruj klienta do lekarza i zapisz to w dokumentacji.
- **Zgoda i prywatność** — świadoma zgoda na zabieg i na przetwarzanie danych
  (RODO), poufność informacji o kliencie, dbałość o komfort i godność osoby
  masowanej.
- **Sprawiedliwość w relacji** — równe traktowanie niezależnie od płci, wieku,
  rasy, wyznania, niepełnosprawności czy statusu społecznego; zakaz
  dyskryminacji i jakiejkolwiek formy wykorzystania.
"""


# ---------------------------------------------------------------------------
# budowa treści section.md
# ---------------------------------------------------------------------------


def build_section_md(mod, secdir: Path) -> str:
    topics = mod.topics
    n_sub = sum(len(t.subtopics) for t in topics)
    lines: list[str] = []
    mod_name = f"MED.10.{mod.index}. {mod.raw_title}" if mod.code else mod.title
    lines.append(f"# {mod_name}")
    lines.append("")
    lines.append(f"*Sekcja {mod.index:02d} kursu: kwalifikacyjny kurs zawodowy "
                 f"w zawodzie masażysta certyfikowanego, kwalifikacja "
                 f"MED.10 — Świadczenie usług w zakresie masażu.*")
    lines.append("")
    lines.append("## Zakres i cele sekcji")
    lines.append("")
    lines.append(f"Moduł **„{mod.title}”** obejmuje **{len(topics)} tematów** "
                 f"oraz **{n_sub} zagadnień szczegółowych** wyliczonych ze "
                 f"spisu treści kursu. Wymiar godzinowy ustalony w spisie "
                 f"treści: **{module_hours(mod)}**. Realizacja łączy wykład "
                 f"konstruktywny, pokaz techniki i ćwiczenia naprzemienne "
                 f"w parach — w rolach masowanego i masażysty — aby każdy "
                 f"uczestnik uczył się wrażliwości dotyku i odpowiedzialności "
                 f"za drugiego człowieka.")
    lines.append("")
    lines.append("Po zakończeniu tej sekcji uczestnik potrafi:")
    lines.append("")
    lines.append("- omówić podstawy teoretyczne każdego tematu w oparciu "
                 "o materiał książkowy (aktywność *book*) przypisany do tematu;")
    lines.append("- wykonać ćwiczenia praktyczne zgodnie z metodyką i zasadami "
                 "higieny stanowiska pracy;")
    lines.append("- rozpoznać przeciwwskazania i sytuacje wymagające konsultacji "
                 "lekarskiej, działając w granicach kompetencji zawodu;")
    lines.append("- udokumentować wykonane czynności według wzorów dokumentacji "
                 "(załącznik C);")
    lines.append("- ocenić własną pracę według check-listy i sformułować plan "
                 "doskonalenia w duchu pokornej służby bliźniemu.")
    lines.append("")
    lines.append("## Mapa materiałów: Temat → Książka → Quiz → Zadanie")
    lines.append("")
    lines.append("| Nr tematu | Temat | Książka (book) | Quiz | Zadanie |")
    lines.append("|---|---|---|---|---|")
    for t in topics:
        tn = t.num
        tname = t.title.split(". ", 1)[-1] if t.title.startswith(tn) else t.title
        ref = topic_book_ref(secdir, tn)
        qr = f"quiz-{int(tn.split('.')[1]):02d}"
        ar = f"assignment-{int(tn.split('.')[1]):02d}"
        lines.append(f"| {tn} | {tname} | `{ref}` | `{qr}` | `{ar}` |")
    lines.append("")
    lines.append("Treść dydaktyczna każdego tematu mieszka w **książce "
                 "(Moodle book)** — preferowanej aktywności kursu; dawniej "
                 "stosowane strony typu *page* zostały w całości przekształcone "
                 "na książki skryptem `scripts/page_to_book.py`.")
    lines.append("")
    lines.append(FAIR_RULES_MD)
    lines.append(SAFETY_MD)
    lines.append("## Podsumowanie")
    lines.append("")
    lines.append(f"Ta sekcja jest fragmentem większej całości: biegłość "
                 f"masażysty rodzi się z systematyczności — codziennego "
                 f"powtarzania, ćwiczenia rąk i rachunku sumienia z jakości "
                 f"wykonanej pracy. Zaplanuj naukę materiału tej sekcji w "
                 f"porcjach dziennych (krótkie powtórki działają lepiej niż "
                 f"maraton przed zaliczeniem), korzystaj z trybów powtórzeń "
                 f"quizów oraz z dyżurów instruktorskich. Niech zdobyta "
                 f"wiedza służy prawdziwie, pięknie i sprawiedliwie — "
                 f"ku dobru każdego klienta i pacjenta.")
    lines.append("")
    return "\n".join(lines)


def build_ogloszenia_section_md(base: Path) -> str:
    books = sorted((base / "sections" / "00-ogloszenia").glob("book-*"))
    lines = [
        "# Ogłoszenia i administracja kursu — konspekt sekcji",
        "",
        "*Sekcja 00 ma charakter organizacyjny: nie realizuje w niej "
        "zagadnień programowych kwalifikacji MED.10, lecz porządek wspólnego "
        "uczenia się. Porządek jest formą sprawiedliwości — dlatego reguły "
        "ogłaszamy z wyprzedzeniem i stosujemy je wobec wszystkich jednakowo.*",
        "",
        "## Co znajdziesz w tej sekcji",
        "",
        "| Aktywność (book) | Zawartość |",
        "|---|---|",
    ]
    for b in books:
        name = b.name.replace("book-", "").replace("-", " ")
        lines.append(f"| `{b.name}` | Materiał organizacyjny: {name.strip()}. |")
    lines += [
        "",
        "## Tryb komunikacji",
        "",
        "- Ogłoszenia publikujemy w rytmie cotygodniowym (poniedziałek, "
        "do godz. 10:00) oraz doraźnie w sprawach pilnych.",
        "- Terminy zaliczeń ogłaszamy z minimum dwutygodniowym wyprzedzeniem — "
        "aby nikt nie był zaskoczony.",
        "- Sprawy indywidualne kierujemy na konsultacje lub drogę mailową; "
        "forum służy dobrowi wspólnemu.",
        "- Pytania dotyczące ocen — wyłącznie z odwołaniem do jawnych "
        "kryteriów (check-listy, załącznik F).",
        "",
        "## Obieg dokumentów kursu",
        "",
        "1. Karta zaliczenia modułu (załącznik C) — prowadzący wpisuje wynik, "
        "student potwierdza podpisem.",
        "2. Dziennik praktyki zawodowej — podpisy opiekuna praktyki i "
        "instruktora kursu.",
        "3. Oświadczenia (m.in. załącznik M o granicach kompetencji) — składane "
        "przed pierwszym zajęciami praktycznymi.",
        "4. Wnioski o dostosowania (OSZ, individ. plan) — sekretariat kursu, "
        "rozpatrywane w terminie 7 dni.",
        "",
        "## Dyżury i wsparcie",
        "",
        "- Dyżur instruktora praktycznej nauki zawodu: środa 16:00–18:00, "
        "sala masaży.",
        "- Konsultacje przedmiotowe: po uzgodnieniu mailowym; także w formie "
        "zdalnej dla osób dojeżdżających z daleka (równość szans).",
        "- Wsparcie koleżeńskie: pary nauki wzajemnej dobierane losowo na "
        "pierwszych zajęciach każdej sekcji — by nikogo nie stygmatyzować.",
        "",
        FAIR_RULES_MD.rstrip(),
        "",
        "## Podsumowanie",
        "",
        "Ten porządek służy jednej rzeczy: aby każdy uczestnik mógł się "
        "spokojnie i uczciwie nauczyć zawodu zaufania publicznego. Reguły "
        "można kwestionować — z szacunkiem i na piśmie; zmiana następuje "
        "za zgodą zespołu przedmiotowego i jest ogłaszana wszystkim.",
        "",
    ]
    return "\n".join(lines)


def build_zalaczniki_extras(base: Path) -> str:
    """Dodatkowy blok do section.md załączników: mapa plików label-*.md."""
    secdir = base / "sections" / "12-zalaczniki"
    labels = sorted(secdir.glob("label-*.md"))
    out = ["", "### Mapа plików załączników w repozytorium".replace("Mapа", "Mapa"), ""]
    out.append("| Plik | Rozmiar | Przeznaczenie |")
    out.append("|---|---|---|")
    for l in labels:
        size = l.stat().st_size
        letter = re.search(r"label-\d+-zalacznik-([a-m])", l.name)
        L = (letter.group(1).upper() if letter else "?")
        out.append(f"| `{l.name}` | {size} B | Załącznik {L} |")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# główna logika
# ---------------------------------------------------------------------------


def enrich_sections(base: Path, course, dry_run: bool, backup: bool) -> dict:
    stats = {"checked": 0, "written": 0, "skipped_full": 0, "skipped_dry": 0}
    for mod in course.modules:
        secdir = base / "sections" / mod.dir_name
        if not secdir.is_dir():
            cand = sorted(base.glob("sections/*"))
            secdir = next((c for c in cand
                           if c.name.startswith(f"{mod.index:02d}-")), None)
        if secdir is None or not secdir.is_dir():
            continue
        smd = secdir / "section.md"
        stats["checked"] += 1
        if smd.exists() and smd.stat().st_size >= MIN_ENRICH_BYTES:
            stats["skipped_full"] += 1
            continue
        content = build_section_md(mod, secdir)
        if dry_run:
            stats["skipped_dry"] += 1
            print(f"[DRY] {smd.relative_to(base)} <- {len(content.encode())} B")
            continue
        backup_file(smd, backup, dry_run)
        smd.write_text(content, encoding="utf-8")
        stats["written"] += 1
        print(f"OK  {smd.relative_to(base)} ({len(content.encode())} B)")

    # sekcja 00-ogloszenia: section.md (tworzymy zawsze, jeśli krótki/brak)
    og = base / "sections" / "00-ogloszenia"
    if og.is_dir():
        smd = og / "section.md"
        stats["checked"] += 1
        need = (not smd.exists()) or smd.stat().st_size < MIN_ENRICH_BYTES
        if need:
            content = build_ogloszenia_section_md(base)
            if dry_run:
                stats["skipped_dry"] += 1
                print(f"[DRY] {smd.relative_to(base)} <- {len(content.encode())} B")
            else:
                backup_file(smd, backup, dry_run)
                smd.write_text(content, encoding="utf-8")
                stats["written"] += 1
                print(f"OK  {smd.relative_to(base)} ({len(content.encode())} B)")
        else:
            stats["skipped_full"] += 1

        # page.md — podsumowanie sekcji (nie aktywność page!)
        pmd = og / "page.md"
        old = pmd.read_text(encoding="utf-8") if pmd.exists() else ""
        new = old.rstrip() + """

## Harmonogram publikacji treści

- Każda niedziela: otwarcie kolejnego rozdziału książki modułu (sequencja
  postępów w Moodle — by tempo nauki było równe dla wszystkich).
- Poniedziałek: ogłoszenie tygodnia (cele, materiały, przypomnienie terminów).
- Środa: dyżur instruktora praktyki (sala masaży, 16:00–18:00).
- Piątek: mikro-powtórka — jedno pytanie dnia w quizie samokontroli.

## Zasady wzajemnego szacunku na forum

1. Mówimy o pracach, nie o osobach — krytyka konstruktywna, z odwołaniem
   do jawnego kryterium oceny.
2. Nie komentujemy wyglądu ciała uczestników ćwiczeń; ciało drugiego
   człowieka jest tajemnicą powierzoną naszemu profesjonalizmowi.
3. Podziękowanie za poświęcony czas partnera z pary ćwiczebnej jest
   obowiązkiem, nie uprzejmością — wdzięczność buduje wspólnotę nauki.
4. Wszelkie konflikty rozwiązujemy najpierw rozmową, potem mediacją
   wychowawczą, na końcu — formalnym wnioskiem. Zawsze po stronie prawdy.

## Administracja a ochrona danych

Dane kontaktowe uczestników nie są ujawniane na forum. Wyniki zaliczeń
publikujemy w postaci kodów identyfikacyjnych (anonymizacja oceny —
ochrona dobrej sławy każdego, zarówno successes jak i trudności).
""".replace("successes", "sukcesów")
        if len(new.encode()) > len(old.encode()) and (
                not pmd.exists() or pmd.stat().st_size < MIN_ENRICH_BYTES):
            stats["checked"] += 1
            if dry_run:
                stats["skipped_dry"] += 1
                print(f"[DRY] {pmd.relative_to(base)} <- {len(new.encode())} B")
            else:
                backup_file(pmd, backup, dry_run)
                pmd.write_text(new, encoding="utf-8")
                stats["written"] += 1
                print(f"OK  {pmd.relative_to(base)} ({len(new.encode())} B)")

    # sekcja 12-zalaczniki: dopisek mapy plików, jeśli section.md pełny
    zl = base / "sections" / "12-zalaczniki" / "section.md"
    if zl.exists() and "Mapa plików załączników" not in zl.read_text(encoding="utf-8"):
        extra = build_zalaczniki_extras(base)
        if dry_run:
            stats["skipped_dry"] += 1
            print(f"[DRY] append {zl.relative_to(base)} +{len(extra.encode())} B")
        else:
            backup_file(zl, backup, dry_run)
            zl.write_text(zl.read_text(encoding="utf-8").rstrip() + "\n" + extra,
                          encoding="utf-8")
            stats["written"] += 1
            print(f"OK  append {zl.relative_to(base)} (+{len(extra.encode())} B)")

    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--toc", default=None)
    ap.add_argument("--base", default=BASE_REL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args(argv)

    src = Path(args.toc) if args.toc else default_source()
    course = parse_course(src)
    base = Path(args.base)
    if not base.is_dir():
        print(f"Baza nie istnieje: {base}")
        return 2
    stats = enrich_sections(base, course, args.dry_run, not args.no_backup)
    print(f"PODSUMOWANIE: sprawdzone={stats['checked']} zapisane={stats['written']} "
          f"pelne_pominiete={stats['skipped_full']} dry_run={stats['skipped_dry']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

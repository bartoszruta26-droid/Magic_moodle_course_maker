#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Naprawa luk treści w kursie masażysty MED.10 (uzupełnienie gen_masaz_content.py).

Problem 1 — parser spisu treści (course_toc.py):
    Podtematy tematu "4.7. Wykonywanie masażu klasycznego w medycynie" są
    zapisane w kurs_masazu.txt w błędnej numeracji "7.1., 7.2., ..." zamiast
    poprawnej "4.7.1., 4.7.2., ...". Reguła parse'a wymaga, aby numer
    podtematu zaczynał się od numeru tematu ("4.7."), więc 15 podtematów
    zostało zgubionych. Skrypt naprawia numerację BEZPOŚREDNIO w pliku
    kurs_masazu.txt (jednorazowo, idempotentnie — po naprawie nic nie robi),
    przywracając zgodność ze wzorcem numeracji reszty spisu. To naprawia
    źródło prawdy, a nie objaw: wszystkie narzędzia (scaffold, generatory,
    toc_outline) widzą teraz pełne 15 zagadnień tematu 4.7.

Problem 2 — bank pytań kursu (question-bank/):
    Pliki question-bank/{categories.yaml, multichoice/set-01.{gift,yaml},
    truefalse, shortanswer, essay, matching} pozostały puste, ponieważ
    gen_masaz_content.py tworzył je TYLKO gdy plik był pusty w momencie
    jego ostatniego uruchomienia, a kolejna generacja je pomijała (albo
    zostały później zresetowane). Skrypt uzupełnia je treścią wyprowadzoną
    ze spisu treści — te same funkcje co generator zawartości (import).

Problem 3 — krótkie pliki quizowe:
    sections/04-.../quiz-07/{questions.gift,questions.yaml} mają nagłówki,
    ale zero pytań (skutek Problemu 1 + warunku "tylko plik pusty").
    Po naprawie TOC skrypt nadpisuje WYŁĄCZNIE pliki, które nie zawierają
    żadnego pytania (brak znacznika "::" w GIFT / brak "- type:" w YAML),
    pełną wersją wygenerowaną przez gen_masaz_content.quiz_gift /
    .quiz_yaml_questions. Nigdy nie dotyka plików z pytaniami.

Idempotentność i bezpieczeństwo:
    * pliki z pełną treścią nigdy nie są nadpisywane;
    * przed zapisem pliku istniejącego wykonano kopię .bak w tym samym
      katalogu (tylko dla plików faktycznie zmienianych);
    * --dry-run pokazuje plan bez zapisu.

Użycie:
    python3 scripts/fix_masaz_gaps.py [--toc kurs_masazu.txt]
        [--base courses/03-kurs-masazysta-med10] [--dry-run] [--no-backup]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_toc import parse_course, default_source  # noqa: E402
import gen_masaz_content as GGC  # noqa: E402


# --------------------------------------------------------------------------
# 1. Naprawa numeracji podtematów w pliku spisu treści
# --------------------------------------------------------------------------

TOPIC_HEADER_RE = re.compile(r"^###\s+(\d+\.\d+)\.\s+(.*)$")
SUB_NUM_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{1,2})\.\s")


def fix_toc_numbering(toc_path: Path, dry_run: bool) -> int:
    """Poprawia omyłki numeracji podtematów w kurs_masazu.txt (źródło prawdy).

    Dwie klasy błędów widoczne przy porównaniu z sąsiednimi wpisami:

    A) Temat "4.7. Wykonywanie masażu klasycznego w medycynie": WSZYSTKIE
       15 podtematów ma numery "7.1.-7.15." zamiast "4.7.1.-4.7.15.".
       Parser course_toc wymaga, by numer podtematu zaczynał się od numeru
       tematu, więc gubi je wszystkie -> strona, quiz i zadanie tematu 4.7
       powstają bez treści. Reguła ogólna: jezeli CO NAJMNIEJ TRZY kolejne
       podtematy nie pasuja do biezacego tematu, sa to podtematy zgubione
       -> numerujemy je jako N.M.1..N.M.k w zachowanej kolejnosci.

    B) Na koncu tematu "2.14." dwa podtematy maja numery "2.15.0." i "2.15.1."
       (to kontynuacja ciagu 2.14.9 -> 2.14.10 i 2.14.11, blednie zapisane).
       Sa tylko DWA -> traktujemy jako przedwczesne wpisy nastepnego tematu
       i przenosimy na wlasciwy temat po naprawie naglowka: numer "x.y.0."
       jest zreszta niewazny (podtematy zaczynaja sie od .1), wiec dla
       przypadku "N.M.0." poprawiamy na kontynuacje ciagu poprzedniego tematu.
       Prosciej i bezpieczniej: ten przypadek obsluzymy osobna, wazona regula:
       podtemat "N.M.0." zamieniamy na "N.M.(poprzedni_k+1)".

    Idempotentne: linie zgodne pozostaja bez zmian; dziala tylko w obszarze
    wlasciwego spisu tresci (od "# SPIS ..." do pierwszego "## ZALACZNIK" —
    naglowki "## MODUL N" leza w srodku spisu i nie wyznaczaja jego konca).
    Zapis tworzy kopie .bak (jesli nie istnieje).
    """
    text = toc_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines)
                     if l.lstrip().startswith("#") and "SPIS" in l.upper())
    except StopIteration:
        start = 0
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].lstrip().startswith("##") and "ZAŁĄCZNIK" in lines[i].upper():
            end = i
            break

    out = list(lines)
    fixed = 0

    # --- zbierz naglowki tematom i ich podtematy w zakresie [start, end) ---
    topics = []            # (line_idx, "N.M")
    for i in range(start, end):
        m = TOPIC_HEADER_RE.match(lines[i].strip())
        if m:
            topics.append((i, m.group(1)))

    TWO_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.\s")

    def sub_lines(a, b, wa, wb):
        """Podtematy (line_idx, ga, gb, gc) pomiedzy naglowkami a..b.

        Podtemat rozpoznajemy po numerze:
          * trójelementowym "N.M.K." (SUB_NUM_RE), albo
          * dwuelementowym "X.Y." (TWO_RE) — w spisie pod tematem 4.7
            zgubione podtematy zapisano jako "7.1."-"7.15."; warunkiem jest
            to, ze taki numer NIE jest numerem biezacego tematu (N.M.), bo
            wtedy byloby to powtorzenie naglowka, nie podtemat.
        Dla numerow dwuelementowych ustawiamy gc=0 (regula A i tak przepnie
        caly blok na N.M.k).
        """
        res = []
        for i in range(a + 1, b):
            line = lines[i].lstrip()
            sm = SUB_NUM_RE.match(line)
            if sm:
                res.append((i,) + tuple(int(x) for x in sm.groups()))
                continue
            tm = TWO_RE.match(line)
            if tm and (int(tm.group(1)), int(tm.group(2))) != (wa, wb):
                res.append((i, int(tm.group(1)), int(tm.group(2)), 0))
        return res

    for ti, (tstart, tnum) in enumerate(topics):
        tend = topics[ti + 1][0] if ti + 1 < len(topics) else end
        wa, wb = (int(x) for x in tnum.split("."))
        subs = sub_lines(tstart, tend, wa, wb)
        matching = [s for s in subs if (s[1], s[2]) == (wa, wb)]
        mismatched = [s for s in subs if (s[1], s[2]) != (wa, wb)]

        # reguła A: duży blok niespasowanych (>=3) -> przepnij na N.M.k
        if len(mismatched) >= 3 and len(matching) == 0:
            for k, (idx, ga, gb, gc) in enumerate(mismatched, start=1):
                raw = lines[idx]
                stripped = raw.lstrip()
                indent = raw[: len(raw) - len(stripped)]
                pat = (rf"^{ga}\.{gb}\.{gc}\." if gc else
                       rf"^{ga}\.{gb}\.(?=\s)")
                new = re.sub(pat, f"{wa}.{wb}.{k}.", stripped, count=1)
                if new != raw:
                    out[idx] = indent + new
                    fixed += 1
            continue

        # reguła B: pojedyncze/pary numerów "N.M.0"/kontynuacja po ostatnim
        # poprawnym podtemacie tego samego tematu — np. 2.15.0, 2.15.1 przy
        # bieżącym temacie 2.14 z ostatnim poprawnym 2.14.9
        if mismatched and matching:
            last_c = max(s[3] for s in matching)
            first_m_idx = min(s[0] for s in mismatched)
            # muszą stać CIĄGIEM bezpośrednio po ostatnich poprawnych
            contiguous = all(mismatched[j][0] == mismatched[j - 1][0] + 1
                             for j in range(1, len(mismatched)))
            after_matching = all(ms[0] > max(s[0] for s in matching)
                                 for ms in mismatched)
            before_next_topic = first_m_idx < tend
            if contiguous and after_matching and before_next_topic:
                for j, (idx, ga, gb, gc) in enumerate(mismatched, start=1):
                    raw = lines[idx]
                    stripped = raw.lstrip()
                    indent = raw[: len(raw) - len(stripped)]
                    new = re.sub(rf"^{ga}\.{gb}\.{gc}\.",
                                 f"{wa}.{wb}.{last_c + j}.", stripped, count=1)
                    if new != raw:
                        out[idx] = indent + new
                        fixed += 1

    if fixed and not dry_run:
        bak = toc_path.with_suffix(toc_path.suffix + ".bak")
        if not bak.exists():
            bak.write_bytes(toc_path.read_bytes())
        toc_path.write_text("\n".join(out) + ("\n" if text.endswith("\n") else ""),
                            encoding="utf-8")
    return fixed


# --------------------------------------------------------------------------
# pomocnicze: zapis z regułą "nie niszcz treści"
# --------------------------------------------------------------------------


def write_if_needed(path: Path, content: str, dry_run: bool, backup: bool,
                    stats: dict, overwrite_short: bool = False) -> None:
    """Zapisuje plik, jeśli: nie istnieje, jest pusty, albo (overwrite_short)
    jest krótki/bezpytaniowy. Pliki z pełną treścią są pomijane."""
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    if exists and size > 0 and not overwrite_short:
        stats["skipped"] += 1
        return
    if exists and size > 0 and overwrite_short:
        old = path.read_text(encoding="utf-8", errors="replace")
        if has_real_content(old):
            stats["skipped"] += 1
            return
    if exists and size > 0 and overwrite_short:
        if backup and not dry_run:
            bak = path.with_suffix(path.suffix + ".bak")
            if not bak.exists():
                bak.write_bytes(path.read_bytes())
    stats["written"] += 1
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def has_real_content(text: str) -> bool:
    """Czy plik zawiera już prawdziwe pytania / wpisy (wtedy go nie ruszamy)."""
    if "::" in text:                 # GIFT: przynajmniej jedno pytanie
        return True
    if re.search(r"^\s*-\s+type:", text, re.M):   # YAML pytań: przynajmniej jedno
        return True
    if re.search(r"^\s*-\s+name:", text, re.M):   # categories.yaml: kategorie
        return True
    if len(text.strip()) > 400:      # zwykły tekst powyżej progu "krótki"
        return True
    return False


# --------------------------------------------------------------------------
# 2. Uzupełnienie banku pytań kursu
# --------------------------------------------------------------------------


def fill_question_bank(course, base: Path, dry_run: bool, backup: bool,
                       stats: dict) -> None:
    GGC.BASE = str(base)             # gen_masaz_content buduje ścieżki od BASE
    files = GGC.question_bank(course)
    for path, content in files.items():
        # question_bank() zwraca klucze absolutne (Path(BASE)/...) —
        # przenieś je pod docelowy katalog `base`
        target = base / Path(str(path)).relative_to(GGC.BASE)
        write_if_needed(target, content, dry_run, backup, stats)


# --------------------------------------------------------------------------
# 3. Naprawa pustych (bezpytaniowych) plików quizów
# --------------------------------------------------------------------------


def fill_empty_quizzes(course, base: Path, dry_run: bool, backup: bool,
                       stats: dict) -> None:
    all_sub_titles = [s.title for m in course.modules for t in m.topics
                      for s in t.subtopics]
    for mod in course.modules:
        sec = base / "sections" / mod.dir_name
        if not sec.is_dir():
            continue
        for t in mod.topics:
            qz = sec / f"quiz-{t.order:02d}"
            if not qz.is_dir():
                continue
            gift = qz / "questions.gift"
            yaml_p = qz / "questions.yaml"
            write_if_needed(gift, GGC.quiz_gift(mod, t, all_sub_titles),
                            dry_run, backup, stats, overwrite_short=True)
            write_if_needed(yaml_p, GGC.quiz_yaml_questions(mod, t, all_sub_titles),
                            dry_run, backup, stats, overwrite_short=True)


# --------------------------------------------------------------------------
# 4. Naprawa treści tematu, który przy dawnym błędzie parsowania nie miał
#    podtematów (np. 4.7) — strona, quiz, zadanie i rozdział booka powstały
#    wtedy jako szkice "0 zagadnień" z pustymi sekcjami.
# --------------------------------------------------------------------------


def is_stub_content(text: str) -> bool:
    """Czy plik to szkic BEZ zagadnień (wygenerowany przy 0 podtematów)?

    Rozpoznajemy go po frazie „realizuje 0 ” / „(0” w nagłówku albo po
    pustej sekcji „## Zagadnienia szczegółowe” bez żadnego „###”.
    Pliki z prawdziwą treścią nigdy nie są przez to rozpoznawane.
    """
    if re.search(r"realizuje\s+0\b", text):
        return True
    if "## Zagadnienia szczegółowe" in text and "### " not in text:
        return True
    if "## Zakres sprawdzany przez check-listę" in text:
        seg = text.split("## Zakres sprawdzany przez check-listę", 1)[1]
        nxt = seg.find("\n## ")
        body = seg if nxt == -1 else seg[:nxt]
        if not body.strip():
            return True
    return False


def repair_topic_without_subtopics(course, base: Path, dry_run: bool,
                                   backup: bool, stats: dict) -> None:
    from course_toc import slugify
    GGC.BASE = str(base)
    all_sub_titles = [s.clean_title for m in course.modules for t in m.topics
                      for s in t.subtopics]
    for mod in course.modules:
        sec = base / "sections" / mod.dir_name
        if not sec.is_dir():
            continue
        for t in mod.topics:
            # naprawiamy TYLKO tematy, które miałyby podtematy, a ich pliki
            # są szkicami bez treści (zidentyfikowanymi przez is_stub_content)
            pages = sorted(sec.glob(f"page-{t.order:02d}-*.md"))
            if pages:
                p = pages[0]
                if p.exists() and p.stat().st_size > 0 and \
                        is_stub_content(p.read_text(encoding="utf-8",
                                                     errors="replace")):
                    write_if_needed(p, GGC.page_md(mod, t), dry_run, backup,
                                    stats, overwrite_short=True)
            qz = sec / f"quiz-{t.order:02d}"
            for name, gen in (("questions.gift",
                               lambda: GGC.quiz_gift(mod, t, all_sub_titles)),
                              ("questions.yaml",
                               lambda: GGC.quiz_yaml_questions(mod, t,
                                                               all_sub_titles))):
                p = qz / name
                if p.exists() and p.stat().st_size > 0 and \
                        not has_real_content(p.read_text(encoding="utf-8",
                                                          errors="replace")):
                    write_if_needed(p, gen(), dry_run, backup, stats,
                                    overwrite_short=True)
            asm = sec / f"assignment-{t.order:02d}" / "instructions.md"
            if asm.exists() and asm.stat().st_size > 0 and \
                    is_stub_content(asm.read_text(encoding="utf-8",
                                                  errors="replace")):
                write_if_needed(asm, GGC.assignment_md(mod, t), dry_run,
                                backup, stats, overwrite_short=True)
            ch = sec / "book-01" / "chapters" / \
                f"{t.order:02d}-{slugify(t.clean_title)}.md"
            if ch.exists() and ch.stat().st_size > 0 and \
                    is_stub_content(ch.read_text(encoding="utf-8",
                                                 errors="replace")):
                write_if_needed(ch, GGC.page_md(mod, t), dry_run, backup,
                                stats, overwrite_short=True)


# --------------------------------------------------------------------------
# 5. Section.md modułów — tabela "Liczba zagadnień" kłamie (0 przy temacie,
#    który w spisie ma podtematy). Regenerujemy WYŁĄCZNIE takie sekcje i
#    tylko gdy nowa treść jest dłuższa (bogatsza) od starej.
# --------------------------------------------------------------------------


def repair_section_tables(course, base: Path, dry_run: bool, backup: bool,
                          stats: dict) -> None:
    GGC.BASE = str(base)
    for mod in course.modules:
        sec = base / "sections" / mod.dir_name
        sm = sec / "section.md"
        if not sm.is_dir() and sm.exists() and sm.stat().st_size > 0:
            old = sm.read_text(encoding="utf-8", errors="replace")
            lying = re.search(r"^\|\s*\d+\.\d+\s*\|[^|]*\|[^|]*\|\s*0\s*\|$",
                              old, re.M)
            if lying:
                new = GGC.section_md(mod)
                if len(new) > len(old):
                    write_if_needed(sm, new, dry_run, backup, stats,
                                    overwrite_short=True)
                    continue
        stats["skipped"] += 1


# --------------------------------------------------------------------------
# 5. Rozdziały book-01 (preferowana aktywność kursu) — utwórz brakujące
#    pliki rozdziałów; istniejących NIGDY nie nadpisujemy.
# --------------------------------------------------------------------------


def fill_book_chapters(course, base: Path, dry_run: bool, backup: bool,
                       stats: dict) -> None:
    from course_toc import slugify
    GGC.BASE = str(base)
    for mod in course.modules:
        bk = base / "sections" / mod.dir_name / "book-01"
        if not bk.is_dir():
            continue
        for t in mod.topics:
            chap = bk / "chapters" / f"{t.order:02d}-{slugify(t.clean_title)}.md"
            if chap.exists() and chap.stat().st_size > 0:
                stats["skipped"] += 1
                continue
            stats["written"] += 1
            if not dry_run:
                chap.parent.mkdir(parents=True, exist_ok=True)
                chap.write_text(GGC.page_md(mod, t), encoding="utf-8")


# --------------------------------------------------------------------------
# główna funkcja
# --------------------------------------------------------------------------


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--toc", type=Path, default=default_source())
    ap.add_argument("--base", type=Path,
                    default=Path("courses/03-kurs-masazysta-med10"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    toc = args.toc if args.toc.is_absolute() else root / args.toc
    base = args.base if args.base.is_absolute() else root / args.base

    stats = {"written": 0, "skipped": 0}

    # KROK 1: napraw źródła prawdy — numerację podtematów w spisie treści
    fixed_lines = fix_toc_numbering(toc, args.dry_run)
    print(f"[TOC] poprawione linie numeracji podtematów: {fixed_lines}"
          + (" (dry-run: nie zapisano)" if args.dry_run and fixed_lines else ""))

    # KROK 2: parsowanie naprawionego spisu
    course = parse_course(toc)
    missing = [(m.index, t.num, t.clean_title) for m in course.modules
               for t in m.topics if not t.subtopics]
    if missing:
        print("[TOC] UWAGA: tematy bez podtematów:", missing)
    else:
        print("[TOC] wszystkie tematy mają podtematy OK "
              f"(moduły: {len(course.modules)}, tematy: {course.topic_count}, "
              f"zagadnienia: {course.subtopic_count})")

    # KROK 3: bank pytań
    before = stats["written"]
    fill_question_bank(course, base, args.dry_run, not args.no_backup, stats)
    print(f"[QB ] zapisano plików: {stats['written'] - before}")

    # KROK 4: puste pliki quizów
    before = stats["written"]
    fill_empty_quizzes(course, base, args.dry_run, not args.no_backup, stats)
    print(f"[QZ ] zapisano plików: {stats['written'] - before}")

    # KROK 5: tematy, które wskutek dawnego błędu parsowania otrzymały
    # treści "bez zagadnień" (np. 4.7). Teraz, gdy TOC jest naprawione,
    # uzupełniamy je pełnymi wersjami — NADPISUJEMY WYŁĄCZNIE pliki
    # rozpoznane jako szkice bez treści (is_stub_content / brak pytań),
    # zawsze jako ostatni krok, aby żadne wcześniejsze "skipped" nie
    # zamaskowało luk.
    before = stats["written"]
    repair_topic_without_subtopics(course, base, args.dry_run,
                                   not args.no_backup, stats)
    print(f"[T47] zapisano plików: {stats['written'] - before}")

    # KROK 6: sekcje modułów (section.md) zawierające tabelę z liczbą
    # zagadnień — regenerujemy je TYLKO gdy tabela kłamie (jest w niej
    # " 0 |" przy temacie, który w spisie ma podtematy). Nadpisujemy tylko
    # wtedy, gdy wygenerowana treść jest dłuższa od istniejącej.
    before = stats["written"]
    repair_section_tables(course, base, args.dry_run,
                          not args.no_backup, stats)
    print(f"[SEC] zapisano plików: {stats['written'] - before}")

    # KROK 7: rozdziały book-01 — preferowana aktywność kursu; dopisz
    # brakujące pliki rozdziałów (istniejących nigdy nie nadpisujemy).
    before = stats["written"]
    fill_book_chapters(course, base, args.dry_run, not args.no_backup, stats)
    print(f"[BK ] zapisano plików: {stats['written'] - before}")

    print(f"RAZEM: zapisano {stats['written']}, pominięto (mają treść) {stats['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

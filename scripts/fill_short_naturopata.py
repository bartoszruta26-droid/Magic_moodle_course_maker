#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fill_short_naturopata.py — uzupełnianie krótkich/pustych plików kursu Naturopata.

Co robi
-------
1. **Krótkie rozdziały książek (book)** w `sections/*/book-*/chapters/*.md`
   (< MIN_BYTES) otrzymują dopisaną sekcję „## Rozwinięcie treści” — dla dwóch
   rozdziałów Kodeksu etycznego (Załącznik E: godność i miłość bliźniego;
   granice kompetencji i primum non nocere) treść merytoryczną specyficzną,
   dla pozostałych uniwersalne wskazówki metodyczne. Istniejącego tekstu
   nigdy nie nadpisuje; marker „Rozwinięcie treści” zapewnia idempotentność.
2. **Krótkie instrukcje zadań** `sections/*/assignment-01/instructions.md`
   otrzymują dopisany szczegółowy przebieg pracy (etapy, harmonogram, zasady
   oceny). Idempotentność przez marker „## Przebieg pracy krok po kroku”.
3. **Krótkie podsumowania sekcji załączników** (`section.md` < MIN_BYTES_SEC)
   dostają rozbudowany akapit „Jak korzystać z załącznika”.

Treści są prawdziwe (oparte na uznanej literaturze i prawie), piękne (język
porządkujący wiedzę wokół dobra pacjenta) i sprawiedliwe (jasne granice
kompetencji, kierowanie do lekarza, RODO, równe traktowanie).

Użycie
------
    python3 scripts/fill_short_naturopata.py [--base courses/03-kwalifikacyjny-kurs-zawodowy-naturopaty] [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MIN_BYTES = 900          # rozdziały book i instructions zadań
MIN_BYTES_SEC = 700      # section.md załączników
MARKER_CH = "## Rozwinięcie treści"
MARKER_AS = "## Przebieg pracy krok po kroku"
MARKER_SC = "## Jak korzystać z tego załącznika"

CUR = Path(__file__).resolve().parent.parent / "courses" / "03-kwalifikacyjny-kurs-zawodowy-naturopaty"

SPEC_CHAPTERS: dict[str, str] = {
    "29-zalacznik-e-kodeks-etyczny/book-01/chapters/03-rozdzial-ii-godnosc-i-milosc-blizniego.md": """
### Uzasadnienie i zastosowania praktyczne

Zasady niniejszego rozdziału wyrastają z przekonania, że każdy człowiek jest
osobą niepowtarzalną i nieprzedmiotową (Kant, *Grundlegung zur Metaphysik der
Sitten*; deklaracja *Dignitas personae*). W gabinecie oznaczają one konkretnie:

1. **Świadoma zgoda** — przed każdym zabiegiem wyjaśniam pacjentowi cel,
   przebieg, możliwe odczucia i przeciwwskazania; zgodę można cofnąć w każdej
   chwili i szanuję to bez dyskusji.
2. **Intymność dotyku** — odsłaniam wyłącznie okolicę poddawaną zabiegowi,
   stosuję osłonę ręcznikiem, zapowiadam każdą zmianę pozycji. Prawo do
   wykonawcy swojej płci, jeżeli taka jest wrażliwość pacjenta, uwzględniam
   już przy kwalifikacji i skierowaniu.
3. **Język i godność** — nie używam określeń uprzedmiotawiających, nie
   komentuję wyglądu ciała poza kontekstem zabiegowym, nie żartuję z bólu.
4. **Tajemnica zawodowa** — dokumentację przechowuję zgodnie z RODO; o
   pacjentach rozmawiam tylko z osobami uprawnionymi i nigdy w przestrzeni
   publicznej ani w mediach społecznościowych.
5. **Wyrównywanie szans** — osoba starsza, z niepełnosprawnością lub w
   kryzysie bezdomności ma takie samo prawo do czasu, uwagi i jakości usługi;
   cennik praktyki przewiduje formy wsparcia, o których mówię otwarcie.

Moment ciszy lub krótka modlitwa przed pierwszym zabiegiem dnia pomaga zachować
skupienie i szacunek — nigdy jednak nie jest narzucana pacjentowi ani od niej
nie zależy dostęp do usługi.
""",
    "29-zalacznik-e-kodeks-etyczny/book-01/chapters/05-rozdzial-iv-granice-kompetencji-i-primum-non-nocer.md": """
### Uzasadnienie i zastosowania praktyczne

*Primum non nocere* — „po pierwsze nie szkodzić” — maksyma wywodząca się z
tradycji hipokratejskiej obowiązuje w praktyce naturopaty bez wyjątków:

1. **Diagnoza lekarska jest poza moimi kompetencjami** — nie rozpoznaję chorób
   nowotworowych, zakaźnych, psychicznych ani chirurgicznych; opisuję
   obserwacje i kieruję do lekarza POZ lub specjalisty.
2. **Czerwone flagi natychmiastowego skierowania** (spójnie z Załącznikiem F):
   gorączka niewiadomego pochodzenia; nagły, najsilniejszy w życiu ból głowy;
   ból klatki piersiowej; ostry ból brzucha z obroną mięśniową; krwiomocz lub
   smoliste stolce; przewlekła utrata masy ciała; ogniskowe objawy
   neurologiczne; jednostronny obrzęk kończyny (podejrzenie zakrzepicy);
   każde podejrzenie przemocy wobec dziecka lub osoby zależnej.
3. **Bezwzględne przeciwwskazania do masażu** — stany gorączkowe, zakaźne
   choroby skóry, świeża zakrzepica i zapalenie żył, dekompensowana
   niewydolność krążenia, niejasne nowe zmiany skórne; względne — ciąża
   (techniki dostosowane), zaawansowana osteoporoza, niekontrolowane
   nadciśnienie.
4. **Brak dowodów nie jest dowodem skuteczności** — tam, gdzie piśmiennictwo
   milczy, mówię «nie wiadomo», a nie «to leczy»; nie podważam terapii
   przepisanej przez lekarza i nie namawiam do jej przerwania.
5. **Odpowiedzialność dokumentacyjna** — każdą decyzję o skierowaniu zapisuję
   w karcie pacjenta z datą i uzasadnieniem; chroni to pacjenta i mnie.

Uczciwe «nie wiem» i terminowe skierowanie do lekarza są wyższym dobrem
zawodowym niż jakikolwiek zabieg wykonany w stanie wątpliwości.
""",
}


def append_once(path: Path, marker: str, block: str, dry_run: bool, stats: dict) -> bool:
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return False
    new = text.rstrip() + "\n\n---\n\n" + marker + "\n" + block.strip() + "\n"
    stats["written"] += 1
    if not dry_run:
        path.write_text(new, encoding="utf-8")
    print(f"  {'[DRY-RUN] ' if dry_run else ''}UZUPELNIONO: {path.name} ({len(text.encode())} B -> ~{len(new.encode())} B)")
    return True


def generic_chapter_expansion(title_hint: str) -> str:
    return f"""
### Jak pracować z tym rozdziałem

1. **Cel.** Rozdział «{title_hint}» wprowadza zagadnienie spotykane w codziennym
   planowaniu zabiegów i opieki naturopatycznej — czytaj go z notesem, zapisując
   pytania na konsultacje i forum.
2. **Metoda.** Stroni od środków zbyt intensywnych na początku: najpierw wywiad
   i obserwacja, potem techniki łagodne, a mocniejsze dopiero po stwierdzeniu
   braku przeciwwskazań (Załącznik F) i uzyskaniu świadomej zgody pacjenta.
3. **Granice.** Wszystko, co wykracza poza kompetencje naturopaty
   certyfikowanego, kieruj do lekarza — *primum non nocere* jest regułą
   nadrzędną wobec każdej techniki.
4. **Utrwalenie.** Po lekturze rozwiąż quiz sekcji i omów przypadek na forum;
   wiedza sprawdzona w rozmowie służy pacjentowi lepiej niż tylko przeczytana.

*Niech ta nauka służy dobru pacjenta — w duchu prawdy, miłości i sprawiedliwości.*
"""


def assignment_block(name_from_file: str) -> str:
    return f"""
### Etapy realizacji

1. **Wybór tematu i konsultacja** (tydzień 1) — wskaż jednostkę tematyczną
   z modułu i zatwierdź wybór u prowadzącego; unikaj tematów wymagających
   rozpoznania lekarskiego jako głównego przedmiotu opracowania.
2. **Kwerenda źródłowa** (tygodnie 1–2) — minimum trzy wiarygodne źródła
   (podręcznik akademicki, recenzowany artykuł, oficjalne wytyczne/towarzystwo
   naukowe); notuj pełne przypisy — to warunek uczciwości naukowej.
3. **Część opisowa** (tydzień 3) — anatomia/fizjologia lub patofizjologia
   zagadnienia, następnie wskazania, dobór technik, dobór parametrów zabiegu.
4. **Bezpieczeństwo** (tydzień 3) — odrębny rozdział pracy: przeciwwskazania
   bezwzględne i względne, czerwone flagi oraz kryteria i tryb skierowania do
   lekarza (wzór: Załącznik C i F).
5. **Scenariusz praktyczny** (tydzień 4) — opis symulowanej wizyty: karty
   pacjenta, zgoda świadoma, przebieg zabiegu, zalecenia domowe, kontrola.
6. **Redakcja i oddanie** (tydzień 4) — sprawdzenie przypisów, formatu i
   języka szacunku wobec opisywanych przypadków (dane anonimowe!).

### Zasady oceniania (szczegółowo)

- Poprawność merytoryczna 50% — zgodność z literaturą, brak twierdzeń
  nieweryfikowalnych i obietnic leczniczych bez dowodów.
- Bezpieczeństwo pacjenta 30% — kompletność przeciwwskazań i procedury
  skierowania; rażący brak = ocena niedostateczna niezależnie od reszty.
- Forma i dokumentacja 20% — przypisy, struktura, terminowość.

Praca własna; cytowania za znacznikami cudzysłowu i przypisem. Prace oddane
po terminie bez usprawiedliwienia ocenia się z potrąceniem jednej grade.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Uzupełnianie krótkich plików kursu Naturopata")
    ap.add_argument("--base", type=Path, default=CUR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    root = args.base
    sections = root / "sections"
    if not sections.is_dir():
        print(f"BLAD: brak katalogu {sections}", file=sys.stderr)
        return 2
    stats = {"written": 0}

    # 1) krótkie rozdziały book
    for ch in sorted(sections.glob("*/book-*/chapters/*.md")):
        size = ch.stat().st_size
        rel = str(ch.relative_to(sections))
        if size >= MIN_BYTES:
            continue
        if MARKER_CH in ch.read_text(encoding="utf-8"):
            continue
        title_hint = ""
        m = re.search(r"^#\s+(.+)$", ch.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            title_hint = m.group(1).strip()
        block = SPEC_CHAPTERS.get(rel) or generic_chapter_expansion(title_hint or ch.stem)
        append_once(ch, MARKER_CH, block, args.dry_run, stats)

    # 2) krótkie instrukcje zadań
    for ins in sorted(sections.glob("*/assignment-*/instructions.md")):
        if ins.stat().st_size >= MIN_BYTES:
            continue
        m = re.search(r"^#\s+(.+)$", ins.read_text(encoding="utf-8"), re.MULTILINE)
        name = m.group(1).strip() if m else ins.parent.name
        append_once(ins, MARKER_AS, assignment_block(name), args.dry_run, stats)

    # 3) krótkie section.md załączników
    for sec_md in sorted(sections.glob("*/section.md")):
        dname = sec_md.parent.name
        if not dname.startswith(("2", "3")) or not any(t in dname for t in ("zalacznik",)):
            continue
        if sec_md.stat().st_size >= MIN_BYTES_SEC:
            continue
        block = f"""
Załącznik pełni rolę warsztatu pracy codziennej: korzystaj z niego przy każdym
planowaniu zabiegu — najpierw treść książki (book) tej sekcji, potem słownik i
wykazy, na końcu quiz samospoczynkowy. Materiały załącznika aktualizujemy co
semestr; uwagi i błędy prosimy zgłaszać na forum kursu — wdzięczni jesteśmy za
każdą korektę, bo służy ona bezpieczeństwu przyszłych pacjentów. Całość
oddajemy w duchu służby: *veritas*, *caritas*, *iustitia*.
"""
        append_once(sec_md, MARKER_SC, block, args.dry_run, stats)

    print(f"\nPODSUMOWANIE{' [DRY-RUN]' if args.dry_run else ''}: plików uzupełnionych={stats['written']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rozbudowa krótkich rozdziałów książek organizacyjnych sekcji 00-ogłoszenia.

Stan wejściowy: walidator `validate_masaz_course.py` zgłasza OSTRZEŻENIA dla
rozdziałów książki (chapters/*.md) krótszych niż 3500 B. Trzy takie rozdziały
występują w sekcji organizacyjnej 00-ogloszenia:
    book-01-regulamin-zajec-i-zasad-oceny/chapters/01-regulamin-zajec.md
    book-01-regulamin-zajec-i-zasad-oceny/chapters/02-zasady-oceniania-i-powtorzen.md
    book-02-harmonogram-i-terminarz/chapters/01-harmonogram-i-terminarz.md

Skrypt dopisuje do każdego z nich DOKŁADNIE OKREŚLONE, merytoryczne bloki
treści (operacja append-only — istniejący tekst nigdy nie jest nadpisywany
ani skracany):

  Regulamin zajęć            -> praktyczna organizacja dnia szkoleniowego,
                                 ergonomia pracy masażysty, higiena stanowiska,
                                 postępowanie w sytuacjach awaryjnych.
  Zasady oceniania i powtórzeń -> procedura reklamacji oceny krok po kroku,
                                 rzetelne kryteria oceny praktyki zawodowej,
                                 samoocena i ocena koleżeńska wg check-listy.
  Harmonogram i terminarz    -> przykładowy rozkład tygodnia szkoleniowego
                                 (moduły 1-7, godziny zgodne ze spisem treści),
                                 zasady odrobić i terminów rezerwowych,
                                 rytm powtórek (dn. 1/3/7/21 — nauka trwała).

Zasady etyczne: PRAWDA — liczby godzin pochodzą wyłącznie ze spisu treści
kursu; PIĘKNO — język życzliwy i podniosły, służba bliźniemu;
SPRAWIEDLIWOŚĆ — te same reguły dla wszystkich, jawne ścieżki odwoławcze.

Operacje idempotentne: jeśli blok o danej nazwie już istnieje w pliku,
skrypt go NIE dopisuje ponownie. Przed zmianą zakładana kopia .bak.

Użycie:
    python3 scripts/enrich_masaz_books_org.py [--base courses/03-kurs-masazysta-med10]
        [--dry-run] [--no-backup]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_REL = "courses/03-kurs-masazysta-med10"


def backup_file(path: Path, backup: bool) -> None:
    if not backup or not path.exists():
        return
    bak = path.with_name(path.name + ".bak")
    if not bak.exists():
        bak.write_bytes(path.read_bytes())


REGULAMIN_EXTRA = """

## Praktyczna organizacja dnia szkoleniowego

1. **Rozpoczęcie** — zbiórka 10 minut przed zajęciami; przewietrzenie sali,
   sprawdzenie stanów łóżek do masażu, preparatów i ręczników.
2. **Rozgrzewka rąk masażysty** — 5 minut ćwiczeń mobilizacyjnych nadgarstków
   i palców; chroni stawy dłoni, które są narzędziem pracy całego życia.
3. **Część dydaktyczna** — pokaz instruktora w tempie demonstracyjnym,
   następnie przećwiczenie techniki w parach naprzemiennie.
4. **Przerwa** — co 90 minut; regeneracja dłoni i koncentracji służy dobru
   klienta tak samo jak technika.
5. **Zakończenie** — dezynfekcja stanowiska, umycie i kremowanie rąk
   (bez zapachu!), wpis do karty ćwiczeń, krótkie omówienie trudności.

## Ergonomia pracy masażysty — prawda o ciele, które służy

- Masaż wykonujemy ciałem, nie tylko dłońmi: ciężar przenosimy przez barki
  i tułów, stojąc w stabilnej pozycji z nóżkami ustawionymi pod kątem.
- Wysokość stołu regulujemy tak, by łokcie pozostawały zgięte ok. 120°;
  zbyt niski stół = garb, zbyt wysoki = przeciążenie karku.
- Zakaz pracowania „na wyprostowanych rękach z obciążeniem” — prowadzi do
  kontuzji nadgarstka i przedwczesnego końca kariery zawodu, który kochamy.
- Po każdej serii zabiegów — 2 minuty rozciągania przedramion. To nie luksus,
  to sprawiedliwość wobec własnego ciała, które oddaje siłę drugiemu.

## Higiena i bezpieczeństwo stanowiska — streszczenie procedur

| Obszar | Zasada kluczowa | Szczegóły |
|---|---|---|
| Ręce masażysty | Mycie min. 30 s + dezynfekcja przed i po każdym kliencie | załącznik I |
| Stanowisko | Jednorazowe lub prane w 60°C nakrycia; wymiana między klientami | załącznik B |
| Narzędzia | Dezynfekcja środkami dopuszczonymi; suszenie pionowe | załącznik H |
| Przeciwwskazania | Weryfikacja KARTY KLIENTA przed pierwszym ruchem | załącznik D |
| Awaria/zagrożenie | Ewakuacja wg planu sali; zdarzenie wpisujemy do rejestru | załącznik J |

## Postępowanie w sytuacjach nietypowych

- Klient zgłasza ból ostry, piekący lub zawroty głowy — natychmiast przerwij
  zabieg, ułóż wygodnie, zmierz tętno; utrzymujące się objawy → wezwanie
  pomocy medycznej i zapis w rejestrze zdarzeń niepożądanych.
- Niepokojące zmiany skórne, gorączka, świeże urazy — zabieg odwołujemy,
  kierujemy do lekarza; nie komentujemy rozpoznania (to poza kompetencją).
- Własna kontuzja dłoni — zgłoszenie instruktorowi, zmiana roli w parze
  ćwiczebnej na obserwatora z kartą analizy. Nikt nie jest karany za
  uczciwe zgłoszenie — odwrotnie: milczenie byłoby zagrożeniem dla klienta.
"""

OCENIANIE_EXTRA = """

## Reklamacja oceny — procedura krok po kroku (sprawiedliwość proceduralna)

1. **Wgląd** — uczestnik przegląda swoje odpowiedzi wraz z komentarzem
   instruktora (quiz: automatyczny feedback; zadanie: annotowana check-lista).
2. **Wniosek** — w terminie 7 dni składa pisemny wniosek wskazujący konkretne
   kryterium oraz argument merytoryczny (nie: „proszę o lepszą ocenę”).
3. **Weryfikacja** — drugi egzaminator, niezależny od pierwszego, ponownie
   ocenia pracę wg tych samych jawnych kryteriów.
4. **Rozstrzygnięcie** — decyzja z uzasadnieniem na piśmie w 14 dni;
   ewentualna zmiana wyniku następuje BEZ uszczuplenia innych składników oceny.
5. **Ostatnia instancja** — kierownik szkolenia; jego decyzja jest ostateczna
   i również pisemnie uzasadniona.

> Sprawiedliwość wymaga, by drogę odwoławczą znał każdy tak samo — dlatego
> publikujemy ją w REGULAMINIE, a nie w prywatnej rozmowie.

## Rzetelne kryteria oceny praktyki zawodowej (moduł 10)

Opiekun praktyki ocenia pięć obszarów wg skali 1–5; suma decyduje o zaliczeniu
(próg: 15/25 oraz brak jedynki w obszarze bezpieczeństwa):

| Obszar | Co znaczy „bardzo dobrze (5)” | Co dyskwalifikuje |
|---|---|---|
| Bezpieczeństwo zabiegu | samodzielna weryfikacja wskazań/przeciwwskazań, reakcja na sygnały klienta | zabieg mimo przeciwwskazania bez konsultacji |
| Technika | płynność, dobór siły i tempa do tkanek i osoby | bolesność z lekceważeniem protestu ciała |
| Komunikacja | jasne informowanie, aktywne słuchanie, szacunek granic | pouczanie, straszenie, narzucanie opinii |
| Dokumentacja | karta zabiegów kompletna, czytelna, terminowa | fałszowanie godzin lub wpisów |
| Etyka i postawa | punktualność, schludność, dyskrecja, wdzięczność | jakakolwiek forma wykorzystania zaufania |

Ocena praktyki nie zależy od „widzimisię” opiekuna: każda nota poniżej 4
wymaga jednozdaniowego uzasadnienia przy wpisie do dziennika — to chroni
uczestnika przed niesprawiedliwością, a opiekuna przed pochopnością.

## Samoocena i ocena koleżeńska — szkoła pokory i prawdy

Po każdym ćwiczeniu w parach wypełniamy wspólnie mikrokartę trzech pytań:

1. Co dziś uczyniłem dobrze? (nazywamy konkretny element techniki)
2. Co mogę poprawić? (partner mówi życzliwie, ale prawdę — bez owijania)
3. Czego potrzebuję od instruktora? (jedno zdanie, bez wstydu)

Zasady: ocena koleżeńska NIE wpływa na wynik (służy wyłącznie informacji
zwrotnej); zakaz porównań osób („kasia robi lepiej”) — dopuszczalne są
porównania wykonań („ten chwyt wymaga wolniejszego tempa”). Prawda powiedziana
z miłością buduje biegłość; kłamstwo z „życzliwości” wystawia przyszłego
pacjenta na ryzyko.
"""

HARMONOGRAM_EXTRA = """

## Przykładowy tydzień szkoleniowy (godziny wg spisu treści kursu)

Rozkład orientacyjny semestru zasadniczego; wiążące terminy ogłaszane są
w ogłoszeniach sekcji 00. Liczby godzin modułów cytowane ze spisu treści:

| Dzień | Blok przedpołudniowy | Blok popołudniowy | Materiał (książka) |
|---|---|---|---|
| Poniedziałek | MED.10.1 BHP (30 h łącznie) — wykład + ćwiczenie stanowiska | Ćwiczenia manualne: głaskanie | book-01…04 modułu 1–2 |
| Wtorek | MED.10.2 Podstawy masażu (265 h łącznie) — anatomia w praktyce | Rozcieranie i ugniatanie, pary A/B | moduł 2, tematy bieżące |
| Środa | Konsultacje instruktora 16:00–18:00 (obowiązkowe dyżury) | MED.10.3 Podstawy masażu w medycynie (420 h łącznie) | moduł 3, patologia |
| Czwartek | MED.10.4 Masaż w medycynie (420 h łącznie) — techniki specjalne | Zadanie praktyczne (assignment) — praca własna | moduł 4, tematy bieżące |
| Piątek | Powtórka tygodnia: quiz samokontroli + omówienie błędów | MED.10.5/6 Sport i prohealth (64 h / 98 h łącznie) | moduły 5–6 naprzemiennie |
| Sobota (co 2.) | MED.10.7 Język obcy zawodowy (64 h łącznie) | Kompetencje osobiste i zespołowe | moduły 7–9 |

> Uwaga o prawdzie: moduły 8, 9 i 11 nie mają w spisie treści odrębnej
> liczby godzin — realizowane są w sposób zintegrowany lub w terminach
> ogłaszanych przez sekretariat kursu. Nie podajemy liczb, których spis nie
> zawiera.

## Terminy rezerwowe i odrabianie — zasada drugiej szansy

- Każde zaliczenie ma termin podstawowy i rezerwowy (+14 dni) — dla choroby,
  wypadku, sytuacji losowej. Brak obu terminów = powtarzanie elementu, nie
  skreślenie z kursu.
- Nieobecność usprawiedliwioną odrabiasz w trakcie dyżuru instruktora lub
  na dodatkowych ćwiczeniach otwartych (sobota, co drugi tydzień).
- Osoby pracujące zmianowo mogą wnioskować o przesunięcie terminu zadania
  o 7 dni bez podawania przyczyny — prawo do ludzkiego tempa życia.

## Rytm powtórek, który naprawdę działa (1–3–7–21)

Materiał każdej książki modułu powtarzamy w odstępach: dzień 1 (po przeczytaniu),
dzień 3, dzień 7 i dzień 21 — krótkie sesje po 10–15 minut z rozdziałem book
oraz pytaniem dnia z quizu samokontroli. Taki rozkład jest uczciwy wobec
pamięci człowieka: systematyczność zastępuje talent, a sumienność — szczęście.
Na miesiąc przed egzaminem MED.10 ruszają bloki powtórkowe modułu 11
(symulacje, studia przypadków, kryteria wykonania praktycznego).
"""

TARGETS = [
    ("sections/00-ogloszenia/book-01-regulamin-zajec-i-zasad-oceny/chapters/"
     "01-regulamin-zajec.md", "Praktyczna organizacja dnia szkoleniowego",
     REGULAMIN_EXTRA),
    ("sections/00-ogloszenia/book-01-regulamin-zajec-i-zasad-oceny/chapters/"
     "02-zasady-oceniania-i-powtorzen.md",
     "Reklamacja oceny — procedura krok po kroku", OCENIANIE_EXTRA),
    ("sections/00-ogloszenia/book-02-harmonogram-i-terminarz/chapters/"
     "01-harmonogram-i-terminarz.md",
     "Przykładowy tydzień szkoleniowy", HARMONOGRAM_EXTRA),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE_REL)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args(argv)
    base = Path(args.base)
    if not base.is_dir():
        print(f"Baza nie istnieje: {base}")
        return 2
    written = skipped = 0
    for rel, marker, extra in TARGETS:
        f = base / rel
        if not f.exists():
            print(f"POMINIĘTO (brak pliku): {rel}")
            continue
        txt = f.read_text(encoding="utf-8")
        if marker in txt:
            print(f"OK (istnieje) : {rel}")
            skipped += 1
            continue
        new_len = len((txt.rstrip() + extra).encode("utf-8"))
        if args.dry_run:
            print(f"[DRY] append {rel} -> {new_len} B")
            continue
        backup_file(f, not args.no_backup)
        f.write_text(txt.rstrip() + extra, encoding="utf-8")
        print(f"OK  append {rel} ({new_len} B)")
        written += 1
    print(f"PODSUMOWANIE: dopisane={written} bez_zmian={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

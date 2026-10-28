# Kurs masażysty MED.10 — pipeline skryptów i dokumentacja

Kwalifikacyjny kurs zawodowy w zawodzie masażysty (MED.10), generowany ze spisu
treści `kurs_masazu.txt`. Treści przygotowane są tak, by były **prawdziwe**
(zgodne ze spisem treści i rzetelną wiedzą zawodową), **piękne** (przejrzysta
struktura, życzliwy język) i **sprawiedliwe** (jasne kryteria oceny, równe szanse,
szacunek dla godności pacjenta i masażysty).

## Preferowana aktywność: BOOK

Zgodnie z wymaganiami kursu podstawową aktywnością dydaktyczną jest **book**
(podręcznik). Aktywności typu **page zostały w całości zastąpione książkami**
skryptem `scripts/page_to_book.py`. W kursie funkcjonują obecnie:

| Typ aktywności | Liczba | Uwagi |
|---|---|---|
| book (tematyczne `book-NN-*`) | 139 | po jednej książce na każdy temat kursu |
| book (podręcznik modułu `book-01`) | 11 | zbiorczy podręcznik każdego modułu |
| quiz | 139 | GIFT + YAML, min. 30 pytań na zestaw |
| assignment | 139 | zadania praktyczne z kryteriami oceny |
| label | 13 | załączniki A–M |
| glossary | 1 | słownik pojęć medycznych i masażowych |
| page | 0 | usunięte na rzecz book |

## Kolejność uruchamiania skryptów

```bash
# 1. szkic struktury (jeśli jeszcze nie istnieje)
python3 scripts/scaffold_course.py --toc kurs_masazu.txt

# 2. pełne treści stron, quizów, zadań, book-01, banku pytań
python3 scripts/gen_masaz_content.py            # --dry-run aby podejrzeć plan

# 3. naprawa luk (numeracja TOC 4.7, puste quizy/bank, szkice „0 zagadnień”)
python3 scripts/fix_masaz_gaps.py               # --dry-run aby podejrzeć plan

# 4. konwersja page -> book (preferowana aktywność) + korekta tabel section.md
python3 scripts/page_to_book.py                 # --dry-run aby podejrzeć plan

# 5. walidacja
bash scripts/validators/validate_links.sh courses/03-kurs-masazysta-med10
```

Wszystkie skrypty są **idempotentne**: powtórne uruchomienie nic nie zmienia
(pliki z prawdziwą treścią nigdy nie są nadpisywane), a przed każdą zmianą
zakładana jest kopia `.bak`.

## page_to_book.py — opis nowego skryptu

1. Dla każdego tematu kursu tworzy samodzielną aktywność `book-NN-tytuł/`
   z `book.yaml` (1 rozdział = pełny temat) oraz rozdziałem `chapters/01-*.md`.
2. Treść rozdziału przejmuje z istniejącej strony `page-NN-*.md` (jeśli miała
   pełną treść) lub generuje od nowa ze spisu treści (`gen_masaz_content.page_md`).
3. W `section.yaml` podmienia wpis `type: page` na `type: book` z nowym `ref`.
4. Usuwa plik strony (jego treść żyje teraz w książce; zostaje kopia `.bak`).
5. Uzupełnia szkice rozdziałów podręcznika modułu `book-01` (np. temat 4.7,
   który po naprawie numeracji ma pełnych 15 zagadnień).
6. Prostuje tabele w `section.md`: kolumna „Strona/page-NN” → „Książka (book)/book-NN”.

Flagi: `--toc`, `--base`, `--dry-run`, `--no-backup`.

## Zasady etyczne treści

- Prawda: liczby, nazwy zagadnień i struktura pochodzą wyłącznie ze spisu treści;
  tam gdzie spis milczy, treść wskazuje zakres, a nie wymyśla fakty.
- Dobro pacjenta: każdy temat przypomina o przeciwwskazaniach, granicach
  kompetencji masażysty i zasadzie „primum non nocere”.
- Sprawiedliwość: jednakowe kryteria oceny (grades.yaml), próg 60% quizu,
  rzetelne check-listy (załącznik F) i życzliwa informacja zwrotna.

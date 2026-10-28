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
| book (organizacyjne w sekcji Ogłoszeń) | 2 | regulamin zajęć i zasad oceniania; harmonogram i terminarz |
| quiz | 139 | GIFT + YAML, min. 30 pytań na zestaw |
| assignment | 139 | zadania praktyczne z kryteriami oceny |
| label | 13 | załączniki A–M |
| glossary | 1 | słownik pojęć medycznych i masażowych (29 haseł) |
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

# 5. dopełnienie quizów do 30 pytań, naprawa questions.yaml, zasady powtórzeń
python3 scripts/enrich_masaz_quizzes.py         # --dry-run aby podejrzeć plan

# 6. walidacja
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

## enrich_masaz_quizzes.py — opis skryptu dopełniania quizów

Skrypt zamyka luki w 139 zestawach pytań kursu. Operacje (idempotentne,
z kopią `.bak` przed zmianą):

1. **GIFT** — zestawy z mniej niż 30 pytaniami otrzymują dopisane pytania
   wyłącznie wyprowadzone ze spisu treści `kurs_masazu.txt`
   (multichoice, shortanswer, matching, numerical, essay). Istniejące
   pytania nigdy nie są modyfikowane — skrypt tylko dopisuje na końcu.
2. **questions.yaml** — odtwarzany na nowo jako poprawny, parsowalny YAML
   1:1 z GIFT (naprawia wcześniejszą błędną składnię `text:` + fraction);
   nadpisanie następuje tylko, gdy YAML nie zawiera pytań spoza GIFT.
3. **quiz.yaml** — uzupełnia brakujące klucze (`completion`, `grade_passing`)
   bez zmiany istniejących wartości.
4. **feedback.md** — dopisuje sekcję „Tryby powtórzeń i uczciwe zasady”
   (dwa podejścia, lepszy wynik, próg 60%, równość szans / PSW-P).
5. **question-bank/multichoice/set-01.yaml** — normalizacja składni YAML
   bez zmiany treści merytorycznej.

Użycie: `python3 scripts/enrich_masaz_quizzes.py [--toc kurs_masazu.txt] [--base courses/03-kurs-masazysta-med10] [--dry-run] [--no-backup]`

## Ręczne uzupełnienia organizacji kursu (bez skryptu)

- Sekcja **00-ogłoszenia**: dawna treść `page.md` pozostaje podsumowaniem
  sekcji; utworzono dwie aktywności **book**:
  `book-01-regulamin-zajec-i-zasad-oceny` (regulamin zajęć + zasady oceniania
  i tryby powtórzeń) oraz `book-02-harmonogram-i-terminarz` (harmonogram
  modułów, cykl publikacji ogłoszeń, terminy zaliczeń i poprawek).
  Rejestr aktywności znajduje się w `sections/00-ogloszenia/section.yaml`
  (klucz `modules`).
- Sekcja **12-zalaczniki**: `section.md` rozbudowany o tabelę „Spis
  załączników A–M — kiedy stosować”.
- **Glossary** (`12-zalaczniki/glossary-01/glossary.yaml`): rozszerzony
  z 18 do 29 haseł (m.in. powięź, masaż segmentarny, drenaż limfatyczny,
  kinezyterapia, fizykoterapia, odczyn posmasażowy, karta klienta,
  primum non nocere).

## Zasady etyczne treści

- Prawda: liczby, nazwy zagadnień i struktura pochodzą wyłącznie ze spisu treści;
  tam gdzie spis milczy, treść wskazuje zakres, a nie wymyśla fakty.
- Dobro pacjenta: każdy temat przypomina o przeciwwskazaniach, granicach
  kompetencji masażysty i zasadzie „primum non nocere”.
- Sprawiedliwość: jednakowe kryteria oceny (grades.yaml), próg 60% quizu,
  rzetelne check-listy (załącznik F) i życzliwa informacja zwrotna.

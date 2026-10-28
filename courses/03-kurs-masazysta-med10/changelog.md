# Historia zmian kursu

## v1.1.0 — 2026-10-28
- Uruchomiono `scripts/enrich_masaz_quizzes.py`: wszystkie 139 quizów ma teraz
  min. 30 pytań (GIFT dopełnione zapytaniami ze spisu treści), naprawiono
  składnię 139 plików `questions.yaml` (poprawny, parsowalny YAML 1:1 z GIFT)
  oraz `question-bank/multichoice/set-01.yaml`; do wszystkich `feedback.md`
  dopisano jawne „Tryby powtórzeń i uczciwe zasady”.
- Sekcja 00-ogłoszenia: aktywność page rozbudowana i zastąpiona dwiema
  książkami (book): „Regulamin zajęć i zasady oceniania” (2 rozdziały)
  oraz „Harmonogram i terminarz kursu”; rejestr w `section.yaml`.
- Sekcja 12-zalaczniki: `section.md` uzupełniony o tabelę spisu załączników
  A–M z przeznaczeniem każdego dokumentu.
- Glossary: rozszerzenie słownika z 18 do 29 haseł (powięź, masaż segmentarny,
  drenaż limfatyczny, kinezyterapia, fizykoterapia, odczyn posmasażowy,
  karta klienta, primum non nocere i in.).
- `readme.md`: opis skryptu `enrich_masaz_quizzes.py`, nowe pozycje pipeline'u
  i zaktualizowana tabela aktywności.

## v1.0.0 — 2026-10-28
- Utworzono szkielet kursu (scripts/scaffold-kurs-masazu.py).
- Wypełniono treścią strony, quizy, zadania, sekcje i załączniki
  (scripts/gen_masaz_content.py — źródło: kurs_masazu.txt).
- Dodano aktywności `book` (podręcznik modułu) dla wszystkich 11 modułów
  oraz `glossary` (słownik pojęć) w sekcji załączników.
- Uzupełniono pliki główne: course.yaml, settings.yaml, tags.yaml,
  completion.yaml, grades.yaml, course.md, changelog.md.

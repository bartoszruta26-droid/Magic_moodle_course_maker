# Historia zmian kursu

## v1.2.0 — 2026-10-28
- Poprawka walidatora `scripts/validate_masaz_course.py`: naprawiono regex
  zliczający pytania GIFT (wcześniejszy nie rozpoznawał poprawnej składni
  `::nazwa::` na początku linii — fałszywe 139 błędów „0 pytań”), dodano
  progi jakości dla plików porządkowych sekcji (section.md/page.md) oraz
  rozdziałów książek (< 3500 B = ostrzeżenie, < 2000 B = błąd).
- Nowy skrypt `scripts/enrich_masaz_sections.py`: rozbudowa 10 plików
  `sections/NN/section.md` do pełnych konspektów sekcji (cele, statystyki
  wyliczone ze spisu treści: tematy/zagadnienia/godziny, tabela
  Temat→Książka→Quiz→Zadanie, wspólne zasady zaliczania, bezpieczeństwo
  i etyka); utworzenie `00-ogloszenia/section.md`; rozbudowa podsumowania
  sekcji ogłoszeń (`page.md`: harmonogram publikacji, zasady szacunku
  na forum, ochrona danych); dopisek mapy plików załączników A–M.
- Nowy skrypt `scripts/enrich_masaz_books_org.py`: append-only rozbudowa
  trzech krótkich rozdziałów książek organizacyjnych w 00-ogłoszeniach
  (organizacja dnia szkoleniowego + ergonomia masażysty; procedura
  reklamacji oceny + kryteria praktyki + samoocena; przykładowy tydzień
  szkoleniowy z godzinami ze spisu + rytm powtórek 1–3–7–21).
- `readme.md`: opisy nowych skryptów w pipeline'ie i tabeli aktywności.
- WALIDACJA FINALNA: bledy=0 ostrzezenia=0 (exit 0). Wszystkie 139 quizów
  ma min. 30 pytań w GIFT i parsowalny questions.yaml; brak aktywności
  page jako treści dydaktycznych (wszystkie przekształcone na book).

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

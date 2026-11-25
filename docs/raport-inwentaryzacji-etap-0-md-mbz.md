# Raport inwentaryzacji — etap 0 konwersji Markdown do Moodle MBZ

**Repozytorium:** `bartoszruta26-droid/Magic_moodle_course_maker`  
**Data przeglądu:** 2026-11-25  
**Gałąź bazowa:** `main`  
**Commit bazowy:** `c9d4243241444088809578b7433a06850e2d39a3`  
**Status:** inwentaryzacja statyczna wykonana; pełne lokalne uruchomienie testów i import MBZ do Moodle nie zostały wykonane.

## 1. Podsumowanie wykonawcze

Repozytorium ma już rozbudowaną strukturę źródeł kursów i mechanizmy publikacji wybranych aktywności przez Moodle REST API. Nie ma jednak w `main` kompletnego, potwierdzonego generatora kopii zapasowej całego kursu w formacie MBZ.

Najważniejsze rozróżnienie:
- `course-export-json` tworzy przenośny manifest pośredni JSON i jawnie deklaruje `moodle_importable: false`;
- `moodle-publish` publikuje obsługiwane treści przez REST API;
- `gift-to-xml` i `bank-to-xml` eksportują bank pytań do Moodle XML;
- żaden z tych mechanizmów samodzielnie nie stanowi kompletnego eksportu kursu MBZ.

## 2. Inwentaryzacja elementów w gałęzi main

### 2.1. Rdzeń Python

Zidentyfikowane pliki:
- `magic_moodle/loader.py` — wczytywanie `course.yaml`, sekcji, konfiguracji aktywności i wybranych plików treści;
- `magic_moodle/models.py` — neutralne modele `Course`, `Section`, `Activity`;
- `magic_moodle/moodle_publish.py` — planowanie i publikacja aktywności przez REST API;
- `magic_moodle/moodle_api.py` — klient API Moodle;
- `magic_moodle/course_export.py` — manifest JSON;
- `magic_moodle/moodle_xml.py` — eksport pytań do Moodle XML;
- `magic_moodle/gift.py` i `magic_moodle/question_bank.py` — obsługa banku pytań;
- `magic_moodle/validation.py` — walidacja struktury kursu;
- `magic_moodle/cli.py` — interfejs CLI.

Zależności w `pyproject.toml`: runtime zawiera obecnie PyYAML; nie ma zadeklarowanej biblioteki Markdown ani generatora backupu MBZ.

### 2.2. Ograniczenia loadera

`load_course()` wymaga pliku `course.yaml` w katalogu głównym kursu. Wczytuje sekcje z katalogów `sections/*/section.yaml`, a aktywności na podstawie listy `modules` z polami `type`, `ref`, `name`.

Obecna obsługa zasobów w loaderze ma jawne ścieżki dla:
- book, assignment, glossary, quiz, url;
- file;
- page i label.

Wczytywanie treści Book opiera się na jawnych wpisach `chapters[].content_file`. Nie jest to ogólny parser dowolnego katalogu Markdown. Wartości `ref` są rozwiązywane względem katalogu sekcji i przechodzą kontrolę ścieżki.

**Wniosek:** obecny format katalogów kursu jest użyteczną podstawą modelu wejściowego, ale nie można zakładać, że każdy katalog z plikiem `course.md` zostanie automatycznie wczytany. Dla kursów zawierających wyłącznie pliki MD potrzebny jest etap importu/normalizacji do jawnego modelu kursu albo rozszerzenie loadera.

### 2.3. Konwersja Markdown

W `magic_moodle/moodle_publish.py` funkcja `_markdown_to_html()` implementuje własny, ograniczony podzbiór Markdown:
- obsługuje podstawowe nagłówki, proste listy punktowane, akapity, kod inline, pogrubienie i kursywę;
- nie obsługuje pełnego zestawu CommonMark/GFM;
- nie obsługuje tabel, zagnieżdżonych list, list numerowanych jako list HTML, cytatów, obrazów, linków i bloków kodu w sposób kompletny;
- nagłówki `#` i `##` mapuje na `h2`, przez co traci rozróżnienie semantyczne poziomów.

Wniosek: należy wybrać jedną bibliotekę Markdown, skonfigurować rozszerzenia i politykę sanitacji, a konwersję udostępnić jako wspólną usługę używaną przez publikator, importer i przyszły eksporter.

### 2.4. Historyczne skrypty i szablony

W `main` następujące pliki mają rozmiar 0 B:
- `scripts/builders/build_mbz.c`;
- `scripts/converters/gift_to_moodle_xml.php`;
- `scripts/converters/md_to_html.php`;
- `scripts/converters/moodle_xml_to_mbz.php`;
- `scripts/converters/yaml_to_gift.php`;
- `scripts/converters/yaml_to_moodle_xml.php`;
- `scripts/importers/moodle_api_client.php`;
- szablony w `templates/moodle-xml/`;
- `tests/test_converters.sh` i `tests/test_validators.sh`.

Nie należy traktować tych plików jako działających konwerterów. Przed usunięciem trzeba sprawdzić, czy jakiekolwiek workflow, dokumentacja, skrypty zewnętrzne lub użytkownicy ich nie wywołują.

### 2.5. Wtyczka Moodle

W repozytorium znajduje się wtyczka `local_magicmoodle` z endpointami tworzenia lub synchronizacji aktywności, m.in.:
- `create_activity.php`;
- `create_assignment.php`;
- `create_book.php`;
- `create_glossary.php`;
- `create_quiz.php`;
- `create_resource.php`;
- `update_section.php`.

Wtyczka i REST API mogą pozostać niezależnym kanałem publikacji. Nie zastępują formatu kopii zapasowej MBZ. Wtyczka ma własny workflow testów Moodle 4.1/PHPUnit.

## 3. PR #101 — aktualna ocena

PR: [#101](https://github.com/bartoszruta26-droid/Magic_moodle_course_maker/pull/101)  
Gałąź: `course-conversion-to-moodle-bb3bf`  
Commit PR: `20b95ac840e51fab10b436618ff226709a8a7180`  
Stan podczas audytu: otwarty, nie scalony, zmienia jeden plik: `scripts/md_to_moodle_activity.py` (614 linii).

PR dodaje skrypt przeznaczony do konwersji pojedynczego pliku Markdown do struktury Book + Quiz, generuje GIFT i próbuje utworzyć archiwum MBZ.

### 3.1. Mocne strony

- próbuje znormalizować źródłowy plik MD do istniejącego układu `sections/`;
- zachowuje rozdziały Book jako osobne pliki Markdown;
- generuje pliki YAML opisujące aktywności;
- korzysta z istniejącego parsera GIFT i eksportera Moodle XML dla banku pytań;
- posiada opcję `--dry-run`;
- nie nadpisuje istniejącego `course.yaml`.

### 3.2. Błędy i ryzyka blokujące

1. **Drugi, niezależny renderer Markdown.** Skrypt definiuje własne `md_to_html()`, zamiast używać wspólnego renderera. Obsługa jest ograniczona: listy numerowane stają się akapitami, brak pełnego CommonMark, obsługi linków/obrazów i zagnieżdżonych list; nagłówki są mapowane niestandardowo.
2. **Błędne odpowiedzi shortanswer.** Klucz odpowiedzi jest tworzony przez przekształcenie treści pytania (usunięcie znaku zapytania i zmiana pierwszej litery). To nie jest odpowiedź merytoryczna i może tworzyć fałszywe pytania z pozornie poprawnym kluczem.
3. **Pytania P/F z nagłówków.** Pytania są generowane z relacji strukturalnej tytułów, a fałszywe warianty przypisują podrozdział do poprzedniego rozdziału. To nie sprawdza wiedzy i nie gwarantuje poprawności dydaktycznej.
4. **Parsowanie struktury.** Parser rozpoznaje tylko numerowane nagłówki `## N. Tytuł`; nie zachowuje ogólnej hierarchii Markdown i zakłada specyficzny układ rozdziału pytań.
5. **Generowanie YAML przez interpolację tekstu.** Nazwy z cudzysłowami, dwukropkami, znakami specjalnymi lub wielowierszową treścią mogą uszkodzić YAML. Należy użyć `yaml.safe_dump` lub równoważnego serializatora.
6. **Ryzyko utraty danych przy ponownym uruchomieniu.** Skrypt nadpisuje pliki oznaczone jako wygenerowane, ale nie wykazuje kompletnej kontroli nad usuwaniem nieaktualnych wcześniej wygenerowanych plików ani nad konfliktami nazw.
7. **Generator MBZ nie jest kompletny.** Funkcja `moodle_xml_export()` ręcznie konstruuje uproszczony dokument XML i zapisuje archiwum ZIP zawierające wyłącznie `moodle_backup.xml` i `questions.xml` w katalogu głównym. Nie buduje kompletnego drzewa backupu z aktywnościami, sekcjami, plikami, manifestem i wymaganymi metadanymi formatu Moodle.
8. **Dane aktywności są niekompletne.** W części Book/Quiz pola i struktura XML są ręcznie uproszczone; brak pełnych danych instancji i plików modułów wymaganych do wiernego odtworzenia kursu.
9. **Brak testu importu MBZ.** Nie dodano testów skryptu, walidacji formatu backupu ani automatycznego przywrócenia wygenerowanego pliku na instancji Moodle.
10. **Brak pełnej walidacji wejścia.** Skrypt zakłada obecność katalogów i poprawne wzorce nazw/treści, a część błędów może ujawnić się dopiero podczas generowania.

**Decyzja audytowa:** nie scalać PR #101 w obecnej postaci. Nie oznacza to, że cały pomysł jest bezużyteczny: można odzyskać koncepcję rozdzielania materiału na Book/Quiz i wykorzystać wybrane fragmenty po refaktoryzacji. Nie należy używać jego funkcji `moodle_xml_export()` do produkcyjnego generowania MBZ.

## 4. Testy i automatyzacja CI

### 4.1. Workflow główny

`.github/workflows/core-tests.yml` uruchamia m.in.:
- testy pytest;
- kontrolę składni Bash;
- smoke test TUI;
- compileall modułów Python;
- kontrolę składni JavaScript;
- inspekcję istniejącego kursu MED.10;
- walidację banku GIFT i eksport banku do Moodle XML;
- kontrolę składni PHP wtyczki.

Nie ma tu testu pełnego przebiegu MD → HTML → struktura kursu → MBZ → przywrócenie kursu Moodle.

### 4.2. Workflow integracyjny Moodle

`.github/workflows/moodle-integration.yml` przygotowuje Moodle 4.1, MariaDB i uruchamia PHPUnit wtyczki `local_magicmoodle`. Workflow jest ograniczony ścieżkami zmian do wtyczki i własnego pliku workflow; nie jest testem eksportera MBZ.

### 4.3. Stan uruchomień zaobserwowany podczas audytu

Dla commitu dokumentującego audyt na `main`:
- Build Python package — zakończony powodzeniem;
- Validate course repository — zakończony powodzeniem;
- Validate GIFT question bank — zakończony powodzeniem;
- Lint YAML files — zakończony powodzeniem;
- Core tests — w trakcie w momencie odczytu.

Dla PR #101:
- Core tests — zakończone powodzeniem;
- Build Python package — zakończone powodzeniem;
- Validate course repository — zakończone powodzeniem;
- Validate GIFT question bank — zakończone powodzeniem;
- Lint YAML files — zakończone powodzeniem.

**Interpretacja:** zielony workflow PR #101 potwierdza istniejące kontrole ogólne, ale nie dowodzi poprawności nowego skryptu, ponieważ PR nie dodaje dedykowanych testów konwertera ani testu importu MBZ.

## 5. Najważniejsze decyzje architektoniczne

1. Utrzymać jeden kanoniczny rdzeń Python.
2. Oddzielić parser źródeł, model pośredni, renderer HTML, mapowanie aktywności, publikację REST i eksport backupu.
3. Zastosować utrzymywaną bibliotekę Markdown (wybór po analizie kompatybilności, np. Python-Markdown lub markdown-it-py) oraz jawne rozszerzenia.
4. Zastosować bezpieczny serializer YAML.
5. Nie generować automatycznie odpowiedzi quizowych z treści pytań lub samych nagłówków.
6. Dla MBZ preferować uruchomienie oficjalnego mechanizmu backupu Moodle na kontrolowanej instancji po zbudowaniu kursu przez wspierane API, zamiast ręcznego odtwarzania wewnętrznego formatu backupu. Alternatywę własnego generatora rozważać dopiero po porównaniu ze wzorcowym backupem z konkretnej wersji Moodle.
7. Ustalić wspieraną wersję Moodle; obecne testy wtyczki wskazują Moodle 4.1, ale eksport MBZ musi mieć osobny test zgodności.
8. Rozbudować CI o testy parsera, modelu, rendererów, plików i pełny test restore.

## 6. Kolejność dalszych prac

### Etap 0A — zakończenie inwentaryzacji
- przeanalizować format źródłowy kursów MD (w szczególności `courses/05-badanie-neurologiczne`);
- porównać go z formatem `course.yaml` + `sections/*/section.yaml`;
- ustalić wszystkie typy aktywności i pola konfiguracji;
- ustalić, czy istniejące mechanizmy plugin/REST mogą tworzyć kurs testowy dla oficjalnego backupu;
- zapisać listę używanych i nieużywanych skryptów.

### Etap 1 — wspólny renderer Markdown
- dodać zależność i skonfigurować parser;
- utworzyć testy wzorcowe dla nagłówków, list, tabel, linków, obrazów, kodu, cytatów, wzorów i HTML;
- zastąpić duplikaty renderowania wspólną usługą;
- zachować dotychczasowe zachowanie w kompatybilnych przypadkach i dodać testy regresji.

### Etap 2 — importer MD do modelu kursu
- opracować parser spisów treści i katalogów źródłowych;
- zachować hierarchię, kolejność, identyfikatory i odnośniki;
- mapować elementy wyłącznie na jawnie opisane typy aktywności;
- generować YAML przez serializer i raportować niejednoznaczności.

### Etap 3 — eksport MBZ przez Moodle
- utworzyć testową instancję wspieranej wersji Moodle;
- zbudować kurs z modelu przez REST/wtyczkę;
- uruchomić oficjalny backup CLI Moodle;
- pobrać MBZ i sprawdzić przywrócenie na czystej instancji;
- ocenić, czy potrzebny jest niezależny generator.

## 7. Kryteria blokujące scalanie PR #101

PR nie może być scalony, dopóki:
- odpowiedzi shortanswer nie pochodzą z jawnego klucza odpowiedzi;
- generator P/F nie zostanie usunięty lub zastąpiony merytorycznie uzasadnionymi pytaniami;
- parser i renderer nie zostaną ujednolicone;
- YAML nie będzie generowany bezpiecznym serializatorem;
- generator MBZ nie zostanie zastąpiony poprawnym mechanizmem;
- powstaną dedykowane testy konwertera;
- wygenerowany MBZ nie przejdzie testu przywrócenia na Moodle.

## 8. Ograniczenia tego raportu

Jest to przegląd statyczny plików i metadanych GitHub. Nie uruchomiono repozytorium w lokalnym środowisku wykonawczym, nie wykonano ręcznego eksportu kursu i nie przywrócono pliku MBZ na serwerze Moodle. Statusy CI odnotowano na podstawie dostępnych metadanych uruchomień. Przed zmianą kodu należy odświeżyć stan gałęzi i uruchomień.


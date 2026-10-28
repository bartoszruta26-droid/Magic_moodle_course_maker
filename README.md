# Qwen Moodle Course Generator

Repozytorium do automatycznego generowania kompletnych kursów Moodle przy wykorzystaniu agentów AI (Qwen Code i Qwen Coder). Projekt umożliwia tworzenie, walidację i eksport kursów w formacie gotowym do importu do platformy Moodle, wykorzystując wyłącznie skrypty Bash, C, C#, C++, Apache2 i PHP.

## 📚 Struktura Repozytorium

```
qwen-moodle-courses/
├── README.md                          # Ten plik
├── LICENSE                            # Licencja projektu (MIT)
├── .gitignore                         # Wykluczenia Git
├── .gitattributes                     # Atrybuty plików
│
├── docs/                              # Dokumentacja techniczna
│   ├── 01-ARCHITECTURE.md             # Struktura repozytorium, nazewnictwo, formaty
│   ├── 02-CONTENT-FORMATS.md          # Metadane, sekcje, aktywności, multimedia
│   ├── 03-QUESTION-FORMATS.md         # GIFT, YAML, XML, Aiken, quizy
│   └── 04-AUTOMATION-AND-ETHICS.md    # Skrypty, CI/CD, walidacja, etyka
│
├── courses/                           # Główny katalog kursów
│   ├── _templates/                    # Szablony kursów
│   │   ├── basic-course/
│   │   │   ├── course.yaml
│   │   │   └── sections/
│   │   │       └── 01-template-section/
│   │   │           ├── section.yaml
│   │   │           └── page.md
│   │   ├── quiz-heavy-course/
│   │   └── multimedia-course/
│   │
│   ├── 01-prawda-i-natura/            # Przykładowy kurs
│   │   ├── course.yaml                # Metadane kursu
│   │   ├── course.md                  # Opis kursu (Markdown)
│   │   ├── course.jpg                 # Obraz kursu (miniaturka)
│   │   ├── tags.yaml                  # Tagi i kategorie
│   │   ├── settings.yaml              # Ustawienia zaawansowane
│   │   ├── completion.yaml            # Reguły ukończenia
│   │   ├── grades.yaml                # Konfiguracja oceniania
│   │   │
│   │   ├── sections/                  # Sekcje kursu
│   │   │   ├── 00-ogloszenia/         # Sekcja 0 (ogłoszenia)
│   │   │   │   ├── section.yaml
│   │   │   │   └── page.md
│   │   │   │
│   │   │   ├── 01-wprowadzenie/
│   │   │   │   ├── section.yaml       # Metadane sekcji
│   │   │   │   ├── section.md         # Podsumowanie sekcji
│   │   │   │   ├── page-01-czym-jest-prawda.md
│   │   │   │   ├── page-02-prawo-naturalne.md
│   │   │   │   ├── url-01-zrodla.yaml
│   │   │   │   ├── file-01-dokument.pdf
│   │   │   │   ├── folder-01-materialy/
│   │   │   │   │   ├── material-01.pdf
│   │   │   │   │   └── material-02.pdf
│   │   │   │   ├── quiz-01/
│   │   │   │   │   ├── quiz.yaml      # Metadane quizu
│   │   │   │   │   ├── questions.gift # Pytania w formacie GIFT
│   │   │   │   │   ├── questions.yaml # Pytania w formacie YAML
│   │   │   │   │   ├── questions.xml  # Pytania w formacie XML
│   │   │   │   │   └── feedback.md
│   │   │   │   ├── lesson-01/
│   │   │   │   │   ├── lesson.yaml
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   ├── 01-start.md
│   │   │   │   │   │   └── 02-rozwinięcie.md
│   │   │   │   │   └── media/
│   │   │   │   │       └── intro.mp4
│   │   │   │   ├── assignment-01/
│   │   │   │   │   ├── assignment.yaml
│   │   │   │   │   └── instructions.md
│   │   │   │   ├── forum-01/
│   │   │   │   │   ├── forum.yaml
│   │   │   │   │   └── first-post.md
│   │   │   │   ├── choice-01/
│   │   │   │   │   └── choice.yaml
│   │   │   │   ├── glossary-01/
│   │   │   │   │   ├── glossary.yaml
│   │   │   │   │   └── entries.yaml
│   │   │   │   ├── book-01/
│   │   │   │   │   ├── book.yaml
│   │   │   │   │   └── chapters/
│   │   │   │   │       ├── 01-chapter.md
│   │   │   │   │       └── 02-chapter.md
│   │   │   │   ├── h5p-01/
│   │   │   │   │   ├── h5p.yaml
│   │   │   │   │   └── content.h5p
│   │   │   │   └── label-01.md
│   │   │   │
│   │   │   ├── 02-godnosc-czlowieka/
│   │   │   │   └── ... (analogiczna struktura)
│   │   │   │
│   │   │   └── 03-podsumowanie/
│   │   │       └── ... (analogiczna struktura)
│   │   │
│   │   ├── question-bank/             # Bank pytań kursu
│   │   │   ├── categories.yaml
│   │   │   ├── multichoice/
│   │   │   │   ├── set-01.gift
│   │   │   │   └── set-01.yaml
│   │   │   ├── truefalse/
│   │   │   │   └── set-01.gift
│   │   │   ├── shortanswer/
│   │   │   │   └── set-01.gift
│   │   │   └── essay/
│   │   │       └── set-01.gift
│   │   │
│   │   ├── media/                     # Zasoby multimedialne kursu
│   │   │   ├── images/
│   │   │   │   ├── logo.png
│   │   │   │   └── diagram-01.svg
│   │   │   ├── videos/
│   │   │   │   └── intro.mp4
│   │   │   ├── audio/
│   │   │   │   └── podcast-01.mp3
│   │   │   └── documents/
│   │   │       ├── syllabus.pdf
│   │   │       └── reading-list.pdf
│   │   │
│   │   ├── output/                    # Wygenerowane pliki (.gitignore)
│   │   │   ├── moodle-xml/
│   │   │   │   └── course.xml
│   │   │   ├── gift/
│   │   │   │   └── all-questions.gift
│   │   │   ├── mbz/
│   │   │   │   └── course.mbz
│   │   │   └── imscc/
│   │   │       └── course.imscc
│   │   │
│   │   └── changelog.md
│   │
│   └── 02-wiara-i-rozum/
│       └── ... (analogiczna struktura)
│
├── shared/                            # Zasoby współdzielone między kursami
│   ├── images/
│   ├── videos/
│   ├── audio/
│   ├── documents/
│   ├── icons/
│   ├── css/
│   │   ├── course-theme.css
│   │   └── accessibility.css
│   ├── js/
│   │   └── interactive-widgets.js
│   └── lti-configs/
│       └── tool-providers.yaml
│
├── question-bank-global/              # Globalny bank pytań
│   ├── categories.yaml
│   ├── theology/
│   ├── philosophy/
│   ├── ethics/
│   └── scripture/
│
├── templates/                         # Szablony konwersji
│   ├── moodle-xml/
│   │   ├── course-backup.xml.j2
│   │   ├── section.xml.j2
│   │   ├── page-module.xml.j2
│   │   ├── quiz-module.xml.j2
│   │   └── question-types/
│   │       ├── multichoice.xml.j2
│   │       ├── truefalse.xml.j2
│   │       └── shortanswer.xml.j2
│   ├── gift/
│   │   ├── multichoice.gift.j2
│   │   └── truefalse.gift.j2
│   ├── schemas/
│   │   ├── course.schema.json
│   │   ├── section.schema.json
│   │   └── question.schema.json
│   └── prompts/
│       ├── generate-course-outline.md
│       ├── generate-quiz-questions.md
│       └── review-content-ethics.md
│
├── scripts/                           # Skrypty narzędziowe Bash, C, C++, PHP, Python
│   ├── config.sh                      # Zmienne wspólne (ścieżki, wersje)
│   ├── course_toc.py                  # Biblioteka: parser spisu treści kursu
│   ├── scaffold_course.py             # Uniwersalny generator szkicu kursu z TOC
│   ├── scaffold.sh                    # One-shot: szkic + stuby + quizy + kontrola
│   ├── toc_outline.py                 # Eksport struktury TOC do JSON/YAML/Markdown
│   ├── toc_prompts.py                 # Prompty AI per temat (do generowania treści)
│   ├── gen_page_stubs.py              # Szkielety stron .md z podtematami ze spisu
│   ├── gen_quiz_templates.py          # Szablony pytań GIFT/YAML + instrukcje zadań
│   ├── gen_masaz_skeleton.py          # (hist.) jednorazowy szkic kursu masażu
│   ├── scaffold-kurs-masazu.py        # (hist.) jednorazowy szkic kursu masażu
│   │
│   ├── validators/
│   │   ├── validate_course.sh
│   │   ├── validate_yaml.sh
│   │   ├── validate_gift.sh
│   │   ├── validate_links.sh
│   │   ├── validate_media.sh
│   │   ├── validate_accessibility.sh
│   │   └── validate_ethics.sh
│   │
│   ├── converters/
│   │   ├── yaml_to_moodle_xml.php
│   │   ├── yaml_to_gift.php
│   │   ├── md_to_html.php
│   │   ├── gift_to_moodle_xml.php
│   │   └── moodle_xml_to_mbz.php
│   │
│   ├── builders/
│   │   ├── build_course.c
│   │   ├── build_quiz.cpp
│   │   └── build_mbz.c
│   │
│   ├── importers/
│   │   ├── moodle_api_client.php
│   │   └── import_course.php
│   │
│   └── utilities/
│       ├── slugify.sh
│       └── link_checker.sh
│
├── tests/                             # Testy automatyczne
│   ├── test_validators.sh
│   ├── test_converters.sh
│   └── fixtures/
│       └── sample-course/
│
├── .github/
│   ├── workflows/
│   │   ├── validate.yml               # Walidacja przy PR
│   │   ├── build.yml                  # Budowanie pakietów
│   │   ├── lint-gift.yml
│   │   └── lint-yaml.yml
│   └── CODEOWNERS
│
├── .env.example
└── Makefile
```

## 🎯 Cel Projektu

Repozytorium służy do automatycznego generowania kompletnych kursów Moodle przy wykorzystaniu agentów AI:

- **Qwen Code** – tworzenie struktury repozytorium, konfiguracji CI/CD, skryptów budujących
- **Qwen Coder** – generowanie treści merytorycznych, pytań quizowych, scenariuszy lekcji

### Obsługiwane formaty eksportu

| Format | Rozszerzenie | Zastosowanie |
|--------|-------------|--------------|
| Moodle Backup | `.mbz` | Pełny backup kursu ze wszystkimi aktywnościami |
| Moodle XML | `.xml` | Definicja kursu/pytań w formacie XML |
| Common Cartridge | `.imscc` | Standard branżowy, przenośny między platformami |
| GIFT | `.gift` | Import pytań do banku pytań Moodle |

### Obsługiwane formaty pytań

| Format | Rozszerzenie | Typy pytań |
|--------|-------------|------------|
| GIFT | `.txt`, `.gift` | multichoice, truefalse, shortanswer, numerical, matching, essay, missingword |
| YAML | `.yaml`, `.yml` | Wszystkie typy (wymaga konwersji) |
| XML | `.xml` | Wszystkie typy (natywny format Moodle) |
| Aiken | `.txt` | Tylko multichoice |

### Obsługiwane formaty treści

| Format | Rozszerzenie | Zastosowanie |
|--------|-------------|--------------|
| Markdown | `.md` | Treści stron, opisów, lekcji (konwersja do HTML) |
| HTML | `.html` | Bezpośrednie osadzanie treści |
| LaTeX | `.tex` | Wzory matematyczne (konwersja do MathJax) |

### Obsługiwane formaty multimedialne

| Format | Rozszerzenie | Zastosowanie |
|--------|-------------|--------------|
| Obrazy | `.png`, `.jpg`, `.svg`, `.webp` | Ilustracje, diagramy |
| Wideo | `.mp4`, `.webm` | Materiały wideo |
| Audio | `.mp3`, `.ogg` | Nagrania, podcasty |
| Dokumenty | `.pdf`, `.docx` | Materiały do pobrania |
| H5P | `.h5p` | Interaktywne treści HTML5 |

## 📋 Opis Plików

### Katalog `courses/`

Każdy kurs posiada własny podkatalog z następującą strukturą:

| Plik/Katalog | Opis |
|-------------|------|
| `course.yaml` | Metadane kursu: nazwa, krótki opis, format kursu, liczba sekcji, język |
| `course.md` | Pełny opis kursu w Markdown |
| `course.jpg` | Miniaturka kursu |
| `tags.yaml` | Tagi i kategorie kursu |
| `settings.yaml` | Ustawienia zaawansowane (role, grupy, filtry) |
| `completion.yaml` | Reguły ukończenia kursu |
| `grades.yaml` | Konfiguracja oceniania |
| `sections/` | Podkatalogi numerowane (00, 01, 02...) zawierające materiały dydaktyczne |
| `question-bank/` | Bank pytań w formatach: GIFT, YAML |
| `media/` | Zasoby multimedialne: obrazy, wideo, dokumenty, audio |
| `output/` | Wygenerowane pliki Moodle (.gitignore) |
| `changelog.md` | Historia zmian kursu |

### Sekcje Kursu (`sections/NN/`)

Każda sekcja zawiera:

| Plik | Format | Opis |
|------|--------|------|
| `section.yaml` | YAML | Metadane sekcji: nazwa, numer, widoczność, moduły |
| `section.md` | Markdown | Podsumowanie sekcji |
| `page-XX-*.md` | Markdown | Treść strony edukacyjnej |
| `label-XX.md` | Markdown | Etykieta (wyświetlana bezpośrednio na stronie kursu) |
| `url-XX.yaml` | YAML | Zasób URL |
| `file-XX.*` | PDF/DOCX | Plik do pobrania |
| `quiz-XX/` | Katalog | Quiz z pytaniami |
| `lesson-XX/` | Katalog | Lekcja rozgałęziona |
| `assignment-XX/` | Katalog | Zadanie do wykonania |
| `forum-XX/` | Katalog | Forum dyskusyjne |
| `book-XX/` | Katalog | Książka (wielostronicowa) |
| `h5p-XX/` | Katalog | Treść interaktywna H5P |

### Bank Pytań (`question-bank/`)

| Format | Rozszerzenie | Zastosowanie |
|--------|-------------|--------------|
| GIFT | `.gift` | Import bezpośredni do Moodle, wszystkie typy pytań |
| YAML | `.yaml` | Konfiguracja quizów, strukturalne dane |
| XML | `.xml` | Natywny format importu Moodle |

## 🚀 Użycie

### 1. Tworzenie nowego kursu

```bash
# Skopiuj szablon
cp -r courses/_templates/basic-course courses/01-nowy-kurs

# Edytuj metadane
nano courses/01-nowy-kurs/course.yaml
```

**Alternatywa — wygeneruj szkic struktury wprost ze spisu treści** (zamiast kopiować szablon):

```bash
# Cały pipeline jednym poleceniem: szkic pustych plików + stuby stron + szablony quizów
./scripts/scaffold.sh kurs_masazu.txt "kurs masazysta med10"

# ...albo krok po kroku:
python3 scripts/toc_outline.py --toc kurs_masazu.txt --format markdown   # przejrzyj strukturę
python3 scripts/scaffold_course.py --toc kurs_masazu.txt \
    --base courses/03-kurs-masazysta-med10 --dry-run                      # pokaż plan plików
python3 scripts/scaffold_course.py --toc kurs_masazu.txt \
    --base courses/03-kurs-masazysta-med10                                # utwórz puste pliki
python3 scripts/gen_page_stubs.py --base courses/03-kurs-masazysta-med10  # szkielety stron .md
python3 scripts/gen_quiz_templates.py --base courses/03-kurs-masazysta-med10
python3 scripts/toc_prompts.py --base courses/03-kurs-masazysta-med10 --out prompts-masaz
python3 scripts/scaffold_course.py --base courses/03-kurs-masazysta-med10 --check
```

### 2. Budowanie kursu

```bash
# Instalacja zależności

# Budowanie wszystkich formatów
./scripts/builders/build_course courses/01-nowy-kurs --format all

# Lub konkretny format
./scripts/builders/build_course courses/01-nowy-kurs --format xml
./scripts/builders/build_course courses/01-nowy-kurs --format gift
./scripts/builders/build_course courses/01-nowy-kurs --format mbz
```

### 3. Walidacja

```bash
# Walidacja YAML
./scripts/validators/validate_yaml.sh courses/

# Walidacja GIFT
./scripts/validators/validate_gift.sh courses/

# Walidacja dostępności
./scripts/validators/validate_accessibility.sh courses/

# Walidacja etyczna
./scripts/validators/validate_ethics.sh courses/
```

### 4. Eksport do Moodle

Wygenerowany plik `.mbz` można zaimportować do Moodle przez:

**Interfejs GUI:**
1. Zaloguj się jako administrator/kreator kursu
2. Przejdź do: Administracja witryną → Kursy → Import
3. Wybierz format "Moodle backup (.mbz)"
4. Przeciągnij plik z `courses/01-nowy-kurs/output/mbz/course.mbz`

**CLI Moodle:**
```bash
php admin/cli/backup --file=/path/to/course.mbz
```

**Import pytań GIFT:**
1. Przejdź do kursu
2. Administracja kursu → Bank pytań → Import
3. Wybierz format "GIFT"
4. Prześlij plik z `courses/01-nowy-kurs/output/gift/all-questions.gift`

## 🔧 Skrypty

| Skrypt | Opis |
|--------|------|
| `scripts/builders/build_course.c` | Główny skrypt budujący kurs w formatach XML/GIFT/MBZ |
| `scripts/validators/validate_yaml.sh` | Walidacja plików YAML względem schematów JSON Schema |
| `scripts/validators/validate_gift.sh` | Walidacja składni plików GIFT |
| `scripts/validators/validate_links.sh` | Sprawdzenie poprawności linków wewnętrznych |
| `scripts/validators/validate_media.sh` | Walidacja plików multimedialnych |
| `scripts/validators/validate_accessibility.sh` | Sprawdzenie zgodności z WCAG 2.1 AA |
| `scripts/validators/validate_ethics.sh` | Walidacja zgodności etycznej treści |
| `scripts/converters/yaml_to_moodle_xml.php` | Konwersja YAML → Moodle XML |
| `scripts/converters/yaml_to_gift.php` | Konwersja YAML → GIFT |
| `scripts/converters/md_to_html.php` | Konwersja Markdown → HTML |
| `scripts/importers/import_course.php` | Import kursu do Moodle przez REST API |
| `scripts/builders/build_quiz.cpp` | Budowa pakietu pytań quizu (GIFT/YAML → XML) |
| `scripts/builders/build_mbz.c` | Pakowanie wyniku budowania do formatu `.mbz` |
| `scripts/validators/validate_course.sh` | Walidacja kompletności struktury katalogu kursu |
| `scripts/converters/gift_to_moodle_xml.php` | Konwersja GIFT → Moodle XML |
| `scripts/converters/moodle_xml_to_mbz.php` | Moodle XML → gotowy pakiet `.mbz` |
| `scripts/importers/moodle_api_client.php` | Klient REST API Moodle (autoryzacja, wysyłka) |
| `scripts/utilities/slugify.sh` | Slug nazwy katalogu/pliku wg konwencji repozytorium |
| `scripts/utilities/link_checker.sh` | Batchowe sprawdzanie linków wewnętrznych |
| `scripts/config.sh` | Zmienne wspólne dla wszystkich skryptów powłoki |

### Skrypty generujące kurs ze spisu treści (Python, biblioteka `course_toc.py`)

Punkt wejścia: **spis treści kursu** w formacie markdown-like (przykład: `kurs_masazu.txt`),
czyli nagłówki `## MODUŁ N`, `### N.M. Temat`, listy `N.M.K. Podtemat`, `## Załącznik X`.
Wszystkie poniższe skrypty działają dla **każdego** takiego spisu, nie tylko dla masażu.

| Skrypt | Rola w pipeline | Opis |
|--------|-----------------|------|
| `scripts/course_toc.py` | biblioteka | Parser spisu treści: `parse_course()` → obiekty `Course/Module/Topic/Subtopic/Attachment/FrontSection`; `slugify()` (polskie znaki, skróty słownikowe, przycinanie po słowach); stałe konwencji (`TOP_FILES`, `MEDIA_SUBDIRS`, `QKINDS`); `Plan`/`build_course_files()` (idempotentne tworzenie pustych plików); `normalize_pages()` (renormalizacja nazw stron); `check_structure()` (stan dysku vs. spis). Uruchomiony bezpośrednio wypisuje podsumowanie parsed TOC. |
| `scripts/scaffold_course.py` | 1. szkic struktury | Uniwersalny generator **pustego szkicu** kursu Moodle na bazie TOC (następca jednorazowego `scaffold-kurs-masazu.py`). Tworzy: pliki główne (`course.yaml|md`, `settings.yaml`, `tags.yaml`, `completion.yaml`, `grades.yaml`, `changelog.md`, `course.jpg`), `media/{images,videos,audio,documents}`, `question-bank/` (kategorie + zestawy per typ pytania), `sections/00-ogloszenia`, sekcje modułów z `page-NN-*.md`, `quiz-NN/`, `assignment-NN/` oraz załączniki A–M jako etykiety lub podkatalogi. Flagi: `--toc`, `--base` (domyślnie liczony `courses/NN-slug`), `--dry-run`, `--attachments labels|subdirs|none`, `--front` (część wstępna), `--first-module-section`, `--no-normalize`, `--check` (walidacja struktury bez tworzenia plików; kod wyjścia 1 przy rozbieżnościach). Idempotentny: nigdy nie nadpisuje plików z treścią. |
| `scripts/gen_page_stubs.py` | 2. szkielety treści | Wypełnia **puste** strony `page-NN-*.md` minimalnym szkicem redakcyjnym: H1 z numerem i tytułem tematu, H2 per podtemat ze spisu + placeholder `TODO`; tworzy też `section.md` sekcji z listą tematów i linkami do stron. Plików z istniejącą treścią nie rusza. Flagi: `--toc`, `--base`, `--dry-run`. |
| `scripts/gen_quiz_templates.py` | 3. szablony oceniania | Dla każdego tematu tworzy (tylko gdy plik pusty/nieistniejący): `quiz-NN/questions.yaml` i `questions.gift` z szablonami pytań wielokrotnego wyboru per podtemat (poprawna odpowiedź i dystraktory do uzupełnienia) oraz `assignment-NN/instructions.md` z checklistem przebiegu zadania wynikającym z podtematów. Flagi: `--toc`, `--base`, `--dry-run`, `--per-topic N`. |
| `scripts/toc_outline.py` | wsparcie/podgląd | Eksport przeanalizowanej struktury TOC do `json`, `yaml` lub `markdown` (stdout lub `--output plik`). Zawiera statystyki (moduły/tematy/podtematy/załączniki) — przydatne do review spisu, diffowania wersji i jako kontekst dla agenta AI. |
| `scripts/toc_prompts.py` | wsparcie/AI | Generuje katalog promptów markdown — po jednym na temat (+ `index.md`): numer i tytuł tematu, lista podtematów ze spisu, docelowa ścieżka pliku strony w kursie oraz reguły stylistyczne/etyczne/WCAG. Gotowy kontekst dla Qwen Code/Coder przy napełnianiu kursu treścią. Flagi: `--toc`, `--base`, `--out`, `--limit N`. |
| `scripts/scaffold.sh` | one-shot | Pipeline pełnego szkicu: kolejny numer `NN` kursu w `courses/`, slug z nazwy (przez `course_toc.slugify`), następnie `scaffold_course.py` → `gen_page_stubs.py` → `gen_quiz_templates.py` → `--check`. Dokumentuje konwencję nazewnictwa kursów/sekcji/stron/quizów. |
| `scripts/gen_masaz_skeleton.py`, `scripts/scaffold-kurs-masazu.py` | (historyczne) | Pierwsze, jednorazowe generatory szkicu kursu masażu (MED.10); zachowane dla historii — nowość: używaj `scaffold_course.py`, który je uogólnia. |

## 📄 Zasady etyczne

Wszystkie treści kursów muszą być zgodne z:

### Prawo Boże
- Treść musi służyć prawdzie, dobru i pięknu
- Nie może zawierać kłamstwa, manipulacji ani dezinformacji
- Wszystkie twierdzenia muszą być prawdziwe i weryfikowalne
- Cytaty muszą mieć podane źródło

### Prawo naturalne
- Treść musi szanować godność osoby ludzkiej, wolną wolę i rozum
- Edukacja ma rozwijać człowieka integralnie
- Język musi być szanujący i inkluzywny

### Prawa człowieka
- Treść musi szanować prawa autorskie, prywatność i godność
- Wszystkie materiały muszą mieć licencję lub być oryginalne
- AI nie może generować treści plagiatujących

### Dostępność (WCAG 2.1 AA)
- Obrazy muszą mieć tekst alternatywny
- Wideo musi mieć napisy
- Audio musi mieć transkrypcję
- Kontrast kolorów musi spełniać normy

### Kontrola jakości
- Każdy kurs musi być zatwierdzony przez ludzkiego recenzenta
- Treści teologiczne muszą być zweryfikowane przez teologa
- AI jest narzędziem wspierającym, nie zastępującym ludzki osąd

## 🔗 GitHub Actions CI/CD

Projekt wykorzystuje GitHub Actions do automatyzacji:

| Workflow | Wyzwalacz | Opis |
|----------|-----------|------|
| `validate.yml` | Pull Request | Walidacja YAML, GIFT, linków, mediów, dostępności, etyki |
| `build.yml` | Push do main | Budowanie pakietów Moodle i upload artifactów |
| `lint-gift.yml` | Pull Request | Linting plików GIFT |
| `lint-yaml.yml` | Pull Request | Linting plików YAML |

## 🛠️ Wymagania

- GCC/G++ (kompilator C/C++)
- Moodle 4.0+ (do importu)
- PHP 8.0+ (CLI)
- Bash 5.0+
- Node.js (opcjonalnie, do narzędzi frontend)

### NarzД™dzia budowania

```txt
# Wymagane pakiety systemowe
gcc >= 11.0
g++ >= 11.0
php-cli >= 8.0
php-xml >= 8.0
php-mbstring >= 8.0
bash >= 5.0
```

## 📄 Licencja

MIT License - zobacz plik [LICENSE](LICENSE)

## 📖 Dokumentacja

Pełna dokumentacja techniczna znajduje się w katalogu `docs/`:

- `01-ARCHITECTURE.md` – Struktura repozytorium i nazewnictwo
- `02-CONTENT-FORMATS.md` – Formaty metadanych, sekcji i aktywności
- `03-QUESTION-FORMATS.md` – Specyfikacja formatów pytań (GIFT, YAML, XML)
- `04-AUTOMATION-AND-ETHICS.md` – Automatyzacja, CI/CD i zasady etyczne

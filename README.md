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
├── scripts/                           # Skrypty narzędziowe Python
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py
│   │
│   ├── validators/
│   │   ├── validate_course.py
│   │   ├── validate_yaml.py
│   │   ├── validate_gift.py
│   │   ├── validate_links.py
│   │   ├── validate_media.py
│   │   ├── validate_accessibility.py
│   │   └── validate_ethics.py
│   │
│   ├── converters/
│   │   ├── yaml_to_moodle_xml.py
│   │   ├── yaml_to_gift.py
│   │   ├── md_to_html.py
│   │   ├── gift_to_moodle_xml.py
│   │   └── moodle_xml_to_mbz.py
│   │
│   ├── builders/
│   │   ├── build_course.py
│   │   ├── build_quiz.py
│   │   └── build_mbz.py
│   │
│   ├── importers/
│   │   ├── moodle_api_client.py
│   │   └── import_course.py
│   │
│   └── utilities/
│       ├── slugify.py
│       └── link_checker.py
│
├── tests/                             # Testy automatyczne
│   ├── test_validators.py
│   ├── test_converters.py
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

### 2. Budowanie kursu

```bash
# Instalacja zależności
pip install -r scripts/requirements.txt

# Budowanie wszystkich formatów
python scripts/builders/build_course.py courses/01-nowy-kurs --format all

# Lub konkretny format
python scripts/builders/build_course.py courses/01-nowy-kurs --format xml
python scripts/builders/build_course.py courses/01-nowy-kurs --format gift
python scripts/builders/build_course.py courses/01-nowy-kurs --format mbz
```

### 3. Walidacja

```bash
# Walidacja YAML
python scripts/validators/validate_yaml.py courses/

# Walidacja GIFT
python scripts/validators/validate_gift.py courses/

# Walidacja dostępności
python scripts/validators/validate_accessibility.py courses/

# Walidacja etyczna
python scripts/validators/validate_ethics.py courses/
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
php admin/cli/backup.py --file=/path/to/course.mbz
```

**Import pytań GIFT:**
1. Przejdź do kursu
2. Administracja kursu → Bank pytań → Import
3. Wybierz format "GIFT"
4. Prześlij plik z `courses/01-nowy-kurs/output/gift/all-questions.gift`

## 🔧 Skrypty

| Skrypt | Opis |
|--------|------|
| `scripts/builders/build_course.py` | Główny skrypt budujący kurs w formatach XML/GIFT/MBZ |
| `scripts/validators/validate_yaml.py` | Walidacja plików YAML względem schematów JSON Schema |
| `scripts/validators/validate_gift.py` | Walidacja składni plików GIFT |
| `scripts/validators/validate_links.py` | Sprawdzenie poprawności linków wewnętrznych |
| `scripts/validators/validate_media.py` | Walidacja plików multimedialnych |
| `scripts/validators/validate_accessibility.py` | Sprawdzenie zgodności z WCAG 2.1 AA |
| `scripts/validators/validate_ethics.py` | Walidacja zgodności etycznej treści |
| `scripts/converters/yaml_to_moodle_xml.py` | Konwersja YAML → Moodle XML |
| `scripts/converters/yaml_to_gift.py` | Konwersja YAML → GIFT |
| `scripts/converters/md_to_html.py` | Konwersja Markdown → HTML |
| `scripts/importers/import_course.py` | Import kursu do Moodle przez REST API |

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

- Python 3.11+
- Moodle 4.0+ (do importu)
- Node.js (opcjonalnie, do narzędzi frontend)

### Zależności Python

```txt
# scripts/requirements.txt
pyyaml>=6.0
jsonschema>=4.17.0
markdown>=3.4.0
requests>=2.28.0
jinja2>=3.1.0
```

## 📄 Licencja

MIT License - zobacz plik [LICENSE](LICENSE)

## 📖 Dokumentacja

Pełna dokumentacja techniczna znajduje się w katalogu `docs/`:

- `01-ARCHITECTURE.md` – Struktura repozytorium i nazewnictwo
- `02-CONTENT-FORMATS.md` – Formaty metadanych, sekcji i aktywności
- `03-QUESTION-FORMATS.md` – Specyfikacja formatów pytań (GIFT, YAML, XML)
- `04-AUTOMATION-AND-ETHICS.md` – Automatyzacja, CI/CD i zasady etyczne

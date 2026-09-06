
# Architektura repozytorium kursów Moodle

> Kompletna architektura repozytorium GitHub do generowania i eksportu
> kursów Moodle z wykorzystaniem agenta Qwen Coder.

---

## Spis treści

1. [Przegląd formatów importu/eksportu Moodle](#przegląd-formatów)
2. [Pełna struktura katalogów](#struktura-katalogów)
3. [Zasady nazewnictwa](#zasady-nazewnictwa)
4. [Plik .gitignore](#gitignore)
5. [Plik .gitattributes](#gitattributes)

---

<a id="przegląd-formatów"></a>
## 1. Przegląd formatów importu/eksportu Moodle

Moodle obsługuje wiele formatów importu i eksportu. Wybór formatu
determinuje strukturę plików w repozytorium.

### 1.1. Formaty importu kursów (pełna struktura)

| Format | Rozszerzenie | Zastosowanie | Poziom złożoności |
|---|---|---|---|
| **Moodle Backup** | `.mbz` | Pełny backup kursu z wszystkimi aktywnościami | Wysoki |
| **Moodle XML Course** | `.xml` | Definicja kursu w formacie XML | Średni |
| **Common Cartridge (IMS CC)** | `.imscc` | Standard branżowy, przenośny między platformami | Wysoki |
| **SCORM** | `.zip` | Pakiety e-learningowe z trackingiem | Wysoki |
| **LTI Package** | `.xml` | Integracja z zewnętrznymi narzędziami | Średni |

### 1.2. Formaty importu pytań i quizów

| Format | Rozszerzenie | Zastosowanie | Obsługiwane typy pytań |
|---|---|---|---|
| **GIFT** | `.txt`, `.gift` | Najbardziej uniwersalny format tekstowy | multichoice, truefalse, shortanswer, numerical, matching, essay, missingword |
| **Moodle XML** | `.xml` | Natywny format XML Moodle | Wszystkie typy pytań |
| **Aiken** | `.txt`, `.aiken` | Prosty format dla pytań wielokrotnego wyboru | Tylko multichoice |
| **Missing Word** | `.txt` | Pytania z luką | missingword |
| **YAML** (własny) | `.yaml`, `.yml` | Strukturalny, czytelny dla AI | Wszystkie typy (wymaga konwersji) |
| **JSON** (własny) | `.json` | Maszynowy format danych | Wszystkie typy (wymaga konwersji) |
| **CSV** | `.csv` | Import masowy pytań | Ograniczony |
| **XHTML** | `.xhtml` | Format webowy | Ograniczony |

### 1.3. Formaty treści i zasobów

| Format | Rozszerzenie | Zastosowanie w Moodle |
|---|---|---|
| **Markdown** | `.md` | Treści stron, opisów, lekcji (konwersja do HTML) |
| **HTML** | `.html`, `.htm` | Bezpośrednie osadzanie treści |
| **Plain Text** | `.txt` | Proste opisy, instrukcje |
| **LaTeX** | `.tex` | Wzory matematyczne (konwersja do MathJax) |
| **AsciiDoc** | `.adoc` | Zaawansowane dokumenty (konwersja do HTML) |
| **reStructuredText** | `.rst` | Dokumentacja techniczna |
| **PDF** | `.pdf` | Materiały do pobrania |
| **EPUB** | `.epub` | E-booki edukacyjne |

### 1.4. Formaty multimedialne

| Format | Rozszerzenie | Zastosowanie |
|---|---|---|
| Obrazy | `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp` | Ilustracje, diagramy |
| Wideo | `.mp4`, `.webm`, `.ogg` | Materiały wideo |
| Audio | `.mp3`, `.wav`, `.ogg`, `.m4a` | Nagrania, podcasty |
| Dokumenty | `.pdf`, `.docx`, `.xlsx`, `.pptx` | Materiały do pobrania |
| H5P | `.h5p` | Interaktywne treści HTML5 |
| GeoGebra | `.ggb` | Interaktywne materiały matematyczne |

---

<a id="struktura-katalogów"></a>
## 2. Pełna struktura katalogów

```text
moodle-courses/
│
├── README.md                                    # Główna dokumentacja projektu
├── LICENSE                                      # Licencja projektu (np. CC BY-SA 4.0)
├── .gitignore                                   # Wykluczenia Git
├── .gitattributes                               # Ustawienia atrybutów plików
├── CONTRIBUTING.md                              # Zasady współpracy
├── CODE_OF_CONDUCT.md                           # Kodeks postępowania
│
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── course_request.md
│   │   └── content_review.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS                               # Właściciele kodu (recenzenci)
│   ├── dependabot.yml                           # Automatyczne aktualizacje zależności
│   └── workflows/
│       ├── validate.yml                         # Walidacja przy PR
│       ├── build.yml                            # Budowanie pakietów
│       ├── deploy-staging.yml                   # Deploy na środowisko testowe
│       ├── deploy-production.yml                # Deploy na produkcję
│       ├── lint-gift.yml                        # Walidacja plików GIFT
│       ├── lint-yaml.yml                        # Walidacja plików YAML
│       └── security-scan.yml                    # Skanowanie bezpieczeństwa
│
├── courses/                                     # Główny katalog kursów
│   ├── _templates/                              # Szablony kursów
│   │   ├── basic-course/
│   │   │   ├── course.yaml
│   │   │   └── sections/
│   │   │       └── 01-template-section/
│   │   │           ├── section.yaml
│   │   │           └── page.md
│   │   ├── quiz-heavy-course/
│   │   └── multimedia-course/
│   │
│   ├── 01-prawda-i-natura/                      # Przykładowy kurs
│   │   ├── course.yaml                          # Metadane kursu
│   │   ├── course.md                            # Opis kursu (Markdown)
│   │   ├── course.jpg                           # Obraz kursu (miniaturka)
│   │   ├── tags.yaml                            # Tagi i kategorie
│   │   ├── settings.yaml                        # Ustawienia zaawansowane
│   │   ├── completion.yaml                      # Reguły ukończenia
│   │   ├── grades.yaml                          # Konfiguracja oceniania
│   │   │
│   │   ├── sections/                            # Sekcje kursu
│   │   │   ├── 00-ogloszenia/                   # Sekcja 0 (ogłoszenia)
│   │   │   │   ├── section.yaml
│   │   │   │   └── page.md
│   │   │   │
│   │   │   ├── 01-wprowadzenie/
│   │   │   │   ├── section.yaml                 # Metadane sekcji
│   │   │   │   ├── section.md                   # Podsumowanie sekcji
│   │   │   │   ├── page-01-czym-jest-prawda.md  # Strona treści
│   │   │   │   ├── page-02-prawo-naturalne.md
│   │   │   │   ├── url-01-zrodla.yaml           # Zasób URL
│   │   │   │   ├── file-01-dokument.pdf         # Plik do pobrania
│   │   │   │   ├── folder-01-materialy/         # Folder z plikami
│   │   │   │   │   ├── material-01.pdf
│   │   │   │   │   └── material-02.pdf
│   │   │   │   ├── quiz-01/                     # Quiz
│   │   │   │   │   ├── quiz.yaml                # Metadane quizu
│   │   │   │   │   ├── questions.gift           # Pytania w formacie GIFT
│   │   │   │   │   ├── questions.yaml           # Pytania w formacie YAML
│   │   │   │   │   ├── questions.xml            # Pytania w formacie XML
│   │   │   │   │   └── feedback.md              # Informacja zwrotna
│   │   │   │   ├── lesson-01/                   # Lekcja (rozgałęziona)
│   │   │   │   │   ├── lesson.yaml              # Struktura lekcji
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   ├── 01-start.md
│   │   │   │   │   │   ├── 02-rozwinięcie.md
│   │   │   │   │   │   ├── 03-branch-a.md
│   │   │   │   │   │   ├── 04-branch-b.md
│   │   │   │   │   │   └── 05-zakończenie.md
│   │   │   │   │   └── media/
│   │   │   │   │       └── intro.mp4
│   │   │   │   ├── assignment-01/               # Zadanie
│   │   │   │   │   ├── assignment.yaml
│   │   │   │   │   └── instructions.md
│   │   │   │   ├── forum-01/                    # Forum dyskusyjne
│   │   │   │   │   ├── forum.yaml
│   │   │   │   │   └── first-post.md
│   │   │   │   ├── choice-01/                   # Głosowanie/ankieta
│   │   │   │   │   └── choice.yaml
│   │   │   │   ├── glossary-01/                 # Słownik
│   │   │   │   │   ├── glossary.yaml
│   │   │   │   │   └── entries.yaml
│   │   │   │   ├── book-01/                     # Książka (multi-page)
│   │   │   │   │   ├── book.yaml
│   │   │   │   │   └── chapters/
│   │   │   │   │       ├── 01-chapter.md
│   │   │   │   │       └── 02-chapter.md
│   │   │   │   ├── wiki-01/                     # Wiki
│   │   │   │   │   ├── wiki.yaml
│   │   │   │   │   └── first-page.md
│   │   │   │   ├── h5p-01/                      # Treść interaktywna H5P
│   │   │   │   │   ├── h5p.yaml
│   │   │   │   │   └── content.h5p
│   │   │   │   ├── scorm-01/                    # Pakiet SCORM
│   │   │   │   │   ├── scorm.yaml
│   │   │   │   │   └── package.zip
│   │   │   │   ├── workshop-01/                 # Warsztat (ocena wzajemna)
│   │   │   │   │   ├── workshop.yaml
│   │   │   │   │   └── rubric.yaml
│   │   │   │   ├── feedback-01/                 # Ankieta zwrotna
│   │   │   │   │   ├── feedback.yaml
│   │   │   │   │   └── questions.gift
│   │   │   │   ├── survey-01/                   # Ankieta
│   │   │   │   │   └── survey.yaml
│   │   │   │   ├── database-01/                 # Baza danych
│   │   │   │   │   ├── database.yaml
│   │   │   │   │   └── template.html
│   │   │   │   ├── external-tool-01/            # Narzędzie LTI
│   │   │   │   │   └── lti.yaml
│   │   │   │   └── label-01.md                  # Etykieta (HTML)
│   │   │   │
│   │   │   ├── 02-godnosc-czlowieka/
│   │   │   │   └── ... (analogiczna struktura)
│   │   │   │
│   │   │   └── 03-podsumowanie/
│   │   │       └── ... (analogiczna struktura)
│   │   │
│   │   ├── question-bank/                       # Bank pytań kursu
│   │   │   ├── categories.yaml                  # Kategorie pytań
│   │   │   ├── multichoice/
│   │   │   │   ├── set-01.gift
│   │   │   │   ├── set-02.gift
│   │   │   │   └── set-01.yaml
│   │   │   ├── truefalse/
│   │   │   │   └── set-01.gift
│   │   │   ├── shortanswer/
│   │   │   │   └── set-01.gift
│   │   │   ├── numerical/
│   │   │   │   └── set-01.gift
│   │   │   ├── matching/
│   │   │   │   └── set-01.gift
│   │   │   ├── essay/
│   │   │   │   └── set-01.gift
│   │   │   ├── missingword/
│   │   │   │   └── set-01.gift
│   │   │   └── calculated/
│   │   │       └── set-01.yaml
│   │   │
│   │   ├── media/                               # Zasoby multimedialne kursu
│   │   │   ├── images/
│   │   │   │   ├── logo.png
│   │   │   │   ├── diagram-01.svg
│   │   │   │   └── photo-01.jpg
│   │   │   ├── videos/
│   │   │   │   ├── intro.mp4
│   │   │   │   └── lecture-01.webm
│   │   │   ├── audio/
│   │   │   │   └── podcast-01.mp3
│   │   │   └── documents/
│   │   │       ├── syllabus.pdf
│   │   │       └── reading-list.pdf
│   │   │
│   │   ├── output/                              # Wygenerowane pliki (gitignore)
│   │   │   ├── moodle-xml/
│   │   │   │   └── course.xml
│   │   │   ├── gift/
│   │   │   │   └── all-questions.gift
│   │   │   ├── mbz/
│   │   │   │   └── course.mbz
│   │   │   └── imscc/
│   │   │       └── course.imscc
│   │   │
│   │   └── changelog.md                         # Historia zmian kursu
│   │
│   └── 02-wiara-i-rozum/
│       └── ... (analogiczna struktura)
│
├── shared/                                      # Zasoby współdzielone
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
│   ├── h5p-libraries/
│   └── lti-configs/
│       └── tool-providers.yaml
│
├── question-bank-global/                        # Globalny bank pytań
│   ├── categories.yaml
│   ├── theology/
│   │   ├── multichoice.gift
│   │   └── truefalse.gift
│   ├── philosophy/
│   │   └── ...
│   ├── ethics/
│   │   └── ...
│   └── scripture/
│       └── ...
│
├── templates/                                   # Szablony konwersji
│   ├── moodle-xml/
│   │   ├── course-backup.xml.j2
│   │   ├── section.xml.j2
│   │   ├── page-module.xml.j2
│   │   ├── quiz-module.xml.j2
│   │   ├── lesson-module.xml.j2
│   │   ├── assignment-module.xml.j2
│   │   ├── forum-module.xml.j2
│   │   ├── book-module.xml.j2
│   │   └── question-types/
│   │       ├── multichoice.xml.j2
│   │       ├── truefalse.xml.j2
│   │       ├── shortanswer.xml.j2
│   │       ├── numerical.xml.j2
│   │       ├── matching.xml.j2
│   │       ├── essay.xml.j2
│   │       └── missingword.xml.j2
│   │
│   ├── gift/
│   │   ├── multichoice.gift.j2
│   │   ├── truefalse.gift.j2
│   │   ├── shortanswer.gift.j2
│   │   ├── numerical.gift.j2
│   │   ├── matching.gift.j2
│   │   └── essay.gift.j2
│   │
│   ├── imscc/
│   │   ├── imsmanifest.xml.j2
│   │   ├── course_structure.xml.j2
│   │   └── resources.xml.j2
│   │
│   ├── schemas/
│   │   ├── course.schema.json
│   │   ├── section.schema.json
│   │   ├── quiz.schema.json
│   │   ├── question.schema.json
│   │   ├── lesson.schema.json
│   │   ├── assignment.schema.json
│   │   ├── forum.schema.json
│   │   ├── glossary.schema.json
│   │   ├── book.schema.json
│   │   ├── workshop.schema.json
│   │   ├── feedback.schema.json
│   │   ├── h5p.schema.json
│   │   ├── lti.schema.json
│   │   └── completion.schema.json
│   │
│   └── prompts/
│       ├── generate-course-outline.md
│       ├── generate-section-content.md
│       ├── generate-quiz-questions.md
│       ├── generate-lesson-branches.md
│       ├── generate-assignment-rubric.md
│       ├── review-content-ethics.md
│       └── convert-to-gift.md
│
├── scripts/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py
│   │
│   ├── validators/
│   │   ├── validate_course.py
│   │   ├── validate_yaml.py
│   │   ├── validate_gift.py
│   │   ├── validate_xml.py
│   │   ├── validate_links.py
│   │   ├── validate_media.py
│   │   └── validate_accessibility.py
│   │
│   ├── converters/
│   │   ├── yaml_to_moodle_xml.py
│   │   ├── yaml_to_gift.py
│   │   ├── md_to_html.py
│   │   ├── gift_to_moodle_xml.py
│   │   ├── moodle_xml_to_mbz.py
│   │   ├── yaml_to_imscc.py
│   │   ├── latex_to_mathjax.py
│   │   └── asciidoc_to_html.py
│   │
│   ├── builders/
│   │   ├── build_course.py
│   │   ├── build_quiz.py
│   │   ├── build_question_bank.py
│   │   ├── build_mbz.py
│   │   ├── build_imscc.py
│   │   └── build_scorm.py
│   │
│   ├── importers/
│   │   ├── moodle_api_client.py
│   │   ├── import_course.py
│   │   ├── import_quiz.py
│   │   ├── import_questions.py
│   │   ├── import_users.py
│   │   └── import_grades.py
│   │
│   ├── exporters/
│   │   ├── export_course.py
│   │   ├── export_quiz.py
│   │   └── export_grades.py
│   │
│   ├── generators/
│   │   ├── qwen_client.py
│   │   ├── generate_course.py
│   │   ├── generate_questions.py
│   │   ├── generate_content.py
│   │   └── review_content.py
│   │
│   ├── utilities/
│   │   ├── slugify.py
│   │   ├── media_optimizer.py
│   │   ├── link_checker.py
│   │   ├── accessibility_checker.py
│   │   └── changelog_generator.py
│   │
│   ├── cli.py
│   └── Makefile
│
├── tests/
│   ├── test_validators.py
│   ├── test_converters.py
│   ├── test_builders.py
│   ├── fixtures/
│   │   ├── sample-course/
│   │   ├── sample-quiz.gift
│   │   └── expected-output/
│   └── integration/
│       ├── test_moodle_api.py
│       └── test_import_export.py
│
├── docs/
│   ├── 01-ARCHITECTURE.md
│   ├── 02-CONTENT-FORMATS.md
│   ├── 03-QUESTION-FORMATS.md
│   ├── 04-AUTOMATION-AND-ETHICS.md
│   └── changelog.md
│
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── Makefile


---

<a id="zasady-nazewnictwa"></a>
## 3. Zasady nazewnictwa

| Element | Konwencja | Przykład |
|---|---|---|
| Katalogi kursów | `NN-nazwa-kursu` (slug) | `01-prawda-i-natura` |
| Katalogi sekcji | `NN-nazwa-sekcji` | `01-wprowadzenie` |
| Pliki stron | `page-NN-tytul.md` | `page-01-czym-jest-prawda.md` |
| Pliki quizów | `quiz-NN/` (katalog) | `quiz-01/` |
| Pliki lekcji | `lesson-NN/` (katalog) | `lesson-01/` |
| Pliki zadań | `assignment-NN/` (katalog) | `assignment-01/` |
| Pliki GIFT | `.gift` lub `.txt` | `questions.gift` |
| Pliki YAML | `.yaml` lub `.yml` | `course.yaml` |
| Pliki XML | `.xml` | `questions.xml` |
| Obrazy | `kebab-case.ext` | `diagram-prawdy.png` |
| Wideo | `kebab-case.ext` | `wyklad-01-wstep.mp4` |

---

<a id="gitignore"></a>
## 4. Plik `.gitignore`

```gitignore
# Wygenerowane pliki wyjściowe
courses/*/output/
*.mbz
*.imscc

# Środowisko Python
__pycache__/
*.py[cod]
*$py.class
.env
.venv/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logi
*.log

# Tymczasowe
*.tmp
*.temp


---

<a id="gitattributes"></a>
## 5. Plik `.gitattributes`

```gitattributes
# Normalizacja końca linii
* text=auto

# Pliki binarne
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.mp4 binary
*.webm binary
*.mp3 binary
*.pdf binary
*.h5p binary
*.zip binary

# Pliki GIFT i YAML jako tekst
*.gift text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
*.md text eol=lf
*.xml text eol=lf


---

## Podsumowanie kluczowych formatów plików

| Cel | Format | Rozszerzenie |
|---|---|---|
| Metadane | YAML | `.yaml` |
| Treści | Markdown | `.md` |
| Pytania (tekstowe) | GIFT | `.gift`, `.txt` |
| Pytania (strukturalne) | YAML | `.yaml` |
| Pytania (natywne Moodle) | XML | `.xml` |
| Pytania (proste MC) | Aiken | `.txt` |
| Pakiet kursu | Moodle Backup | `.mbz` |
| Standard branżowy | Common Cartridge | `.imscc` |
| Schematy walidacji | JSON Schema | `.json` |
| Szablony konwersji | Jinja2 | `.j2` |


---


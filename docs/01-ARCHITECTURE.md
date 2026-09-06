
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


---

<a id="moodle-formats-deep"></a>
## 8. Szczegółowa specyfikacja formatów Moodle

### 8.1. Format MBZ (Moodle Backup)

Format `.mbz` to natywny format backupu Moodle, będący archiwum ZIP z określoną strukturą wewnętrznych plików XML.

#### Struktura pliku MBZ:
```
course.mbz (ZIP archive)
├── backup-moodle2/
│   ├── course.xml              # Główna definicja kursu
│   ├── section.xml             # Definicje sekcji
│   ├── activity.xml            # Lista aktywności
│   ├── roles.xml               # Role i uprawnienia
│   ├── gradebook.xml           # Konfiguracja oceniania
│   ├── completion.xml          # Kryteria ukończenia
│   ├── logs.xml                # Logi aktywności
│   └── files/                  # Katalog z plikami zasobów
│       ├── file_1
│       ├── file_2
│       └── ...
└── moodle_backup.xml           # Metadane backupu
```

#### Kluczowe elementy `course.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<moodle_backup>
  <information>
    <name>course_backup</name>
    <moodle_version>2023100904</moodle_version>
    <moodle_release>4.3</moodle_release>
    <backup_version>2023100904</backup_version>
    <backup_release>4.3</backup_release>
    <date>1699876543</date>
    <mnet_remoteusers>false</mnet_remoteusers>
    <include_files>true</include_files>
    <include_activities>true</include_activities>
    <include_blocks>true</include_blocks>
    <include_badges>true</include_badges>
    <include_calendarevents>true</include_calendarevents>
    <include_comments>true</include_comments>
    <include_competencies>true</include_competencies>
    <include_course_contents>true</include_course_contents>
    <include_groups>true</include_groups>
    <include_grades>true</include_grades>
    <include_groupings>true</include_groupings>
    <include_logs>true</include_logs>
    <include_questioncategories>true</include_questioncategories>
    <include_users>false</include_users>
  </information>
  <settings>
    <!-- Ustawienia przywracania -->
  </settings>
  <activities>
    <!-- Lista wszystkich aktywności -->
  </activities>
  <sections>
    <!-- Definicje sekcji kursu -->
  </sections>
</moodle_backup>
```

#### Tworzenie backupu MBZ programowo:
```python
import zipfile
from pathlib import Path

def create_mbz_backup(course_data: dict, output_path: str):
    """Tworzy plik .mbz z danych kursu."""
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as mbz:
        # Dodaj moodle_backup.xml
        backup_info = create_backup_metadata(course_data)
        mbz.writestr('moodle_backup.xml', backup_info)
        
        # Dodaj backup-moodle2/course.xml
        course_xml = create_course_xml(course_data)
        mbz.writestr('backup-moodle2/course.xml', course_xml)
        
        # Dodaj pliki zasobów
        for file_path in course_data.get('files', []):
            arcname = f"backup-moodle2/files/{Path(file_path).name}"
            mbz.write(file_path, arcname)
    
    return output_path
```

### 8.2. Common Cartridge (IMS CC)

Common Cartridge to standard branżowy umożliwiający przenoszenie treści między różnymi platformami LMS (Moodle, Canvas, Blackboard, itp.).

#### Wersje IMS CC:
| Wersja | Rok | Główne funkcje |
|--------|-----|----------------|
| 1.0 | 2008 | Podstawowa struktura, zasoby, linki |
| 1.1 | 2010 | Autoryzacja, rozszerzone metadane |
| 1.2 | 2014 | LTI 1.0, lepsza obsługa quizów |
| 1.3 | 2019 | LTI 1.3, Advantage, improved security |

#### Struktura pliku IMSCC:
```
course.imscc (ZIP archive)
├── imsmanifest.xml           # Manifest IMS (główny plik konfiguracyjny)
├── org/imsglc/
│   └── cartridgeinfo.xml     # Informacje o kartridżu
├── resources/                # Zasoby kursu
│   ├── resource1/
│   │   ├── content.html
│   │   └── image.png
│   └── resource2/
│       └── quiz.xml
└── associations/             # Asocjacje między zasobami
```

#### Przykład `imsmanifest.xml`:
```xml
<?xml version="1.0" standalone="no"?>
<manifest identifier="CC-MANIFEST-ID" 
          xmlns="http://www.imsglobal.org/xsd/imscc_v1p3"
          xmlns:lti="http://www.imsglobal.org/xsd/imslticc_v1p0"
          xmlns:md="http://www.imsglobal.org/xsd/imsmd_v1p2">
  
  <metadata>
    <schema>IMS Content Packaging</schema>
    <schemaversion>1.1.3</schemaversion>
    <md:lom>
      <md:general>
        <md:title>
          <md:string>Prawda i Natura – Kurs antropologii</md:string>
        </md:title>
        <md:language>pl-PL</md:language>
      </md:general>
    </md:lom>
  </metadata>
  
  <organizations default="ORG-001">
    <organization identifier="ORG-001">
      <title>Kurs Prawda i Natura</title>
      <item identifier="ITEM-001" identifierref="RES-001">
        <title>Sekcja 1: Wprowadzenie</title>
      </item>
    </organization>
  </organizations>
  
  <resources>
    <resource identifier="RES-001" type="webcontent">
      <resourcefile href="resources/resource1/content.html"/>
    </resource>
  </resources>
</manifest>
```

### 8.3. SCORM (Sharable Content Object Reference Model)

SCORM to standard dla pakietów e-learningowych z możliwością trackingu postępów.

#### Wersje SCORM:
| Wersja | Nazwa | Rok | Charakterystyka |
|--------|-------|-----|-----------------|
| SCORM 1.1 | - | 2000 | Pierwsza wersja, rzadko używana |
| SCORM 1.2 | - | 2001 | Najpopularniejsza, szeroka obsługa |
| SCORM 2004 2nd Ed | - | 2004 | Sekwencjonowanie, nawigacja |
| SCORM 2004 3rd Ed | - | 2006 | Poprawki, stabilność |
| SCORM 2004 4th Ed | - | 2009 | Aktualna wersja |

#### Struktura pakietu SCORM:
```
scorm-package.zip
├── imsmanifest.xml           # Manifest SCORM (wymagany)
├── sco1/                     # Sharable Content Objects
│   ├── index.html
│   ├── script.js
│   └── style.css
├── assets/                   # Zasoby multimedialne
│   ├── image.png
│   └── video.mp4
└── adlcp_rootv1p2.xsd        # Schematy XSD (opcjonalne)
```

#### Przykład `imsmanifest.xml` dla SCORM 1.2:
```xml
<?xml version="1.0" standalone="no"?>
<manifest identifier="SCORM-COURSE-001" 
          version="1.0"
          xmlns="http://www.adlnet.gov/scorm/scorm_v1p2"
          xmlns:adlcp="http://www.adlnet.gov/scorm/additionalSchema">
  
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  
  <organizations default="ORG-001">
    <organization identifier="ORG-001">
      <title>Kurs Prawda i Natura</title>
      <item identifier="SCO-001" identifierref="RES-001">
        <title>Wprowadzenie do prawa naturalnego</title>
      </item>
    </organization>
  </organizations>
  
  <resources>
    <resource identifier="RES-001" type="webcontent" adlcp:scormtype="sco">
      <resourcefile href="sco1/index.html"/>
    </resource>
  </resources>
</manifest>
```

#### Komunikacja SCORM z LMS (JavaScript API):
```javascript
// Inicjalizacja połączenia z LMS
var API = getAPI();
var result = API.LMSInitialize("");

// Ustawienie statusu ukończenia
API.LMSSetValue("cmi.core.lesson_status", "completed");

// Ustawienie wyniku (score)
API.LMSSetValue("cmi.core.score.raw", "85");
API.LMSSetValue("cmi.core.score.min", "0");
API.LMSSetValue("cmi.core.score.max", "100");

// Zapisanie danych
API.LMSCommit("");

// Zamknięcie połączenia
API.LMSFinish("");

function getAPI() {
  // Szukanie obiektu API w oknach nadrzędnych
  var currentWindow = window;
  while (currentWindow.parent !== currentWindow) {
    if (currentWindow.parent.API) {
      return currentWindow.parent.API;
    }
    currentWindow = currentWindow.parent;
  }
  return null;
}
```

### 8.4. LTI (Learning Tools Interoperability)

LTI umożliwia integrację zewnętrznych narzędzi edukacyjnych z Moodle.

#### Wersje LTI:
| Wersja | Rok | Główne zmiany |
|--------|-----|---------------|
| LTI 1.0 | 2010 | Podstawowa integracja |
| LTI 1.1 | 2012 | Usługi REST, rozszerzenia |
| LTI 1.2 | 2014 | Restful services |
| LTI 1.3/Advantage | 2019 | OAuth 2.0, JSON Web Tokens, improved security |

#### Konfiguracja LTI 1.3 w Moodle (`lti.yaml`):
```yaml
lti:
  name: "External Quiz Tool"
  tool_url: "https://external-tool.example.com/launch"
  oidc_initiation_url: "https://external-tool.example.com/initiate"
  jwks_url: "https://external-tool.example.com/jwks"
  
  # Client credentials (LTI 1.3)
  client_id: "moodle-client-12345"
  deployment_id: "deployment-001"
  
  # Scopes
  scopes:
    - "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"
    - "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
    - "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
  
  # Custom parameters
  custom_parameters:
    resource_link_id: "$ResourceLink.id"
    user_id: "$User.id"
    context_id: "$Context.id"
  
  # Privacy settings
  privacy_level: "anonymous"
  
  # Grades integration
  grade_services:
    enabled: true
    lineitem_url: "https://moodle.example.com/grade/lineitems"
```

### 8.5. H5P (HTML5 Package)

H5P to format interaktywnych treści HTML5 obsługiwany natywnie przez Moodle.

#### Struktura pliku H5P:
```
content.h5p (ZIP archive)
├── content/
│   └── content.json          # Główna zawartość
├── libraries/                # Biblioteki H5P
│   ├── H5P.CoursePresentation-1.24/
│   │   ├── library.json
│   │   ├── css/
│   │   ├── js/
│   │   └── semantics/
│   └── H5P.Image-1.1/
└── h5p.json                  # Metadane pakietu
```

#### Przykład `h5p.json`:
```json
{
  "mainLibrary": "H5P.CoursePresentation",
  "preloadedDependencies": [
    {"machineName": "H5P.CoursePresentation", "majorVersion": 1, "minorVersion": 24},
    {"machineName": "H5P.Image", "majorVersion": 1, "minorVersion": 1}
  ],
  "title": "Interaktywna prezentacja: Prawda naturalna",
  "language": "pl",
  "author": "Zespół Misyjny",
  "license": "CC BY-SA 4.0",
  "embedType": "div",
  "contentType": "Course Presentation"
}
```

#### Typy treści H5P dostępne w Moodle:
| Typ | Opis | Zastosowanie |
|-----|------|--------------|
| Course Presentation | Interaktywne slajdy | Lekcje multimedialne |
| Interactive Video | Wideo z pytaniami | Materiały wideo z check-pointami |
| Drag and Drop | Przeciąganie elementów | Ćwiczenia dopasowania |
| Branching Scenario | Scenariusze rozgałęzione | Symulacje decyzyjne |
| Quiz | Różne typy pytań | Sprawdziany wiedzy |
| Timeline | Oś czasu | Prezentacja historyczna |
| Flashcards | Fiszki | Nauka pojęć |
| Dialog Cards | Karty dialogowe | Nauka języków |
| Accordion | Rozwijane sekcje | Organizacja treści |
| Hotspot Image | Obraz z punktami | Anotacje wizualne |

---

## Podsumowanie kluczowych formatów plików

| Cel | Format | Rozszerzenie | Poziom złożoności |
|---|---|---|---|
| Metadane | YAML | `.yaml` | Niski |
| Treści | Markdown | `.md` | Niski |
| Pytania (tekstowe) | GIFT | `.gift`, `.txt` | Średni |
| Pytania (strukturalne) | YAML | `.yaml` | Niski |
| Pytania (natywne Moodle) | XML | `.xml` | Wysoki |
| Pytania (proste MC) | Aiken | `.txt` | Niski |
| Pełny backup kursu | Moodle Backup | `.mbz` | Wysoki |
| Standard branżowy | Common Cartridge | `.imscc` | Wysoki |
| Pakiet e-learning | SCORM | `.zip` | Wysoki |
| Integracja zewnętrzna | LTI | `.xml` + konfiguracja | Średni |
| Treści interaktywne | H5P | `.h5p` | Średni |
| Schematy walidacji | JSON Schema | `.json` | Średni |
| Szablony konwersji | Jinja2 | `.j2` | Średni |


---

# Qwen Moodle Course Generator

## 📚 Struktura Repozytorium

```
qwen-moodle-courses/
├── README.md                          # Ten plik
├── docs/                              # Dokumentacja techniczna
│   ├── qwen_moodle_strategy_architecture.md
│   ├── qwen_coder_formats_specification.md
│   └── qwen_moodle_implementation_guide.md
│
├── courses/                           # Główny katalog kursów
│   │
│   ├── course-01-intro-programowania/ # Kurs 1: Wstęp do programowania
│   │   ├── course.yaml                # Metadane kursu (nazwa, opis, format)
│   │   │
│   │   ├── sections/                  # Sekcje tematyczne
│   │   │   ├── 01/                    # Sekcja 1
│   │   │   │   ├── topic.md           # Treść tematyczna (Markdown)
│   │   │   │   ├── activity.md        # Opis aktywności
│   │   │   │   └── quiz.yaml          # Konfiguracja quizu sekcji
│   │   │   ├── 02/                    # Sekcja 2
│   │   │   │   ├── topic.md
│   │   │   │   ├── activity.md
│   │   │   │   └── quiz.yaml
│   │   │   └── 03/                    # Sekcja 3
│   │   │       ├── topic.md
│   │   │       ├── activity.md
│   │   │       └── quiz.yaml
│   │   │
│   │   ├── questions/                 # Bank pytań kursu
│   │   │   ├── gift/                  # Pytania w formacie GIFT
│   │   │   │   └── questions.gift
│   │   │   ├── yaml/                  # Pytania w formacie YAML
│   │   │   │   └── questions.yaml
│   │   │   └── xml/                   # Pytania w formacie XML Moodle
│   │   │       └── questions.xml
│   │   │
│   │   └── assets/                    # Zasoby multimedialne
│   │       ├── images/                # Obrazy (.png, .jpg, .svg)
│   │       │   └── .gitkeep
│   │       ├── videos/                # Wideo (.mp4, .webm)
│   │       │   └── .gitkeep
│   │       └── documents/             # Dokumenty (.pdf, .docx)
│   │           └── .gitkeep
│   │
│   ├── course-02-bazy-danych/         # Kurs 2: Bazy danych
│   │   ├── course.yaml
│   │   ├── sections/
│   │   │   ├── 01/
│   │   │   │   ├── topic.md
│   │   │   │   ├── activity.md
│   │   │   │   └── quiz.yaml
│   │   │   ├── 02/
│   │   │   │   ├── topic.md
│   │   │   │   ├── activity.md
│   │   │   │   └── quiz.yaml
│   │   │   └── 03/
│   │   │       ├── topic.md
│   │   │       ├── activity.md
│   │   │       └── quiz.yaml
│   │   ├── questions/
│   │   │   ├── gift/
│   │   │   │   └── questions.gift
│   │   │   ├── yaml/
│   │   │   │   └── questions.yaml
│   │   │   └── xml/
│   │   │       └── questions.xml
│   │   └── assets/
│   │       ├── images/
│   │       │   └── .gitkeep
│   │       ├── videos/
│   │       │   └── .gitkeep
│   │       └── documents/
│   │           └── .gitkeep
│   │
│   └── course-03-sieci-komputerowe/   # Kurs 3: Sieci komputerowe
│       ├── course.yaml
│       ├── sections/
│       │   ├── 01/
│       │   │   ├── topic.md
│       │   │   ├── activity.md
│       │   │   └── quiz.yaml
│       │   ├── 02/
│       │   │   ├── topic.md
│       │   │   ├── activity.md
│       │   │   └── quiz.yaml
│       │   └── 03/
│       │       ├── topic.md
│       │       ├── activity.md
│       │       └── quiz.yaml
│       ├── questions/
│       │   ├── gift/
│       │   │   └── questions.gift
│       │   ├── yaml/
│       │   │   └── questions.yaml
│       │   └── xml/
│       │       └── questions.xml
│       └── assets/
│           ├── images/
│           │   └── .gitkeep
│           ├── videos/
│           │   └── .gitkeep
│           └── documents/
│               └── .gitkeep
│
├── scripts/                           # Skrypty bash automatyzujące proces
│   ├── build-course.sh                # Budowanie pakietu kursu
│   ├── validate-course.sh             # Walidacja struktury i plików
│   ├── export-to-moodle.sh            # Eksport do formatu .mbz
│   ├── generate-quiz.sh               # Generowanie quizów z pytań
│   └── sync-assets.sh                 # Synchronizacja zasobów
│
├── templates/                         # Szablony dla nowych kursów
│   ├── course-template.yaml
│   ├── section-template.md
│   └── quiz-template.yaml
│
├── .github/
│   └── workflows/
│       └── moodle-ci.yml              # GitHub Actions CI/CD
│
├── .gitignore
└── LICENSE
```

## 🎯 Cel Projektu

Repozytorium służy do automatycznego generowania kompletnych kursów Moodle przy wykorzystaniu agentów AI:

- **Qwen Code** - tworzenie struktury repozytorium, konfiguracji CI/CD, skryptów budujących
- **Qwen Coder** - generowanie treści merytorycznych, pytań quizowych, scenariuszy lekcji

## 📋 Opis Plików

### Katalog `courses/`

Każdy kurs posiada własny podkatalog z następującą strukturą:

| Plik/Katalog | Opis |
|-------------|------|
| `course.yaml` | Metadane kursu: nazwa, krótki opis, format kursu (tygodniowy, tematyczny), liczba sekcji, język |
| `sections/` | Podkatalogi numerowane (01, 02, 03...) zawierające materiały dydaktyczne |
| `questions/` | Bank pytań w trzech formatach: GIFT, YAML, XML |
| `assets/` | Zasoby multimedialne: obrazy, wideo, dokumenty |

### Sekcje Kursu (`sections/NN/`)

Każda sekcja zawiera:

| Plik | Format | Opis |
|------|--------|------|
| `topic.md` | Markdown | Główna treść edukacyjna sekcji |
| `activity.md` | Markdown | Opis aktywności, zadań, ćwiczeń |
| `quiz.yaml` | YAML | Konfiguracja quizu sekcji (ustawienia, limit czasu, liczba prób) |

### Bank Pytań (`questions/`)

| Format | Rozszerzenie | Zastosowanie |
|--------|-------------|--------------|
| GIFT | `.gift` | Import bezpośredni do Moodle, wszystkie typy pytań |
| YAML | `.yaml` | Konfiguracja quizów, strukturyzowane dane |
| XML | `.xml` | Natywny format importu Moodle, pełna kompatybilność |

## 🚀 Użycie

### 1. Tworzenie nowego kursu

```bash
# Skopiuj szablon
cp -r templates/course-template courses/course-XX-nazwa-kursu

# Edytuj metadane
nano courses/course-XX-nazwa-kursu/course.yaml
```

### 2. Budowanie kursu

```bash
./scripts/build-course.sh course-01-intro-programowania
```

### 3. Walidacja

```bash
./scripts/validate-course.sh course-01-intro-programowania
```

### 4. Eksport do Moodle

```bash
./scripts/export-to-moodle.sh course-01-intro-programowania
```

Wygenerowany plik `.mbz` można zaimportować do Moodle przez:
- **Interfejs GUI**: Administracja → Kursy → Import
- **CLI Moodle**: `php admin/cli/backup.php --file=/path/to/course.mbz`

## 🔧 Skrypty

| Skrypt | Opis |
|--------|------|
| `build-course.sh` | Kompiluje wszystkie sekcje i zasoby w pakiet gotowy do eksportu |
| `validate-course.sh` | Sprawdza poprawność struktury, formatów i referencji |
| `export-to-moodle.sh` | Generuje finalny plik `.mbz` do importu w Moodle |
| `generate-quiz.sh` | Tworzy quizy na podstawie plików z banku pytań |
| `sync-assets.sh` | Synchronizuje i optymalizuje zasoby multimedialne |

## 📄 Licencja

MIT License - zobacz plik [LICENSE](LICENSE)

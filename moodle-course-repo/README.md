# 🎓 Moodle Course Repository - Automated Course Generation with Qwen AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Moodle Version](https://img.shields.io/badge/Moodle-4.x-f06a2e.svg)](https://moodle.org)
[![Qwen AI](https://img.shields.io/badge/Qwen-Code%2FCoder-purple.svg)](https://qwen.ai)

## 📖 Opis Repozytorium

To repozytorium GitHub służy do **automatycznego generowania kursów edukacyjnych Moodle** przy wykorzystaniu agentów AI:
- **Qwen Code** - tworzy strukturę kursu, organizuje pliki i zarządza metadanymi
- **Qwen Coder** - generuje zawartość merytoryczną, pytania quizowe i aktywności w formatach kompatybilnych z Moodle

Repozytorium zawiera kompletną strukturę katalogów, szablony plików, skrypty konwertujące oraz dokumentację umożliwiającą eksport kursów do formatu `.mbz` (Moodle Backup) gotowego do importu na serwer Moodle.

---

## 🌳 Struktura Katalogów i Plików

```
moodle-course-repo/
├── README.md                          # Ten plik - główna dokumentacja
├── LICENSE                            # Licencja repozytorium
├── .gitignore                         # Pliki ignorowane przez Git
├── .github/
│   └── workflows/
│       ├── build_course.yml           # CI/CD: Budowa kursu
│       ├── validate_course.yml        # CI/CD: Walidacja struktury
│       └── deploy_moodle.yml          # CI/CD: Automatyczny deployment
│
├── course-metadata/                   # Metadane kursu (konfiguracja główna)
│   ├── course.yaml                    # Definicja kursu: nazwa, opis, kategoria, ustawienia
│   └── manifest.json                  # Manifest JSON z wersjami i checksumami
│
├── sections/                          # Sekcje/Tematy kursu (numeryczne lub tygodniowe)
│   ├── 01-introduction/               # Sekcja 1: Wprowadzenie
│   │   ├── section.yaml               # Metadane sekcji: tytuł, opis, cele kształcenia
│   │   ├── content.md                 # Zawartość merytoryczna w Markdown
│   │   └── activities.yaml            # Aktywności sekcji: zadania, forum, zasoby
│   │
│   ├── 02-basics/                     # Sekcja 2: Podstawy
│   │   ├── section.yaml
│   │   ├── content.md
│   │   └── activities.yaml
│   │
│   ├── 03-advanced/                   # Sekcja 3: Zagadnienia zaawansowane
│   │   ├── section.yaml
│   │   ├── content.md
│   │   └── activities.yaml
│   │
│   └── 04-assessment/                 # Sekcja 4: Ocena i egzystencja
│       ├── section.yaml
│       ├── content.md
│       └── quiz.yaml                  # Konfiguracja quizu końcowego
│
├── question-banks/                    # Banki pytań (puli pytań do quizów)
│   ├── multiple-choice/               # Pytania wielokrotnego wyboru
│   │   ├── questions.gift             # Format GIFT dla MCQ
│   │   └── questions.yaml             # Format YAML dla MCQ
│   │
│   ├── true-false/                    # Pytania prawda/fałsz
│   │   ├── questions.gift
│   │   └── questions.yaml
│   │
│   ├── matching/                      # Pytania typu dopasowanie
│   │   ├── questions.gift
│   │   └── questions.yaml
│   │
│   ├── essay/                         # Pytania otwarte (eseje)
│   │   ├── questions.gift
│   │   └── questions.yaml
│   │
│   ├── calculation/                   # Pytania obliczeniowe
│   │   ├── questions.gift
│   │   └── questions.yaml
│   │
│   └── bank.xml                       # Eksport XML wszystkich pytań (Moodle XML format)
│
├── assets/                            # Zasoby multimedialne i pliki binarne
│   ├── images/                        # Obrazy: diagramy, schematy, ilustracje (.png, .jpg, .svg)
│   │   └── .gitkeep
│   ├── videos/                        # Filmy: wykłady, tutoriale (.mp4, .webm)
│   │   └── .gitkeep
│   ├── documents/                     # Dokumenty: PDF, DOCX do pobrania
│   │   └── .gitkeep
│   └── presentations/                 # Prezentacje: PPTX, ODP
│       └── .gitkeep
│
├── scripts/                           # Skrypty automatyzujące budowę kursu
│   ├── build_course.py                # Główny skrypt budujący strukturę kursu
│   ├── convert_to_mbz.py              # Konwersja do formatu Moodle Backup (.mbz)
│   └── validate_course.py             # Walidacja poprawności struktury i formatów
│
├── tests/                             # Testy jednostkowe i integracyjne
│   ├── test_converter.py              # Testy konwertera formatów
│   └── test_validator.py              # Testy walidatora kursu
│
├── docs/                              # Dokumentacja techniczna i użytkownika
│   ├── 01_ARCHITECTURE.md             # Architektura repozytorium i przepływ danych
│   ├── 02_FORMATS_SPECIFICATION.md    # Specyfikacja formatów: GIFT, YAML, XML, Aiken
│   ├── 03_IMPLEMENTATION_GUIDE.md     # Przewodnik wdrożeniowy krok po kroku
│   ├── API_REFERENCE.md               # Referencje API skryptów Python
│   └── DEPLOYMENT.md                  # Instrukcje deploymentu na serwer Moodle
│
└── examples/                          # Przykłady i szablony do nauki
    ├── sample_section.yaml            # Przykładowa definicja sekcji
    └── sample_quiz.gift               # Przykładowy quiz w formacie GIFT
```

---

## 🚀 Szybki Start

### 1. Klonowanie Repozytorium

```bash
git clone https://github.com/twoj-user/moodle-course-repo.git
cd moodle-course-repo
```

### 2. Instalacja Zależności

```bash
pip install -r requirements.txt
```

### 3. Generowanie Kursu z Qwen AI

Uruchom agenta Qwen Code w celu wygenerowania struktury kursu:

```bash
python scripts/build_course.py --config course-metadata/course.yaml --output ./build
```

### 4. Budowa Pakietu Moodle (.mbz)

```bash
python scripts/convert_to_mbz.py --input ./build --output course-backup.mbz
```

### 5. Walidacja Kursu

```bash
python scripts/validate_course.py --course ./build
```

### 6. Import do Moodle

- **Przez GUI:** Zaloguj się do Moodle → Kursy → Import → Wybierz `course-backup.mbz`
- **Przez CLI:** 
  ```bash
  php admin/cli/backup.php --file=/path/to/course-backup.mbz --categoryid=1
  ```

---

## 📄 Formaty Plików

### Metadane Kursu (`course.yaml`)

```yaml
course:
  shortname: "WPROG-2025"
  fullname: "Wstęp do Programowania 2025"
  category: "Informatyka"
  summary: "Kurs wprowadzający do programowania w Pythonie"
  format: "topics"
  numsections: 4
  lang: "pl"
  enablecompletion: true
  showactivitydates: true
```

### Sekcja Kursu (`section.yaml`)

```yaml
section:
  number: 1
  title: "Wprowadzenie do Programowania"
  summary: "Podstawowe pojęcia: zmienne, typy danych, operatory"
  availability:
    startdate: "2025-01-15T00:00:00Z"
    enddate: "2025-01-30T23:59:59Z"
  completioncriteria:
    - type: "view"
      required: true
    - type: "quiz"
      grade_required: 70
```

### Pytania Quizowe (GIFT Format)

```gift
// Pytanie wielokrotnego wyboru
::Q001:: Jaki jest wynik 2 + 2? {
  =4
  ~5
  ~3
  ~6
}

// Pytanie prawda/fałsz
::Q002:: Python jest językiem kompilowanym. {F}

// Pytanie typu dopasowanie
::Q003:: Dopasuj język do roku powstania: {
  =Python -> 1991
  =Java -> 1995
  =JavaScript -> 1995
}
```

### Aktywności (`activities.yaml`)

```yaml
activities:
  - type: "page"
    name: "Witamy w kursie"
    content: "content.md"
    completion: "view"
    
  - type: "quiz"
    name: "Sprawdzian 1"
    questionbank: "question-banks/multiple-choice/questions.gift"
    timelimit: 1800
    attempts: 2
    
  - type: "assignment"
    name: "Zadanie domowe 1"
    description: "Napisz program w Pythonie..."
    duedate: "2025-01-25T23:59:59Z"
    maxgrade: 100
    
  - type: "forum"
    name: "Dyskusja ogólna"
    subscription: "optional"
```

---

## 🤖 Integracja z Qwen AI

### Qwen Code - Agent Strukturalny

Qwen Code odpowiada za:
- Tworzenie hierarchii katalogów zgodnie ze specyfikacją
- Generowanie plików konfiguracyjnych YAML/JSON
- Zarządzanie zależnościami między sekcjami
- Organizację banków pytań według typów
- Konfigurację workflow GitHub Actions

**Przykład polecenia dla Qwen Code:**
```
Stwórz strukturę kursu "Bezpieczeństwo Cybernetyczne" z 6 sekcjami tematycznymi.
Dla każdej sekcji wygeneruj plik section.yaml z celami kształcenia,
plik content.md z materiałem teoretycznym oraz activities.yaml z listą aktywności.
Utwórz bank 50 pytań w formacie GIFT podzielonych na 5 kategorii.
```

### Qwen Coder - Agent Merytoryczny

Qwen Coder odpowiada za:
- Pisanie treści edukacyjnych w formacie Markdown
- Generowanie pytań quizowych w formatach: GIFT, YAML, XML, Aiken
- Tworzenie scenariuszy lekcji interaktywnych
- Przygotowanie przykładów kodu i studiów przypadku
- Redagowanie feedbacku do odpowiedzi

**Przykład polecenia dla Qwen Coder:**
```
Napisz 10 pytań wielokrotnego wyboru z zakresu kryptografii symetrycznej.
Format: GIFT. Dołącz szczegółowy feedback dla każdej odpowiedzi.
Poziom trudności: średniozaawansowany. Język: polski.
```

---

## ⚙️ GitHub Actions - Automatyzacja CI/CD

### Workflow: Budowa Kursu (`.github/workflows/build_course.yml`)

```yaml
name: Build Moodle Course

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Validate course structure
      run: python scripts/validate_course.py --course ./
    
    - name: Build course package
      run: python scripts/convert_to_mbz.py --output course-backup.mbz
    
    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: moodle-course-backup
        path: course-backup.mbz
```

### Workflow: Deployment na Moodle (`.github/workflows/deploy_moodle.yml`)

```yaml
name: Deploy to Moodle Server

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Download backup
      uses: actions/download-artifact@v4
      with:
        name: moodle-course-backup
    
    - name: Deploy via Moodle CLI
      run: |
        ssh ${{ secrets.MOODLE_SERVER }} "php /var/www/moodle/admin/cli/restore.php \
          --file=/tmp/course-backup.mbz \
          --categoryid=${{ secrets.MOODLE_CATEGORY_ID }} \
          --userid=${{ secrets.MOODLE_ADMIN_USER }}"
```

---

## 📊 Tabela Formatów Plików

| Rozszerzenie | Format | Zastosowanie | Narzędzia |
|-------------|--------|--------------|-----------|
| `.yaml` / `.yml` | YAML | Metadane kursu, konfiguracja sekcji, definicje aktywności | Qwen Code, Python PyYAML |
| `.md` | Markdown | Treści edukacyjne, opisy lekcji, instrukcje | Qwen Coder, Pandoc |
| `.gift` | GIFT | Pytania quizowe (wszystkie typy) | Qwen Coder, Moodle Import |
| `.xml` | Moodle XML | Banki pytań, import/export między kursami | Qwen Coder, Moodle XML Parser |
| `.json` | JSON | Manifesty, konfiguracja CI/CD, API responses | Python json, Node.js |
| `.mbz` | Moodle Backup | Finalny pakiet kursu do importu | scripts/convert_to_mbz.py |
| `.pdf` | PDF | Materiały do pobrania, certyfikaty | LaTeX, wkhtmltopdf |
| `.png` / `.jpg` / `.svg` | Obrazy | Diagramy, infografiki, zrzuty ekranu | Draw.io, Canva |
| `.mp4` / `.webm` | Wideo | Wykłady wideo, tutoriale screencast | OBS Studio, FFmpeg |

---

## 🔧 Skrypty Python

### `scripts/build_course.py`

Buduje kompletną strukturę kursu na podstawie pliku konfiguracyjnego `course.yaml`.

**Użycie:**
```bash
python scripts/build_course.py --config course-metadata/course.yaml --output ./build --verbose
```

**Opcje:**
- `--config`: Ścieżka do pliku YAML z metadanymi kursu
- `--output`: Katalog wyjściowy dla zbudowanego kursu
- `--verbose`: Tryb szczegółowego logowania
- `--dry-run`: Symulacja bez zapisu plików

### `scripts/convert_to_mbz.py`

Konwertuje zbudowaną strukturę kursu do formatu Moodle Backup (`.mbz`).

**Użycie:**
```bash
python scripts/convert_to_mbz.py --input ./build --output course-backup.mbz --compression gzip
```

**Opcje:**
- `--input`: Katalog z zbudowanym kursem
- `--output`: Nazwa pliku wyjściowego `.mbz`
- `--compression`: Algorytm kompresji (gzip, bz2, xz)
- `--include-assets`: Dołącz zasoby z katalogu `assets/`

### `scripts/validate_course.py`

Waliduje poprawność struktury kursu, formatów plików i spójność danych.

**Użycie:**
```bash
python scripts/validate_course.py --course ./build --strict --report validation-report.json
```

**Opcje:**
- `--course`: Ścieżka do katalogu z kursem
- `--strict`: Tryb ścisły (błędy krytyczne przerywają walidację)
- `--report`: Generuje raport JSON z wynikami walidacji
- `--fix`: Automatycznie naprawia wykryte problemy (gdzie możliwe)

---

## 📚 Dokumentacja

Szczegółowa dokumentacja znajduje się w katalogu `docs/`:

| Plik | Opis |
|------|------|
| [`01_ARCHITECTURE.md`](docs/01_ARCHITECTURE.md) | Architektura repozytorium, diagramy przepływu danych, model warstwowy |
| [`02_FORMATS_SPECIFICATION.md`](docs/02_FORMATS_SPECIFICATION.md) | Pełna specyfikacja formatów: GIFT, YAML, XML, Aiken, Markdown z front-matter |
| [`03_IMPLEMENTATION_GUIDE.md`](docs/03_IMPLEMENTATION_GUIDE.md) | Przewodnik wdrożeniowy: instalacja, konfiguracja, testowanie, troubleshooting |
| [`API_REFERENCE.md`](docs/API_REFERENCE.md) | Referencje API dla skryptów Python: klasy, funkcje, wyjątki |
| [`DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Instrukcje deploymentu na różne środowiska Moodle (on-premise, cloud, Docker) |

---

## 🧪 Testowanie

Uruchomienie zestawu testów:

```bash
# Wszystkie testy
pytest tests/

# Testy z coverage
pytest tests/ --cov=scripts --cov-report=html

# Pojedynczy plik testowy
pytest tests/test_converter.py -v
```

---

## 🔐 Bezpieczeństwo

- **Nie commituj poufnych danych** (hasła, klucze API) do repozytorium
- Używaj **GitHub Secrets** dla zmiennych środowiskowych w workflows
- Zasoby multimedialne powyżej 50MB przechowuj w **Git LFS** lub zewnętrznie (S3, Azure Blob)
- Regularnie aktualizuj zależności (`pip install --upgrade -r requirements.txt`)

---

## 🤝 Contributing

1. Forkuj repozytorium
2. Utwórz branch feature (`git checkout -b feature/nowa-funkcjonalnosc`)
3. Commit zmian (`git commit -m 'Dodano nową funkcjonalność'`)
4. Push na branch (`git push origin feature/nowa-funkcjonalnosc`)
5. Otwórz Pull Request

---

## 📄 Licencja

MIT License - zobacz plik [LICENSE](LICENSE) для szczegółów.

---

## 👥 Autorzy i Współpracownicy

- **Qwen Code Agent** - Architektura i struktura repozytorium
- **Qwen Coder Agent** - Generowanie treści i formatów pytań
- **Twoje Imię** - Implementacja i dostosowanie do potrzeb instytucji

---

## 📞 Kontakt i Wsparcie

- **Issues:** [GitHub Issues](https://github.com/twoj-user/moodle-course-repo/issues)
- **Email:** twoj.email@instytucja.edu.pl
- **Dokumentacja Moodle:** [docs.moodle.org](https://docs.moodle.org)

---

*Ostatnia aktualizacja: Styczeń 2025*  
*Wersja repozytorium: 1.0.0*

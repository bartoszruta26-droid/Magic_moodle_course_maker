# Strategia Integracji Qwen Code z Moodle: Architektura Repozytorium GitHub

## 1. Wstęp i Cel Dokumentu

Niniejszy dokument stanowi kompleksowy przewodnik architektoniczny dla agentów AI (Qwen Code oraz Qwen Coder), których zadaniem jest automatyczne generowanie, strukturyzacja i utrzymywanie kursów edukacyjnych w repozytorium GitHub w celu późniejszej bezproblemowej integracji z systemem LMS Moodle.

Celem jest zdefiniowanie standardu, który pozwoli na przekształcenie kodu źródłowego (Markdown, YAML, GIFT, XML) w natywny pakiet instalacyjny Moodle (`.mbz`) przy użyciu narzędzi CLI (Command Line Interface) lub skryptów CI/CD. Struktura ta musi uwzględniać specyfikę formatu backupu Moodle, wymagania dotyczące metadanych, zasobów multimedialnych oraz różnorodnych typów aktywności.

## 2. Filozofia "Moodle-as-Code" (MaC)

Podejście "Moodle-as-Code" traktuje kurs edukacyjny jako projekt programistyczny. Zamiast klikać w interfejsie graficznym Moodle, definiujemy strukturę kursu w plikach tekstowych. Agent Qwen Code pełni rolę architekta systemu, dbając o spójność katalogów, podczas gdy Qwen Coder wypełnia te struktury treścią merytoryczną i logiką quizów.

### Kluczowe Zalety:
- **Wersjonowanie:** Pełna historia zmian w treści kursu dzięki Git.
- **Automatyzacja:** Możliwość masowego tworzenia kursów i ich aktualizacji.
- **Modułowość:** Łatwe przenoszenie sekcji między różnymi kursami.
- **Recenzja:** Możliwość przeprowadzania Code Review dla treści edukacyjnych (Pull Requests).

## 3. Ogólna Struktura Katalogów Repozytorium

Repozytorium GitHub powinno być zorganizowane w sposób hierarchiczny, odzwierciedlający logiczną strukturę systemu Moodle. Poniżej przedstawiono rekomendowany drzewo katalogów.

```text
nazwa-repozytorium/
├── .github/                  # Konfiguracja workflow CI/CD (GitHub Actions)
│   └── workflows/
│       └── moodle-build.yml  # Skrypt budujący pakiet .mbz
├── courses/                  # Główny katalog zawierający definicje kursów
│   └── [KOD_KURSU]/          # Np. MAT-101, PROG-PYTHON-ADV
│       ├── course.json       # Metadane kursu (nazwa, opis, format)
│       ├── sections/         # Definicje sekcji/tygodni kursu
│       │   ├── 0_general/    # Sekcja ogólna (news forum, opis)
│       │   ├── 1_week/       # Sekcja 1
│       │   ├── 2_week/       # Sekcja 2
│       │   └── ...
│       ├── question_banks/   # Banki pytań współdzielone w kursie
│       │   ├── category.xml  # Struktura kategorii pytań
│       │   └── questions/    # Pliki z pytaniami (GIFT, YAML, XML)
│       ├── assets/           # Zasoby statyczne (obrazy, wideo, PDF)
│       │   ├── images/
│       │   ├── videos/
│       │   └── documents/
│       └── backups/          # Katalog wyjściowy dla wygenerowanych .mbz
├── templates/                # Szablony powtarzalnych aktywności
│   ├── quiz_template.xml
│   └── lesson_structure.json
├── scripts/                  # Skrypty pomocnicze (Python/Bash) do konwersji
│   ├── convert_to_moodle.py
│   └── validate_gift.sh
├── docs/                     # Dokumentacja projektu
└── README.md                 # Główny plik readme z instrukcją
```

## 4. Szczegółowa Specyfikacja Plików i Rozszerzeń

### 4.1. Metadane Kursu (`course.json` / `course.yaml`)

Agent Qwen Code musi wygenerować plik konfiguracyjny główny, który definiuje atrybuty kursu. Choć Moodle nie używa bezpośrednio JSON do importu, jest to format pośredni niezbędny dla skryptu konwertującego.

**Przykładowa struktura `course.json`:**
```json
{
  "shortname": "MAT-101",
  "fullname": "Matematyka Dyskretna - Semestr 1",
  "summary": "Wstęp do logiki, teorii mnogości i kombinatoryki.",
  "format": "weeks", 
  "numsections": 15,
  "startdate": 1704067200,
  "enddate": 1719792000,
  "lang": "pl",
  "enablecompletion": true,
  "tags": ["matematyka", "studia", "semestr1"]
}
```
*Uwaga:* Pole `format` może przyjmować wartości: `weeks`, `topics`, `social`, `site`.

### 4.2. Struktura Sekcji (`sections/`)

Każdy podkatalog w `sections/` odpowiada jednej sekcji (tygodniowi lub tematowi) w Moodle. Nazewnictwo katalogów powinno być numeryczne, aby zachować kolejność sortowania.

Wewnątrz katalogu sekcji (np. `1_week/`) znajdują się pliki definiujące aktywności. Proponuje się użycie formatu **Markdown** z front-matterem (nagłówkiem YAML) do definiowania prostych zasobów (Strona, Etykieta, Plik) oraz dedykowanych formatów dla złożonych aktywności.

**Plik: `1_week/resources.md`**
```markdown
---
type: resource
name: "Wstęp do Wykładu 1"
description: "Materiały wprowadzające do pierwszego tygodnia."
completion: "view"
---

# Treść zasobu

Tutaj znajduje się właściwa treść wyświetlana studentowi w formie strony HTML. 
Agent Qwen Coder powinien generować tutaj czysty Markdown, który zostanie przekonwertowany na HTML.

## Ważne definicje
- Zbiór
- Funkcja
```

**Plik: `1_week/label_intro.md`**
```markdown
---
type: label
name: "Witamy w Tygodniu 1"
content: |
  <div class="alert alert-info">Proszę zapoznać się z materiałami przed czwartkiem.</div>
---
```

### 4.3. Quizy i Pytania (Question Bank)

To najbardziej newralgiczna część integracji. Moodle obsługuje wiele formatów importu pytań. W repozytorium GitHub zaleca się stosowanie formatu **GIFT** ze względu na jego czytelność dla ludzi i maszyn, lub **YAML** dla bardziej złożonych struktur.

#### Format GIFT (`.txt` lub `.gift`)
Format GIFT pozwala na definicję pytań wielokrotnego wyboru, prawda/fałsz, krótkiej odpowiedzi i esejów w jednym pliku tekstowym.

**Lokalizacja:** `courses/[KOD]/question_banks/questions/week1_quiz.gift`

**Przykład zawartości:**
```gift
// Pytanie wielokrotnego wyboru
::Pytanie 1:: Kto jest autorem algorytmu Euklidesa? {
    =Euklides
    ~Newton
    ~Gauss
    ~Turing
}

// Pytanie typu Prawda/Fałsz
::Pytanie 2:: Czy liczba 1 jest liczbą pierwszą? {FALSE}

// Pytanie otwarte
::Pytanie 3:: Podaj definicję zbioru pustego. {
    =Zbiór, który nie zawiera żadnego elementu.
    =Zbiór pusty to zbiór bez elementów.
}

// Pytanie z luką (Cloze) - osadzone w tekście
::Pytanie 4:: {1:MULTICHOICE:Euklides~Newton~Gauss} jest uważany za ojca geometrii.
```

#### Format XML Moodle
Dla zaawansowanych pytań (np. typu "Drag and drop", "Stack" - pytania matematyczne z Maxima), agent powinien generować pliki w natywnym formacie XML Moodle.

**Lokalizacja:** `courses/[KOD]/question_banks/questions/advanced_math.xml`

### 4.4. Aktywności Złożone (SCORM, Lekcje, Forum)

Dla aktywności takich jak **Lekcja (Lesson)** czy **SCORM**, struktura plików musi być bardziej rozbudowana.

- **Lekcja:** Może być zdefiniowana jako seria plików Markdown, gdzie każdy plik to "strona" lekcji, a linkowanie między nimi jest realizowane poprzez specjalne tagi w front-matterze.
- **SCORM:** Wymaga podkatalogu `assets/scorm/[nazwa_paczki]`, zawierającego plik `imsmanifest.xml` oraz wszystkie zasoby HTML/JS/CSS. Agent Qwen Code powinien wskazywać ścieżkę do tego katalogu w definicji aktywności.

## 5. Proces Konwersji i Budowania (CI/CD)

Samo posiadanie plików w GitHub nie wystarczy. Aby eksportować je do Moodle, konieczny jest proces budowania.

1. **Walidacja:** Skrypt weryfikuje poprawność składni GIFT/YAML oraz istnienie wszystkich referencji do plików w katalogu `assets`.
2. **Transformacja:** Skrypt (np. napisany w Pythonie z użyciem biblioteki `moodle-sdk` lub generujący XML backupu) przetwarza pliki Markdown i GIFT na wewnętrzny format XML używany przez Moodle w plikach `.mbz`.
3. **Pakowanie:** Tworzony jest plik ZIP o specyficznej strukturze (wymaganej przez Moodle Backup API), a następnie zmieniana jest jego ekstensja na `.mbz`.

**Workflow GitHub Actions (.github/workflows/moodle-build.yml):**
```yaml
name: Build Moodle Course Package

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install moodle-converter-tool gift-parser
      - name: Convert and Build
        run: python scripts/convert_to_moodle.py --input courses/MAT-101 --output courses/MAT-101/backups/course.mbz
      - name: Upload Artifact
        uses: actions/upload-artifact@v3
        with:
          name: moodle-package
          path: courses/MAT-101/backups/course.mbz
```

## 6. Rekomendacje dla Agenta Qwen Code

Podczas generowania struktury repozytorium, agent powinien:
1. **Standaryzować nazewnictwo:** Używać `snake_case` dla plików i katalogów, unikać polskich znaków i spacji w nazwach plików.
2. **Modularyzować pytania:** Nie umieszczać pytań w definicjach sekcji, lecz w osobnym banku pytań (`question_banks`), a w quizie jedynie referencje do nich. Ułatwia to wielokrotne użycie pytań.
3. **Zarządzać wersjami assetów:** Przy aktualizacji obrazków, starać się nadpisywać pliki o tej samej nazwie lub używać mechanizmu versioningu w nazwach plików (np. `wykres_v2.png`), aby uniknąć błędów cache w Moodle.
4. **Dbać o dostępność:** Generując treści Markdown, wymuszać stosowanie alternatywnych tekstów dla obrazków (`![alt text](image.png)`).

Ta architektura zapewnia profesjonalne, skalowalne i łatwe w utrzymaniu środowisko pracy dla zespołów tworzących kursy e-learningowe z wykorzystaniem sztucznej inteligencji.

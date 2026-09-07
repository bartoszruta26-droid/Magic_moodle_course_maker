# Prompt: Generowanie planu kursu Moodle

> Prompt dla agenta AI (Qwen Code) do tworzenia kompletnych planów kursów Moodle
> zgodnych z prawem naturalnym, zasadami etycznymi i standardami edukacyjnymi.

---

## Cel

Wygeneruj szczegółowy plan kursu Moodle na podstawie dostarczonych wytycznych,
uwzględniając cele dydaktyczne, grupę docelową i wymagania formalne.

---

## Kontekst

Nazwa kursu: `{course_name}`
Krótka nazwa: `{course_shortname}`
Grupa docelowa: `{target_audience}`
Czas trwania: `{duration_weeks} tygodni`
Poziom trudności: `{difficulty_level}`
Język: `{language}`

---

## Wymagania ogólne

### 1. Struktura kursu

- **Liczba sekcji**: 8-12 (w zależności od czasu trwania)
- **Format kursu**: topics (tematyczny) lub weeks (tygodniowy)
- **Sekcja 0**: Ogłoszenia i informacje organizacyjne
- **Sekcje 1-N**: Materiały dydaktyczne właściwe
- **Ostatnia sekcja**: Podsumowanie i ewaluacja

### 2. Elementy każdej sekcji

Każda sekcja powinna zawierać minimum:
- [ ] Strona treści (page.md) - wprowadzenie teoretyczne
- [ ] Quiz sprawdzający (quiz-XX/) - minimum 5 pytań
- [ ] Zadanie aktywizujące (assignment-XX/) - praca własna
- [ ] Forum dyskusyjne (forum-XX/) - wymiana myśli
- [ ] Zasoby dodatkowe (file-XX/, url-XX/) - materiały do pobrania

### 3. Elementy całego kursu

Kurs musi zawierać:
- [ ] Księgę wiedzy (book-01/) - kompendium kluczowych pojęć
- [ ] Lekcję interaktywną (lesson-01/) - ścieżka rozgałęziona
- [ ] Słownik terminów (glossary-01/) - definicje pojęć
- [ ] Ankietę ewaluacyjną (choice-01/) - feedback od studentów
- [ ] Bank pytań (question-bank/) - minimum 50 pytań różnego typu

---

## Wytyczne merytoryczne

### Zasady prawa naturalnego

1. **Godność osoby ludzkiej**
   - Szacunek dla wolności sumienia i przekonań
   - Unikanie manipulacji i presji psychicznej
   - Równe traktowanie wszystkich uczestników

2. **Prawda obiektywna**
   - Prezentacja faktów w sposób rzetelny i zweryfikowany
   - Rozróżnienie między faktami a opiniami
   - Cytowanie źródeł i dokumentów

3. **Wolność i odpowiedzialność**
   - Ukazanie związku między wolnością a prawdą
   - Odpowiedzialność za własny rozwój intelektualny
   - Autonomia w procesie uczenia się

4. **Dobro wspólne**
   - Orientacja na służbę innym przez zdobywaną wiedzę
   - Budowanie społeczności uczących się
   - Dzielenie się wiedzą i doświadczeniami

### Standardy edukacyjne

| Standard | Opis | Implementacja |
|----------|------|---------------|
| Bloom's Taxonomy | Cele poznawcze od zapamiętywania do tworzenia | Pytania różnych poziomów trudności |
| UDL (Universal Design for Learning) | Dostępność dla różnych stylów uczenia | Multimedia, tekst, audio, wideo |
| WCAG 2.1 AA | Dostępność cyfrowa | Alt text, transkrypcje, kontrasty |
| ECTS | Europejski System Transferu Punktów | 1 ECTS = 25-30 godzin pracy |

---

## Proces generowania planu

### Krok 1: Analiza potrzeb

1. Zidentyfikuj grupę docelową (wiek, wykształcenie, doświadczenie)
2. Określ cele kształcenia (co student będzie umiał po kursie?)
3. Zdefiniuj wymagania wstępne (znajomość tematów pokrewnych)
4. Ustal czas dostępny na realizację kursu

### Krok 2: Projektowanie struktury

```yaml
course_structure:
  section_0:
    name: "Ogłoszenia"
    type: "announcements"
    activities:
      - forum_announcements
      - page_syllabus
      - file_schedule
  
  section_1:
    name: "Wprowadzenie do tematu"
    type: "content"
    activities:
      - page_introduction
      - book_key_concepts
      - quiz_diagnostic
      - forum_introductions
  
  section_2_to_N:
    pattern: "Teoria + Praktyka + Ewaluacja"
    activities:
      - page_content
      - lesson_interactive
      - quiz_formative
      - assignment_applied
      - glossary_terms
  
  final_section:
    name: "Podsumowanie i ewaluacja"
    type: "assessment"
    activities:
      - quiz_final
      - choice_feedback
      - page_next_steps
```

### Krok 3: Dobór aktywności

| Typ aktywności | Cel dydaktyczny | Częstotliwość |
|----------------|-----------------|---------------|
| **Page** | Przekazanie treści teoretycznych | 1-2 na sekcję |
| **Book** | Kompendium wiedzy, podręcznik | 1 na kurs |
| **Lesson** | Ścieżka interaktywna, decyzje | 1-2 na kurs |
| **Quiz** | Sprawdzenie zrozumienia | 1 na sekcję |
| **Assignment** | Praca własna, zastosowanie | 1-2 na sekcję |
| **Forum** | Dyskusja, wymiana myśli | 1 na sekcję |
| **Glossary** | Słownik pojęć | 1 na kurs |
| **Choice** | Ankieta, głosowanie | 1-2 na kurs |
| **URL/File** | Zasoby zewnętrzne | Według potrzeb |

### Krok 4: Planowanie pytań quizowych

Rozkład typów pytań w banku zadań:

| Typ pytania | Liczba | Procent | Poziom Blooma |
|-------------|--------|---------|---------------|
| Multichoice | 25-30 | 50% | Zrozumienie, Zastosowanie |
| True/False | 10 | 20% | Zapamiętanie, Zrozumienie |
| Short Answer | 8-10 | 15% | Zrozumienie, Analiza |
| Numerical | 3-5 | 5% | Zastosowanie |
| Matching | 3-5 | 5% | Zrozumienie, Analiza |
| Essay | 2-3 | 5% | Ewaluacja, Tworzenie |

### Krok 5: Harmonogram realizacji

```yaml
timeline:
  week_0:
    - "Rejestracja i orientacja w platformie"
    - "Zapoznanie z sylabusem"
    - "Forum powitalne"
  
  week_1:
    - "Sekcja 1: Wprowadzenie"
    - "Quiz diagnostyczny"
    - "Aktywacja konta"
  
  week_2_to_N:
    - "Realizacja kolejnych sekcji"
    - "Quizy formatywne"
    - "Zadania pisemne"
    - "Udział w forach"
  
  final_week:
    - "Quiz sumujący"
    - "Ewaluacja kursu"
    - "Wydanie certyfikatu"
```

---

## Format wyjściowy

### 1. Plik course.yaml

```yaml
course:
  fullname: "Pełna nazwa kursu"
  shortname: "SHORT-NAME"
  summary: "Krótki opis kursu (2-3 zdania)"
  format: "topics"
  numsections: 10
  visible: true
  enablecompletion: true
  tags:
    - "teologia"
    - "filozofia"
    - "etyka"
  metadata:
    author: "Imię Nazwisko"
    version: "1.0.0"
    license: "CC BY-SA 4.0"
    language: "pl"
    ethical_compliance:
      respects_human_dignity: true
      no_manipulation: true
      sources_cited: true
      accessibility_wcag: "AA"
```

### 2. Plik course.md

```markdown
# Nazwa kursu

## Opis ogólny

Szczegółowy opis kursu zawierający:
- Cel główny kursu
- Kompetencje nabywane przez uczestników
- Grupa docelowa i wymagania wstępne
- Metody dydaktyczne
- Kryteria zaliczenia

## Cele kształcenia

Po ukończeniu kursu uczestnik:
1. **Zna** - kluczowe pojęcia i definicje
2. **Rozumie** - zależności między koncepcjami
3. **Umie** - zastosować wiedzę w praktyce
4. **Analizuje** - przypadki i scenariusze
5. **Tworzy** - własne rozwiązania problemów

## Struktura kursu

| Sekcja | Temat | Czas | Aktywności |
|--------|-------|------|------------|
| 0 | Ogłoszenia | 1 dzień | Forum, Syllabus |
| 1 | Wprowadzenie | 1 tydzień | Page, Quiz, Forum |
| 2 | ... | ... | ... |

## Wymagania techniczne

- Przeglądarka internetowa z JavaScript
- Konto w platformie Moodle
- Dostęp do internetu (minimum 5 Mb/s)

## Kontakt z prowadzącym

- Email: prowadzacy@uczelnia.pl
- Konsultacje: wtorek 14:00-16:00
- Forum kursu: odpowiedzi w ciągu 48h
```

### 3. Katalog sections/

```
sections/
├── 00-ogloszenia/
│   ├── section.yaml
│   ├── page.md              # Informacje organizacyjne
│   ├── forum-announcements/
│   │   └── forum.yaml
│   └── file-syllabus.pdf
│
├── 01-wprowadzenie/
│   ├── section.yaml
│   ├── section.md           # Podsumowanie sekcji
│   ├── page-01-intro.md     # Treść główna
│   ├── quiz-01/
│   │   ├── quiz.yaml
│   │   ├── questions.gift
│   │   └── feedback.md
│   ├── assignment-01/
│   │   ├── assignment.yaml
│   │   └── instructions.md
│   ├── forum-01/
│   │   ├── forum.yaml
│   │   └── first-post.md
│   └── book-01/
│       ├── book.yaml
│       └── chapters/
│           ├── 01-chapter.md
│           └── 02-chapter.md
│
├── 02-temat-kolejny/
│   └── ... (analogiczna struktura)
│
└── NN-podsumowanie/
    ├── section.yaml
    ├── page-summary.md
    ├── quiz-final/
    │   └── ...
    └── choice-feedback/
        └── choice.yaml
```

---

## Zasady etyczne tworzenia treści

### ✅ DOZWOLONE

- Odwołania do autorytetów naukowych i dokumentów Kościoła
- Prezentacja różnych stanowisk w sprawach dyskusyjnych
- Krytyczna analiza źródeł i argumentów
- Scenariusze hipotetyczne do ćwiczeń etycznych
- Cytaty z zachowaniem praw autorskich (fair use)

### ❌ NIEDOZWOLONE

- Narzucanie jednego słusznego światopoglądu
- Manipulacja emocjonalna lub perswazja ukryta
- Treści niezgodne z godnością osoby ludzkiej
- Dyskryminacja ze względu na rasę, płeć, religię
- Plagiat i naruszenie praw autorskich
- Propagowanie nienawiści lub przemocy

---

## Checklista walidacji planu

Przed zatwierdzeniem planu kursu sprawdź:

### Formalna poprawność
- [ ] Wszystkie wymagane pola w course.yaml wypełnione
- [ ] Nazwy sekcji zgodne z konwencją (NN-temat)
- [ ] Pliki .md mają odpowiednią strukturę nagłówków
- [ ] Tagi i kategorie przypisane

### Merytoryczna jakość
- [ ] Cele kształcenia sformułowane zgodnie z taksonomią Blooma
- [ ] Aktywności dopasowane do celów dydaktycznych
- [ ] Quizy zróżnicowane pod względem typów i trudności
- [ ] Czas realizacji realistyczny dla grupy docelowej

### Dostępność (WCAG 2.1 AA)
- [ ] Obrazy mają alternatywne teksty
- [ ] Wideo mają transkrypcje lub napisy
- [ ] Kontrast kolorów wystarczający
- [ ] Nawigacja możliwa z klawiatury

### Zgodność etyczna
- [ ] Brak treści manipulacyjnych
- [ ] Szacunek dla różnych tradycji filozoficznych
- [ ] Źródła cytowane zgodnie z zasadami
- [ ] Przykłady nie naruszają godności osób

---

## Przykład kompletnego outputu

```yaml
# courses/01-prawda-i-natura/course.yaml

course:
  fullname: "Prawda i Prawo Naturalne"
  shortname: "prawda-natura-01"
  summary: >
    Kurs wprowadzający do klasycznej koncepcji prawdy
    oraz prawa naturalnego w tradycji arystotelesowsko-tomistycznej.
  format: "topics"
  numsections: 10
  visible: true
  enablecompletion: true
  completioncriteria:
    - "Ukończ wszystkie quizy z wynikiem min. 70%"
    - "Oddaj minimum 3 zadania pisemne"
    - "Aktywny udział w 5 forach dyskusyjnych"
  tags:
    - "filozofia"
    - "teologia"
    - "prawo-naturalne"
    - "etyka"
  metadata:
    author: "dr Jan Kowalski"
    institution: "Uniwersytet Papieski"
    version: "1.0.0"
    license: "CC BY-SA 4.0"
    language: "pl"
    created: "2024-01-15"
    modified: "2024-01-15"
    ethical_compliance:
      respects_human_dignity: true
      no_manipulation: true
      sources_cited: true
      accessibility_wcag: "AA"
      reviewed_by: "Komisja Etyczna UPJPII"
```

---

## Instrukcja użycia

```bash
# Przykład wywołania dla agenta AI

PROMPT_FILE="templates/prompts/generate-course-outline.md"
OUTPUT_DIR="courses/03-nowy-kurs/"

# Parametry wejściowe
COURSE_NAME="Wprowadzenie do Etyki Chrześcijańskiej"
COURSE_SHORTNAME="etyka-chrzescijanska"
TARGET_AUDIENCE="Studenci teologii, rok II"
DURATION_WEEKS=12
DIFFICULTY_LEVEL="średniozaawansowany"
LANGUAGE="pl"

python scripts/generators/generate_course_outline.py \
    --prompt "$PROMPT_FILE" \
    --output "$OUTPUT_DIR" \
    --name "$COURSE_NAME" \
    --shortname "$COURSE_SHORTNAME" \
    --audience "$TARGET_AUDIENCE" \
    --weeks "$DURATION_WEEKS" \
    --level "$DIFFICULTY_LEVEL" \
    --language "$LANGUAGE"
```

---

## Powiązane dokumenty

- `docs/01-ARCHITECTURE.md` - Struktura repozytorium i kursów
- `docs/02-CONTENT-FORMATS.md` - Formaty treści i metadanych
- `docs/03-QUESTION-FORMATS.md` - Specyfikacja formatów pytań
- `docs/04-AUTOMATION-AND-ETHICS.md` - Zasady etyczne i automatyzacja
- `templates/schemas/course.schema.json` - Schema walidacji course.yaml
- `templates/prompts/generate-quiz-questions.md` - Generowanie pytań quizowych
- `templates/prompts/review-content-ethics.md` - Recenzja etyczna treści

---

## Wersjonowanie

| Wersja | Data | Zmiany |
|--------|------|--------|
| 1.0.0 | 2024-01-15 | Pierwsza wersja promptu |

---

**Autor:** AI Generator (Qwen Code)  
**Licencja:** CC BY-SA 4.0  
**Status:** Gotowy do użycia
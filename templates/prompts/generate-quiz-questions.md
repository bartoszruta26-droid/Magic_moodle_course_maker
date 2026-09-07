# Prompt: Generowanie pytań do quizu

> Prompt dla agenta AI (Qwen Coder) do generowania pytań quizowych
> w formatach GIFT, YAML i Moodle XML, zgodnych z prawem naturalnym
> i zasadami etycznymi.

---

## Cel

Wygeneruj zestaw pytań quizowych do sekcji kursu Moodle na podstawie
dostarczonych materiałów źródłowych (Markdown, YAML, dokumenty).

---

## Kontekst

Kurs: `{course_name}`
Sekcja: `{section_number} - {section_title}`
Materiały źródłowe: `{source_files}`

---

## Wymagania ogólne

1. **Liczba pytań**: Minimum 10 pytań różnego typu
2. **Poziom trudności**: Zróżnicowany (łatwe, średnie, trudne)
3. **Zgodność merytoryczna**: Pytania muszą być zgodne z treściami
   z materiałów źródłowych
4. **Zgodność etyczna**: 
   - Szacunek dla godności osoby ludzkiej
   - Brak manipulacji i sugestywnych sformułowań
   - Obiektywizm w pytaniach dotyczących faktów
   - Cytowanie źródeł przy pytaniach opartych na dokumentach

---

## Formaty wyjściowe

### 1. Format GIFT (priorytetowy)

```gift
::Nazwa pytania::
Treść pytania? {
    =Poprawna odpowiedź
        #Informacja zwrotna dla odpowiedzi poprawnej
    ~Niepoprawna odpowiedź 1
        #Wyjaśnienie dlaczego niepoprawna
    ~Niepoprawna odpowiedź 2
}
```

### 2. Format YAML (strukturalny)

```yaml
quiz_questions:
  metadata:
    course: "{course_shortname}"
    section: "{section_number}"
    author: "AI Generator"
    language: "pl"
  
  questions:
    - id: "q001"
      type: "multichoice"
      category: "{category}"
      name: "Nazwa pytania"
      questiontext: "Treść pytania?"
      answers:
        - text: "Odpowiedź A"
          fraction: 100
          feedback: "Feedback"
        - text: "Odpowiedź B"
          fraction: 0
          feedback: "Feedback"
```

### 3. Format Moodle XML

```xml
<question type="multichoice">
  <name><text>Nazwa pytania</text></name>
  <questiontext format="html">
    <text><![CDATA[Treść pytania?]]></text>
  </questiontext>
  <answer fraction="100">
    <text>Poprawna odpowiedź</text>
    <feedback><text>Feedback</text></feedback>
  </answer>
</question>
```

---

## Typy pytań do wygenerowania

| Typ | Liczba | Opis |
|-----|--------|------|
| `multichoice` | 4-5 | Wielokrotnego wyboru (jedna lub więcej poprawnych) |
| `truefalse` | 2 | Prawda/Fałsz z uzasadnieniem |
| `shortanswer` | 2 | Krótka odpowiedź (1-3 słowa) |
| `numerical` | 1 | Numeryczne (daty, liczby) |
| `matching` | 1 | Dopasowanie pojęć do definicji |
| `essay` | 0-1 | Esej (opcjonalnie, do oceny ręcznej) |

---

## Wytyczne dla każdego typu pytania

### Multichoice (wielokrotnego wyboru)

- **Struktura**: 1 poprawna + 3-4 dystraktory LUB 2+ poprawne + dystraktory
- **Dystraktory**: Muszą być wiarygodne, ale jednoznacznie niepoprawne
- **Unikaj**: "Wszystkie powyższe", "Żadne z powyższych"
- **Kolejność**: Losowa (shuffleanswers: true)

**Przykład**:
```gift
::Definicja prawdy::
Czym jest prawda w ujęciu klasycznym? {
    =Zgodnością umysłu z rzeczywistością
    ~Subiektywnym odczuciem jednostki
    ~Konsensusem społecznym
    ~Wynikiem głosowania większości
}
```

### True/False (prawda/fałsz)

- **Stwierdzenie**: Jednoznaczne, bez podwójnego zaprzeczenia
- **Feedback**: Wyjaśnienie zarówno dla TRUE jak i FALSE
- **Balans**: Około 50% TRUE i 50% FALSE w całym quizie

**Przykład**:
```gift
::Prawo naturalne::
Prawo naturalne jest dostępne wyłącznie przez objawienie Boże. {FALSE}
```

### Short Answer (krótka odpowiedź)

- **Oczekiwana długość**: 1-5 słów
- **Warianty odpowiedzi**: Uwzględnij synonimy i różne formy
- **Case sensitivity**: Ustaw na false (wyjątek: nazwy własne)

**Przykład**:
```gift
::Uzupełnij cytat::
"Poznacie prawdę, a prawda was ..." {
    =wyzwoli
    =uwolni
}
```

### Numerical (numeryczne)

- **Tolerancja**: Określ dopuszczalny margines błędu
- **Jednostki**: Podaj jeśli wymagane
- **Kontekst**: Wyjaśnij znaczenie liczby

**Przykład**:
```gift
::Rok encykliki::
W którym roku ogłoszono encyklikę "Veritatis Splendor"? {
    =1993:0
}
```

### Matching (dopasowanie)

- **Liczba par**: 4-6 par
- **Spójność**: Wszystkie elementy z tej samej kategorii
- **Instrukcja**: Jasno określ kryterium dopasowania

**Przykład**:
```gift
::Dopasuj pojęcia::
Dopasuj pojęcia do ich definicji. {
    =Prawda -> Zgodność umysłu z rzeczywistością
    =Wolność -> Zdolność do samostanowienia w świetle prawdy
    =Godność -> Przyrodzona wartość każdego człowieka
    =Rozum -> Zdolność poznania prawdy
}
```

### Essay (esej) - opcjonalnie

- **Temat**: Otwarty, wymagający refleksji
- **Wymagania**: Określ minimalną długość i kryteria
- **Rubryka**: Dołącz kryteria oceny

**Przykład**:
```gift
::Esej: Prawda w życiu::
Opisz, w jaki sposób prawda obiektywna wpływa na relacje
międzyludzkie. Podaj konkretne przykłady z życia codziennego.
(min. 200 słów) {}
```

---

## Zasady etyczne generowania pytań

### ✅ DOZWOLONE

- Pytania oparte na faktach i źródłach
- Odwołania do dokumentów Kościoła, filozofii, prawa
- Pytania sprawdzające zrozumienie pojęć
- Scenariusze hipotetyczne do analizy moralnej
- Cytaty z zastrzeżeniem praw autorskich

### ❌ NIEDOZWOLONE

- Pytania sugerujące jedną słuszną opinię w sprawach dyskusyjnych
- Manipulacja emocjonalna w sformułowaniach
- Stereotypy i uprzedzenia
- Treści niezgodne z godnością osoby ludzkiej
- Naruszenie praw autorskich (cytaty >50 słów bez dozwolonego użytku)

---

## Proces generowania

### Krok 1: Analiza materiałów źródłowych

1. Przeczytaj wszystkie dostarczone pliki `.md` i `.yaml`
2. Zidentyfikuj kluczowe pojęcia, definicje, fakty
3. Wypisz daty, liczby, cytaty do pytań numerycznych i shortanswer
4. Zgrupuj pojęcia do pytań matching

### Krok 2: Planowanie struktury quizu

| ID | Typ | Kategoria | Temat | Trudność |
|----|-----|-----------|-------|----------|
| q001 | multichoice | Prawda | Definicja | Łatwe |
| q002 | truefalse | Prawo naturalne | Dostępność | Średnie |
| ... | ... | ... | ... | ... |

### Krok 3: Generowanie pytań

Dla każdego pytania:
1. Napisz treść pytania (jasna, jednoznaczna)
2. Stwórz odpowiedzi (1+ poprawnych, reszta dystraktory)
3. Dodaj feedback dla każdej odpowiedzi
4. Przypisz kategorię i tagi
5. Określ punktację (defaultmark)

### Krok 4: Walidacja

Sprawdź każde pytanie pod kątem:
- [ ] Poprawność merytoryczna
- [ ] Jasność sformułowania
- [ ] Brak dwuznaczności
- [ ] Zgodność z materiałami źródłowymi
- [ ] Zgodność z zasadami etycznymi
- [ ] Poprawność formatu (GIFT/YAML/XML)

### Krok 5: Eksport

Wygeneruj pliki:
- `questions.gift` - format GIFT (priorytetowy)
- `questions.yaml` - format YAML (strukturalny)
- `questions.xml` - format Moodle XML

---

## Przykład kompletnego outputu

```gift
// ============================================================
// Quiz: Sekcja 1 - Wprowadzenie
// Kurs: Prawda i Natura
// Wygenerowano: {date}
// ============================================================

// --- Pytanie 1: Multichoice ---
::Definicja prawdy::
Czym jest prawda w ujęciu klasycznym? {
    =Zgodnością umysłu z rzeczywistością
        #Poprawnie! To klasyczna definicja (adaequatio intellectus et rei).
    ~Subiektywnym odczuciem jednostki
        #Niepoprawnie. To relatywizm, nie prawda obiektywna.
    ~Konsensusem społecznym
        #Niepoprawnie. Prawda nie zależy od głosowania.
    ~Wynikiem głosowania większości
        #Niepoprawnie.
}

// --- Pytanie 2: True/False ---
::Prawo naturalne - dostępność::
Prawo naturalne jest dostępne wyłącznie przez objawienie Boże. {
    FALSE#Niepoprawnie. Prawo naturalne jest wpisane w naturę
         człowieka i dostępne poznaniu rozumowemu, niezależnie
         od objawienia.
}

// --- Pytanie 3: Short Answer ---
::Cytat biblijny::
Uzupełnij cytat: "Poznacie prawdę, a prawda was ..." {
    =wyzwoli
    =uwolni
}

// --- Pytanie 4: Numerical ---
::Encyklika Veritatis Splendor::
W którym roku Jan Paweł II ogłosił encyklikę "Veritatis Splendor"? {
    =1993:0
}

// --- Pytanie 5: Matching ---
::Dopasuj pojęcia::
Dopasuj pojęcia do ich definicji. {
    =Prawda -> Zgodność umysłu z rzeczywistością
    =Wolność -> Zdolność do samostanowienia w świetle prawdy
    =Godność -> Przyrodzona wartość każdego człowieka
    =Rozum -> Zdolność poznania prawdy
}
```

---

## Metadane outputu

Na końcu pliku dodaj komentarz z metadanymi:

```gift
// ============================================================
// METADANE
// ============================================================
// Kurs: {course_fullname}
// Sekcja: {section_number} - {section_title}
// Liczba pytań: {total_questions}
// Autor: AI Generator (Qwen Coder)
// Data generowania: {iso_date}
// Wersja: 1.0.0
// Licencja: CC BY-SA 4.0
// ============================================================
```

---

## Instrukcja użycia

```bash
# Przykład wywołania dla agenta AI

PROMPT_FILE="templates/prompts/generate-quiz-questions.md"
SOURCE_DIR="courses/01-prawda-i-natura/sections/01-wprowadzenie/"
OUTPUT_DIR="courses/01-prawda-i-natura/sections/01-wprowadzenie/quiz-01/"

python scripts/generators/generate_questions.py \
    --prompt "$PROMPT_FILE" \
    --source "$SOURCE_DIR" \
    --output "$OUTPUT_DIR" \
    --formats gift,yaml,xml \
    --min-questions 10
```

---

## Powiązane dokumenty

- `docs/03-QUESTION-FORMATS.md` - Specyfikacja formatów pytań
- `docs/04-AUTOMATION-AND-ETHICS.md` - Zasady etyczne
- `templates/schemas/question.schema.json` - Schema walidacji
# Prompt: Recenzja etyczna treści edukacyjnych

> Prompt dla agenta AI (Qwen Code) do przeprowadzania recenzji etycznej treści kursów Moodle
> zgodnych z prawem naturalnym, godnością osoby ludzkiej i zasadami etyki akademickiej.

---

## Cel

Przeprowadź kompleksową recenzję etyczną materiałów edukacyjnych kursu Moodle,
weryfikując zgodność z zasadami prawa naturalnego, standardami akademickimi
i wytycznymi etycznymi instytucji edukacyjnej.

---

## Kontekst

Nazwa kursu: `{course_name}`
Wersja materiałów: `{version}`
Autor treści: `{author}`
Data recenzji: `{review_date}`
Typ recenzji: `{review_type}` (wstępna/okresowa/koncowa)

---

## Zakres recenzji

### 1. Obszary podlegające ocenie

| Obszar | Elementy sprawdzane | Priorytet |
|--------|---------------------|-----------|
| **Treści merytoryczne** | Page, Book, Lesson | Wysoki |
| **Pytania quizowe** | Quiz, Question Bank | Wysoki |
| **Zadania i ćwiczenia** | Assignment, Workshop | Średni |
| **Forum i komunikacja** | Forum, Chat | Średni |
| **Zasoby zewnętrzne** | URL, File | Niski |
| **Metadane i opis** | Course summary, Tags | Niski |

### 2. Poziomy recenzji

- **Poziom 1**: Automatyczna weryfikacja formalna (checklista)
- **Poziom 2**: Analiza merytoryczna treści
- **Poziom 3**: Głęboka analiza przypadków granicznych
- **Poziom 4**: Konsultacja z komisją etyczną (wymaga człowieka)

---

## Zasady prawa naturalnego

### 1. Godność osoby ludzkiej

#### Kryteria pozytywne ✅

- [ ] Treść szanuje wolność sumienia i przekonań odbiorcy
- [ ] Prezentacja tematów kontrowersyjnych w sposób zrównoważony
- [ ] Unikanie języka dehumanizującego lub uprzedmiotawiającego
- [ ] Równe traktowanie wszystkich grup demograficznych
- [ ] Szacunek dla prywatności i autonomii uczestników

#### Czerwone flagi ❌

- [ ] Język manipulacyjny lub perswazja ukryta
- [ ] Presja psychiczna lub emocjonalna
- [ ] Stereotypy i uprzedzenia wobec grup społecznych
- [ ] Naruszanie prywatności w przykładach i case studies
- [ ] Treści o charakterze pornograficznym lub przemocowym

#### Przykłady naruszeń

```markdown
# ❌ ŹLE: Manipulacja emocjonalna

"Tylko ludzie ograniczeni umysłowo nie zgadzają się z tą tezą.
Jeśli chcesz być człowiekiem inteligentnym, musisz przyjąć..."

# ✅ DOBRZE: Szacunek dla autonomii

"Stanowisko A przedstawia argumenty X, Y, Z.
Stanowisko B przedstawia argumenty P, Q, R.
Zachęcamy do samodzielnej refleksji i krytycznej analizy obu stanowisk."
```

### 2. Prawda obiektywna

#### Kryteria pozytywne ✅

- [ ] Rozróżnienie między faktami naukowymi a opiniami
- [ ] Cytowanie źródeł pierwotnych i recenzowanych
- [ ] Aktualność informacji (nie starsze niż 5 lat dla nauk empirycznych)
- [ ] Transparentność co do ograniczeń wiedzy w danej dziedzinie
- [ ] Korekta błędów w trybie natychmiastowym

#### Czerwone flagi ❌

- [ ] Dezinformacja lub pseudonauka przedstawiana jako fakt
- [ ] Brak odniesień do źródeł naukowych
- [ ] Wybiórcze cytowanie (cherry-picking) dla potwierdzenia tezy
- [ ] Mieszanie faktów z interpretacjami bez oznaczenia
- [ ] Ignorowanie konsensusu naukowego bez uzasadnienia

#### Checklista weryfikacji źródeł

```yaml
source_verification:
  primary_sources:
    - "Czy cytowane są dokumenty źródłowe?"
    - "Czy przytoczono oryginalne badania?"
    - "Czy wskazano kontekst historyczny źródeł?"
  
  peer_review:
    - "Czy źródła pochodzą z czasopism recenzowanych?"
    - "Czy autorzy mają odpowiednie kwalifikacje?"
    - "Czy badania były replikowane?"
  
  balance:
    - "Czy przedstawiono różne stanowiska w sporach naukowych?"
    - "Czy uniknięto jednostronności w prezentacji?"
    - "Czy wskazano ograniczenia każdego ze stanowisk?"
```

### 3. Wolność i odpowiedzialność

#### Kryteria pozytywne ✅

- [ ] Ukazanie związku między wolnością a prawdą
- [ ] Podkreślenie odpowiedzialności za własny rozwój
- [ ] Autonomia w procesie uczenia się (wybór ścieżek)
- [ ] Możliwość kwestionowania i dyskusji
- [ ] Brak sankcji za odmienne zdanie (w granicach merytoryki)

#### Czerwone flagi ❌

- [ ] Determinizm lub fatalizm w nauczaniu
- [ ] Sugerowanie braku wpływu na własne życie
- [ ] Nakazywanie jednego słusznego sposobu myślenia
- [ ] Karanie za kreatywność lub nieszablonowe podejście
- [ ] Brak możliwości odwołania się od ocen

### 4. Dobro wspólne

#### Kryteria pozytywne ✅

- [ ] Orientacja na służbę innym przez zdobywaną wiedzę
- [ ] Budowanie społeczności uczących się
- [ ] Dzielenie się wiedzą i zasobami (open access gdzie możliwe)
- [ ] Uwzględnienie wymiaru społecznego kompetencji
- [ ] Promocja postaw obywatelskich i prospołecznych

#### Czerwone flagi ❌

- [ ] Indywidualizm i konkurencja za wszelką cenę
- [ ] Wiedza jako narzędzie dominacji nad innymi
- [ ] Brak odniesienia do odpowiedzialności społecznej
- [ ] Ignorowanie wymiaru ekologicznego i środowiskowego
- [ ] Komercjalizacja treści bez wartości dodanej

---

## Standardy etyki akademickiej

### 1. Autorstwo i plagiat

| Zasada | Implementacja | Weryfikacja |
|--------|---------------|-------------|
| **Oznaczenie autorstwa** | Wszystkie cytaty w nawiasach lub przypisach | Turnitin/iThenticate |
| **Bibliografia** | Pełne dane bibliograficzne według APA/MLA/Chicago | Walidacja automatyczna |
| **Parafraza** | Własnymi słowami z odniesieniem do źródła | Review ręczny |
| **Self-plagiat** | Zakaz kopiowania własnych prac bez oznaczenia | Deklaracja autora |
| **Ghostwriting** | Zakaz tworzenia treści przez osoby niewymienione | Oświadczenie |

### 2. Konflikty interesów

```yaml
conflict_of_interest:
  financial:
    - "Czy autor ma udziały w firmach wymienianych w treści?"
    - "Czy otrzymano finansowanie od zainteresowanych stron?"
  
  personal:
    - "Czy autor ma relacje osobiste z opisywanymi osobami?"
    - "Czy istnieją powiązania instytucjonalne?"
  
  intellectual:
    - "Czy autor promuje własną teorię bez dystansu?"
    - "Czy pominięto konkurencyjne szkoły myślenia?"
  
  declaration_required: true
  public_disclosure: true
```

### 3. Ochrona danych osobowych

- [ ] Przykłady nie zawierają prawdziwych danych osobowych
- [ ] Case studies anonimizowane zgodnie z RODO
- [ ] Zgody na wykorzystanie wizerunku (jeśli dotyczy)
- [ ] Brak linków do profili społecznościowych osób trzecich
- [ ] Secure handling of student data in examples

---

## Proces recenzji etycznej

### Krok 1: Przygotowanie

```bash
# Skrypt inicjalizujący recenzję
python scripts/review/init_ethics_review.py \
    --course "courses/01-prawda-i-natura/" \
    --output "reviews/ethics/01-prawda-i-natura/" \
    --type "full" \
    --auto-check true
```

**Działania:**
1. Skopiowanie wszystkich plików .md do folderu recenzji
2. Wygenerowanie listy kontrolnej (checklist.json)
3. Uruchomienie automatycznych skanerów treści

### Krok 2: Automatyczna weryfikacja formalna

**Narzędzia:**
- `grep` - wyszukiwanie problematycznych fraz
- `wc` - statystyki długości tekstów
- `link-checker` - weryfikacja URLi
- `citation-validator` - sprawdzanie formatu cytowań

**Skrypt automatyczny:**
```bash
./scripts/review/auto-scan.sh \
    --input "reviews/ethics/01-prawda-i-natura/" \
    --output "reviews/ethics/01-prawda-i-natura/report-auto.json" \
    --flags "manipulation,stereotype,pseudoscience,hate-speech"
```

### Krok 3: Analiza merytoryczna

**Checklista dla recenzenta:**

```markdown
## Sekcja: [NAZWA_SEKCJI]

### Treść główna (page.md)
- [ ] Brak stwierdzeń absolutnych bez dowodów
- [ ] Rozróżnienie fakt/opinia
- [ ] Cytowania poprawne
- [ ] Ton neutralny, nieperswazyjny

### Pytania quizowe (quiz-XX/)
- [ ] Brak pytań tendencyjnych
- [ ] Odpowiedzi nie stygmatyzują
- [ ] Feedback konstruktywny, nieoceniający

### Zadania (assignment-XX/)
- [ ] Instrukcje jasne i wykonalne
- [ ] Brak narzucania światopoglądu
- [ ] Możliwość różnych rozwiązań

### Forum (forum-XX/)
- [ ] Zasady netiquette określone
- [ ] Moderacja przewidziana
- [ ] Ochrona przed hejtem
```

### Krok 4: Identyfikacja przypadków granicznych

**Kategorie problemów:**

| Kategoria | Opis | Akcja |
|-----------|------|-------|
| 🟢 Brak uwag | Treść w pełni zgodna | Zatwierdź |
| 🟡 Drobne uwagi | Wymaga korekty językowej | Popraw i zatwierdź |
| 🟠 Uwagi merytoryczne | Wymaga przeredagowania | Zwróć autorowi |
| 🔴 Poważne naruszenie | Niezgodność z etyką | Odrzuć lub konsultuj z komisją |

### Krok 5: Raport końcowy

**Struktura raportu:**

```yaml
ethics_review_report:
  metadata:
    course_name: "Prawda i Prawo Naturalne"
    review_date: "2024-01-15"
    reviewer: "AI Ethics Agent v1.0"
    review_type: "full"
    
  summary:
    total_files_reviewed: 45
    issues_found: 7
    critical_issues: 0
    major_issues: 2
    minor_issues: 5
    
  findings:
    - id: "ETH-001"
      severity: "major"
      location: "sections/01-wprowadzenie/page-01-czym-jest-prawda.md"
      line: 23
      issue: "Stwierdzenie absolutne bez dowodów"
      recommendation: "Dodać odniesienia do źródeł filozoficznych"
      
    - id: "ETH-002"
      severity: "minor"
      location: "sections/02-sumienie/quiz-01/questions.gift"
      line: 15
      issue: "Pytanie sugerujące jedną słuszną odpowiedź"
      recommendation: "Przeformułować na pytanie otwarte lub dodać kontekst"
      
  compliance_scores:
    human_dignity: 95/100
    objective_truth: 88/100
    freedom_responsibility: 92/100
    common_good: 90/100
    academic_integrity: 97/100
    overall: 92/100
    
  recommendations:
    short_term:
      - "Poprawić 2 pytania w quizie 01"
      - "Dodać 3 cytaty w sekcji 03"
    long_term:
      - "Rozważyć dodanie perspektywy alternatywnej w sekcji 05"
      - "Aktualizacja bibliografii o nowsze źródła"
      
  conclusion: "Materiały spełniają wymagania etyczne z drobnymi uwagami.
               Zaleca się wprowadzenie poprawek przed publikacją."
               
  approval_status: "conditional_approval"
  next_review_date: "2025-01-15"
```

---

## Algorytm detekcji problemów etycznych

### Pattern matching dla czerwonych flag

```python
# Przykładowe patterny do wykrywania problemów

MANIPULATION_PATTERNS = [
    r"\btylko\s+\w+\s+nie\s+zgadz",  # "tylko głupi nie zgadza"
    r"\bmusisz\s+przyjąć",           # "musisz przyjąć"
    r"\bjedynie\s+słuszny",          # "jedynie słuszny"
    r"\bkażdy\s+zdroworozsądkowy",   # "każdy zdroworozsądkowy"
]

STEREOTYPE_PATTERNS = [
    r"\bkobiety\s+zawsze",           # generalizacje
    r"\bmężczyźni\s+nigdy",
    r"\bwszyscy\s+\w+\s+są",
]

PSEUDOSCIENCE_PATTERNS = [
    r"\bnaukowo\s+dowodzone\s+bez\s+przypisu",
    r"\bbadania\s+potwierdzają\s+bez\s+źródła",
    r"\bsto\s+procent\s+skuteczności",
]

HATE_SPEECH_PATTERNS = [
    # Lista słów kluczowych zdefiniowana w osobnym pliku
    # load_from: config/hate_speech_dictionary.yaml
]
```

### Scoring system

```yaml
scoring:
  base_score: 100
  
  deductions:
    manipulation_language: -5 per instance
    missing_citations: -2 per instance
    stereotyping: -10 per instance
    pseudoscience: -15 per instance
    hate_speech: -50 per instance (automatic fail)
    
  bonuses:
    multiple_perspectives: +2 per section
    accessibility_features: +5 total
    open_licensing: +3 total
    
  thresholds:
    excellent: 95-100
    good: 80-94
    acceptable: 60-79
    needs_revision: 40-59
    reject: below 40
```

---

## Format wyjściowy recenzji

### 1. Plik ethics-review.yaml

```yaml
# reviews/ethics/01-prawda-i-natura/ethics-review.yaml

review:
  id: "ETH-2024-001"
  course: "prawda-natura-01"
  date: "2024-01-15"
  reviewer: "AI Ethics Agent"
  version_reviewed: "1.0.0"
  
  assessment:
    human_dignity:
      score: 95
      notes: "Brak istotnych uwag"
      
    objective_truth:
      score: 88
      notes: "Wymaga uzupełnienia 3 cytaty"
      
    freedom_responsibility:
      score: 92
      notes: "Dobra równowaga między wskazówkami a autonomią"
      
    common_good:
      score: 90
      notes: "Można dodać więcej przykładów prospołecznych"
      
    academic_integrity:
      score: 97
      notes: "Wzorowe cytowania i bibliografia"
      
  overall_score: 92
  status: "approved_with_minor_revisions"
  
  required_actions:
    - action: "add_citations"
      location: "sections/01/page-01.md:23"
      deadline: "2024-01-22"
      
    - action: "rephrase_question"
      location: "sections/02/quiz-01/questions.gift:15"
      deadline: "2024-01-22"
      
  optional_recommendations:
    - "Rozważyć dodanie case study z perspektywą alternatywną"
    - "Aktualizacja bibliografii o pozycje z 2023 roku"
    
  next_steps:
    - "Autor wprowadza poprawki do 2024-01-22"
    - "Powtórna weryfikacja automatyczna"
    - "Publikacja po zatwierdzeniu"
```

### 2. Plik ethics-report.md

```markdown
# Raport z recenzji etycznej

**Kurs:** Prawda i Prawo Naturalne  
**Data recenzji:** 2024-01-15  
**Recenzent:** AI Ethics Agent v1.0  
**Status:** ✅ Zatwierdzono z drobnymi uwagami

---

## Podsumowanie wykonawcze

Przeprowadzono kompleksową recenzję etyczną materiałów kursu "Prawda i Prawo Naturalne". 
Materiały uzyskały łączny wynik **92/100 punktów**, co kwalifikuje je do zatwierdzenia 
z obowiązkiem wprowadzenia drobnych poprawek.

### Najważniejsze wnioski

✅ **Mocne strony:**
- Wysoki poziom integralności akademickiej
- Szacunek dla godności osoby ludzkiej
- Zrównoważona prezentacja różnych stanowisk

⚠️ **Obszary do poprawy:**
- Uzupełnić 3 cytaty w sekcji 1
- Przeformułować 2 pytania quizowe

---

## Szczegółowe wyniki

[Tabela z scoringiem per sekcja]

---

## Rekomendacje

[Konkretne rekomendacje z lokalizacją w plikach]

---

## Decyzja

**Status:** APPROVED_WITH_REVISIONS  
**Termin poprawek:** 2024-01-22  
**Następna recenzja:** 2025-01-15
```

---

## Integracja z workflow CI/CD

### GitHub Actions workflow

```yaml
# .github/workflows/ethics-review.yml

name: Ethics Review

on:
  pull_request:
    paths:
      - 'courses/**/*.md'
      - 'courses/**/*.yaml'
      
jobs:
  ethics-scan:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements-review.txt
          
      - name: Run automatic ethics scan
        run: |
          python scripts/review/auto-scan.py \
            --input courses/ \
            --output reports/ethics-auto.json \
            --fail-on critical
            
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: ethics-report
          path: reports/ethics-auto.json
          
      - name: Comment on PR
        if: always()
        uses: actions/github-script@v6
        with:
          script: |
            // Add comment with ethics scan results
```

### Pre-commit hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running ethics pre-commit check..."

python scripts/review/pre-commit-ethics.py \
    --staged-files \
    --block-on "hate-speech,manipulation,pseudoscience"

if [ $? -ne 0 ]; then
    echo "❌ Ethics check failed. Please fix issues before committing."
    exit 1
fi

echo "✅ Ethics check passed."
exit 0
```

---

## Checklista szybkiej recenzji

### 5-minutowy check przed publikacją

```markdown
## Quick Ethics Checklist

### Godność osoby
- [ ] Brak języka dehumanizującego
- [ ] Szacunek dla różnych przekonań
- [ ] Brak presji psychicznej

### Prawda
- [ ] Fakty oddzielone od opinii
- [ ] Źródła cytowane
- [ ] Brak pseudonauki

### Wolność
- [ ] Autonomia uczestnika zachowana
- [ ] Możliwość dyskutowania
- [ ] Brak nakazów światopoglądowych

### Dobro wspólne
- [ ] Orientacja prospołeczna
- [ ] Brak dyskryminacji
- [ ] Dostępność zapewniona

### Integralność akademicka
- [ ] Brak plagiatu
- [ ] Autorstwo jasne
- [ ] Konflikty interesów ujawnione

## Decyzja
- [ ] ✅ Publikuj
- [ ] ⚠️ Publikuj z uwagami
- [ ] ❌ Wstrzymaj do poprawek
```

---

## Powiązane dokumenty

- `docs/04-AUTOMATION-AND-ETHICS.md` - Zasady etyczne i automatyzacja
- `templates/prompts/generate-course-outline.md` - Generowanie planów kursów
- `templates/prompts/generate-quiz-questions.md` - Generowanie pytań quizowych
- `scripts/review/auto-scan.py` - Skrypt automatycznej recenzji
- `config/ethics-dictionary.yaml` - Słownik terminów etycznych

---

## Wersjonowanie

| Wersja | Data | Zmiany |
|--------|------|--------|
| 1.0.0 | 2024-01-15 | Pierwsza wersja promptu |

---

**Autor:** AI Ethics Review Agent (Qwen Code)  
**Licencja:** CC BY-SA 4.0  
**Status:** Gotowy do użycia  
**Zatwierdził:** Komisja Etyczna (do wypełnienia)
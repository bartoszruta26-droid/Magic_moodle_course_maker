# Specyfikacja Techniczna Formatów Plików dla Qwen Coder: Quizy, Aktywności i Zasoby

## 1. Wprowadzenie

Ten dokument stanowi szczegółowy podręcznik techniczny dla agenta AI **Qwen Coder**. Jego celem jest dostarczenie precyzyjnych wytycznych dotyczących składni, formatowania i struktury plików tekstowych używanych do definiowania zawartości kursów Moodle. Dokument koncentruje się na specyficznych formatach danych: GIFT, YAML, Aiken, XML oraz Markdown z rozszerzeniami semantycznymi.

Zrozumienie tych formatów jest kluczowe dla zapewnienia poprawności merytorycznej i technicznej generowanych kursów. Błędy w składni tych plików uniemożliwią import do systemu Moodle.

---

## 2. Format GIFT (General Import Format Technology)

Format GIFT jest najbardziej wszechstronnym formatem tekstowym obsługiwanym przez Moodle. Pozwala na definiowanie większości typów pytań w czytelny sposób.

### 2.1. Podstawowa Składnia

- **Komentarze:** Linie zaczynające się od `//` są ignorowane.
- **Nazwa pytania:** Umieszczana w podwójnych nawiasach `::Nazwa Pytania::`.
- **Treść pytania:** Następuje bezpośrednio po nazwie.
- **Odpowiedzi:** Umieszczane w nawiasach klamrowych `{}`.
- **Poprawna odpowiedź:** Poprzedzona znakiem `=`.
- **Błędna odpowiedź:** Poprzedzona znakiem `~`.
- **Sprzężenie zwrotne:** Umieszczane w nawiasach `(#komentarz do odpowiedzi)`.

### 2.2. Typy Pytań w GIFT

#### A. Wielokrotnego Wyboru (Multiple Choice - Single Answer)
Użytkownik wybiera jedną poprawną odpowiedź.

```gift
::Stolica Francji:: Które miasto jest stolicą Francji? {
    =Paryż (#Doskonale! Paryż to stolica Francji.)
    ~Berlin (#Błąd. Berlin to stolica Niemiec.)
    ~Madryt (#Błąd. Madryt to stolica Hiszpanii.)
    ~Rzym (#Błąd. Rzym to stolica Włoch.)
}
```

#### B. Wielokrotnego Wyboru (Wiele Odpowiedzi)
Użytkownik musi zaznaczyć wszystkie poprawne odpowiedzi. Należy użyć procentowej wagi odpowiedzi. Suma wag poprawnych odpowiedzi musi wynosić 100%.

```gift
::Liczb Parzyste:: Zaznacz wszystkie liczby parzyste: {
    %50%2 (#Dobra odpowiedź, ale nie jedyna.)
    %50%4 (#Dobra odpowiedź, ale nie jedyna.)
    ~1 (#To liczba nieparzysta.)
    ~3 (#To liczba nieparzysta.)
}
```

#### C. Prawda / Fałsz (True/False)
Skrócony zapis dla pytań binarnych.

```gift
::Słońce:: Czy Słońce jest planetą? {FALSE}
::Woda:: Czy woda wrze w 100 stopniach Celsjusza na poziomie morza? {TRUE}
```

#### D. Krótka Odpowiedź (Short Answer)
Użytkownik wpisuje tekst. Można zdefiniować wiele wariantów poprawnej odpowiedzi. Użycie znaku `*` jako wzorca akceptuje wszystko (rzadko stosowane).

```gift
::Autor Hamleta:: Kto napisał Hamleta? {
    =Szekspir
    =William Szekspir
    =Shakespeare
    =William Shakespeare
}
```

Można używać znaków wieloznacznych:
- `*` zastępuje dowolną sekwencję znaków.
- `?` zastępuje pojedynczy znak.

```gift
::Kolor:: Jaki kolor ma trawa? {
    =zielon* (#Akceptuje: zielony, zielona, zielone.)
}
```

#### E. Dopasowanie (Matching)
Pytania typu "połącz w pary". Format wymaga listy propozycji oddzielonych znakiem `=`.

```gift
::Stolice Państw:: Połącz państwo ze stolicą: {
    =Polska -> Warszawa
    =Niemcy -> Berlin
    =Francja -> Paryż
    =Hiszpania -> Madryt
}
```

#### F. Pytania Osadzone (Cloze / Embedded Answers)
Najpotężniejszy typ pytania w GIFT, pozwalający na tworzenie tekstów z lukami różnych typów wewnątrz jednego akapitu. Składnia jest bardziej złożona i wykorzystuje nawiasy klamrowe z indeksami.

**Składnia:** `{INDEX:TYP:OPCJE}`

**Przykład:**
```gift
::Cloze Example::
Mozart urodził się w roku {1:SHORTANSWER:=1756}, a zmarł w wieku {2:NUMERICAL:=35}.
Jego najsłynniejsza opera to {3:MULTICHOICE:=Czarodziejski Flet~Don Giovanni~Wesele Figara}.
```

**Typy w Cloze:**
- `SHORTANSWER`: Krótka odpowiedź tekstowa.
- `NUMERICAL`: Odpowiedź liczbowa (można dodać tolerancję, np. `:1756:5`).
- `MULTICHOICE`: Wybór z listy rozwijanej.
- `MULTIRESPONSE`: Wybór wielu opcji (checkbox).

### 2.3. Kodowanie Znaków Specjalnych
Jeśli w treści pytania lub odpowiedzi potrzebne są znaki specjalne używane w składni GIFT (`{`, `}`, `=`, `~`, `#`, `:`), należy poprzedzić je odwrotnym ukośnikiem `\`.

```gift
::Symbol:: Jaki symbol oznacza zbiór pusty? {
    =\emptyset
    =\{\}
}
```

---

## 3. Format YAML dla Konfiguracji Aktywności

YAML (YAML Ain't Markup Language) jest używany do definiowania metadanych aktywności, ustawień quizów oraz struktury lekcji. Jest czytelny dla człowieka i łatwy do parsowania przez skrypty.

### 3.1. Definicja Quizu

Plik `.yaml` definiujący ustawienia całego quizu.

```yaml
quiz_name: "Sprawdzian z Algebry - Tydzień 3"
intro: "Proszę rozwiązać 5 pytań w ciągu 30 minut."
introformat: 1 # 1 = HTML
timeopen: 1704067200 # Timestamp Unix
timeclose: 1704153600
timelimit: 1800 # Sekundy (30 min)
attempts: 2 # Liczba prób
attemptonlast: 0
grademethod: 1 # 1 = Highest grade
decimalpoints: 2
reviewopinions: 1 # Pokaż opinie po próbie
questionsperpage: 1
shufflequestions: 1 # Mieszaj pytania
shuffleanswers: 1 # Mieszaj odpowiedzi
questionbankcategory: "Algebra/Liniowa"
tags:
  - algebra
  - sprawdzian
  - semestr1
```

### 3.2. Definicja Lekcji (Lesson Activity)

Lekcja w Moodle to sekwencja stron. YAML idealnie nadaje się do opisu tej sekwencji.

```yaml
lesson_name: "Wstęp do Programowania Obiektowego"
completion: "view"
pages:
  - id: start
    title: "Strona Startowa"
    type: branchtable
    contents: |
      <h2>Witaj w lekcji!</h2>
      <p>Dowiesz się tutaj o klasach i obiektach.</p>
    jumps:
      - next_id: class_def
        label: "Dalej: Definicja Klasy"
      - next_id: end
        label: "Zakończ lekcję"

  - id: class_def
    title: "Czym jest Klasa?"
    type: contentpage
    contents: |
      Klasa to szablon do tworzenia obiektów.
    questions:
      - type: multichoice
        text: "Czy klasa jest obiektem?"
        options:
          - "Tak"
          - "Nie"
        correct: 1 # Indeks poprawnej odpowiedzi (0-based)
        jump_correct: next_id: object_ex
        jump_wrong: next_id: class_def # Powrót do przeczytania

  - id: object_ex
    title: "Przykład Obiektu"
    type: contentpage
    contents: "Obiekt to instancja klasy."
    jumps:
      - next_id: end
        label: "Zakończ"

  - id: end
    title: "Koniec"
    type: endofbranch
```

---

## 4. Format Aiken

Format Aiken jest bardzo prostym formatem do pytań wielokrotnego wyboru. Jest mniej elastyczny niż GIFT, ale niezwykle czytelny. Wymaga ścisłego przestrzegania formatowania liter (A., B., C., D.).

**Zasady:**
1. Treść pytania w pierwszej linii.
2. Odpowiedzi zaczynają się od wielkiej litery, kropki i spacji (np. `A. `).
3. Linia z odpowiedzią musi zaczynać się od początku wiersza (brak wcięć).
4. Ostatnia linia musi zaczynać się od `ANSWER: ` i zawierać literę poprawnej odpowiedzi.

**Przykład pliku `quiz_aiken.txt`:**

```text
Jakiego języka używa się do stylizacji stron WWW?
A. HTML
B. CSS
C. Python
D. SQL
ANSWER: B

Który tag HTML służy do tworzenia nagłówków?
A. <head>
B. <header>
C. <h1> do <h6>
D. <top>
ANSWER: C
```

*Uwaga dla Qwen Coder:* Nie dodawaj żadnych komentarzy ani pustych linii między pytaniem a odpowiedziami w formacie Aiken, gdyż może to spowodować błąd parsera.

---

## 5. Natywny Format XML Moodle

Dla najbardziej zaawansowanych typów pytań, których nie obsługuje GIFT (np. pytania typu "Drag and drop into text", "Pexeso", "Stack" z obsługą wyrażeń matematycznych), konieczne jest użycie natywnego formatu XML Moodle.

Struktura pliku XML musi być zgodna ze schematem Moodle Backup.

**Przykład struktury XML:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name>
      <text>Pytanie Matematyczne XML</text>
    </name>
    <questiontext format="html">
      <text>Oblicz granicę: $$ \lim_{x \to 0} \frac{\sin x}{x} $$</text>
    </questiontext>
    <generalfeedback format="html">
      <text>Granica ta wynosi 1, co jest fundamentalnym twierdzeniem rachunku różniczkowego.</text>
    </generalfeedback>
    <defaultgrade>1.0000000</defaultgrade>
    <penalty>0.3333333</penalty>
    <hidden>0</hidden>
    <single>true</single>
    <answernumbering>abc</answernumbering>
    <answer fraction="100" format="html">
      <text>1</text>
      <feedback format="html">
        <text>Dobrze!</text>
      </feedback>
    </answer>
    <answer fraction="0" format="html">
      <text>0</text>
      <feedback format="html">
        <text>Źle.</text>
      </feedback>
    </answer>
  </question>
  
  <!-- Przykład pytania typu Stack (wymaga pluginu) -->
  <question type="stack">
    <name><text>Stack Question Example</text></name>
    <questiontext format="html">
      <text><![CDATA[
        Wpisz pochodną funkcji \( f(x) = x^2 \): 
        [[input:ans1]] [[validation:ans1]]
      ]]></text>
    </questiontext>
    <stackversion>
      <text><![CDATA[2023010100]]></text>
    </stackversion>
    <questionvariables>
      <text></text>
    </questionvariables>
    <specificfeedback format="html">
      <text></text>
    </specificfeedback>
    <prtcorrect format="html">
      <text><![CDATA[Dobra robota!]]></text>
    </prtcorrect>
  </question>
</quiz>
```

*Wskazówka:* Używaj sekcji `CDATA` w XML, aby uniknąć problemów z escapowaniem znaków specjalnych (np. `<`, `>`, `&`) w treściach matematycznych lub kodzie programistycznym.

---

## 6. Markdown z Front-Matter dla Zasobów

Dla standardowych zasobów Moodle takich jak "Strona" (Page), "Etykieta" (Label) czy "Książka" (Book), agent Qwen Coder powinien generować pliki Markdown z nagłówkiem YAML (Front-Matter).

**Struktura pliku `.md`:**

```markdown
---
moodle_type: page  # page, label, book_chapter
title: "Wprowadzenie do Sieci Neuronowych"
section: 1
completion_rule: "view"
restrict_access:
  - type: date
    operator: ">="
    value: 1704067200
---

# Sieci Neuronowe

Sieć neuronowa to model inspirowany działaniem ludzkiego mózgu.

## Budowa Neuronu

Neuron składa się z:
1. Dendrytów (wejścia)
2. Somatu (ciało komórki)
3. Aksonu (wyjście)

```python
# Przykład kodu wewnątrz zasobu
def activate(x):
    return 1 / (1 + exp(-x))
```

> Ważne: Funkcja aktywacji musi być różniczkowalna.
```

**Obsługa Assetów:**
Odnośniki do obrazków w Markdown muszą być względne wobec katalogu `assets`.

```markdown
![Schemat neuronu](../../assets/images/neuron_schema.png)
```

Agent musi upewnić się, że ścieżka jest poprawna względem lokalizacji pliku `.md` w strukturze katalogów `sections`.

---

## 7. Walidacja i Najczęstsze Błędy

Podczas generowania plików, Qwen Coder powinien stosować się do następujących zasad walidacji:

1. **Spójność ID:** W plikach YAML (Lekcje), identyfikatory `id` oraz `next_id` muszą być unikalne w ramach jednej lekcji i tworzyć spójny graf przejść bez pętli nieskończonych (chyba że zamierzone).
2. **Suma Procentów:** W pytaniach GIFT typu "wiele odpowiedzi", suma procentów poprawnych odpowiedzi musi równać się 100%.
3. **Brak Znaków Specjalnych:** W formacie Aiken absolutnie zabronione są wcięcia przed opcjami odpowiedzi.
4. **Encodowanie:** Wszystkie pliki muszą być zapisywane w kodowaniu **UTF-8 bez BOM**.
5. **Nazwy Plików:** Nazwy plików z pytaniami powinny być opisowe, np. `week1_algebra.gift`, `final_exam.xml`, ale nie mogą zawierać spacji (należy używać `_` lub `-`).

Przestrzeganie tych wytycznych zapewni bezbłędny proces konwersji repozytorium GitHub na pakiet instalacyjny Moodle.

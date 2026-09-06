

# Formaty pytań i struktura quizów

> Pełna specyfikacja formatów pytań: GIFT, YAML, Moodle XML, Aiken.
> Struktura quizów, bank pytań, porównanie formatów.

---

## Spis treści

1. [Struktura quizu (quiz.yaml)](#quiz-yaml)
2. [Informacja zwrotna quizu (feedback.md)](#feedback)
3. [Format GIFT – pełna specyfikacja](#gift)
4. [Format YAML – pytania strukturalne](#yaml-questions)
5. [Format Moodle XML – pytania](#xml-questions)
6. [Format Aiken – prosty multichoice](#aiken)
7. [Porównanie formatów](#comparison)

---

<a id="quiz-yaml"></a>
## 1. Struktura quizu – `quiz.yaml`

```yaml
# ============================================================
# Plik: quiz-01/quiz.yaml
# Typ modułu: quiz
# ============================================================

quiz:
  # --- Identyfikacja ---
  name: "Test: Podstawy Prawdy"
  intro: |
    Ten test sprawdza wiedzę zdobytą w pierwszej sekcji kursu.

    **Zasady:**
    - Czas: 30 minut
    - Liczba prób: 3
    - Ocena: najwyższy wynik z prób
    - Można wrócić do poprzednich pytań
  intro_format: "html"

  # --- Ustawienia czasu ---
  timeopen: "2025-09-01T00:00:00Z"
  timeclose: null
  timelimit: 1800
  overduehandling: "autoabandon"
  gracetimeout: 300

  # --- Ustawienia prób ---
  attempts: 3
  grademethod: "highest"
  canredoquestions: false

  # --- Kolejność i nawigacja ---
  shuffleanswers: true
  questionsperpage: 5
  navmethod: "free"

  # --- Ocenianie ---
  sumgrades: 10.0
  grade: 10.0
  passgrade: 60
  decimalpoints: 2

  # --- Feedback ogólny ---
  overallfeedback:
    - grade: 100
      text: "Doskonale! Opanowałeś materiał w pełni."
    - grade: 80
      text: "Bardzo dobrze! Solidna wiedza."
    - grade: 60
      text: "Zaliczone, ale warto powtórzyć materiał."
    - grade: 0
      text: "Nie zaliczyłeś. Wróć do materiałów i spróbuj ponownie."

  # --- Bezpieczeństwo ---
  password: null
  subnet: null
  browsersecurity: ""

  # --- Ukończenie ---
  completion:
    enabled: true
    type: "pass"

  # --- Źródła pytań ---
  question_sources:
    - type: "local_file"
      format: "gift"
      path: "questions.gift"
    - type: "local_file"
      format: "yaml"
      path: "questions.yaml"
    - type: "local_file"
      format: "xml"
      path: "questions.xml"
    - type: "question_bank"
      category: "Prawda"
      count: 5
    - type: "random"
      from_category: "Prawo naturalne"
      count: 3

  questions_inline: false

  tags:
    - "test"
    - "sekcja-01"
    - "prawda"


---

<a id="feedback"></a>
## 2. Informacja zwrotna quizu – `feedback.md`


<!-- Plik: quiz-01/feedback.md -->
<!-- Konwersja: Markdown → HTML → Moodle Overall Feedback -->

# Informacja zwrotna

## Wynik 90-100%
🎉 **Doskonale!** Opanowałeś materiał sekcji pierwszej w pełni.
Jesteś gotowy, aby przejść do sekcji drugiej.

## Wynik 70-89%
👍 **Bardzo dobrze!** Masz solidną wiedzę, ale warto powtórzyć
kilka zagadnień. Zwróć uwagę na pytania, które sprawiły Ci trudność.

## Wynik 60-69%
📖 **Zaliczone**, ale zachęcam do powtórzenia materiału.
Przeczytaj ponownie strony sekcji i spróbuj quizu jeszcze raz.

## Wynik poniżej 60%
🔄 **Nie zaliczyłeś.** Nie martw się – wróć do materiałów,
przeczytaj je uważnie i spróbuj ponownie. Masz jeszcze próby.

---

> *„Nie lękaj się! Wypłyń na głębię."* (Łk 5, 4)


---

<a id="gift"></a>
## 3. Format GIFT – pełna specyfikacja

GIFT jest najbardziej uniwersalnym formatem tekstowym do importu
pytań do Moodle. Poniżej pełna specyfikacja z przykładami dla
każdego typu pytania.

### 3.1. Pytania wielokrotnego wyboru (multichoice)

```gift
// ============================================================
// Plik: quiz-01/questions.gift
// Format: GIFT
// Kodowanie: UTF-8
// ============================================================

// --- Komentarz (ignorowany przez parser) ---

::Definicja prawdy::
Czym jest prawda w ujęciu klasycznym? {
    =Zgodnością umysłu z rzeczywistością
    ~Subiektywnym odczuciem jednostki
    ~Konsensusem społecznym
    ~Wynikiem głosowania większości
}

// Pytanie z informacją zwrotną dla każdej odpowiedzi
::Prawda obiektywna::
Prawda obiektywna oznacza, że: {
    =%100%Istnieje niezależnie od ludzkich opinii
        #Poprawnie! Prawda jest niezależna od subiektywnych przekonań.
    ~%0%Jest ustalana przez większość społeczeństwa
        #Niepoprawnie. Prawda nie zależy od głosowania.
    ~%0%Każdy ma swoją własną prawdę
        #Niepoprawnie. To relatywizm, nie prawda obiektywna.
    ~%-50%Jest zawsze względna i kontekstowa
        #Częściowo niepoprawnie. Prawda może mieć kontekst,
         ale nie jest względna w swej istocie.
}

// Pytanie z wieloma poprawnymi odpowiedziami (multiselect)
::Wymiary prawdy::
Które z poniższych stwierdzeń dotyczą prawdy? (wybierz wszystkie poprawne) {
    ~%50%Prawda jest dostępna rozumowi ludzkiemu
    ~%50%Prawda ma wymiar osobowy
    ~%-50%Prawda jest zawsze subiektywna
    ~%50%Prawda wyzwala człowieka
}

// Pytanie z obrazkiem
::Diagram prawdy::
Co przedstawia poniższy diagram? {
    <img src="../../media/images/diagram-prawda.png"
         alt="Diagram przedstawiający relację prawdy i wolności"
         width="400" height="300">
    =Relację między prawdą a wolnością
    ~Hierarchię wartości
    ~Proces poznania naukowego
}


### 3.2. Pytania Prawda/Fałsz (truefalse)

```gift
::Prawo naturalne::
Prawo naturalne jest dostępne wyłącznie przez objawienie Boże. {FALSE}

::Godność człowieka::
Godność człowieka jest przyrodzona i niezbywalna. {TRUE}

::Prawda i wolność::
Poznawanie prawdy ogranicza wolność człowieka. {
    FALSE#Niepoprawnie. Prawda nie ogranicza, lecz wyzwala.
}

::Źródło prawa naturalnego::
Prawo naturalne jest wpisane w naturę człowieka i dostępne
poznaniu rozumowemu. {
    TRUE#Poprawnie. To klasyczna definicja prawa naturalnego.
}


### 3.3. Pytania krótkiej odpowiedzi (shortanswer)

```gift
::Uzupełnij cytat::
Uzupełnij cytat: "Poznacie prawdę, a prawda was ..." {
    =wyzwoli
    =uwolni
}

::Definicja jednym słowem::
Jak jednym słowem określa się zgodność umysłu z rzeczywistością? {
    =prawda
    =Prawda
    =PRAWDA
}

::Autor encykliki::
Kto jest autorem encykliki "Veritatis Splendor"? {
    =Jan Paweł II
    =Jan Paweł Drugi
    =Karol Wojtyła
}


### 3.4. Pytania numeryczne (numerical)

```gift
::Rok ogłoszenia encykliki::
W którym roku ogłoszono encyklikę "Veritatis Splendor"? {
    =1993:0
}

::Liczba przykazań::
Ile jest przykazań Bożych? {
    =10:0
}

::Temperatura wrzenia wody::
W jakiej temperaturze (°C) wrze woda na poziomie morza? {
    =100:1
}

::Procent zaliczenia::
Jaki minimalny procent punktów (0-100) jest wymagany
do zaliczenia kursu? {
    =60:5
}

// Zakres numeryczny
::Wiek pełnoletności::
Od ilu lat człowiek osiąga pełnoletność w Polsce? {
    =18..18
}


### 3.5. Pytania dopasowania (matching)

```gift
::Dopasuj pojęcia::
Dopasuj pojęcia do ich definicji. {
    =Prawda -> Zgodność umysłu z rzeczywistością
    =Wolność -> Zdolność do samostanowienia w świetle prawdy
    =Godność -> Przyrodzona wartość każdego człowieka
    =Rozum -> Zdolność poznania prawdy
}

::Dopasuj dokumenty::
Dopasuj dokumenty do ich autorów. {
    =Veritatis Splendor -> Jan Paweł II
    =Fides et Ratio -> Jan Paweł II
    =Dei Verbum -> Sobór Watykański II
    =Katechizm Kościoła Katolickiego -> Jan Paweł II
}


### 3.6. Pytania esejowe (essay)

```gift
::Esej: Prawda w życiu codziennym::
Opisz, w jaki sposób prawda obiektywna wpływa na relacje
międzyludzkie. Podaj konkretne przykłady z życia codziennego.
Odwołaj się do nauczania Kościoła Katolickiego. (min. 200 słów) {
}

::Esej: Prawo naturalne::
Wyjaśnij znaczenie prawa naturalnego dla współczesnego
prawodawstwa. Czy prawo naturalne może być podstawą
praw człowieka? Uzasadnij swoją odpowiedź. {
}


### 3.7. Pytania z luką (missingword)

```gift
::Luka: Definicja prawdy::
Prawda jest {=zgodnością ~subiektywnością ~konsensusem}
umysłu z rzeczywistością.

::Luka: Cytat biblijny::
"Poznacie {=prawdę ~wolność ~mądrość}, a prawda was wyzwoli."

::Luka: Wiele luk::
Prawo {=naturalne ~pozytywne ~zwyczajowe} jest wpisane
w {=naturę ~kulturę ~historię} człowieka i dostępne
poznaniu {=rozumowemu ~empirycznemu ~mistycznemu}.


### 3.8. Pytania obliczeniowe (calculated)

```gift
::Oblicz pole prostokąta::
Oblicz pole prostokąta o długości {x} i szerokości {y}. {
    ={x}*{y}
}
// Dataset definitions (w osobnej sekcji lub pliku YAML):
// x: min=1, max=10, step=1, distribution=uniform
// y: min=1, max=10, step=1, distribution=uniform


---

<a id="yaml-questions"></a>
## 4. Format YAML – pytania strukturalne

### Plik `questions.yaml` – pełna specyfikacja

```yaml
# ============================================================
# Plik: quiz-01/questions.yaml
# Format: YAML (własny format strukturalny)
# Konwersja: YAML → GIFT lub YAML → Moodle XML
# ============================================================

quiz_questions:
  metadata:
    course: "PRAWDA_NATURA_01"
    section: "01-wprowadzenie"
    quiz: "quiz-01"
    author: "Zespół Misyjny"
    version: "1.0.0"
    language: "pl"
    difficulty: "beginner"

  categories:
    - name: "Prawda"
      description: "Pytania dotyczące pojęcia prawdy"
    - name: "Prawo naturalne"
      description: "Pytania dotyczące prawa naturalnego"
    - name: "Godność człowieka"
      description: "Pytania dotyczące godności osoby"

  questions:
    # === PYTANIE 1: Multichoice ===
    - id: "q001"
      type: "multichoice"
      category: "Prawda"
      name: "Definicja prawdy"
      questiontext: "Czym jest prawda w ujęciu klasycznym?"
      questiontext_format: "html"
      generalfeedback: |
        Prawda w ujęciu klasycznym jest zgodnością umysłu
        z rzeczywistością (adaequatio intellectus et rei).
      defaultmark: 1.0
      penalty: 0.3333
      shuffleanswers: true
      answernumbering: "abc"

      single: true
      answers:
        - text: "Zgodnością umysłu z rzeczywistością"
          fraction: 100
          feedback: "Poprawnie! To klasyczna definicja prawdy."
        - text: "Subiektywnym odczuciem jednostki"
          fraction: 0
          feedback: "Niepoprawnie. To relatywizm."
        - text: "Konsensusem społecznym"
          fraction: 0
          feedback: "Niepoprawnie. Prawda nie zależy od głosowania."
        - text: "Wynikiem głosowania większości"
          fraction: 0
          feedback: "Niepoprawnie."

      tags:
        - "prawda"
        - "filozofia"
        - "definicja"

      media:
        type: "none"

    # === PYTANIE 2: True/False ===
    - id: "q002"
      type: "truefalse"
      category: "Prawo naturalne"
      name: "Dostępność prawa naturalnego"
      questiontext: |
        Prawo naturalne jest dostępne wyłącznie przez objawienie Boże.
      answer: false
      feedbacktrue: |
        Niepoprawnie. Prawo naturalne jest dostępne poznaniu
        rozumowemu, niezależnie od objawienia.
      feedbackfalse: |
        Poprawnie. Prawo naturalne jest wpisane w naturę
        człowieka i dostępne rozumowi.
      defaultmark: 1.0
      penalty: 1.0
      tags:
        - "prawo naturalne"
        - "rozum"

    # === PYTANIE 3: Short Answer ===
    - id: "q003"
      type: "shortanswer"
      category: "Prawda"
      name: "Uzupełnij cytat biblijny"
      questiontext: |
        Uzupełnij cytat: "Poznacie prawdę, a prawda was ..."
      usecase: false
      answers:
        - text: "wyzwoli"
          fraction: 100
          feedback: "Poprawnie!"
        - text: "uwolni"
          fraction: 50
          feedback: "Blisko, ale dokładny cytat to 'wyzwoli'."
      defaultmark: 1.0
      penalty: 0.3333
      tags:
        - "Pismo Święte"
        - "Ewangelia Jana"

    # === PYTANIE 4: Numerical ===
    - id: "q004"
      type: "numerical"
      category: "Prawda"
      name: "Rok ogłoszenia encykliki"
      questiontext: |
        W którym roku ogłoszono encyklikę "Veritatis Splendor"?
      answers:
        - value: 1993
          tolerance: 0
          fraction: 100
          feedback: "Poprawnie! Encyklika została ogłoszona
                     6 sierpnia 1993 roku."
      defaultmark: 1.0
      penalty: 0.3333
      units: []
      tags:
        - "Jan Paweł II"
        - "encyklika"

    # === PYTANIE 5: Matching ===
    - id: "q005"
      type: "matching"
      category: "Prawda"
      name: "Dopasuj pojęcia do definicji"
      questiontext: "Dopasuj pojęcia do ich definicji."
      shuffleanswers: true
      subquestions:
        - question: "Prawda"
          answer: "Zgodność umysłu z rzeczywistością"
        - question: "Wolność"
          answer: "Zdolność do samostanowienia w świetle prawdy"
        - question: "Godność"
          answer: "Przyrodzona wartość każdego człowieka"
        - question: "Rozum"
          answer: "Zdolność poznania prawdy"
      defaultmark: 1.0
      penalty: 0.3333
      tags:
        - "definicje"
        - "pojęcia"

    # === PYTANIE 6: Essay ===
    - id: "q006"
      type: "essay"
      category: "Godność człowieka"
      name: "Esej: Prawda w życiu codziennym"
      questiontext: |
        Opisz, w jaki sposób prawda obiektywna wpływa na relacje
        międzyludzkie. Podaj konkretne przykłady z życia codziennego.
        Odwołaj się do nauczania Kościoła Katolickiego.

        **Wymagania:**
        - Minimum 200 słów
        - Odwołanie do minimum jednego dokumentu Kościoła
        - Własne przemyślenia i przykłady
      responseformat: "editor"
      responsefieldlines: 15
      attachments: 1
      attachmentsrequired: 0
      graderinfo: |
        Kryteria oceny:
        - Zrozumienie tematu (30%)
        - Odwołanie do źródeł (30%)
        - Własna refleksja (20%)
        - Poprawność językowa (20%)
      defaultmark: 5.0
      penalty: 0
      tags:
        - "esej"
        - "godność"
        - "relacje"

    # === PYTANIE 7: Missing Word ===
    - id: "q007"
      type: "missingword"
      category: "Prawda"
      name: "Luka w definicji"
      questiontext: |
        Prawda jest {=zgodnością ~subiektywnością ~konsensusem}
        umysłu z rzeczywistością.
      defaultmark: 1.0
      penalty: 0.3333
      tags:
        - "definicja"
        - "prawda"

    # === PYTANIE 8: Multiselect ===
    - id: "q008"
      type: "multichoice"
      category: "Prawda"
      name: "Wymiary prawdy (wielokrotny wybór)"
      questiontext: |
        Które z poniższych stwierdzeń dotyczą prawdy?
        (wybierz wszystkie poprawne odpowiedzi)
      single: false
      answers:
        - text: "Prawda jest dostępna rozumowi ludzkiemu"
          fraction: 33.333
          feedback: "Poprawnie."
        - text: "Prawda ma wymiar osobowy"
          fraction: 33.333
          feedback: "Poprawnie."
        - text: "Prawda jest zawsze subiektywna"
          fraction: -33.333
          feedback: "Niepoprawnie. Prawda jest obiektywna."
        - text: "Prawda wyzwala człowieka"
          fraction: 33.334
          feedback: "Poprawnie."
      shuffleanswers: true
      answernumbering: "abc"
      defaultmark: 1.0
      penalty: 0.3333
      tags:
        - "prawda"
        - "wymiary"


---

<a id="xml-questions"></a>
## 5. Format Moodle XML – pytania

### Plik `questions.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!--
Plik: quiz-01/questions.xml
Format: Moodle XML (Question format)
Kodowanie: UTF-8
Import: Moodle → Course Administration → Import → Moodle XML format
-->
<quiz>
  <!-- Kategoria pytań -->
  <question type="category">
    <category>
      <text>$course$/Prawda</text>
    </category>
  </question>

  <!-- Pytanie 1: Multichoice -->
  <question type="multichoice">
    <name>
      <text>Definicja prawdy</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>Czym jest prawda w ujęciu klasycznym?</p>]]></text>
    </questiontext>
    <generalfeedback format="html">
      <text><![CDATA[<p>Prawda w ujęciu klasycznym jest zgodnością
      umysłu z rzeczywistością.</p>]]></text>
    </generalfeedback>
    <defaultgrade>1.0</defaultgrade>
    <penalty>0.3333</penalty>
    <hidden>0</hidden>
    <single>true</single>
    <shuffleanswers>true</shuffleanswers>
    <answernumbering>abc</answernumbering>

    <answer fraction="100" format="html">
      <text>Zgodnością umysłu z rzeczywistością</text>
      <feedback format="html">
        <text>Poprawnie! To klasyczna definicja prawdy.</text>
      </feedback>
    </answer>
    <answer fraction="0" format="html">
      <text>Subiektywnym odczuciem jednostki</text>
      <feedback format="html">
        <text>Niepoprawnie. To relatywizm.</text>
      </feedback>
    </answer>
    <answer fraction="0" format="html">
      <text>Konsensusem społecznym</text>
      <feedback format="html">
        <text>Niepoprawnie. Prawda nie zależy od głosowania.</text>
      </feedback>
    </answer>

    <tags>
      <tag><text>prawda</text></tag>
      <tag><text>filozofia</text></tag>
    </tags>
  </question>

  <!-- Pytanie 2: True/False -->
  <question type="truefalse">
    <name>
      <text>Dostępność prawa naturalnego</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>Prawo naturalne jest dostępne wyłącznie
      przez objawienie Boże.</p>]]></text>
    </questiontext>
    <defaultgrade>1.0</defaultgrade>
    <penalty>1.0</penalty>
    <hidden>0</hidden>
    <answer fraction="0" format="html">
      <text>true</text>
      <feedback format="html">
        <text>Niepoprawnie. Prawo naturalne jest dostępne rozumowi.</text>
      </feedback>
    </answer>
    <answer fraction="100" format="html">
      <text>false</text>
      <feedback format="html">
        <text>Poprawnie. Prawo naturalne jest dostępne rozumowi.</text>
      </feedback>
    </answer>
  </question>

  <!-- Pytanie 3: Short Answer -->
  <question type="shortanswer">
    <name>
      <text>Uzupełnij cytat biblijny</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>Uzupełnij cytat: "Poznacie prawdę,
      a prawda was ..."</p>]]></text>
    </questiontext>
    <defaultgrade>1.0</defaultgrade>
    <penalty>0.3333</penalty>
    <hidden>0</hidden>
    <usecase>0</usecase>

    <answer fraction="100" format="plain_text">
      <text>wyzwoli</text>
      <feedback format="html">
        <text>Poprawnie!</text>
      </feedback>
    </answer>
    <answer fraction="50" format="plain_text">
      <text>uwolni</text>
      <feedback format="html">
        <text>Blisko, ale dokładny cytat to 'wyzwoli'.</text>
      </feedback>
    </answer>
  </question>

  <!-- Pytanie 4: Numerical -->
  <question type="numerical">
    <name>
      <text>Rok ogłoszenia encykliki</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>W którym roku ogłoszono encyklikę
      "Veritatis Splendor"?</p>]]></text>
    </questiontext>
    <defaultgrade>1.0</defaultgrade>
    <penalty>0.3333</penalty>
    <hidden>0</hidden>

    <answer fraction="100" format="plain_text">
      <text>1993</text>
      <tolerance>0</tolerance>
      <feedback format="html">
        <text>Poprawnie! Encyklika została ogłoszona
        6 sierpnia 1993 roku.</text>
      </feedback>
    </answer>
  </question>

  <!-- Pytanie 5: Matching -->
  <question type="matching">
    <name>
      <text>Dopasuj pojęcia do definicji</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[<p>Dopasuj pojęcia do ich definicji.</p>]]></text>
    </questiontext>
    <defaultgrade>1.0</defaultgrade>
    <penalty>0.3333</penalty>
    <hidden>0</hidden>
    <shuffleanswers>true</shuffleanswers>

    <subquestion format="html">
      <text>Prawda</text>
      <answer>
        <text>Zgodność umysłu z rzeczywistością</text>
      </answer>
    </subquestion>
    <subquestion format="html">
      <text>Wolność</text>
      <answer>
        <text>Zdolność do samostanowienia w świetle prawdy</text>
      </answer>
    </subquestion>
    <subquestion format="html">
      <text>Godność</text>
      <answer>
        <text>Przyrodzona wartość każdego człowieka</text>
      </answer>
    </subquestion>
  </question>

  <!-- Pytanie 6: Essay -->
  <question type="essay">
    <name>
      <text>Esej: Prawda w życiu codziennym</text>
    </name>
    <questiontext format="html">
      <text><![CDATA[
        <p>Opisz, w jaki sposób prawda obiektywna wpływa na relacje
        międzyludzkie. Podaj konkretne przykłady z życia codziennego.</p>
        <p><strong>Wymagania:</strong></p>
        <ul>
          <li>Minimum 200 słów</li>
          <li>Odwołanie do minimum jednego dokumentu Kościoła</li>
          <li>Własne przemyślenia i przykłady</li>
        </ul>
      ]]></text>
    </questiontext>
    <defaultgrade>5.0</defaultgrade>
    <penalty>0</penalty>
    <hidden>0</hidden>
    <responseformat>editor</responseformat>
    <responserequired>1</responserequired>
    <responsefieldlines>15</responsefieldlines>
    <attachments>1</attachments>
    <attachmentsrequired>0</attachmentsrequired>
    <graderinfo format="html">
      <text><![CDATA[
        <p>Kryteria oceny:</p>
        <ul>
          <li>Zrozumienie tematu (30%)</li>
          <li>Odwołanie do źródeł (30%)</li>
          <li>Własna refleksja (20%)</li>
          <li>Poprawność językowa (20%)</li>
        </ul>
      ]]></text>
    </graderinfo>
  </question>
</quiz>


---

<a id="aiken"></a>
## 6. Format Aiken – prosty multichoice

```text
// Plik: questions.aiken
// Format: Aiken (tylko multichoice z jedną odpowiedzią)
// Kodowanie: UTF-8

Czym jest prawda w ujęciu klasycznym?
A. Zgodnością umysłu z rzeczywistością
B. Subiektywnym odczuciem jednostki
C. Konsensusem społecznym
D. Wynikiem głosowania większości
ANSWER: A

Kto jest autorem encykliki "Veritatis Splendor"?
A. Benedykt XVI
B. Jan Paweł II
C. Franciszek
D. Paweł VI
ANSWER: B


---

<a id="comparison"></a>
## 7. Porównanie formatów pytań

| Cecha | GIFT | YAML | Moodle XML | Aiken |
|---|---|---|---|---|
| **Czytelność dla człowieka** | Średnia | Wysoka | Niska | Wysoka |
| **Czytelność dla AI** | Średnia | Wysoka | Średnia | Wysoka |
| **Obsługiwane typy pytań** | 8+ | Wszystkie | Wszystkie | Tylko multichoice |
| **Informacja zwrotna** | Tak | Tak | Tak | Nie |
| **Multimedia** | Tak | Tak | Tak | Nie |
| **Tagi** | Nie | Tak | Tak | Nie |
| **Kategorie** | Tak | Tak | Tak | Nie |
| **Walidacja składni** | Trudna | Łatwa (schema) | Łatwa (XSD) | Łatwa |
| **Generowanie przez AI** | Średnie | Łatwe | Średnie | Łatwe |
| **Import do Moodle** | Bezpośredni | Wymaga konwersji | Bezpośredni | Bezpośredni |
| **Eksport z Moodle** | Tak | Wymaga konwersji | Tak | Nie |


---




# Formaty treści, sekcji, aktywności i zasobów multimedialnych

> Specyfikacja wszystkich plików treści kursu Moodle: metadane,
> sekcje, strony, lekcje, zadania, fora, słowniki, książki,
> warsztaty, H5P, LTI oraz zasoby multimedialne.

---

## Spis treści

1. [Metadane kursu (course.yaml)](#course-yaml)
2. [Metadane sekcji (section.yaml)](#section-yaml)
3. [Ustawienia zaawansowane (settings.yaml)](#settings-yaml)
4. [Treści stron w Markdown](#page-md)
5. [Etykiety (label)](#label)
6. [Zasoby URL](#url-yaml)
7. [Zadanie (assignment.yaml)](#assignment)
8. [Lekcja rozgałęziona (lesson.yaml)](#lesson)
9. [Forum dyskusyjne (forum.yaml)](#forum)
10. [Słownik (glossary.yaml)](#glossary)
11. [Książka wielostronicowa (book.yaml)](#book)
12. [Warsztat – ocena wzajemna (workshop.yaml)](#workshop)
13. [Treść H5P (h5p.yaml)](#h5p)
14. [Narzędzie zewnętrzne LTI (lti.yaml)](#lti)
15. [Zasoby multimedialne](#media)

---

<a id="course-yaml"></a>
## 1. Metadane kursu – `course.yaml`

```yaml
# ============================================================
# Metadane kursu Moodle
# Plik: courses/01-prawda-i-natura/course.yaml
# Format: YAML 1.2
# Kodowanie: UTF-8
# ============================================================

course:
  # --- Identyfikacja ---
  fullname: "Prawda i Natura – Podstawy antropologii chrześcijańskiej"
  shortname: "PRAWDA_NATURA_01"
  idnumber: "KURS-2025-001"

  # --- Klasyfikacja ---
  category: "Kursy Misyjne"
  category_id: null
  tags:
    - "prawda"
    - "prawo naturalne"
    - "antropologia"
    - "teologia"
    - "edukacja"

  # --- Opis ---
  summary: |
    Kurs edukacyjny dla dorosłych poświęcony zrozumieniu prawa naturalnego,
    godności osoby ludzkiej i prawdy jako fundamentu edukacji.

    Kurs jest zgodny z nauczaniem Kościoła Katolickiego i szanuje
    godność każdego uczestnika jako osoby stworzonej na obraz Boży.
  summary_format: "html"
  summary_files:
    - "course.jpg"

  # --- Struktura ---
  format: "topics"                     # topics | weeks | single | social
  numsections: 4
  coursedisplay: "singlepage"

  # --- Widoczność i dostęp ---
  visible: true
  visibleoncoursepage: true
  groupmode: 0                         # 0=brak, 1=separate, 2=visible
  groupmodeforce: false

  # --- Daty ---
  startdate: "2025-09-01T00:00:00Z"
  enddate: null

  # --- Ukończenie kursu ---
  enablecompletion: true
  completioncriteria:
    - type: "self"
    - type: "activity"
      activity: "quiz-01"
      condition: "pass"
    - type: "grade"
      grade: 60

  # --- Ocenianie ---
  gradepass: 60
  showgrades: true
  gradebook_display: "letter"

  # --- Pliki i zasoby ---
  course_image: "course.jpg"
  course_image_alt: "Ikona kursu: Prawda i Natura"

  # --- Ustawienia zaawansowane ---
  lang: "pl"
  theme: ""
  maxbytes: 104857600
  showreports: false

  # --- Metadane rozszerzone ---
  metadata:
    author: "Zespół Misyjny"
    version: "1.0.0"
    created: "2025-01-15"
    modified: "2025-01-20"
    license: "CC BY-SA 4.0"
    language: "pl"
    level: "beginner"
    audience: "Dorośli, katecheci, misjonarze"
    prerequisites: []
    keywords:
      - "prawo naturalne"
      - "godność człowieka"
      - "prawda obiektywna"

    # Zgodność z wytycznymi etycznymi
    ethical_compliance:
      respects_human_dignity: true
      no_manipulation: true
      sources_cited: true
      accessibility_wcag: "AA"
      content_reviewed_by: "Komisja Teologiczna"


---

<a id="section-yaml"></a>
## 2. Metadane sekcji – `section.yaml`

```yaml
# ============================================================
# Metadane sekcji kursu
# Plik: courses/01-prawda-i-natura/sections/01-wprowadzenie/section.yaml
# ============================================================

section:
  # --- Identyfikacja ---
  name: "Wprowadzenie: Czym jest Prawda?"
  number: 1

  # --- Treść ---
  summary: |
    W tej sekcji uczestnik poznaje podstawowe pojęcia związane z prawdą,
    prawem naturalnym i godnością osoby ludzkiej.
  summary_format: "html"
  summary_file: "section.md"

  # --- Widoczność ---
  visible: true
  availability:
    type: "none"
    # type: "date"
    # direction: "from"
    # date: "2025-09-01T00:00:00Z"

  # --- Moduły w sekcji (kolejność ma znaczenie) ---
  modules:
    - type: "label"
      file: "label-01.md"
      position: 1

    - type: "page"
      file: "page-01-czym-jest-prawda.md"
      position: 2

    - type: "page"
      file: "page-02-prawo-naturalne.md"
      position: 3

    - type: "url"
      file: "url-01-zrodla.yaml"
      position: 4

    - type: "file"
      file: "file-01-dokument.pdf"
      position: 5

    - type: "folder"
      directory: "folder-01-materialy/"
      position: 6

    - type: "quiz"
      directory: "quiz-01/"
      position: 7

    - type: "lesson"
      directory: "lesson-01/"
      position: 8

    - type: "assignment"
      directory: "assignment-01/"
      position: 9

    - type: "forum"
      directory: "forum-01/"
      position: 10

  # --- Ukończenie sekcji ---
  completion:
    enabled: true
    criteria:
      - type: "all_activities"


---

<a id="settings-yaml"></a>
## 3. Ustawienia zaawansowane – `settings.yaml`

```yaml
# ============================================================
# Zaawansowane ustawienia kursu
# Plik: courses/01-prawda-i-natura/settings.yaml
# ============================================================

settings:
  roles:
    - name: "Nauczyciel"
      type: "editingteacher"
      users: []
    - name: "Asystent"
      type: "teacher"
      users: []

  groups:
    - name: "Grupa A"
      description: "Grupa poranna"
      grouping: "Grupa główna"
    - name: "Grupa B"
      description: "Grupa wieczorowa"
      grouping: "Grupa główna"

  filters:
    - name: "tex"
      state: "on"
    - name: "mediaplugin"
      state: "on"
    - name: "glossary"
      state: "off"

  blocks:
    - name: "navigation"
      region: "side-pre"
    - name: "completion"
      region: "side-post"
    - name: "news_items"
      region: "side-post"

  access_restrictions:
    enabled: false


---

<a id="page-md"></a>
## 4. Treści stron w Markdown – `page-NN-tytul.md`


<!--
Plik: page-01-czym-jest-prawda.md
Typ modułu: page
Konwersja: Markdown → HTML → Moodle Page Module
-->

# Czym jest Prawda?

## Definicja klasyczna

Prawda, w klasycznym ujęciu filozoficznym, jest **zgodnością umysłu
z rzeczywistością** (*adaequatio intellectus et rei*). Oznacza to,
że poznanie jest prawdziwe wtedy, gdy odpowiada temu, co istnieje
obiektywnie.

## Wymiar osobowy prawdy

W tradycji chrześcijańskiej prawda nie jest jedynie abstrakcyjną
kategorią logiczną. Ma wymiar **osobowy** – jest nią sam Chrystus:

> „Ja jestem drogą i prawdą, i życiem." (J 14, 6)

## Prawda a wolność

Prawda i wolność są nierozerwalnie związane. Poznawanie prawdy
nie ogranicza człowieka, lecz go wyzwala:

![Diagram: Prawda → Wolność](../../media/images/diagram-prawda-wolnosc.png)

## Podsumowanie

- Prawda jest obiektywna i niezależna od opinii
- Prawda jest dostępna rozumowi ludzkiemu
- Prawda ma wymiar osobowy i relacyjny
- Prawda wyzwala, nie zniewala

## Pytania do refleksji

1. Czy w Twoim życiu codziennym kierujesz się prawdą obiektywną
   czy subiektywnymi odczuciami?
2. Jakie konsekwencje ma odrzucenie prawdy obiektywnej dla
   relacji międzyludzkich?

---

**Źródła:**
- Katechizm Kościoła Katolickiego, §§ 2465-2470
- Jan Paweł II, *Veritatis Splendor*, §§ 26-35


---

<a id="label"></a>
## 5. Etykieta – `label-01.md`


<!--
Plik: label-01.md
Typ modułu: label
Konwersja: Markdown → HTML (bez nagłówka strony)
Uwaga: Etykiety są wyświetlane bezpośrednio na stronie kursu
-->

<div style="text-align: center; padding: 20px; background: #f5f5f5;
            border-radius: 8px; margin: 10px 0;">

## 📚 Sekcja 1: Wprowadzenie

*W tej sekcji poznasz fundamenty naszego kursu.*

**Czas nauki:** ~2 godziny | **Modułów:** 8

</div>


---

<a id="url-yaml"></a>
## 6. Zasób URL – `url-01-zrodla.yaml`

```yaml
# Plik: url-01-zrodla.yaml
# Typ modułu: url

url:
  name: "Źródła i materiały uzupełniające"
  description: |
    Zbiór linków do dokumentów i materiałów uzupełniających
    treści pierwszej sekcji kursu.
  url: "https://www.vatican.va/archive/ccc/index.htm"
  display: "newwindow"
  popup_width: 800
  popup_height: 600
  completion:
    enabled: true
    type: "view"


---

<a id="assignment"></a>
## 7. Zadanie – `assignment.yaml`

```yaml
# Plik: assignment-01/assignment.yaml
# Typ modułu: assign

assignment:
  name: "Esej: Prawda w moim życiu"
  intro: |
    Napisz esej (500-800 słów) na temat roli prawdy
    w Twoim codziennym życiu.

    **Wymagania:**
    - Odwołanie do minimum jednego dokumentu Kościoła
    - Własne przemyślenia i przykłady
    - Poprawność językowa i logiczna
  intro_format: "html"
  intro_file: "instructions.md"

  submissiontypes:
    - "onlinetext"
    - "file"
  maxfiles: 1
  maxsubmissionsizebytes: 10485760
  filetypes:
    - "docx"
    - "pdf"
    - "odt"

  allowsubmissionsfromdate: "2025-09-08T00:00:00Z"
  duedate: "2025-09-15T23:59:59Z"
  cutoffdate: "2025-09-22T23:59:59Z"
  alwaysshowdescription: true

  grade:
    type: "point"
    value: 100
    passmark: 60

  rubric:
    enabled: true
    file: "rubric.yaml"

  teamsubmission: false
  requireallteammemberssubmit: false
  submissiondrafts: true
  requiresubmissionstatement: true
  preventsubmissionnotingroup: false

  sendnotifications: true
  sendlatenotifications: true
  sendstudentnotifications: true

  completion:
    enabled: true
    type: "submit"


---

<a id="lesson"></a>
## 8. Lekcja rozgałęziona – `lesson.yaml`

```yaml
# Plik: lesson-01/lesson.yaml
# Typ modułu: lesson

lesson:
  name: "Droga do Prawdy – Lekcja interaktywna"
  intro: |
    Interaktywna lekcja prowadząca przez podstawowe pojęcia
    związane z prawdą. Twoje wybory wpływają na przebieg lekcji.
  intro_format: "html"

  practice: false
  modattempts: 2
  usepassword: false
  password: ""

  grade:
    type: "point"
    value: 100
  customscoring: true
  retakesallowed: true
  handlingofretakes: "average"

  slideshow: false
  displayleft: true
  displayleftif: 0
  progressbar: true
  ongoing: true
  displayreview: false

  maxtime: 1800
  maxpages: 0

  pages:
    # === STRONA 1: Strona treści ===
    - id: "page-01"
      type: "content"
      title: "Czym jest prawda?"
      content_file: "pages/01-start.md"
      jumps:
        - label: "Kontynuuj"
          target: "page-02"

    # === STRONA 2: Strona treści ===
    - id: "page-02"
      type: "content"
      title: "Prawda obiektywna i subiektywna"
      content_file: "pages/02-rozwinięcie.md"
      jumps:
        - label: "Przejdź do pytania"
          target: "question-01"

    # === STRONA 3: Pytanie (rozgałęzienie) ===
    - id: "question-01"
      type: "question"
      qtype: "multichoice"
      title: "Sprawdź swoją wiedzę"
      questiontext: "Czym jest prawda obiektywna?"
      answers:
        - text: "Istnieje niezależnie od ludzkich opinii"
          fraction: 100
          jump: "page-03a"
          feedback: "Poprawnie! Przejdźmy dalej."
        - text: "Jest ustalana przez większość"
          fraction: 0
          jump: "page-03b"
          feedback: "Niepoprawnie. Prawda nie zależy od głosowania."
        - text: "Każdy ma swoją prawdę"
          fraction: 0
          jump: "page-03b"
          feedback: "To relatywizm, nie prawda obiektywna."

    # === STRONA 4a: Gałąź A (poprawna odpowiedź) ===
    - id: "page-03a"
      type: "content"
      title: "Prawda obiektywna – pogłębienie"
      content_file: "pages/03-branch-a.md"
      jumps:
        - label: "Kontynuuj"
          target: "page-04"

    # === STRONA 4b: Gałąź B (błędna odpowiedź) ===
    - id: "page-03b"
      type: "content"
      title: "Wyjaśnienie: Dlaczego prawda jest obiektywna?"
      content_file: "pages/03-branch-b.md"
      jumps:
        - label: "Wróć do pytania"
          target: "question-01"
        - label: "Kontynuuj mimo wszystko"
          target: "page-04"

    # === STRONA 5: Podsumowanie ===
    - id: "page-04"
      type: "content"
      title: "Podsumowanie lekcji"
      content_file: "pages/05-zakończenie.md"
      jumps:
        - label: "Zakończ lekcję"
          target: "endoflesson"


---

<a id="forum"></a>
## 9. Forum dyskusyjne – `forum.yaml`

```yaml
# Plik: forum-01/forum.yaml
# Typ modułu: forum

forum:
  name: "Dyskusja: Prawda w życiu codziennym"
  intro: |
    Podziel się swoimi przemyśleniami na temat roli prawdy
    w życiu codziennym. Odpowiedz na pytanie i skomentuj
    wypowiedzi minimum dwóch innych uczestników.
  intro_format: "html"

  type: "general"
  forcesubscribe: 0
  trackingtype: 1
  displaymode: 1
  maxattachments: 3
  maxbytes: 5242880

  assessed: true
  scale: 100
  assesstimestart: null
  assesstimefinish: null
  assessthreshold: null

  blockperiod: 0
  blockafter: 0

  completion:
    enabled: true
    type: "posts"
    posts: 1
    discussions: 1
    replies: 2

  first_post:
    subject: "Zaproszenie do dyskusji"
    message_file: "first-post.md"
    message_format: "html"
    created: "2025-09-01T08:00:00Z"
    mailnow: true


---

<a id="glossary"></a>
## 10. Słownik – `glossary.yaml` i `entries.yaml`

```yaml
# Plik: glossary-01/glossary.yaml
# Typ modułu: glossary

glossary:
  name: "Słownik pojęć: Prawda i Natura"
  intro: |
    Słownik kluczowych pojęć używanych w kursie.
  intro_format: "html"

  globalglossary: false
  main: true
  entbypage: 10
  displayformat: "dictionary"
  mainglossary: true
  allowspecialall: true
  allowcomments: true
  allowprint: true

  defaultapproval: 1

  categories:
    - name: "Filozofia"
      usedynalink: true
    - name: "Teologia"
      usedynalink: true
    - name: "Prawo"
      usedynalink: true

  completion:
    enabled: true
    type: "entries"
    entries: 3


```yaml
# Plik: glossary-01/entries.yaml

glossary_entries:
  - concept: "Prawda"
    definition: |
      Zgodność umysłu z rzeczywistością (*adaequatio intellectus et rei*).
      W tradycji chrześcijańskiej prawda ma wymiar osobowy – jest nią
      sam Chrystus (J 14, 6).
    definition_format: "html"
    categories:
      - "Filozofia"
      - "Teologia"
    aliases:
      - "Veritas"
      - "Aletheia"
    usedynalink: true
    casesensitive: false
    fullmatch: true

  - concept: "Prawo naturalne"
    definition: |
      Zespół norm moralnych wpisanych w naturę człowieka, dostępnych
      poznaniu rozumowemu. Stanowi fundament praw człowieka i
      porządku społecznego.
    definition_format: "html"
    categories:
      - "Filozofia"
      - "Prawo"
    aliases:
      - "Lex naturalis"
    usedynalink: true

  - concept: "Godność człowieka"
    definition: |
      Przyrodzona i niezbywalna wartość każdego człowieka,
      wynikająca z faktu stworzenia na obraz i podobieństwo Boże
      (Rdz 1, 26-27).
    definition_format: "html"
    categories:
      - "Teologia"
      - "Filozofia"
    aliases:
      - "Dignitas humana"
    usedynalink: true


---

<a id="book"></a>
## 11. Książka wielostronicowa – `book.yaml`

```yaml
# Plik: book-01/book.yaml
# Typ modułu: book

book:
  name: "Podręcznik: Prawda i Natura"
  intro: |
    Kompletny podręcznik kursu w formie wielostronicowej książki.
  intro_format: "html"

  numbering: 1
  customtitles: 0
  revision: 1

  chapters:
    - title: "Rozdział 1: Czym jest prawda?"
      subchapter: false
      content_file: "chapters/01-chapter.md"
      hidden: false

      subchapters:
        - title: "1.1 Definicja klasyczna"
          content_file: "chapters/01-01-subchapter.md"
          hidden: false
        - title: "1.2 Wymiar osobowy prawdy"
          content_file: "chapters/01-02-subchapter.md"
          hidden: false

    - title: "Rozdział 2: Prawo naturalne"
      subchapter: false
      content_file: "chapters/02-chapter.md"
      hidden: false

    - title: "Rozdział 3: Godność człowieka"
      subchapter: false
      content_file: "chapters/03-chapter.md"
      hidden: false

  completion:
    enabled: true
    type: "view"


---

<a id="workshop"></a>
## 12. Warsztat – ocena wzajemna – `workshop.yaml`

```yaml
# Plik: workshop-01/workshop.yaml
# Typ modułu: workshop

workshop:
  name: "Warsztat: Analiza tekstów o prawdzie"
  intro: |
    Warsztat oceny wzajemnej. Każdy uczestnik analizuje tekst
    źródłowy i ocenia prace innych uczestników.
  intro_format: "html"

  phases:
    setup:
      title: "Faza przygotowawcza"
      start: "2025-09-01T00:00:00Z"
    submission:
      title: "Faza przesyłania prac"
      start: "2025-09-08T00:00:00Z"
      end: "2025-09-15T23:59:59Z"
    assessment:
      title: "Faza oceny wzajemnej"
      start: "2025-09-16T00:00:00Z"
      end: "2025-09-22T23:59:59Z"
    grading:
      title: "Faza oceny końcowej"
      start: "2025-09-23T00:00:00Z"

  strategy: "rubric"
  grade_submission: 100
  grade_assessment: 100
  submissiontypetext: 1
  submissiontypefile: 1

  rubric_file: "rubric.yaml"

  allocation:
    method: "random"
    numofreviews: 3


---

<a id="h5p"></a>
## 13. Treść H5P – `h5p.yaml`

```yaml
# Plik: h5p-01/h5p.yaml
# Typ modułu: h5p

h5p:
  name: "Interaktywna prezentacja: Prawda"
  intro: |
    Interaktywna prezentacja z pytaniami i elementami multimedialnymi.
  intro_format: "html"

  source:
    type: "file"
    file: "content.h5p"

  displayoptions:
    frame: true
    download: true
    embed: true
    copyright: true

  grade:
    enabled: true
    type: "point"
    value: 100
  passmark: 60

  completion:
    enabled: true
    type: "view"


---

<a id="lti"></a>
## 14. Narzędzie zewnętrzne LTI – `lti.yaml`

```yaml
# Plik: external-tool-01/lti.yaml
# Typ modułu: lti

lti:
  name: "Zewnętrzne narzędzie: Wirtualna biblioteka"
  intro: |
    Dostęp do zewnętrznej biblioteki cyfrowej z materiałami
    teologicznymi.
  intro_format: "html"

  toolurl: "https://library.example.com/lti"
  securetoolurl: "https://library.example.com/lti"
  resourcekey: "COURSE_001"
  resourcekey_secret: "${LTI_SECRET}"

  lti_version: "1.3"

  launchcontainer: 3
  iconurl: ""
  secureiconurl: ""

  grade:
    enabled: false
    type: "none"

  completion:
    enabled: true
    type: "view"


---

<a id="media"></a>
## 15. Zasoby multimedialne

### 15.1. Struktura katalogu `media/`

```text
media/
├── images/
│   ├── logo.png
│   ├── course-hero.jpg
│   ├── diagram-01.svg
│   ├── photo-01.jpg
│   ├── icon-truth.png
│   └── infographic-01.webp
│
├── videos/
│   ├── intro.mp4
│   ├── lecture-01.webm
│   ├── subtitle-01.vtt
│   └── transcript-01.txt
│
├── audio/
│   ├── podcast-01.mp3
│   ├── meditation-01.ogg
│   └── transcript-01.txt
│
├── documents/
│   ├── syllabus.pdf
│   ├── reading-list.pdf
│   ├── worksheet-01.pdf
│   ├── source-text.docx
│   └── presentation.pptx
│
└── interactive/
    ├── timeline-01.h5p
    ├── quiz-interactive.h5p
    └── geogebra-01.ggb


### 15.2. Specyfikacja formatów multimedialnych

| Typ | Format | Zalecane parametry | Rozszerzenie |
|---|---|---|---|
| Logo | PNG | 300x300px, przezroczystość, < 50 KB | `.png` |
| Obraz główny | JPG | 1200x630px, 85% jakość, < 200 KB | `.jpg` |
| Diagram | SVG | Wektorowy, skalowalny, < 100 KB | `.svg` |
| Zdjęcie | JPG/WebP | Max 1920px szerokość, < 500 KB | `.jpg`, `.webp` |
| Ikona | PNG/SVG | 64x64px lub 128x128px | `.png`, `.svg` |
| Wideo | MP4 (H.264) | 1920x1080, 30fps, AAC audio | `.mp4` |
| Wideo (alt) | WebM (VP9) | 1920x1080, 30fps, Opus audio | `.webm` |
| Napisy | WebVTT | UTF-8, znaczniki czasowe | `.vtt` |
| Audio | MP3 | 128-192 kbps, 44.1 kHz | `.mp3` |
| Audio (alt) | OGG | Vorbis, 128 kbps | `.ogg` |
| Dokument | PDF | Tekst warstwowy (nie skan), < 10 MB | `.pdf` |
| Prezentacja | PPTX/ODP | < 50 MB | `.pptx`, `.odp` |
| H5P | H5P | Zgodny z bibliotekami Moodle | `.h5p` |

### 15.3. Manifest multimediów – `media-manifest.yaml`

```yaml
# Plik: media/media-manifest.yaml

media_manifest:
  course: "PRAWDA_NATURA_01"
  version: "1.0.0"

  resources:
    - id: "img-001"
      type: "image"
      file: "images/diagram-prawda.png"
      alt_text: "Diagram przedstawiający relację prawdy i wolności"
      caption: "Relacja prawdy i wolności według nauczania KKK"
      license: "CC BY-SA 4.0"
      author: "Zespół Misyjny"
      width: 800
      height: 600
      file_size: "125KB"
      accessibility:
        has_alt_text: true
        has_long_description: true

    - id: "vid-001"
      type: "video"
      file: "videos/intro.mp4"
      title: "Wprowadzenie do kursu"
      description: "Wideo wprowadzające w tematykę kursu"
      duration: "05:30"
      subtitles:
        - lang: "pl"
          file: "videos/subtitle-01.vtt"
      transcript: "videos/transcript-01.txt"
      license: "CC BY-SA 4.0"
      author: "Zespół Misyjny"
      accessibility:
        has_subtitles: true
        has_transcript: true
        has_audio_description: false

    - id: "aud-001"
      type: "audio"
      file: "audio/podcast-01.mp3"
      title: "Podcast: Czym jest prawda?"
      duration: "15:00"
      transcript: "audio/transcript-01.txt"
      license: "CC BY-SA 4.0"



---


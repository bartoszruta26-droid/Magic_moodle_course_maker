

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
16. [Pakiet SCORM](#scorm)
17. [Common Cartridge (IMS CC)](#imscc)
18. [Dodatkowe aktywności Moodle](#additional-activities)

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

<a id="scorm"></a>
## 16. Pakiet SCORM – `scorm.yaml`

SCORM (Sharable Content Object Reference Model) to standard pakietów e-learningowych z możliwością śledzenia postępów użytkownika. Moodle obsługuje SCORM 1.2 i SCORM 2004.

### 16.1. Struktura katalogu SCORM

```
scorm-01/
├── scorm.yaml          # Metadane pakietu
├── package.zip         # Plik ZIP z zawartością SCORM
└── media/              # Dodatkowe zasoby (opcjonalnie)
    ├── image.png
    └── video.mp4
```

### 16.2. Plik `scorm.yaml` – metadane pakietu SCORM

```yaml
# ============================================================
# Metadane pakietu SCORM
# Plik: scorm-01/scorm.yaml
# Format: YAML 1.2
# Kodowanie: UTF-8
# ============================================================

scorm:
  # --- Identyfikacja ---
  name: "Interaktywny moduł: Prawda i Wolność"
  intro: |
    Interaktywny pakiet e-learningowy zawierający prezentacje,
    quizy i symulacje dotyczące relacji między prawdą a wolnością.
  intro_format: "html"

  # --- Wersja SCORM ---
  version: "1.2"                     # 1.2 | 2004_3ed | 2004_4ed
  
  # --- Wyświetlanie ---
  display: "embed"                   # embed | new_window | popup
  width: 800
  height: 600
  auto_continue: true                # Automatyczna kontynuacja
  force_complete: true               # Wymuś ukończenie
  force_new_window: false
  
  # --- Ocenianie ---
  grade_method: "highest"            # highest | lowest | average | first | last
  max_grade: 100
  what_grade: "completed"            # completed | passed | completed_or_passed
  
  # --- Śledzenie ---
  tracking:
    track_views: true
    track_score: true
    track_status: true
    track_time: true
  
  # --- Dostępność ---
  available_from: "2025-09-01T00:00:00Z"
  available_until: "2025-12-31T23:59:59Z"
  
  # --- Ukończenie ---
  completion_enabled: true
  completion_view: true              # Ukończ po wyświetleniu
  completion_score: 70               # Minimalny wynik do ukończenia
  completion_status: "completed"     # Status wymagany do ukończenia
  
  # --- Plik pakietu ---
  package_file: "package.zip"
  package_size: "2.5MB"
  package_hash: "sha256:abc123..."   # Hash SHA256 dla integralności
  
  # --- Zawartość pakietu ---
  contents:
    - type: "sco"                    # SCO = Sharable Content Object
      identifier: "SCO_001"
      title: "Wprowadzenie do prawa naturalnego"
      file: "intro/index.html"
      launch: "intro/index.html"
    
    - type: "sco"
      identifier: "SCO_002"
      title: "Quiz: Prawda i Wolność"
      file: "quiz/index.html"
      launch: "quiz/index.html"
    
    - type: "asset"                  # Asset = zasób bez śledzenia
      identifier: "ASSET_001"
      title: "Diagram relacji"
      file: "media/diagram.png"
  
  # --- Manifest IMS ---
  manifest:
    schema_version: "1.2"
    organization: "Zespół Misyjny"
    organization_id: "MISSION_TEAM_001"
```

### 16.3. Struktura pliku `package.zip` (SCORM 1.2)

Plik ZIP musi zawierać:

```
package.zip
├── imsmanifest.xml          # Manifest pakietu (wymagany)
├── intro/
│   ├── index.html           # Strona startowa SCO
│   ├── styles.css
│   └── script.js
├── quiz/
│   ├── index.html
│   └── questions.js
└── media/
    ├── diagram.png
    └── video.mp4
```

### 16.4. Przykład `imsmanifest.xml` (SCORM 1.2)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
          xmlns:imsmd="http://www.imsglobal.org/xsd/imsmd_rootv1p2p1"
          identifier="MANIFEST_001">
  
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
    <imsmd:lom>
      <imsmd:general>
        <imsmd:title>
          <imsmd:string>Prawda i Wolność - Moduł Interaktywny</imsmd:string>
        </imsmd:title>
        <imsmd:description>
          <imsmd:string>Interaktywny moduł e-learningowy dotyczący relacji między prawdą a wolnością.</imsmd:string>
        </imsmd:description>
      </imsmd:general>
    </imsmd:lom>
  </metadata>
  
  <organizations default="ORG_001">
    <organization identifier="ORG_001">
      <title>Prawda i Wolność</title>
      <item identifier="ITEM_001" identifierref="SCO_001">
        <title>Wprowadzenie</title>
      </item>
      <item identifier="ITEM_002" identifierref="SCO_002">
        <title>Quiz</title>
      </item>
    </organization>
  </organizations>
  
  <resources>
    <resource identifier="SCO_001" type="webcontent" adlcp:scormtype="sco" href="intro/index.html">
      <file href="intro/index.html"/>
      <file href="intro/styles.css"/>
      <file href="intro/script.js"/>
    </resource>
    <resource identifier="SCO_002" type="webcontent" adlcp:scormtype="sco" href="quiz/index.html">
      <file href="quiz/index.html"/>
      <file href="quiz/questions.js"/>
    </resource>
  </resources>
</manifest>
```

### 16.5. Skrypt budujący pakiet SCORM (`build_scorm.py`)

```python
#!/usr/bin/env python3
"""
Budowanie pakietu SCORM 1.2 z plików źródłowych
Użycie: python build_scorm.py scorm-01/
"""

import os
import sys
import yaml
import zipfile
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def build_manifest(scorm_data):
    """Buduje imsmanifest.xml z danych YAML"""
    manifest = Element('manifest', {
        'xmlns': 'http://www.imsproject.org/xsd/imscp_rootv1p1p2',
        'xmlns:adlcp': 'http://www.adlnet.org/xsd/adlcp_rootv1p2',
        'identifier': 'MANIFEST_001'
    })
    
    # Metadata
    metadata = SubElement(manifest, 'metadata')
    SubElement(metadata, 'schema').text = 'ADL SCORM'
    SubElement(metadata, 'schemaversion').text = scorm_data['scorm']['version']
    
    # Organizations
    orgs = SubElement(manifest, 'organizations', {'default': 'ORG_001'})
    org = SubElement(orgs, 'organization', {'identifier': 'ORG_001'})
    SubElement(org, 'title').text = scorm_data['scorm']['name']
    
    for content in scorm_data['scorm']['contents']:
        if content['type'] == 'sco':
            item = SubElement(org, 'item', {
                'identifier': content['identifier'],
                'identifierref': content['identifier']
            })
            SubElement(item, 'title').text = content['title']
    
    # Resources
    resources = SubElement(manifest, 'resources')
    for content in scorm_data['scorm']['contents']:
        if content['type'] == 'sco':
            res = SubElement(resources, 'resource', {
                'identifier': content['identifier'],
                'type': 'webcontent',
                'adlcp:scormtype': 'sco',
                'href': content['launch']
            })
            SubElement(res, 'file', {'href': content['launch']})
    
    return parseString(tostring(manifest, encoding='unicode')).toprettyxml()

def create_scorm_package(source_dir, output_zip):
    """Tworzy pakiet ZIP SCORM"""
    source = Path(source_dir)
    
    # Load metadata
    scorm_data = load_yaml(source / 'scorm.yaml')
    
    # Build manifest
    manifest_xml = build_manifest(scorm_data)
    
    # Create ZIP
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add manifest
        zipf.writestr('imsmanifest.xml', manifest_xml)
        
        # Add content files
        for content in scorm_data['scorm']['contents']:
            if 'file' in content:
                file_path = source / content['file']
                if file_path.exists():
                    zipf.write(file_path, content['file'])
        
        # Add additional files from directories
        for dir_path in source.iterdir():
            if dir_path.is_dir() and dir_path.name not in ['__pycache__']:
                for file_path in dir_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source)
                        zipf.write(file_path, str(arcname))
    
    print(f"Pakiet SCORM utworzony: {output_zip}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Użycie: python build_scorm.py <source_dir>")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    output_zip = f"{source_dir}/package.zip"
    create_scorm_package(source_dir, output_zip)
```

---

<a id="imscc"></a>
## 17. Common Cartridge (IMS CC)

Common Cartridge to standard IMS Global Learning Consortium umożliwiający przenośność treści edukacyjnych między różnymi platformami LMS.

### 17.1. Struktura katalogu IMS CC

```
imscc-01/
├── imscc.yaml              # Metadane pakietu
├── package.imscc           # Plik ZIP z rozszerzeniem .imscc
└── resources/
    ├── content/
    │   ├── index.html
    │   └── styles.css
    └── assessments/
        └── quiz.xml
```

### 17.2. Plik `imscc.yaml` – metadane pakietu

```yaml
# ============================================================
# Metadane pakietu Common Cartridge
# Plik: imscc-01/imscc.yaml
# Format: YAML 1.2
# Kodowanie: UTF-8
# ============================================================

imscc:
  # --- Identyfikacja ---
  title: "Prawda i Natura - Moduł 1"
  description: |
    Pierwszy moduł kursu antropologii chrześcijańskiej
    obejmujący wprowadzenie do prawa naturalnego.
  
  # --- Wersja standardu ---
  version: "1.1.0"             # 1.0.0 | 1.1.0 | 1.2.0 | 1.3.0
  
  # --- Autorzy i licencja ---
  authors:
    - name: "Zespół Misyjny"
      email: "team@example.org"
  license: "CC BY-SA 4.0"
  
  # --- Zawartość ---
  content_types:
    - "web_content"
    - "assessment"
    - "discussion"
  
  # --- Oceny ---
  grading:
    enabled: true
    scale: "percentage"
    passing_score: 70
  
  # --- Pliki ---
  package_file: "package.imscc"
  manifest_file: "imsmanifest.xml"
```

### 17.3. Porównanie formatów pakietów

| Cecha | SCORM 1.2 | SCORM 2004 | Common Cartridge | Moodle Backup (.mbz) |
|-------|-----------|------------|------------------|---------------------|
| Śledzenie postępów | Tak | Tak (rozszerzone) | Ograniczone | Pełne |
| Przenośność | Wysoka | Wysoka | Bardzo wysoka | Tylko Moodle |
| Wsparcie Moodle | Tak | Tak | Tak | Natywne |
| Złożoność | Średnia | Wysoka | Wysoka | Średnia |
| Quizy | Tak | Tak | Tak | Tak |
| Forum dyskusyjne | Nie | Nie | Tak | Tak |
| Wersjonowanie | Nie | Nie | Tak | Nie |

---

<a id="additional-activities"></a>
## 18. Dodatkowe aktywności Moodle

Oprócz opisanych powyżej, Moodle obsługuje dodatkowe typy aktywności:

### 18.1. Ankieta (Feedback) – `feedback.yaml`

```yaml
# Plik: feedback-01/feedback.yaml
feedback:
  name: "Ankieta ewaluacyjna kursu"
  intro: "Prosimy o wypełnienie ankiety oceniającej kurs."
  intro_format: "html"
  
  # --- Ustawienia ---
  anonymous: "full"              # full | partial | none
  submit_multiple: false
  submit_numbers: true
  show_analysis: "student"       # student | teacher | none
  
  # --- Pytania ---
  questions:
    - type: "label"
      label: "Oceń następujące aspekty kursu:"
    
    - type: "multichoicerated"
      label: "Jak oceniasz jakość materiałów?"
      options:
        - "Bardzo dobrze"
        - "Dobrze"
        - "Średnio"
        - "Źle"
      required: true
    
    - type: "textarea"
      label: "Twoje sugestie:"
      required: false
```

### 18.2. Baza danych – `database.yaml`

```yaml
# Plik: database-01/database.yaml
database:
  name: "Baza zasobów edukacyjnych"
  intro: "Wspólna baza materiałów dydaktycznych."
  intro_format: "html"
  
  # --- Pola ---
  fields:
    - name: "title"
      type: "text"
      required: true
    
    - name: "description"
      type: "textarea"
      required: true
    
    - name: "file"
      type: "file"
      required: false
    
    - name: "category"
      type: "menu"
      options:
        - "Artykuły"
        - "Wideo"
        - "Prezentacje"
  
  # --- Szablon ---
  template_file: "template.html"
  css_file: "styles.css"
  js_file: "script.js"
  
  # --- Dostęp ---
  entries_required: 1
  comments_allowed: true
  rating_enabled: true
  rating_scale: "scale_1_5"
```

### 18.3. Głosowanie (Choice) – `choice.yaml`

```yaml
# Plik: choice-01/choice.yaml
choice:
  name: "Wybór terminu konsultacji"
  intro: "Wybierz dogodny termin spotkania."
  intro_format: "html"
  
  # --- Opcje ---
  options:
    - "Poniedziałek 15:00-16:00"
    - "Środa 10:00-11:00"
    - "Piątek 14:00-15:00"
  
  # --- Ustawienia ---
  allow_multiple: false
  limit_answers: true
  limits:
    - option: 0
      limit: 10
    - option: 1
      limit: 15
    - option: 2
      limit: 8
  
  # --- Czas ---
  timeopen: "2025-09-01T00:00:00Z"
  timeclose: "2025-09-15T23:59:59Z"
  
  # --- Wyniki ---
  show_results: "after_answer"    # after_answer | after_close | never
  privacy: "anonymous"            # anonymous | names
```

### 18.4. Warsztat (Workshop) – rozszerzenie `workshop.yaml`

```yaml
# Plik: workshop-01/workshop.yaml (rozszerzenie)
workshop:
  name: "Warsztat: Esej o godności"
  
  # --- Fazy ---
  phases:
    setup:
      submission_enabled: true
      assessment_enabled: false
    
    submission:
      submission_enabled: true
      assessment_enabled: false
      deadline: "2025-10-15T23:59:59Z"
    
    assessment:
      submission_enabled: false
      assessment_enabled: true
      deadline: "2025-10-30T23:59:59Z"
    
    grading_evaluation:
      submission_enabled: false
      assessment_enabled: false
    
    grading_complete:
      grades_released: true
  
  # --- Strategia oceny ---
  strategy: "rubric"
  rubric:
    criteria:
      - id: 1
        description: "Trafność argumentacji"
        levels:
          - score: 10
            description: "Argumentacja bardzo trafna"
          - score: 7
            description: "Argumentacja trafna"
          - score: 4
            description: "Argumentacja częściowo trafna"
          - score: 1
            description: "Argumentacja nietrafna"
      
      - id: 2
        description: "Struktura eseju"
        levels:
          - score: 5
            description: "Struktura bardzo dobra"
          - score: 3
            description: "Struktura dobra"
          - score: 1
            description: "Struktura słaba"
  
  # --- Przydział recenzji ---
  allocation:
    mode: "random"               # random | manual | scheduled
    reviews_per_submission: 3
    reviews_per_reviewer: 3
```

---


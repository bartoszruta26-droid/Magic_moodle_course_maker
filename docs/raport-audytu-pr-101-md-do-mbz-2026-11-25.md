# Kontynuacja audytu konwersji Markdown → Moodle MBZ — PR #101

**Data kontroli:** 2026-11-25  
**Repozytorium:** `bartoszruta26-droid/Magic_moodle_course_maker`  
**Gałąź bazowa:** `main`  
**Badana gałąź:** `course-conversion-to-moodle-bb3bf`  
**Commit badanego PR:** `20b95ac840e51fab10b436618ff226709a8a7180`  
**PR:** [#101](https://github.com/bartoszruta26-droid/Magic_moodle_course_maker/pull/101)  
**Status:** audyt statyczny rozszerzony; PR nie jest gotowy do scalenia.

## 1. Zakres i metoda

Kontynuowano audyt zapisany w:
- `docs/audyt-i-plan-konwersji-md-do-mbz.md`;
- `docs/raport-inwentaryzacji-etap-0-md-mbz.md`.

Sprawdzono aktualny stan PR #101, pełną treść dodawanego skryptu `scripts/md_to_moodle_activity.py`, listę zmienionych plików, statusy GitHub Actions powiązane z commitem PR oraz zgodność deklarowanego działania z loaderem i istniejącymi modułami rdzenia.

PR #101 zmienia tylko jeden plik: `scripts/md_to_moodle_activity.py` (614 linii). PR pozostaje otwarty i niescalony. Nie wykonano importu wygenerowanego MBZ na instancji Moodle.

## 2. Status CI — interpretacja

Dla commita `20b95ac840e51fab10b436618ff226709a8a7180` GitHub Actions zwrócił zakończone powodzeniem następujące przebiegi:
- Validate GIFT question bank;
- Lint YAML files;
- Validate course repository;
- Core tests;
- Build Python package.

To są pozytywne wyniki istniejących workflow, ale nie dowodzą poprawności nowego skryptu eksportu MBZ. W szczególności:
- PR zmienia wyłącznie skrypt, a workflow GIFT/YAML/repozytorium nie stanowią testów zachowania tego skryptu;
- nie znaleziono uruchomionego testu jednostkowego `scripts/md_to_moodle_activity.py`;
- nie ma potwierdzonego testu struktury MBZ ani przywrócenia kursu na Moodle 4.1;
- istniejący workflow `moodle-integration.yml` uruchamia testy wtyczki `local_magicmoodle`, a nie import wygenerowanego backupu.

Wniosek: status CI „success” nie jest równoznaczny z akceptacją PR ani potwierdzeniem poprawności MBZ.

## 3. Błędy blokujące w skrypcie PR #101

### B1. Serializacja XML może zakończyć eksport wyjątkiem

W `moodle_xml_export()` tworzony jest element:
```python
ET.SubElement(root, "info", component="core_course", subplugin=None)
```

Atrybut `subplugin=None` jest przekazywany do `xml.etree.ElementTree`. Podczas serializacji dokumentu `ET.tostring(...)` wartości atrybutów muszą być tekstowe; wartość `None` powoduje `TypeError: cannot serialize None (type NoneType)`. Potwierdzono to uruchomieniem minimalnego reproduktora z dokładnie takim wywołaniem ElementTree. Nie uruchomiono jeszcze całego skryptu na rzeczywistym kursie. Należy usunąć ten atrybut albo nadać mu poprawną wartość zgodną ze schematem Moodle. Dodać test regresyjny obejmujący faktyczną serializację.

### B2. Archiwum ZIP nie ma struktury kopii zapasowej Moodle

Skrypt zapisuje tylko dwa wpisy w katalogu głównym ZIP:
- `moodle_backup.xml`;
- `questions.xml`.

Nie tworzy kompletnego drzewa backupu kursu, w tym wymaganych katalogów i plików kursu/aktywności, manifestu plików, danych aktywności i powiązań z plikami. Samo nazwanie ZIP rozszerzeniem `.mbz` nie czyni go kopią Moodle.

### B3. Dokument XML nie odpowiada strukturze backupu Moodle

Skrypt buduje uproszczony dokument z korzeniem `moodle`, elementami `info/details` i własnym układem `section/module/content`. To nie jest potwierdzony schemat pliku `moodle_backup.xml` Moodle 4.1. Nie ma walidacji względem rzeczywistego formatu backupu ani zgodności z importerem Moodle.

### B4. Dane modułów Book i Quiz są niekompletne

Ręcznie tworzone elementy `module`, `instance`, `content`, `book` i `quiz` nie są pełnymi danymi wymaganymi do odtworzenia instancji aktywności. Przykładowo identyfikator instancji jest utożsamiany z identyfikatorem modułu kursowego, zawartość rozdziałów jest umieszczana w autorskim układzie `chunks`, a dane pytań są dodawane jako niezależny plik w katalogu głównym ZIP. Nie ma spójnego mapowania course module → instance → activity data.

### B5. Pytania Short Answer otrzymują nieprawdziwy klucz odpowiedzi

Dla każdego pytania skrypt tworzy odpowiedź przez usunięcie znaku zapytania i zmianę pierwszej litery pytania. Przykład: pytanie „Jaką funkcję pełni nerw błędny?” otrzymuje jako odpowiedź „jaką funkcję pełni nerw błędny”. Jest to błąd merytoryczny, który tworzy fałszywe klucze odpowiedzi. Nie wolno automatycznie przekształcać pytań w pytania z odpowiedzią, jeżeli źródło nie zawiera jawnego klucza.

### B6. Pytania P/F są generowane z relacji nagłówków, nie z wiedzy

Twierdzenia „podrozdział należy do rozdziału” sprawdzają strukturę dokumentu, a nie wiedzę kursanta. Wariant fałszywy jest konstruowany przez przypisanie podrozdziału do poprzedniego rozdziału. Nie jest to wiarygodne pytanie dydaktyczne i może wprowadzać nieprawidłową ocenę. Należy usunąć tę automatyczną generację; pytania P/F mogą powstawać wyłącznie z jawnych danych pytania i odpowiedzi.

### B7. Renderer Markdown jest drugim, niezgodnym konwerterem

Funkcja `md_to_html()` jest ręcznym parserem opartym na wyrażeniach regularnych. Nie zapewnia CommonMark/GFM. W szczególności:
- listy numerowane są emitowane jako akapity, nie `<ol>`;
- brak poprawnej obsługi list zagnieżdżonych;
- brak konwersji składni linków i obrazów do `<a>` i `<img>`;
- bloki kodu fenced nie są obsługiwane jako `<pre><code>`;
- nagłówki `#` i `##` są mapowane na `h2`, a `###` na `h4`, co gubi poziomy i tworzy skok semantyczny;
- cytaty są obsługiwane tylko jako pojedyncze linie zaczynające się od `> `;
- tabele są parsowane przez proste dzielenie po znaku `|`, co nie obsługuje poprawnie escapowanych separatorów ani złożonych treści;
- brak jawnej polityki sanitacji HTML.

Renderer powinien zostać zastąpiony wspólną usługą Markdown używaną również przez publikator REST i pozostałe ścieżki eksportu.

### B8. Generowanie YAML przez interpolację łańcuchów

`book.yaml`, `quiz.yaml` i `section.yaml` są składane przez konkatenację tekstu. Cudzysłowy są usuwane lub nieescapowane, a dwukropki, znaki specjalne, ukośniki i wielowierszowe nazwy mogą uszkodzić YAML. Należy użyć `yaml.safe_dump` z jawnie określonym kodowaniem i stabilnym formatowaniem, a po zapisie wczytać pliki przez ten sam loader.

### B9. Generator jest związany z jednym kursem

Gdy `course.yaml` nie istnieje, skrypt tworzy metadane na stałe dla „Badanie neurologiczne pacjenta” i `BN-NEURO-2026`. Dla innego kursu plik będzie błędny. Jeżeli `course.yaml` istnieje, skrypt go nie aktualizuje, ale nie weryfikuje też, czy wygenerowana sekcja została dodana do konfiguracji kursu. Należy przekazać metadane kursu jawnie lub odczytać istniejące i walidować zgodność.

### B10. Deklarowana idempotentność nie jest wystarczająco zabezpieczona

Skrypt nadpisuje pliki generowane, ale nie wykazuje bezpiecznego usuwania nieaktualnych plików po zmianie źródła ani kontroli kolizji nazw. Nie ma manifestu wygenerowanych ścieżek, który pozwalałby odróżnić pliki własne skryptu od ręcznie utrzymywanych. Powtórne uruchomienie może pozostawić osierocone rozdziały lub nadpisać plik o kolizyjnej nazwie.

### B11. Parser źródła ma założenia specyficzne dla jednego formatu

Rozpoznaje wyłącznie numerowane nagłówki `## N. Tytuł` oraz określone nazwy sekcji pytań (np. „Pytania kontrolne”, „Pytania sprawdzające”, „Zadania problemowe”). Nie waliduje braku tytułu H1, duplikatów numerów, pustych rozdziałów ani nieobsługiwanych układów. Słownik jest rozpoznawany przez prosty podział wiersza po `|`, bez pełnego parsera tabel Markdown.

### B12. Brak testów skryptu i ścieżki końcowej

W PR nie dodano żadnych testów. `tests/test_converters.sh` w gałęzi bazowej jest pusty (0 B). Brakuje:
- testów parsowania przykładowych plików kursów;
- testów wyjściowego HTML;
- testów poprawności YAML;
- testów GIFT z kontrolą semantyczną odpowiedzi;
- testów XML;
- testów zawartości ZIP i wymaganych wpisów;
- testu przywrócenia MBZ w czystej instancji Moodle 4.1.

## 4. Problemy spójności z istniejącym rdzeniem

1. Skrypt definiuje osobną funkcję `md_to_html()`, mimo że repozytorium ma już `magic_moodle/moodle_publish.py` z własną, również ograniczoną implementacją. Powstają dwie rozbieżne ścieżki renderowania.
2. Skrypt zapisuje strukturę Book + Quiz, ale nie przechodzi po wygenerowaniu przez `load_course()` i walidator rdzenia.
3. Zapisuje pliki `book.yaml`, `quiz.yaml`, `section.yaml` przez własne serializatory tekstowe zamiast użyć schematu i walidacji rdzenia.
4. Obsługa quizu miesza bank pytań z danymi instancji quizu. Eksport banku Moodle XML nie jest sam w sobie eksportem aktywności Quiz.
5. Publikacja przez Moodle REST, manifest JSON i backup MBZ pozostają różnymi formatami wyjściowymi i nie wolno ich utożsamiać.

## 5. Zalecane decyzje

- Nie scalać PR #101.
- Nie rozwijać ręcznego generatora MBZ z tego PR.
- Zachować użyteczne rozpoznawanie wejściowych plików i koncepcję normalizacji do katalogów kursu, ale przepisać parser i serializację na bazie wspólnego rdzenia.
- Zrezygnować z automatycznego generowania odpowiedzi i pytań P/F z nagłówków.
- Wprowadzić wspólny renderer Markdown oparty na bibliotece i testach wzorcowych.
- Dla MBZ preferować wywołanie oficjalnego mechanizmu backupu Moodle na testowej instancji (po utworzeniu kursu/aktywności przez API/wtyczkę) albo implementować pełny format tylko po oparciu go o backup wygenerowany przez wspieraną wersję Moodle.
- Dodać test E2E: wygeneruj → sprawdź archiwum → przywróć na Moodle 4.1 → sprawdź aktywności, kolejność, treści i pliki.
- Zapisywać artefakty testowe i raporty w GitHub Actions; duże MBZ publikować jako artefakty Actions lub Release, nie automatycznie w repozytorium.

## 6. Dalszy plan prac

### Etap 0A — zakończenie przeglądu PR
- [x] Ustalić stan PR #101 i badany commit.
- [x] Ustalić listę zmienionych plików.
- [x] Odczytać pełną treść skryptu.
- [x] Sprawdzić statusy workflow powiązane z commitem.
- [x] Zidentyfikować błędy blokujące na poziomie statycznym.
- [ ] Uruchomić skrypt w kontrolowanym środowisku i potwierdzić wyjątek serializacji XML.
- [ ] Uzyskać próbkę źródłowego kursu i sprawdzić wynik parsera na rzeczywistych plikach.
- [ ] Wykonać test importu na Moodle 4.1 (oczekiwany brak zgodności obecnego archiwum).

### Etap 1 — wspólny renderer Markdown
- [ ] Wybrać i dodać bibliotekę Markdown oraz wymagane rozszerzenia.
- [ ] Ustalić sanitację i obsługę surowego HTML.
- [ ] Dodać zestaw testów: nagłówki, akapity, listy numerowane i zagnieżdżone, tabele, kod, linki, obrazy, cytaty, wzory, polskie znaki.
- [ ] Przełączyć publikator REST na wspólny renderer.
- [ ] Nie usuwać starego renderer'a, dopóki testy regresji nie potwierdzą równoważności lub świadomej zmiany.

### Etap 2 — importer Markdown do modelu kursu
- [ ] Zaprojektować parser całego kursu na podstawie `course.md` i powiązanych plików MD.
- [ ] Zachować hierarchię i kolejność.
- [ ] Generować bezpieczne YAML przez serializer lub tworzyć model IR bez pośredniego YAML.
- [ ] Weryfikować wynik przez `load_course()` i walidator.
- [ ] Rozdzielić rozdziały Book od osobnych aktywności Page/Quiz/Assignment według jawnej konfiguracji.
- [ ] Nie generować odpowiedzi, których nie ma w danych źródłowych.

### Etap 3 — MBZ przez mechanizm Moodle
- [ ] Utworzyć kurs testowy i aktywności na Moodle 4.1 z użyciem obsługiwanej ścieżki API/wtyczki.
- [ ] Uruchomić oficjalny mechanizm backupu Moodle.
- [ ] Zachować przykładowy, poprawny backup jako fixture referencyjny (bez danych wrażliwych).
- [ ] Porównać strukturę i wymagane elementy backupu.
- [ ] Zaimplementować generator/orkiestrację dopiero po uzyskaniu wzorca.
- [ ] Importować wynik na czystej instancji i weryfikować kurs.

### Etap 4 — GitHub
- [ ] Dodać workflow konwersji/testu, wyzwalany zmianami w `courses/**`, `magic_moodle/**`, `scripts/**` i plikach workflow.
- [ ] Publikować raport, manifest i sumę SHA-256.
- [ ] Przechowywać MBZ jako artefakt Actions lub Release, z retencją i limitem rozmiaru.
- [ ] Nie zapisywać sekretów ani tokenów w Git.

## 7. Werdykt

**PR #101: REQUEST CHANGES / nie scalać.**

Powody blokujące: błąd serializacji XML, niezgodna i niekompletna struktura backupu, brak testu importu Moodle, generowanie fałszywych kluczy odpowiedzi oraz brak wspólnego renderera Markdown.

Pozytywne statusy pięciu workflow nie obejmują testowania nowego skryptu i nie zmieniają tego werdyktu.

Ten raport dokumentuje audyt statyczny. Nie deklaruje uruchomienia skryptu, wytworzenia prawidłowego MBZ ani udanego importu.

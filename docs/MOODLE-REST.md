# Zdalna publikacja w Moodle przez REST API

## Wymagania

1. Moodle 4.1.x (w tym 4.1.8) z włączonym protokołem REST.
2. Utworzona usługa zewnętrzna, token dla dedykowanego konta technicznego i uprawnienia do tworzenia kursów oraz aktywności.
3. Zainstalowany lokalny plugin `local_magicmoodle` z katalogu `moodle-plugin/local/magicmoodle`.
4. Dozwolone funkcje usługi:
   - `core_webservice_get_site_info`
   - `core_course_get_courses_by_field`
   - `core_course_create_courses`
   - `local_magicmoodle_update_section`
   - `local_magicmoodle_create_activity`
   - `local_magicmoodle_create_book`
   - `local_magicmoodle_create_quiz`
   - `local_magicmoodle_create_assignment`
   - `local_magicmoodle_create_resource`
   - `local_magicmoodle_create_glossary`

Konfiguracja usługi i tokenu odbywa się po stronie administratora Moodle:
**Administracja witryną → Serwer → Usługi sieciowe**. Funkcje zewnętrzne i uprawnienia konta muszą być jawnie przyznane. Plugin jest zgodny z mechanizmem External API w Moodle 4.1: klasy są ładowane z `lib/externallib.php` i używana jest globalna klasa `external_api`. W Moodle 4.2 przeniesiono te klasy do przestrzeni nazw `core_external`, dlatego kodu z nowszych przykładów nie można bezpośrednio zastosować do Moodle 4.1. Zob. [dokumentację Moodle 4.1 – Function Definitions](https://noeldemartin.github.io/moodledevdocs/docs/4.1/apis/subsystems/external/functions) oraz [zmiany w Moodle 4.2](https://noeldemartin.github.io/moodledevdocs/docs/4.2/devupdate).

## Instalacja pluginu

Skopiuj katalog `moodle-plugin/local/magicmoodle` do `<moodle>/local/magicmoodle`, a następnie zaloguj się jako administrator i przejdź do powiadomień, aby wykonać instalację. Dodaj siedem funkcji pluginu do usługi zewnętrznej. Plugin w wersji 0.1.15 udostępnia funkcje do synchronizacji Page, Label, URL, Book, Glossary, Assignment i Resource oraz tworzenia Quiz z kontrolą kontekstu i uprawnień.

## Konfiguracja klienta

Ustaw zmienne środowiskowe (nie zapisuj tokenu w repozytorium):

```bash
export MOODLE_URL="https://moodle.example.org"
export MOODLE_TOKEN="TOKEN_Z_MOODLE"
export MOODLE_CATEGORY_ID="2"
export MOODLE_VERIFY_TLS="true"
```

Połączenia HTTP są blokowane poza localhost. Nie wyłączaj weryfikacji certyfikatu TLS w środowisku produkcyjnym.

## Kontrola i publikacja

Najpierw uruchom plan bez połączenia sieciowego:

```bash
python -m magic_moodle moodle-publish courses/03-kurs-masazysta-med10 --dry-run
```

Następnie wykonaj publikację z manifestem stanu (wymagany dla Book i Glossary):

```bash
python -m magic_moodle moodle-publish courses/03-kurs-masazysta-med10 --state-file .local-state/med10-publish.json
```

Klient sprawdza istnienie kursu po `shortname` i nie tworzy duplikatu. Nowy kurs otrzymuje kategorię wskazaną przez `MOODLE_CATEGORY_ID`, format i liczbę sekcji z konfiguracji. Sekcje otrzymują nazwy z repozytorium. Wbudowany adapter publikuje Page, Label, URL, Book, Quiz, Assignment, Glossary oraz pliki jako aktywności Resource. Aktywność typu `glossary` wskazuje katalog z `glossary.yaml`, zawierającym obiekt `glossary` i listę `entries` z polami `term`, `definition` oraz opcjonalnym `format` (`html`, `markdown`, `plain`). Limit słownika wynosi 500 haseł i 5 MiB łącznej treści; powtórzone hasła są odrzucane. Wpisy są tworzone przez natywny interfejs Glossary Moodle i domyślnie zatwierdzane. Przy ponownej publikacji mapowanie `source_id` do `entryid` pozwala aktualizować istniejące hasła bez zmiany identyfikatorów. Aktywność typu `file` wskazuje pojedynczy plik binarny w repozytorium kursu; przesyłany jest on jako base64, z limitem 5 MiB. Moodle zapisuje plik przez własny obszar roboczy użytkownika i File API, a następnie tworzy natywną aktywność Resource. Dla aktywności URL plik YAML wskazany przez `ref` powinien zawierać `url: https://...` lub `externalurl: https://...`. Dla Book katalog wskazany przez `ref` zawiera `book.yaml` z obiektem `book` i listą `chapters`; każdy rozdział ma `title` oraz `content_file` (ścieżka względna względem katalogu książki) albo tekstowe `content`. Opcjonalne `subchapter: true` oznacza podrozdział, a `numbering` przyjmuje 0–3. Pierwszy rozdział musi być rozdziałem głównym; limit publikacji wynosi 200 rozdziałów, a łączny rozmiar ich treści 5 MiB. Pole `source_id` (lub `id`) w rozdziale jest stabilnym identyfikatorem źródłowym; gdy go brak, publikator generuje identyfikator z tytułu, który pozostaje stabilny tylko do czasu zmiany tytułu. Manifest przechowuje mapowanie `source_id` → `chapterid`. Dla Assignment katalog wskazany przez `ref` zawiera `assignment.yaml`. Obsługiwane pola to `intro` lub `markdown_file`, `submission_type` (`onlinetext`, `file`, `both`) lub `submission_types` (lista `file`/`onlinetext`), `grade` lub `grademax`, `max_files` lub `max_attachments`, `max_file_size` w bajtach, `allowsubmissionsfromdate`, `duedate` i `cutoffdate` jako znaczniki czasu Unix, `submission_drafts`, `require_submission_statement` oraz `completion.enabled`. Domyślnie aktywne są przesyłanie tekstu i plików, limit 5 plików po 10 MiB, a powiadomienia o wysłaniu pracy są wyłączone. Pliki przesyłane przez studentów są obsługiwane natywnie przez moduł Assignment Moodle; ten adapter konfiguruje typy przesyłania, nie wysyła z góry plików studentów. Dla Quiz katalog wskazany przez `ref` zawiera `quiz.yaml` oraz plik GIFT wskazany przez `questions_file` (domyślnie `questions.gift`). Obsługiwane ustawienia obejmują `intro`, `time_limit` w sekundach, `attempts` (0 oznacza bez limitu), `grade`, `grade_passing` w procentach, `shuffle_answers` i `questions_per_page`. Reguła `completion: {enabled: true, type: grade, min_score: 60}` ustawia automatyczne ukończenie aktywności na podstawie progu oceny; `type: view` wymaga wyświetlenia aktywności. Import pytań odbywa się natywnym importerem GIFT Moodle do domyślnej kategorii banku pytań w kontekście kursu, a następnie pytania są dodawane do quizu. Limit wynosi 250 pytań i 2 MiB źródła GIFT na quiz. Próg zaliczenia jest zapisywany jako próg oceny w dzienniku ocen. Inne typy aktywności zatrzymują publikację na etapie kontroli wstępnej — przed pierwszą zmianą zdalną.


### Synchronizacja Book i Glossary

- Publikacja Book i Glossary wymaga `--state-file` — manifest przechowuje identyfikatory elementów podrzędnych i jest wiązany z witryną, nazwą skróconą kursu oraz tożsamością aktywności.
- Zmiana treści może być publikowana ponownie przy zachowaniu stabilnej tożsamości kursu i aktywności.
- Dla rozdziałów Book zalecane jest jawne `source_id` lub `id` w każdym elemencie `chapters`. Dla Glossary użyj `source_id` lub `id` w każdym wpisie `entries`. Gdy identyfikator jest pominięty, generowany jest identyfikator z tytułu rozdziału albo terminu hasła; jego zmiana oznacza nową tożsamość elementu.
- Rozdziały i hasła usunięte ze źródła nie są automatycznie usuwane w Moodle. Ich mapowania pozostają w manifeście.
- Istniejący Book lub Glossary zawierający elementy, ale bez mapowania w manifeście, jest odrzucany zamiast uzupełniania duplikatami.
- Aktualizacja rozdziału Book z plikami osadzonymi oraz wpisu Glossary z załącznikami jest obecnie odrzucana. Wymagana jest osobna obsługa File API.
- Assignment: zmiana wtyczek przesyłania i limitów plików jest blokowana, jeśli istnieją już rekordy zgłoszeń. Opis, terminy, ocena i ustawienia niezwiązane z historią zgłoszeń mogą być aktualizowane.
- Resource: manifest przechowuje `filename` i `sha256`. Jeśli plik zdalny nie odpowiada ostatniemu opublikowanemu skrótowi albo brak mapowania starszego zasobu, publikator zgłasza konflikt zamiast nadpisywać plik.
- Dla starszych kursów i manifestów bez mapowań potrzebna jest ręczna, kontrolowana migracja identyfikatorów; publikator nie zgaduje powiązań na podstawie kolejności ani samego tytułu.

## Bezpieczeństwo i ograniczenia

- Token jest pobierany wyłącznie ze zmiennej środowiskowej; nigdy nie umieszczaj go w YAML, CLI ani repozytorium.
- Konto techniczne powinno mieć minimalne wymagane role i capabilities.
- REST Moodle jest wywoływany metodą POST, z kodowaniem parametrów tablicowych Moodle.
- Operacja nie jest transakcją rozproszoną. Błąd w trakcie publikacji może pozostawić częściowo utworzony kurs. Komunikat błędu wskazuje sekcję lub aktywność, pozycję w kolejce, identyfikator `idnumber` i liczbę wcześniej obsłużonych aktywności. Po usunięciu przyczyny można ponowić całe polecenie: kurs i aktywności są rozpoznawane idempotentnie, więc wcześniej utworzone elementy nie są duplikowane.
- Idempotencja obejmuje wyszukanie kursu po shortname oraz stabilne identyfikatory źródłowe `idnumber` wyliczane z kursu, sekcji, typu i ścieżki `ref`. Zmiana nazwy aktywności nie tworzy duplikatu; dla wcześniej utworzonych aktywności bez `idnumber` identyfikator jest uzupełniany przy ponownym odnalezieniu po nazwie. Ponowna publikacja Page, Label i URL aktualizuje istniejący obiekt przez update_moduleinfo, zachowując cmid i instanceid. Aktualizacja jest wykonywana w transakcji Moodle, a cache kursu jest przebudowywany przed zatwierdzeniem. Book, Glossary, Assignment i Resource są synchronizowane w miejscu. Book aktualizuje rozdziały przez mapowanie `source_id` → `chapterid`; Glossary aktualizuje hasła przez mapowanie `source_id` → `entryid`. Assignment aktualizuje wyłącznie pola jawnie zarządzane w źródle, zachowując ustawienia pominięte w YAML. Zmiana typów wtyczek przesyłania i limitów plików jest blokowana, jeśli istnieją już zgłoszenia studentów. Resource przechowuje nazwę i skrót SHA-256 zarządzanego pliku; przed podmianą sprawdza, czy plik zdalny nie został ręcznie zmieniony, i używa File API do podmiany jednego zarządzanego pliku, zachowując pozostałe pliki. Quiz nadal wymaga osobnego adaptera aktualizacji.
- Wbudowane tworzenie aktywności obejmuje Page, Label, URL, Book, Quiz, Assignment, Glossary i Resource. Synchronizacja istniejących aktywności w wersji 0.1.15 obejmuje Page, Label, URL, Book, Glossary, Assignment i Resource.
- Testy automatyczne używają atrap HTTP; rzeczywista publikacja wymaga testu na osobnej instancji Moodle 4.1.8.

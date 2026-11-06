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

Skopiuj katalog `moodle-plugin/local/magicmoodle` do `<moodle>/local/magicmoodle`, a następnie zaloguj się jako administrator i przejdź do powiadomień, aby wykonać instalację. Dodaj siedem funkcji pluginu do usługi zewnętrznej. Plugin w wersji 0.1.9 udostępnia funkcje do aktualizacji nazwy sekcji oraz tworzenia aktywności Page, Label, URL, Book, Quiz, Assignment, Resource i Glossary z kontrolą kontekstu i uprawnień.

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

Następnie wykonaj publikację:

```bash
python -m magic_moodle moodle-publish courses/03-kurs-masazysta-med10
```

Klient sprawdza istnienie kursu po `shortname` i nie tworzy duplikatu. Nowy kurs otrzymuje kategorię wskazaną przez `MOODLE_CATEGORY_ID`, format i liczbę sekcji z konfiguracji. Sekcje otrzymują nazwy z repozytorium. Wbudowany adapter publikuje Page, Label, URL, Book, Quiz, Assignment, Glossary oraz pliki jako aktywności Resource. Aktywność typu `glossary` wskazuje katalog z `glossary.yaml`, zawierającym obiekt `glossary` i listę `entries` z polami `term`, `definition` oraz opcjonalnym `format` (`html`, `markdown`, `plain`). Limit słownika wynosi 500 haseł i 5 MiB łącznej treści; powtórzone hasła są odrzucane. Wpisy są tworzone przez natywny interfejs Glossary Moodle i domyślnie zatwierdzane. Aktywność typu `file` wskazuje pojedynczy plik binarny w repozytorium kursu; przesyłany jest on jako base64, z limitem 5 MiB. Moodle zapisuje plik przez własny obszar roboczy użytkownika i File API, a następnie tworzy natywną aktywność Resource. Dla aktywności URL plik YAML wskazany przez `ref` powinien zawierać `url: https://...` lub `externalurl: https://...`. Dla Book katalog wskazany przez `ref` zawiera `book.yaml` z obiektem `book` i listą `chapters`; każdy rozdział ma `title` oraz `content_file` (ścieżka względna względem katalogu książki) albo tekstowe `content`. Opcjonalne `subchapter: true` oznacza podrozdział, a `numbering` przyjmuje 0–3. Pierwszy rozdział musi być rozdziałem głównym; limit publikacji wynosi 200 rozdziałów, a łączny rozmiar ich treści 5 MiB. Dla Assignment katalog wskazany przez `ref` zawiera `assignment.yaml`. Obsługiwane pola to `intro` lub `markdown_file`, `submission_type` (`onlinetext`, `file`, `both`) lub `submission_types` (lista `file`/`onlinetext`), `grade` lub `grademax`, `max_files` lub `max_attachments`, `max_file_size` w bajtach, `allowsubmissionsfromdate`, `duedate` i `cutoffdate` jako znaczniki czasu Unix, `submission_drafts`, `require_submission_statement` oraz `completion.enabled`. Domyślnie aktywne są przesyłanie tekstu i plików, limit 5 plików po 10 MiB, a powiadomienia o wysłaniu pracy są wyłączone. Pliki przesyłane przez studentów są obsługiwane natywnie przez moduł Assignment Moodle; ten adapter konfiguruje typy przesyłania, nie wysyła z góry plików studentów. Dla Quiz katalog wskazany przez `ref` zawiera `quiz.yaml` oraz plik GIFT wskazany przez `questions_file` (domyślnie `questions.gift`). Obsługiwane ustawienia obejmują `intro`, `time_limit` w sekundach, `attempts` (0 oznacza bez limitu), `grade`, `grade_passing` w procentach, `shuffle_answers` i `questions_per_page`. Reguła `completion: {enabled: true, type: grade, min_score: 60}` ustawia automatyczne ukończenie aktywności na podstawie progu oceny; `type: view` wymaga wyświetlenia aktywności. Import pytań odbywa się natywnym importerem GIFT Moodle do domyślnej kategorii banku pytań w kontekście kursu, a następnie pytania są dodawane do quizu. Limit wynosi 250 pytań i 2 MiB źródła GIFT na quiz. Próg zaliczenia jest zapisywany jako próg oceny w dzienniku ocen. Inne typy aktywności zatrzymują publikację na etapie kontroli wstępnej — przed pierwszą zmianą zdalną.

## Bezpieczeństwo i ograniczenia

- Token jest pobierany wyłącznie ze zmiennej środowiskowej; nigdy nie umieszczaj go w YAML, CLI ani repozytorium.
- Konto techniczne powinno mieć minimalne wymagane role i capabilities.
- REST Moodle jest wywoływany metodą POST, z kodowaniem parametrów tablicowych Moodle.
- Operacja nie jest transakcją rozproszoną. Błąd w trakcie publikacji może pozostawić częściowo utworzony kurs; przed ponownym uruchomieniem sprawdź kurs i jego aktywności.
- Idempotencja obejmuje wyszukanie kursu po shortname oraz ponowne użycie aktywności o tej samej nazwie, typie i sekcji. Istniejąca aktywność Book jest pozostawiana bez zmian — synchronizacja treści istniejących aktywności będzie osobnym etapem.
- Wbudowane tworzenie aktywności obejmuje Page, Label, URL, Book, Quiz i Assignment. Synchronizacja treści już istniejących aktywności wymaga dalszego adaptera aktualizacji.
- Testy automatyczne używają atrap HTTP; rzeczywista publikacja wymaga testu na osobnej instancji Moodle 4.1.8.

# Zdalna publikacja w Moodle przez REST API

## Wymagania

1. Moodle 4.2 lub nowszy z włączonym protokołem REST.
2. Utworzona usługa zewnętrzna, token dla dedykowanego konta technicznego i uprawnienia do tworzenia kursów oraz aktywności.
3. Zainstalowany lokalny plugin `local_magicmoodle` z katalogu `moodle-plugin/local/magicmoodle`.
4. Dozwolone funkcje usługi:
   - `core_webservice_get_site_info`
   - `core_course_get_courses_by_field`
   - `core_course_create_courses`
   - `local_magicmoodle_update_section`
   - `local_magicmoodle_create_activity`

Konfiguracja usługi i tokenu odbywa się po stronie administratora Moodle:
**Administracja witryną → Serwer → Usługi sieciowe**. Funkcje zewnętrzne i uprawnienia konta muszą być jawnie przyznane. Zob. [Moodle Web Services](https://moodledev.io/docs/5.3/apis/subsystems/external) oraz [Using web services](https://docs.moodle.org/500/en/How_to_create_and_enable_a_web_service).

## Instalacja pluginu

Skopiuj katalog `moodle-plugin/local/magicmoodle` do `<moodle>/local/magicmoodle`, a następnie zaloguj się jako administrator i przejdź do powiadomień, aby wykonać instalację. Dodaj dwie funkcje pluginu do usługi zewnętrznej. Plugin udostępnia bezpieczne funkcje do aktualizacji nazwy sekcji oraz tworzenia aktywności Page i Label z kontrolą kontekstu i uprawnień.

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

Klient sprawdza istnienie kursu po `shortname` i nie tworzy duplikatu. Nowy kurs otrzymuje kategorię wskazaną przez `MOODLE_CATEGORY_ID`, format i liczbę sekcji z konfiguracji. Sekcje otrzymują nazwy z repozytorium. Wbudowany adapter publikuje Page i Label. Inne typy aktywności zatrzymują publikację na etapie kontroli wstępnej — przed pierwszą zmianą zdalną.

## Bezpieczeństwo i ograniczenia

- Token jest pobierany wyłącznie ze zmiennej środowiskowej; nigdy nie umieszczaj go w YAML, CLI ani repozytorium.
- Konto techniczne powinno mieć minimalne wymagane role i capabilities.
- REST Moodle jest wywoływany metodą POST, z kodowaniem parametrów tablicowych Moodle.
- Operacja nie jest transakcją rozproszoną. Błąd w trakcie publikacji może pozostawić częściowo utworzony kurs; przed ponownym uruchomieniem sprawdź kurs i jego aktywności.
- Idempotencja obejmuje wyszukanie kursu po shortname. Ponowne uruchomienie może dodać ponownie aktywności — przed kolejnym przebiegiem należy je zweryfikować.
- Wbudowane tworzenie aktywności obejmuje na razie wyłącznie Page i Label. Quiz, Assignment, Book, Glossary, pliki i zasoby URL wymagają dalszych adapterów oraz obsługi plików Moodle.
- Testy automatyczne używają atrap HTTP; rzeczywista publikacja wymaga testu na osobnej instancji Moodle.

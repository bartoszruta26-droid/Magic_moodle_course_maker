# Architektura wielointerfejsowa Magic Moodle Course Maker

Status: propozycja architektury (ADR do zatwierdzenia przez właściciela projektu)  
Powiązany audyt: [GUI_PLATFORM_AUDIT.md](../audit/GUI_PLATFORM_AUDIT.md)

## 1. Decyzja

Projekt ma utrzymywać jeden rdzeń domenowy i aplikacyjny oraz cztery niezależne klienty:
- TUI — Textual;
- DesktopGUI — PySide6 / Qt 6;
- WebUI — HTML/CSS/TypeScript lub JavaScript;
- AndroidGUI — Kotlin / Jetpack Compose.

Nie tworzymy czterech implementacji logiki kursu. Każdy klient wywołuje te same przypadki użycia, walidację, eksport i usługi publikacji.

## 2. Docelowy podział

```text
Klienci lokalni                         Klienci zdalni
+----------------+ +----------------+   +----------------+ +----------------+
| TUI / Textual  | | Desktop / Qt   |   | WebUI          | | Android        |
+-------+--------+ +-------+--------+   +-------+--------+ +-------+--------+
        |                  |                    |                  |
        +------------------+                    +------------------+
                 |                                       |
        Application Services                    HTTP API Adapter
                 |                                       |
        +--------+---------------------------------------+
        |              Application Core                  |
        | Use cases / policies / authorization           |
        +------------------------+----------------------+
                                 |
                         Domain + Ports
                                 |
              +------------------+------------------+
              |                  |                  |
          File Storage       Moodle Gateway      Job Runner
```

TUI i DesktopGUI mogą uruchamiać warstwę aplikacyjną bezpośrednio w procesie. WebUI i AndroidGUI komunikują się z nią przez API. WebUI działające wyłącznie lokalnie może korzystać z tego samego API na loopback; nie powinno otrzymywać bezpośredniego dostępu do plików systemowych.

## 3. Proponowany układ pakietów

Docelowo, po migracji stopniowej:

```text
magic_moodle/
  domain/
    models.py
    identifiers.py
    errors.py
  application/
    ports.py
    course_queries.py
    course_commands.py
    validation.py
    publishing.py
    jobs.py
  infrastructure/
    filesystem/
    moodle/
    persistence/
  api/
    app.py
    schemas/
    routes/
  cli.py
  __main__.py

tui/
  app.py
  screens/
  widgets/

desktopgui/
  app.py
  views/
  viewmodels/

webui/
  server.py
  static/

android/
  app/
    src/main/
      java/

tests/
  unit/
  contract/
  integration/
  e2e/
```

To jest układ docelowy, a nie instrukcja jednorazowego przeniesienia istniejących modułów. Obecne importy z `magic_moodle.models`, `loader.py`, `validation.py` i `moodle_publish.py` należy zachować przez warstwę zgodności do czasu migracji.

## 4. Przypadki użycia — wspólny kontrakt

Pierwszy zestaw usług aplikacyjnych:
- `ListCourses` — lista kursów dostępnych dla użytkownika;
- `GetCourse` — szczegóły kursu i jego wersja;
- `ValidateCourse` — raport błędów i ostrzeżeń;
- `CreateCourseDraft` — utworzenie wersji roboczej z szablonu;
- `UpdateCourseDraft` — zapis kontrolowanej zmiany;
- `PreviewExport` — plan eksportu bez zapisu;
- `ExportCourse` — eksport do wybranego formatu;
- `BuildPublishPlan` — plan publikacji Moodle bez operacji zdalnej;
- `PublishCourse` — publikacja po jawnej autoryzacji i potwierdzeniu;
- `GetJob` / `CancelJob` — stan i anulowanie zadania, jeśli operacja wspiera bezpieczne przerwanie.

Każdy przypadek użycia powinien przyjmować jawne dane wejściowe i zwracać typowany wynik. Nie powinien zależeć od Textual, Qt, przeglądarki ani Android SDK.

## 5. Kontrakt HTTP API — wersja 1

Prefiks: `/api/v1`. JSON UTF-8. Daty ISO 8601 UTC. Identyfikatory zasobów są nieprzezroczystymi ciągami, nie ścieżkami plików.

| Metoda i ścieżka | Cel | Charakter |
|---|---|---|
| `GET /health` | Stan usługi | odczyt |
| `GET /courses` | Lista kursów | odczyt |
| `GET /courses/{course_id}` | Szczegóły i wersja kursu | odczyt |
| `POST /courses/{course_id}/validation` | Uruchomienie walidacji | zadanie/odczyt |
| `POST /courses/drafts` | Utworzenie wersji roboczej | zapis |
| `PUT /courses/{course_id}/draft` | Zapis wersji roboczej | zapis warunkowy |
| `POST /courses/{course_id}/exports` | Zlecenie eksportu | zadanie |
| `POST /courses/{course_id}/publish-plan` | Przygotowanie planu | odczyt/zadanie |
| `POST /courses/{course_id}/publications` | Publikacja po potwierdzeniu | operacja krytyczna |
| `GET /jobs/{job_id}` | Postęp zadania | odczyt |
| `POST /jobs/{job_id}/cancel` | Anulowanie, jeśli wspierane | zapis |

### 5.1. Kształt odpowiedzi

Sukces:
```json
{
  "data": {},
  "meta": {
    "request_id": "opaque-id",
    "api_version": "1"
  }
}
```

Błąd:
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Kurs zawiera błędy walidacji.",
    "details": [],
    "request_id": "opaque-id"
  }
}
```

Nie zwracać ścieżek bezwzględnych, tokenów, sekretów, pełnych wyjątków ani danych uwierzytelniających. Komunikaty dla użytkownika muszą być oddzielone od diagnostyki technicznej.

### 5.2. Wersjonowanie i konflikty

- Odczyt zasobu zwraca `version` lub silny `ETag`.
- Zapis wymaga `If-Match` albo pola `expected_version`.
- Konflikt wersji zwraca HTTP 409 i kod `VERSION_CONFLICT`.
- Nie stosować strategii „ostatni zapis wygrywa” dla edycji kursu.
- API jest wersjonowane przez prefiks ścieżki; zmiana niekompatybilna wymaga nowej wersji.

### 5.3. Publikacja Moodle

Publikacja jest operacją krytyczną:
1. klient pobiera plan publikacji;
2. użytkownik widzi kurs, serwer docelowy, kategorię, typy aktywności i ostrzeżenia;
3. klient przesyła jawne potwierdzenie powiązane z identyfikatorem planu;
4. serwer ponownie sprawdza plan i uprawnienia;
5. publikacja jest wykonywana jako zadanie z manifestem wznowienia;
6. wynik zawiera identyfikatory Moodle, stan każdej operacji i raport częściowej realizacji.

Token Moodle pozostaje wyłącznie po stronie bezpiecznej warstwy serwerowej/lokalnej infrastruktury, nigdy w kliencie przeglądarkowym ani mobilnym.

## 6. Bezpieczeństwo i uprawnienia

Minimalne role:
- `viewer` — przegląd i raporty;
- `author` — tworzenie i edycja wersji roboczych;
- `reviewer` — przegląd, zatwierdzanie i uwagi;
- `publisher` — publikacja do skonfigurowanych witryn;
- `administrator` — konfiguracja, użytkownicy i uprawnienia.

Zasady:
- domyślna odmowa dostępu;
- autoryzacja na poziomie zasobu i operacji, nie tylko widoku;
- walidacja danych wejściowych i limitów rozmiaru;
- ochrona przed CSRF dla sesji przeglądarkowych;
- restrykcyjne CORS — tylko jawnie dozwolone źródła;
- HTTPS dla dostępu zdalnego;
- sekrety w magazynie sekretów lub zmiennych środowiskowych po stronie serwera;
- dziennik audytowy: kto, co, kiedy, na jakim zasobie i z jakim wynikiem;
- brak tokenów, haseł i treści wrażliwych w logach;
- kopie zapasowe i testowane odtwarzanie.

Obecny serwer `webui.server` pozostaje narzędziem lokalnym. Nie należy traktować go jako gotowego serwera produkcyjnego.

## 7. Zadania długotrwałe

Generowanie, walidacja dużych kursów, eksport i publikacja powinny zwracać `job_id`. Minimalny model zadania:
- `queued`, `running`, `succeeded`, `failed`, `cancelled`;
- postęp liczbowy opcjonalny i opis etapu;
- czas utworzenia, rozpoczęcia i zakończenia;
- kod błędu i bezpieczny komunikat;
- możliwość wznowienia tylko dla operacji jawnie idempotentnych;
- anulowanie wyłącznie wtedy, gdy nie narusza spójności operacji.

## 8. Zasady dla czterech interfejsów

### TUI — Textual
- nawigacja klawiaturą, skróty i pomoc kontekstowa;
- widok listy kursów, szczegółów, walidacji, banku pytań i zadań;
- formularze z walidacją pól;
- wyraźne potwierdzenie eksportu i publikacji;
- czytelny tryb tekstowy i działanie w terminalach o ograniczonych możliwościach.

### DesktopGUI — PySide6
- układ wielopanelowy: nawigacja, edytor, inspektor i dziennik;
- edytor Markdown/YAML z podglądem i diagnostyką;
- zadania poza głównym wątkiem Qt;
- automatyczny zapis wersji roboczej, historia i odzyskiwanie;
- dostępność klawiatury, skalowanie DPI i obsługa systemów docelowych.

### WebUI
- responsywność, semantyczny HTML i WCAG 2.2 AA;
- bezpieczne renderowanie treści kursu;
- edycja z kontrolą wersji i konfliktem 409;
- sesje, CSRF, CSP, CORS i autoryzacja;
- podgląd zmian przed zatwierdzeniem.

### AndroidGUI — Kotlin / Compose
- MVVM i repozytoria;
- Room jako lokalna pamięć podręczna i kolejka wersji roboczych;
- WorkManager dla synchronizacji odroczonej;
- bezpieczne przechowywanie tokenów sesyjnych w Android Keystore;
- synchronizacja z konfliktem wersji, bez cichego nadpisywania;
- mobilny zakres funkcji ograniczony do wygodnych operacji dotykowych.

## 9. Testowanie

- jednostkowe: domena i przypadki użycia;
- kontraktowe: schematy request/response, błędy, wersjonowanie;
- integracyjne: system plików, Moodle gateway, manifest publikacji;
- TUI: testy widoków i interakcji klawiaturą;
- DesktopGUI: testy widoków i zadań w tle;
- WebUI: testy API oraz Playwright;
- Android: testy jednostkowe, Compose UI i synchronizacji;
- bezpieczeństwo: autoryzacja negatywna, CSRF, CORS, limity, path traversal, ujawnianie sekretów;
- dostępność: WCAG 2.2 AA dla WebUI i równoważne testy użyteczności pozostałych klientów.

## 10. Kolejność wdrożenia

1. Wprowadzić warstwę `application` i typowane przypadki użycia, nie zmieniając zachowania CLI.
2. Dodać testy jednostkowe i kontraktowe.
3. Zbudować TUI jako pierwszy nowy klient, ponieważ korzysta bezpośrednio z Pythona.
4. Wydzielić adapter HTTP i kontrakt API.
5. Rozwinąć WebUI na bazie API, utrzymując lokalny tryb bezpieczny.
6. Zbudować DesktopGUI na wspólnych usługach.
7. Zbudować AndroidGUI po ustabilizowaniu API i uwierzytelniania.
8. Dodać testy E2E i wydania wieloplatformowe.

## 11. Kryteria akceptacji fundamentu

- [ ] Rdzeń aplikacyjny nie importuje frameworków GUI ani HTTP.
- [ ] CLI używa przypadków użycia zamiast dublować logikę.
- [ ] Walidacja i eksport są dostępne przez wspólny kontrakt.
- [ ] Testy kontraktowe potwierdzają stabilny format wyników i błędów.
- [ ] Zapis wersji roboczej wymaga kontroli wersji.
- [ ] Publikacja wymaga jawnego potwierdzenia i uprawnień.
- [ ] Sekrety Moodle nie trafiają do klientów.
- [ ] Długotrwałe zadania raportują stan i bezpieczne błędy.

## 12. Otwarte decyzje przed implementacją

1. Czy WebUI ma być domyślnie wyłącznie lokalne, czy docelowo hostowane dla wielu użytkowników?
2. Jaki mechanizm tożsamości będzie używany: lokalne konta, OIDC czy integracja z istniejącym dostawcą?
3. Czy DesktopGUI ma pracować całkowicie offline, czy wymagać lokalnego API?
4. Jakie systemy desktopowe i minimalne wersje Androida będą wspierane?
5. Czy użytkownicy będą edytować ten sam kurs współbieżnie?

Do czasu podjęcia tych decyzji implementacja powinna unikać nieodwracalnych wyborów dotyczących dostawcy uwierzytelniania i synchronizacji wieloużytkownikowej.

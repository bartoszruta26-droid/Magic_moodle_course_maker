# API HTTP v1 — tryb lokalny i klienci

## Status

API jest lokalnym adapterem nad wspólną warstwą aplikacyjną. Udostępnia odczyt kursów, walidację oraz ograniczoną edycję w postaci izolowanych wersji roboczych. Wersje robocze nie nadpisują plików źródłowych kursu.

## Uruchomienie

```bash
python -m pip install -e .
MAGIC_MOODLE_COURSES=./courses \
MAGIC_MOODLE_API_HOST=127.0.0.1 \
MAGIC_MOODLE_API_PORT=8766 \
MAGIC_MOODLE_API_TOKEN='wygenerowany-losowy-sekret' \
magic-moodle-api
```

Token jest wymagany do tworzenia i aktualizowania wersji roboczych. Jeśli nie ustawiono `MAGIC_MOODLE_API_TOKEN`, operacje odczytu pozostają dostępne lokalnie, ale zapisy wersji roboczych zwracają HTTP 503. Jeśli token jest skonfigurowany, wszystkie żądania muszą zawierać `Authorization: Bearer <token>`.

## Endpointy

| Metoda | Ścieżka | Opis |
|---|---|---|
| GET | `/api/v1/health` | Stan usługi |
| GET | `/api/v1/courses` | Lista kursów |
| GET | `/api/v1/courses/{course_id}` | Szczegóły kursu i sekcji |
| POST | `/api/v1/courses/{course_id}/validation` | Raport walidacji |
| POST | `/api/v1/courses/{course_id}/drafts` | Utworzenie wersji roboczej |
| GET | `/api/v1/drafts/{draft_id}` | Odczyt wersji roboczej |
| PATCH | `/api/v1/drafts/{draft_id}` | Aktualizacja wersji roboczej |
| GET | `/api/v1/drafts/{draft_id}/preview` | Podgląd zmian i walidacja |

Aktualizacja wymaga treści JSON o kształcie:

```json
{
  "expected_revision": 1,
  "changes": {
    "full_name": "Nowa nazwa kursu",
    "short_name": "NOWY-KURS",
    "description": "Opis wersji roboczej",
    "section_names": {
      "intro": "Wprowadzenie"
    },
    "activity_names": {
      "intro|page.md": "Nowy tytuł aktywności"
    }
  }
}
```

Dozwolone pola to `full_name`, `short_name`, `description`, `section_names` i `activity_names`. Nieznane identyfikatory sekcji i aktywności są odrzucane. Aktualizacja na nieaktualnej rewizji zwraca HTTP 409. Treść żądania jest ograniczona do 256 KiB.

Odpowiedź sukcesu zawiera `data` i `meta.api_version`. Błędy mają `error.code` i bezpieczny komunikat.

## Model wersji roboczych

- pliki wersji roboczych są przechowywane w `.magic_moodle/drafts/` pod katalogiem kursów;
- każda wersja ma identyfikator UUID, numer rewizji, znaczniki czasu i skrót bazowego modelu kursu;
- zapis JSON odbywa się atomowo;
- aktualizacja wymaga zgodności `expected_revision`;
- podgląd nakłada dozwolone zmiany na kanoniczny model kursu i uruchamia walidator;
- jeśli kurs źródłowy zmienił się po utworzeniu wersji roboczej, zapis i podgląd wykrywają konflikt;
- ten etap nie zapisuje zmian do `course.yaml`, plików sekcji ani zasobów aktywności.

## Bezpieczeństwo

- serwer odmawia nasłuchiwania na adresach innych niż loopback;
- zdalny dostęp należy realizować przez reverse proxy z TLS;
- token Bearer jest sprawdzany w stałym czasie przez `hmac.compare_digest`;
- zapisy wersji roboczych wymagają jawnie skonfigurowanego tokenu;
- API odrzuca niepoprawne typy i pola, a treść żądania ogranicza do 256 KiB;
- ścieżki systemu plików, tokeny i pełne wyjątki nie są zwracane klientom;
- odpowiedzi mają `Cache-Control: no-store` i `X-Content-Type-Options: nosniff`;
- API nie udostępnia jeszcze zatwierdzania zmian do kursu ani publikacji Moodle.

Nie należy wystawiać wbudowanego serwera HTTP bezpośrednio do Internetu. Reverse proxy powinien terminować HTTPS i przekazywać żądania do lokalnego adresu API.

## Kolejne etapy

1. Historia rewizji, przywracanie i usuwanie wersji roboczych.
2. Zatwierdzanie zmian do plików kursu z transakcją, kopią zapasową i ponowną walidacją.
3. Edytor WebUI i DesktopGUI oparty na tych samych operacjach.
4. Synchronizacja wersji roboczych w AndroidGUI.
5. Role użytkowników, audyt zdarzeń i testy bezpieczeństwa.

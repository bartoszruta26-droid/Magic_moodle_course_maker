# API HTTP v1 — tryb lokalny i klienci

## Status

Pierwsza implementacja API jest lokalnym, tylko do odczytu adapterem nad `CourseApplicationService`. Udostępnia listę kursów, szczegóły i walidację. Nie realizuje jeszcze edycji, eksportu ani publikacji.

## Uruchomienie

```bash
python -m pip install -e .
MAGIC_MOODLE_COURSES=./courses \
MAGIC_MOODLE_API_HOST=127.0.0.1 \
MAGIC_MOODLE_API_PORT=8766 \
magic-moodle-api
```

Opcjonalnie można ustawić `MAGIC_MOODLE_API_TOKEN`. Gdy token jest skonfigurowany, każde żądanie wymaga nagłówka `Authorization: Bearer <token>`.

## Endpointy

| Metoda | Ścieżka | Opis |
|---|---|---|
| GET | `/api/v1/health` | Stan usługi |
| GET | `/api/v1/courses` | Lista kursów |
| GET | `/api/v1/courses/{course_id}` | Szczegóły kursu i sekcji |
| POST | `/api/v1/courses/{course_id}/validation` | Raport walidacji |

Odpowiedź sukcesu zawiera `data` i `meta.api_version`. Błędy mają `error.code` i bezpieczny komunikat.

## Bezpieczeństwo

- serwer odmawia nasłuchiwania na adresach innych niż loopback;
- zdalny dostęp należy realizować przez reverse proxy z TLS;
- token Bearer jest sprawdzany w stałym czasie przez `hmac.compare_digest`;
- nie przyjmujemy treści żądań w endpointach POST;
- ścieżki systemu plików, tokeny i pełne wyjątki nie są zwracane klientom;
- odpowiedzi mają `Cache-Control: no-store` i `X-Content-Type-Options: nosniff`;
- API nie udostępnia operacji zapisu ani publikacji.

Nie należy wystawiać wbudowanego serwera HTTP bezpośrednio do Internetu. Reverse proxy powinien terminować HTTPS i przekazywać żądania do lokalnego adresu API.

## Ograniczenia i dalsze etapy

1. Uwierzytelnianie użytkowników i role autoryzacyjne.
2. Wersjonowanie zasobów i kontrola konfliktów.
3. Edycja wersji roboczych i eksport.
4. Kolejka zadań i raportowanie postępu.
5. Integracja AndroidGUI przez HTTPS.
6. Testy penetracyjne, limity żądań i audyt zdarzeń.

# Etap 3 — audyt bezpieczeństwa rdzenia Python i pluginu Moodle

Data: 2026-11-06  
Gałąź: `audit/php-endpoints-python-hardening`  
Bazowa rewizja `main`: `011652d7d0e790f75bf7cf2a11952ede78f75e42`

## Zakres przeglądu

Przegląd statyczny objął moduły pakietu `magic_moodle`: CLI, modele, loader, walidator, parser GIFT, obsługę banków pytań, klienta REST Moodle, plan publikacji, eksport JSON i eksport Moodle XML. Obejmuje też wszystkie siedem endpointów zarejestrowanych przez `local_magicmoodle`:

- `update_section`
- `create_activity`
- `create_assignment`
- `create_book`
- `create_glossary`
- `create_quiz`
- `create_resource`

Nie jest to audyt dynamiczny na żywym Moodle. Zgodność API i zachowanie transakcji muszą być jeszcze potwierdzone integracyjnie na Moodle 4.1 (minimalna wersja zadeklarowana przez plugin) i na docelowej wersji produkcyjnej.

## Zmiany przygotowane w tej gałęzi

### Rdzeń Python

1. **Loader i ścieżki**
   - odrzucanie ścieżek bezwzględnych i wyjść poza katalog kursu;
   - kontrola dowiązań symbolicznych dla katalogów sekcji, plików konfiguracyjnych i zasobów;
   - limity rozmiaru YAML, tekstu, GIFT i plików binarnych przed odczytem;
   - regresje dla dowiązań zewnętrznych i nadmiernych plików.

2. **Walidator**
   - wykrywanie sekcji poza katalogiem kursu;
   - wykrywanie zewnętrznych dowiązań symbolicznych;
   - limit 2 MiB dla plików YAML podczas walidacji.

3. **Bank pytań GIFT**
   - limit 5 MiB na plik, 25 MiB na bank i 500 plików;
   - odrzucanie dowiązań symbolicznych prowadzących poza katalog banku.

4. **Klient REST Moodle**
   - blokowanie automatycznych przekierowań żądań zawierających token;
   - weryfikacja TLS obowiązkowa dla hostów zdalnych;
   - wyłączenie weryfikacji TLS dopuszczone wyłącznie dla localhost;
   - redagowanie tokenu w komunikatach błędów HTTP i Moodle;
   - walidacja skończonego, dodatniego timeoutu.

5. **Eksporty**
   - atomowy zapis JSON i Moodle XML przez plik tymczasowy i `os.replace`;
   - odrzucanie wartości NaN i nieskończoności w JSON;
   - kontrola kategorii i znaków niedozwolonych w XML 1.0.

### Plugin Moodle — wszystkie endpointy zapisu

| Endpoint | Kontrole i zabezpieczenia objęte zmianą |
|---|---|
| `update_section` | uprawnienie `moodle/course:update`, transakcja delegowana, przebudowa cache przed zatwierdzeniem |
| `create_activity` | transakcja, czyszczenie HTML, kontrola URL i odrzucanie danych logowania w adresie |
| `create_assignment` | walidacja terminów, ocen i limitów przesyłania, transakcja |
| `create_book` | limity rozdziałów i treści, sprawdzenie uprawnienia edycji, transakcja |
| `create_glossary` | limity liczby/rozmiaru haseł, kontrola duplikatów, transakcja |
| `create_quiz` | limit GIFT i liczby pytań, transakcja importu, kontrola pełnego zapisu pliku tymczasowego i sprzątanie |
| `create_resource` | walidacja nazwy i rozmiaru pliku, transakcja oraz sprzątanie obszaru roboczego w `finally` |

Dodatkowo wszystkie sześć endpointów tworzących aktywności:
- odrzuca konflikt między nazwą a stabilnym `idnumber`, zamiast zwracać pozorny sukces;
- odrzuca ponowne użycie tego samego `idnumber` w innej sekcji;
- serializuje zapisy danego typu modułu w obrębie kursu przy użyciu blokady Moodle, ograniczając wyścig typu check-then-create.

## Znane ograniczenia i dalsze zadania

1. **Brak pełnej synchronizacji aktualizacji.** Endpointy tworzące aktywności nadal nie aktualizują istniejącej treści. W razie konfliktu kończą operację błędem, zamiast udawać, że synchronizacja się odbyła. Następny etap powinien dodać jawne endpointy aktualizacji dla każdego typu modułu.
2. **Brak trwałego manifestu publikacji.** Ponowienie polecenia wykorzystuje identyfikatory źródłowe i idempotencję, ale nie ma jeszcze trwałego dziennika postępu, wersji źródła i stanu każdej aktywności.
3. **Brak testu współbieżności na bazie Moodle.** Blokady wymagają weryfikacji na używanym przez instalację Moodle lock factory i bazie danych.
4. **Brak testu integracyjnego PHP na rzeczywistym Moodle.** Testy statyczne i `php -l` nie potwierdzają zgodności pól `moduleinfo`, zdarzeń modułów i API importera pytań z każdą wersją Moodle.
5. **Book i Glossary.** Część operacji używa natywnych funkcji Moodle, ale tworzenie rozdziałów Book nadal obejmuje bezpośredni zapis do tabeli modułu. Należy porównać tę ścieżkę z publicznym API modułu w docelowej wersji Moodle.
6. **Odporność na częściową publikację.** Potrzebny jest test awarii po każdej operacji zapisu oraz weryfikacja, że wznowienie nie dubluje pytań, rozdziałów, wpisów słownika i plików.
7. **Uprawnienia.** Należy przetestować role i konteksty usługi zewnętrznej na kontach o minimalnych uprawnieniach, nie tylko na administratorze.

## Kryteria zamknięcia etapu

- wszystkie testy CI dla rewizji PR zakończone powodzeniem;
- poprawność składni wszystkich plików PHP;
- test integracyjny endpointów na Moodle 4.1 i docelowej wersji produkcyjnej;
- testy ponawiania publikacji po awarii dla każdego endpointu;
- osobny projekt i testy endpointów aktualizacji oraz manifestu wznowienia.

**Status:** poprawki przygotowane do przeglądu w PR; etap audytu pozostaje otwarty.

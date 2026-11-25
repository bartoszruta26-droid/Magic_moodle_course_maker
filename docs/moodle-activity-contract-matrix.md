# Kontrakt publikacji aktywności Moodle

> Status dokumentu: analiza statyczna kodu repozytorium na 2026-11-25. Dokument nie jest potwierdzeniem testu na działającej instancji Moodle 4.1.

## Cel i granice

Dokument wiąże neutralny model `Course → Section → Activity`, loader katalogów kursu, plan publikacji REST oraz funkcje zewnętrzne wtyczki `local_magicmoodle`. Ma zapobiegać sytuacji, w której aktywność zostaje zaakceptowana przez loader, ale jej konfiguracja lub treść nie dociera do Moodle.

Publikator REST i wtyczka Moodle są odrębną ścieżką od eksportu MBZ. Żaden z poniższych kontraktów nie stanowi dowodu, że archiwum MBZ jest generowane lub importowalne.

## Macierz obsługi

| Typ źródłowy | Dane ładowane przez `magic_moodle.loader` | Funkcja REST | Warunek trwałej synchronizacji |
|---|---|---|---|
| `page` | Tekst z pliku wskazanego przez `ref` | `local_magicmoodle_create_activity` (`modname=page`) | Nie wymaga manifestu podrzędnych identyfikatorów |
| `label` | Tekst z pliku wskazanego przez `ref` | `local_magicmoodle_create_activity` (`modname=label`) | Nie wymaga manifestu podrzędnych identyfikatorów |
| `url` | `url.yaml` lub plik YAML; pole `url` | `local_magicmoodle_create_activity` (`modname=url`) | Bezwzględny adres HTTP/HTTPS; bez danych uwierzytelniających w URL |
| `book` | `book.yaml`, lista rozdziałów oraz pliki `content_file` | `local_magicmoodle_create_book` | Wymaga `--state-file` do mapowania rozdziałów źródłowych na identyfikatory Moodle |
| `assignment` | `assignment.yaml` i opcjonalny `markdown_file` | `local_magicmoodle_create_assignment` | Manifest nie jest obecnie wymagany przez warstwę publikacji |
| `quiz` | `quiz.yaml` i plik GIFT wskazany przez `questions_file` | `local_magicmoodle_create_quiz` | Wymaga `--state-file`; istniejące pytania nie są automatycznie nadpisywane |
| `file` | Jeden plik zakodowany Base64; limit loadera 5 MiB | `local_magicmoodle_create_resource` | Wymaga `--state-file` do zachowania tożsamości pliku i skrótu treści |
| `glossary` | `glossary.yaml`, lista `entries` | `local_magicmoodle_create_glossary` | Wymaga `--state-file` do mapowania haseł na identyfikatory Moodle |

Typy spoza tej listy są odrzucane na etapie budowania planu publikacji ostrzeżeniem, które zatrzymuje publikację przed wykonaniem zmian.

## Kontrakty wspólne

### Kurs i sekcje

- Kurs jest tworzony lub odnajdywany przez `core_course_get_courses_by_field` i `core_course_create_courses`.
- Sekcje są aktualizowane przez `local_magicmoodle_update_section`.
- Wtyczka przyjmuje numer sekcji Moodle liczony od zera i wymaga istniejącego rekordu `course_sections`.
- Publikator wylicza `sectionnum` jako indeks sekcji w kolejności zwróconej przez loader. Weryfikacja zgodności tej konwencji z rzeczywistym układem kursu musi być częścią testu integracyjnego na Moodle.

### Identyfikacja i ponawianie

- Publikator generuje stabilny `idnumber` na podstawie nazwy skróconej kursu, identyfikatora sekcji, typu i `ref` aktywności.
- Wtyczka używa `idnumber` do odnajdywania aktywności i unikania duplikatów.
- Manifest publikacji wiąże stan z adresem witryny Moodle i tożsamością kursu.
- Manifest nie jest magazynem sekretów; token dostępu nie powinien być w nim zapisywany.
- Dla Book, Glossary, Resource i Quiz brak `--state-file` zatrzymuje publikację przed zmianami.

## Szczegóły typów i wymagane kontrole

### Page i Label

- Oba typy korzystają z jednego endpointu, ale z różnymi wartościami `modname`.
- Treść Markdown jest przekształcana do HTML przed wysłaniem.
- Wtyczka stosuje `clean_text(..., FORMAT_HTML)` przed zapisem.
- Należy zachować testy, że surowy HTML z wejścia Markdown nie staje się wykonywalnym HTML.

### URL

- Loader dopuszcza konfigurację w katalogu lub pojedynczym pliku YAML.
- Plan publikacji wymaga bezwzględnego adresu HTTP lub HTTPS z hostem.
- Wtyczka dodatkowo odrzuca inne schematy oraz dane użytkownika i hasło w adresie.
- Warto dodać testy adresów z portem, znakami białymi, IPv6 i nietypowymi schematami.

### Book

- Każdy rozdział musi mieć stabilny identyfikator źródłowy, tytuł i treść.
- Wtyczka obsługuje do 200 rozdziałów i łącznie do 5 MiB treści.
- Pierwszy rozdział nie może być podrozdziałem.
- Manifest przechowuje pary identyfikatorów źródłowych i Moodle.
- Zmiany kolejności, usuwanie i ponowne dodawanie rozdziałów wymagają osobnych testów synchronizacji.

### Assignment

- Obsługiwane ustawienia obejmują terminy, ocenę maksymalną, typ przesyłania, limity plików, szkice, oświadczenie o samodzielności i ukończenie.
- Publikator przesyła listę `syncfields`, aby nie nadpisywać ustawień, których źródło nie zarządza.
- Wtyczka wymaga uprawnień do zarządzania aktywnościami i tworzenia zadań.
- Test integracyjny powinien sprawdzić, że ponowna publikacja nie usuwa istniejących prac ani ocen.

### Quiz

- Pytania są walidowane przez parser GIFT przed wywołaniem REST.
- Limit źródła GIFT wynosi 2 MiB, a liczba pytań 1–250.
- Wtyczka importuje pytania przy tworzeniu nowego quizu.
- Dla istniejącego quizu chroni sloty pytań, próby i historię ocen; zmiana treści pytań nie jest automatyczną aktualizacją.
- Manifest przechowuje skrót GIFT. Zmiana skrótu przy istniejącym quizie jest świadomie blokowana, dopóki synchronizacja wersji pytań nie będzie osobno zaprojektowana i przetestowana.

### File / Resource

- Loader koduje jeden plik Base64; publikator ponownie dekoduje go walidacyjnie.
- Dopuszczalny rozmiar to 1 B–5 MiB.
- Wtyczka korzysta z Moodle File API.
- Manifest zachowuje nazwę i SHA-256 pliku, co pozwala rozpoznać zmianę zasobu.
- Należy testować nazwy plików Unicode, kolizje nazw, aktualizację zawartości i zachowanie plików istniejących.

### Glossary

- Wymagane jest 1–500 haseł.
- Każde hasło ma `term`, `definition` oraz stabilny `source_id` (lub zgodny wstecznie identyfikator wyliczany z terminu).
- Powtórzone terminy i identyfikatory źródłowe są odrzucane.
- Format definicji może być `html`, `markdown` lub `plain`; przed produkcyjnym użyciem formatu `html` należy potwierdzić zasady sanitacji i filtrowania w docelowej wersji Moodle.
- Manifest przechowuje mapowanie haseł na identyfikatory wpisów Moodle.

## Minimalny plan testów kontraktowych

1. Dla każdego typu sprawdzić plan publikacji: poprawny payload, stabilny `idnumber` i prawidłowy numer sekcji.
2. Dla każdego endpointu sprawdzić dokładne nazwy parametrów zgodne z `db/services.php` i `execute_parameters()` klasy PHP.
3. Dla niekompletnej konfiguracji potwierdzić zatrzymanie przed jakimkolwiek wywołaniem API.
4. Sprawdzić ponowne uruchomienie z tym samym manifestem oraz odmowę użycia manifestu z innego serwera lub kursu.
5. Sprawdzić zachowanie po przerwaniu publikacji w połowie aktywności.
6. Uruchomić testy na czystym Moodle 4.1 z włączoną wtyczką i kontem serwisowym o minimalnych wymaganych uprawnieniach.
7. Wykonać próbę eksportu/backup i importu osobno; nie utożsamiać jej z publikacją REST.

## Ograniczenia potwierdzenia

Analiza została wykonana statycznie na podstawie kodu loadera, publikatora, definicji usług i klas endpointów. Nie potwierdzono działania na żywym Moodle, zgodności z każdą wersją Moodle ani importu MBZ. Każde takie potwierdzenie wymaga osobnego wyniku testu integracyjnego z numerem wersji Moodle, wersją PHP, konfiguracją wtyczki i logiem operacji.

# Kontrakt publikacji aktywności Moodle

> Analiza statyczna kodu repozytorium. Dokument nie potwierdza działania na żywej instancji Moodle ani importu MBZ.

## Granice architektury

Model źródłowy ma postać `Course → Section → Activity`. Loader, plan publikacji REST i wtyczka `local_magicmoodle` tworzą ścieżkę publikacji. Nie jest ona równoważna eksportowi ani importowi kopii zapasowej MBZ.

## Macierz typów

| Typ | Źródło danych | Funkcja REST | Uwagi synchronizacji |
|---|---|---|---|
| `page` | Treść wskazana przez `ref` | `local_magicmoodle_create_activity` | Markdown renderowany do HTML |
| `label` | Treść wskazana przez `ref` | `local_magicmoodle_create_activity` | Markdown renderowany do HTML |
| `url` | `url.yaml` / YAML | `local_magicmoodle_create_activity` | Tylko bezwzględny HTTP/HTTPS bez danych użytkownika |
| `book` | `book.yaml` i pliki rozdziałów | `local_magicmoodle_create_book` | `--state-file` mapuje identyfikatory rozdziałów |
| `assignment` | `assignment.yaml`, opcjonalny Markdown | `local_magicmoodle_create_assignment` | Synchronizacja ograniczona do jawnie zarządzanych pól |
| `quiz` | `quiz.yaml` i GIFT | `local_magicmoodle_create_quiz` | `--state-file`; zmiana pytań istniejącego quizu jest blokowana |
| `file` | Plik Base64, maks. 5 MiB | `local_magicmoodle_create_resource` | `--state-file` przechowuje mapowanie i SHA-256 |
| `glossary` | `glossary.yaml` | `local_magicmoodle_create_glossary` | `--state-file` mapuje wpisy na identyfikatory Moodle |

## Kontrakty wspólne

- Kurs jest wyszukiwany lub tworzony przez standardowe funkcje Moodle `core_course_get_courses_by_field` i `core_course_create_courses`.
- Sekcje są aktualizowane przez `local_magicmoodle_update_section`; numeracja sekcji od zera wymaga potwierdzenia na docelowej instancji.
- Identyfikator `idnumber` powinien być stabilny dla kursu, sekcji, typu i `ref`, aby ponowienie publikacji nie tworzyło duplikatów.
- Manifest wiąże stan z adresem witryny i tożsamością kursu. Nie może przechowywać tokenu dostępu.
- Dla Book, Glossary, Resource i Quiz brak `--state-file` powinien zatrzymać publikację przed wykonaniem zmian.

## Ograniczenia poszczególnych typów

### Book
Wtyczka obsługuje maksymalnie 200 rozdziałów i łącznie 5 MiB treści. Pierwszy rozdział nie może być podrozdziałem. Trzeba testować zmianę kolejności, usuwanie i ponowne dodawanie rozdziałów.

### Assignment
Ponowna publikacja nie może usuwać przesłanych prac, ocen ani ustawień, których źródło nie zarządza. Test integracyjny powinien sprawdzić ochronę tych danych.

### Quiz
GIFT jest walidowany przed wysłaniem; limit wynosi 2 MiB i 1–250 pytań. Dla istniejącego quizu nie wolno bezpiecznie nadpisywać pytań bez osobnego mechanizmu wersjonowania, z uwagi na próby i historię ocen.

### Resource
Plik ma rozmiar 1 B–5 MiB. Należy testować nazwy Unicode, kolizje nazw i aktualizację zawartości z kontrolą SHA-256.

### Glossary
Obsługiwane jest 1–500 haseł z polami `term`, `definition` i stabilnym `source_id`. Format HTML wymaga potwierdzenia sanitacji w docelowej wersji Moodle.

## Plan weryfikacji

1. Sprawdzić payload i stabilny `idnumber` dla każdego typu.
2. Porównać parametry Pythona z `db/services.php` i `execute_parameters()` w PHP.
3. Potwierdzić, że błędna konfiguracja zatrzymuje publikację przed pierwszym wywołaniem REST.
4. Testować ponowienie publikacji, manifest z innego hosta/kursu i przerwanie w połowie.
5. Zweryfikować synchronizację Book, Glossary i Resource oraz ochronę prac i ocen Assignment i Quiz.
6. Uruchomić testy na czystej instancji Moodle 4.1 z wtyczką i kontem o minimalnych uprawnieniach.
7. Osobno wykonać eksport kopii i import MBZ.

## Status potwierdzenia

Powyższe ustalenia wynikają z analizy statycznej loadera, publikatora, deklaracji usług i klas PHP. Nie wykonano testu na działającym Moodle 4.1 ani próby importu MBZ. Każde takie potwierdzenie wymaga zapisu wersji Moodle i PHP, konfiguracji wtyczki oraz logu testu.

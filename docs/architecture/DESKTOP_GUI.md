# DesktopGUI — PySide6

## Status

Pierwszy klient desktopowy korzystający ze wspólnej warstwy aplikacyjnej `CourseApplicationService`.

## Instalacja i uruchomienie

```bash
python -m pip install -e ".[desktop]"
MAGIC_MOODLE_COURSES=./courses magic-moodle-desktop
```

Opcjonalna zmienna `MAGIC_MOODLE_EXPORTS` wskazuje domyślny katalog eksportu. Okno dialogowe zapisu pozwala użytkownikowi wybrać inną lokalizację.

## Zakres pierwszej wersji

- lista kursów i odświeżanie;
- podgląd szczegółów;
- walidacja kursu;
- walidacja banku pytań GIFT;
- eksport manifestu JSON;
- eksport banku pytań do Moodle XML.

Wersja ta jest klientem inspekcyjno-eksportowym. Nie zawiera jeszcze edytora YAML/Markdown, tworzenia kursów, publikacji Moodle ani synchronizacji wieloużytkownikowej.

## Granice architektoniczne

- Qt jest importowane dopiero przy uruchomieniu DesktopGUI;
- logika kursu i walidacji pozostaje w `magic_moodle.application` oraz istniejącym rdzeniu;
- tokeny Moodle i sekrety nie są przechowywane przez interfejs;
- manifest JSON pozostaje formatem pośrednim, nie kopią MBZ;
- eksport Moodle XML nie oznacza publikacji kursu na serwerze.

Operacje są obecnie wykonywane synchronicznie. Przed dodaniem generowania dużych kursów i zadań sieciowych należy przenieść długotrwałe operacje do `QThreadPool`/workerów i raportować postęp bez blokowania głównego wątku Qt.

## Dalszy rozwój

1. edytor wersji roboczej z walidacją w czasie edycji;
2. historia zmian i kontrola konfliktów;
3. podgląd planu publikacji Moodle oraz jawne potwierdzenie;
4. kolejka zadań w tle i anulowanie bez naruszenia spójności;
5. testy GUI z Qt Test i uruchomieniem w trybie offscreen;
6. pakietowanie dla Windows, macOS i Linux.

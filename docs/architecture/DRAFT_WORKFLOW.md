# Przepływ wersji roboczej kursu

## Zasada architektoniczna

Wszystkie interfejsy korzystają z `CourseDraftService` i kanonicznego modelu `Course`. Nie powinny tworzyć własnych formatów zmian ani modyfikować bezpośrednio plików YAML kursu podczas edycji.

## Cykl pracy

1. Użytkownik wybiera kurs i tworzy wersję roboczą.
2. Usługa zapisuje identyfikator UUID, rewizję początkową i skrót bazowego modelu kursu.
3. Interfejs pobiera podgląd i prezentuje edytowalne pola.
4. Zapis wysyła zmiany wraz z `expected_revision`.
5. Usługa sprawdza rewizję, aktualność kursu źródłowego i dozwolone identyfikatory sekcji/aktywności.
6. Zmiany są atomowo zapisywane w `.magic_moodle/drafts/`.
7. Podgląd nakłada zmiany na model w pamięci i uruchamia walidator.

## Zakres interfejsów

- WebUI: nazwa kursu, nazwa skrócona, opis, nazwy sekcji i aktywności.
- DesktopGUI: nazwa kursu, nazwa skrócona, opis i nazwy sekcji.
- API v1: te same pola co usługa aplikacyjna, bez odrębnej logiki domenowej.
- TUI i AndroidGUI: kolejne adaptery mogą użyć tego samego kontraktu.

## Konflikty

- Nieaktualna rewizja wersji roboczej: konflikt rewizji.
- Zmieniony model kursu źródłowego: konflikt bazowego skrótu.
- Nieznany identyfikator sekcji lub aktywności: błąd walidacji zmian.

Interfejs powinien odświeżyć podgląd lub poprosić o utworzenie nowej wersji roboczej. Nie powinien po cichu nadpisywać nowszych zmian.

## Granica bezpieczeństwa

Wersja robocza nie jest opublikowanym kursem. Aktualny mechanizm nie zapisuje zmian do `course.yaml`, `section.yaml` ani zasobów aktywności. Zatwierdzanie wymaga osobnego etapu: transakcyjnego zapisu, kopii zapasowej, ponownego wczytania, walidacji i możliwości wycofania.

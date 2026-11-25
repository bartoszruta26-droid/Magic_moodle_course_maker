# Analiza źródeł Markdown i modelu kursu Moodle

**Data:** 2026-11-25  
**Gałąź robocza:** `feature/unified-markdown-renderer`  
**Cel:** określenie rzeczywistego formatu źródeł kursów i zasad importu do modelu `Course`.

## 1. Kurs neurologiczny — źródło spisu treści i treści

Katalog `courses/05-badanie-neurologiczne/` zawiera:
- `course.md` — spis treści i opis kursu;
- `1_1_podstawowe_pojecia_i_definicje.md`;
- `1_2_anatomia_funkcjonalna_ukladu_nerwowego.md`;
- `1_3_fizjologia_funkcji_neurologicznych.md`;
- `1_4_cele_i_zasady_badania_neurologicznego.md`;
- `1_5_przygotowanie_do_badania.md`.

W katalogu nie ma obecnie `course.yaml`, `sections/` ani plików `section.yaml`. Zatem bieżący `load_course()` nie może bezpośrednio wczytać tego kursu.

Spis treści ma około 42,9 kB, obejmuje 16 modułów i 155 podrozdziałów. Dostępnych jest pięć plików treści modułu 1 (1.1–1.5). Oznacza to, że importer musi rozróżniać:
1. pozycje spisu treści opisujące planowany zakres;
2. istniejące pliki z opracowaną treścią;
3. pozycje, dla których plik treści jeszcze nie istnieje.

Nie wolno tworzyć pustych aktywności Moodle dla niezrealizowanych tematów bez jawnej decyzji autora. Raport importu powinien wykazać brakujące pliki, a tryb ścisły powinien zatrzymać eksport, jeśli wymagane treści są niekompletne.

## 2. Istniejący model kursu — przykład MED.10

Kurs `courses/03-kurs-masazysta-med10/` reprezentuje docelowy format repozytorium:
- `course.yaml` opisuje metadane kursu, język, format i sekcje;
- `sections/<slug>/section.yaml` zawiera nazwę sekcji i uporządkowaną listę modułów;
- aktywność Book ma własny katalog i `book.yaml`;
- `book.yaml` wskazuje rozdziały przez `chapters[].content_file`;
- aktywności Quiz i Assignment mają własne konfiguracje i pliki treści.

Przykładowa sekcja MED.10 zawiera Book, Quiz i Assignment. Book zachowuje hierarchię rozdziałów i podrozdziałów przez `subchapter: false/true`. Jest to model bardziej szczegółowy niż pojedynczy plik Markdown.

## 3. Różnice wymagające adaptera źródłowego

| Obszar | Kurs neurologiczny | Model MED.10 / loader |
|---|---|---|
| Metadane kursu | `course.md` | `course.yaml` |
| Sekcje | nagłówki `## Moduł N` w spisie | katalogi z `section.yaml` |
| Tematy | pliki `N_N_*.md` | aktywności Book/Page |
| Podrozdziały | nagłówki Markdown w treści | wpisy Book `chapters[]` |
| Quiz | nie wynika automatycznie ze spisu | jawny katalog Quiz i plik GIFT |
| Zadanie | nie wynika automatycznie ze spisu | jawny katalog Assignment |
| Stan treści | część plików może nie istnieć | loader wymaga wskazanych zasobów |

Nie należy rozszerzać obecnego loadera o heurystyki rozpoznające wszystkie możliwe układy nazw plików. Lepszy jest jawny adapter `import-md-course`, który:
1. odczytuje spis treści;
2. rozpoznaje moduły i podrozdziały;
3. wiąże pozycje z istniejącymi plikami na podstawie numeracji i metadanych;
4. tworzy model pośredni;
5. generuje katalog `course.yaml` + `sections/` z bezpiecznym serializerem YAML;
6. tworzy raport rozbieżności i brakujących treści;
7. nie generuje quizów z samego tytułu lub tekstu.

## 4. Proponowana reguła mapowania

- Kurs → jeden obiekt `Course`.
- Moduł główny → `Section`.
- Plik tematu → `Activity(kind="book")`, jeżeli ma hierarchię rozdziałów; w przeciwnym razie `page` lub `book` według jawnej konfiguracji.
- Nagłówki wewnątrz pliku → rozdziały/podrozdziały Book; nie tworzyć osobnej aktywności dla każdego nagłówka.
- Pytania i klucze odpowiedzi → jawne źródło GIFT albo jawny format quizu w metadanych.
- Zadania, słownik, pliki i adresy URL → osobne typy aktywności tylko wtedy, gdy istnieje ich jawna definicja.
- Pliki graficzne i inne załączniki → rejestr plików źródłowych z kontrolą ścieżek, MIME, sum kontrolnych i późniejszym przypisaniem do obszaru plików Moodle.

## 5. Konsekwencje dla wspólnego renderera

Materiały medyczne wykorzystują:
- nagłówki wielu poziomów i numerowane tytuły;
- listy punktowane i numerowane;
- tabele;
- cytaty i wyróżnienia;
- odnośniki bibliograficzne oraz przypisy;
- fragmenty kodu i potencjalnie wzory matematyczne;
- obrazy i pliki z katalogów zasobów.

Wspólny renderer powinien obsługiwać semantyczne HTML5 i oczyszczać surowy HTML. Nie może jednak samodzielnie rozstrzygać lokalizacji plików ani zmieniać ścieżek względnych — to zadanie późniejszego etapu obsługi zasobów Moodle.

## 6. Kryteria importu i walidacji

Importer powinien tworzyć raport z polami:
- liczba modułów w spisie treści;
- liczba znalezionych plików treści;
- liczba plików nieprzypisanych;
- liczba pozycji bez pliku;
- liczba wykrytych nagłówków i tabel;
- liczba obrazów i linków;
- liczba jawnych pytań i zadań;
- lista ostrzeżeń oraz błędów z numerem pliku i wiersza.

Eksport produkcyjny powinien wymagać braku błędów krytycznych. Braki treści mogą być ostrzeżeniami wyłącznie wtedy, gdy autor wyraźnie dopuści częściowy eksport.

## 7. Wniosek

Kurs neurologiczny i MED.10 reprezentują dwa różne, lecz kompatybilne poziomy organizacji treści. MED.10 jest wzorcem docelowego modelu Moodle, a kurs neurologiczny jest źródłem Markdown wymagającym adaptera importowego. Właściwa kolejność prac to: wspólny renderer Markdown → adapter spisu treści i plików → model pośredni → walidacja → publikacja aktywności → oficjalny backup Moodle.

Dokument nie oznacza jeszcze wykonania importu ani wygenerowania MBZ.

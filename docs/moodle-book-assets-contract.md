# Kontrakt synchronizacji zasobów Moodle Book

## Cel

Importer Markdown zapisuje zasoby lokalne w katalogu `chapters/assets/`. Publikator musi przesłać bajty tych plików do Moodle File API w obszarze `mod_book/chapter`, z `itemid` równym identyfikatorowi rozdziału i kontekstem modułu Book. Samo skopiowanie plików do katalogu kursu nie publikuje ich w Moodle.

## Kontrakt REST

Rozszerzenie istniejącej funkcji `local_magicmoodle_create_book` (bez tworzenia konkurencyjnego endpointu):

- Każdy element `chapters[]` otrzymuje opcjonalną listę `files[]`.
- Element `files[]` zawiera dokładnie:
  - `filepath`: ścieżka katalogu wewnątrz obszaru rozdziału, zaczynająca się i kończąca ukośnikiem, np. `/assets/diagramy/`;
  - `filename`: pojedyncza nazwa pliku, bez separatorów i segmentów specjalnych;
  - `contentbase64`: zawartość binarna zakodowana base64.
- Identyfikacja rozdziału pozostaje oparta na istniejącym `sourceid` i mapowaniu `chapterids`. Nie wolno wiązać plików wyłącznie z kolejnością rozdziałów.
- Limity początkowe: maksymalnie 100 plików na rozdział, 2 MiB na plik, 5 MiB łącznie na aktywność (pliki i treść rozdziałów); limity należy egzekwować po stronie Python i PHP.

## Zapis w Moodle

Dla każdego pliku:
- `contextid`: kontekst modułu Book (`context_module::instance($cmid)`);
- `component`: `mod_book`;
- `filearea`: `chapter`;
- `itemid`: identyfikator rozdziału;
- `filepath` i `filename`: wartości po walidacji;
- zapis przez `get_file_storage()->create_file_from_string()`.

Przy aktualizacji rozdziału:
1. zweryfikować, że mapowany rozdział należy do aktualnej książki;
2. zweryfikować całą listę plików przed rozpoczęciem modyfikacji;
3. zastąpić zarządzany zestaw plików tego rozdziału, usuwając stare pliki z obszaru `chapter`, aby nie pozostawić osieroconych zasobów;
4. zapisać nowy zestaw i treść rozdziału w tej samej operacji transakcyjnej, o ile gwarantuje to używana wersja Moodle File API;
5. nie usuwać plików innych rozdziałów ani innych komponentów.

Przed wdrożeniem należy potwierdzić zachowanie transakcyjne `file_storage` na wspieranej wersji Moodle. Jeśli operacje na plikach nie podlegają rollbackowi, implementacja musi przygotować i zweryfikować nowy zestaw przed usunięciem poprzedniego oraz obsłużyć kompensację błędu.

## Odwołania w HTML

Po renderowaniu i sanitacji Markdown publikator zamienia wyłącznie lokalne odwołania wskazujące pliki dołączone do bieżącego rozdziału:
- atrybuty `src`, `href`, `poster`;
- CSS `url(...)` w atrybutach `style` i elementach `<style>`.

Adresy plików zmieniają się z `assets/...` na `@@PLUGINFILE@@/assets/...`. Należy zachować query i fragment URL. Nie wolno przepisywać adresów `http:`, `https:`, `data:`, kotwic ani odwołań do plików, których nie ma w przesyłanym zestawie. Nie wykonuje się globalnego zamieniania tekstu `assets/` w całym HTML.

## Walidacja bezpieczeństwa

Python:
- odczyt binarny, bez dekodowania UTF-8;
- odrzucenie ścieżek bezwzględnych, `..`, backslashy, NUL i symlinków na każdym poziomie;
- sprawdzenie containment względem katalogu `assets`;
- limity liczby i rozmiaru plików przed base64;
- base64 ASCII bez łamania linii.

PHP:
- `filepath` musi być ścieżką względną obszaru rozdziału, bez pustych, `.`, `..` i zakodowanych separatorów;
- `filename` musi być pojedynczym bezpiecznym segmentem;
- rygorystyczne `base64_decode(..., true)`, kontrola rozmiaru po dekodowaniu;
- brak duplikatów par `filepath+filename`;
- odrzucenie nieobsługiwanych MIME/plików? Nie wprowadzać arbitralnej listy rozszerzeń; Moodle File API i limity serwera pozostają nadrzędne;
- wymagane `mod/book:edit` w kontekście modułu.

## Testy wymagane przed scaleniem

- tworzenie rozdziału z obrazem i plikiem binarnym;
- aktualizacja rozdziału: usunięcie starego zasobu, dodanie nowego, zachowanie plików innych rozdziałów;
- wznowienie publikacji z istniejącym `chapterids`;
- niepoprawny base64, za duży plik, zbyt wiele plików, duplikaty nazw, path traversal, backslash, pusty filepath;
- zachowanie zewnętrznych URL, `data:`, kotwic, query i fragmentów;
- potwierdzenie w Moodle, że odwołania `@@PLUGINFILE@@` są renderowane i pobierane;
- test utworzenia i aktualizacji aktywności w rzeczywistym Moodle oraz eksport/restore kursu.

Brak testowego Moodle oznacza, że można potwierdzić jedynie testy jednostkowe i statyczną zgodność kontraktu, a nie działanie plików po publikacji ani poprawność backupu MBZ.

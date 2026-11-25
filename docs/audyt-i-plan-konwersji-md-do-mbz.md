# Założenia audytu i plan prac: konwersja Markdown do kursu Moodle (MBZ)

**Repozytorium:** `bartoszruta26-droid/Magic_moodle_course_maker`  
**Dokument:** założenia audytu i plan techniczny  
**Status:** przyjęte jako punkt wyjścia do dalszych prac; implementacja i testy end-to-end pozostają do wykonania.

## 1. Cel

Zbudować jeden spójny, powtarzalny i testowalny proces przekształcania źródłowych materiałów kursowych Markdown (`.md`) w kompletny kurs Moodle, który można:
- opublikować na instancji Moodle;
- wyeksportować jako prawidłową kopię zapasową Moodle `.mbz`;
- odtworzyć na docelowej instancji Moodle;
- przechowywać i wersjonować w GitHub wraz z materiałami źródłowymi, manifestem i raportem walidacji.

Nie uznaje się za równoważne: wygenerowania HTML, wygenerowania manifestu JSON, wywołania Moodle REST API i utworzenia rzeczywistej kopii zapasowej `.mbz`. Są to odrębne rezultaty.

## 2. Zakres funkcjonalny

### 2.1. Wejście

Proces powinien obsługiwać:
- główny plik spisu treści kursu (np. `course.md`);
- pliki rozdziałów i podrozdziałów;
- metadane i konfigurację kursu;
- lokalne grafiki, dokumenty, pliki audio i wideo;
- odnośniki wewnętrzne i zewnętrzne;
- opcjonalne pliki konfiguracyjne sekcji i aktywności.

Należy zachować kolejność, hierarchię, nazwy, numerację i relacje pomiędzy elementami kursu.

### 2.2. Markdown → HTML

Wdrożyć jeden kanoniczny konwerter oparty na utrzymywanej bibliotece Markdown, zamiast utrzymywać kilka niezależnych, niezgodnych implementacji.

Wymagane elementy:
- nagłówki i hierarchia treści;
- akapity, wyróżnienia, cytaty;
- listy uporządkowane, nieuporządkowane i zagnieżdżone;
- tabele;
- bloki i fragmenty kodu;
- odnośniki i obrazy;
- przypisy i rozszerzenia używane w materiałach kursowych;
- polskie znaki i UTF-8;
- wzory matematyczne, jeśli występują w źródle;
- stabilne kotwice nagłówków i linki wewnętrzne.

Konwerter ma mieć jawnie określoną politykę obsługi surowego HTML i sanitacji. Nie wolno bezwarunkowo przepuszczać niezaufanego HTML ani usuwać prawidłowych elementów dydaktycznych. Wynik powinien być semantycznym HTML zgodnym z możliwościami edytora i modułów docelowej wersji Moodle.

### 2.3. Model pośredni kursu

Wprowadzić lub dopracować niezależny od formatu wyjściowego model pośredni (IR), który opisuje:
- kurs i jego metadane;
- sekcje kursu;
- rozdziały i podrozdziały;
- aktywności i zasoby;
- treści HTML;
- pliki i ich powiązania;
- identyfikatory, kolejność, widoczność i ustawienia;
- zależności między elementami.

Parser źródła nie powinien bezpośrednio budować XML backupu ani wywoływać API Moodle. Oddzielenie parsowania, modelowania i generatorów ułatwi testowanie i dodawanie kolejnych formatów wyjściowych.

### 2.4. Mapowanie na Moodle

Rozdzielić pojęcia sekcji kursu, jednostki treści i aktywności Moodle. Mapowanie powinno być jawne, konfigurowalne i walidowane.

Docelowo uwzględnić co najmniej:
- Page — pojedyncza strona dydaktyczna;
- Book — uporządkowany materiał wielostronicowy;
- URL — odnośnik;
- File — pojedynczy plik do pobrania;
- Folder — zestaw plików;
- Label — etykieta/treść w sekcji;
- Quiz — sprawdzian i pytania;
- Assignment — zadanie;
- Glossary — słownik;
- Forum — forum, jeśli przewiduje je konfiguracja kursu.

Nie generować pytań sprawdzających przez mechaniczne przekształcanie nagłówków lub zdań opisowych. Pytania, odpowiedzi, punktacja, informacja zwrotna i typ pytania muszą pochodzić z jawnych danych źródłowych albo z osobnego, zatwierdzonego procesu autorskiego. Brak danych nie może skutkować wymyślaniem poprawnych odpowiedzi.

### 2.5. Eksport MBZ

Zaimplementować rzeczywisty generator kopii zapasowej Moodle, zgodny z formatem backupu dla jawnie wspieranych wersji Moodle.

Generator musi uwzględniać wymagane elementy formatu, w szczególności:
- strukturę archiwum i pliki XML wymagane przez backup Moodle;
- manifest i metadane kopii;
- opis kursu, sekcje i moduły aktywności;
- konfigurację instancji modułów;
- pliki kursu, ich metadane, obszary plików i referencje;
- spójne identyfikatory i powiązania;
- kodowanie, ścieżki i wymagane wartości kontrolne.

Nie zakładać, że dowolny ZIP zawierający HTML i XML jest plikiem MBZ. Preferować wykorzystanie oficjalnych mechanizmów backupu Moodle lub zweryfikowanej implementacji formatu, jeśli pozwalają one zachować zgodność i nie dublować logiki platformy. Każda obsługiwana wersja Moodle musi być określona i testowana.

### 2.6. Pliki i multimedia

Wymagane:
- wykrywanie lokalnych zasobów wskazanych w Markdown;
- kopiowanie ich do odpowiednich obszarów wynikowych;
- zachowanie nazw, typów MIME i relacji z aktywnościami;
- poprawne przekształcanie ścieżek i odnośników;
- wykrywanie brakujących plików i osieroconych zasobów;
- raportowanie duplikatów i potencjalnych kolizji nazw;
- kontrola rozmiaru i bezpieczeństwa plików.

Nie pozostawiać w HTML ścieżek lokalnych z komputera autora, które nie będą dostępne po imporcie kursu.

## 3. Architektura docelowa

Preferowany jest jeden kanoniczny rdzeń Python z rozdzielonymi warstwami:

1. **Loader** — odczyt plików i konfiguracji.
2. **Parser** — parsowanie Markdown i metadanych.
3. **Course IR** — walidowany model pośredni.
4. **Renderer HTML** — generowanie semantycznego HTML.
5. **Activity mapper** — mapowanie IR na sekcje, zasoby i aktywności Moodle.
6. **MBZ exporter** — generowanie kopii zapasowej Moodle.
7. **Moodle publisher** — opcjonalna publikacja przez Moodle REST API; oddzielna od eksportu MBZ.
8. **Validator** — walidacja strukturalna, semantyczna i integracyjna.
9. **GitHub publisher** — zapis artefaktów, manifestów i raportów.

Historyczne skrypty PHP/C należy zinwentaryzować. Nie rozwijać równoległych implementacji logiki konwersji. Jeśli są potrzebne ze względu na zgodność, powinny być cienkimi interfejsami do wspólnego rdzenia albo zostać jawnie oznaczone jako przestarzałe po sprawdzeniu zależności.

## 4. GitHub i artefakty

Repozytorium powinno przechowywać:
- źródła kursu;
- kod konwertera i testy;
- schemat lub wersję modelu pośredniego;
- manifest eksportu;
- raport walidacji;
- sumy kontrolne SHA-256;
- plik MBZ tylko wtedy, gdy jego rozmiar i polityka repozytorium na to pozwalają.

Duże pliki wynikowe mogą być publikowane jako artefakty GitHub Actions lub w wydaniu (Release), zamiast bezwarunkowo trafiać do historii Git. Nie commitować sekretów, tokenów Moodle, danych użytkowników ani plików konfiguracyjnych zawierających hasła.

Każdy eksport powinien mieć jednoznaczny identyfikator przebiegu, datę, wersję konwertera, wersję Moodle, listę wejść i ich sumy kontrolne.

## 5. Walidacja i testy — warunek ukończenia

Samo przejście testów jednostkowych lub wygenerowanie pliku nie potwierdza poprawności eksportu.

Wymagane poziomy testów:

### 5.1. Testy jednostkowe
- parser Markdown;
- renderer HTML;
- obsługa polskich znaków;
- nagłówki, listy, tabele, kod, linki, obrazy i wzory;
- mapowanie typów aktywności;
- identyfikatory, kolejność i relacje;
- obsługa brakujących i nieprawidłowych danych.

### 5.2. Testy integracyjne
- kompletny kurs testowy od źródłowych MD do MBZ;
- weryfikacja struktury archiwum;
- kontrola XML względem wymagań odpowiedniej wersji Moodle;
- kompletność plików i odnośników;
- brak osieroconych lub brakujących zasobów.

### 5.3. Test end-to-end
1. Wygenerować MBZ z reprezentatywnego kursu testowego.
2. Zaimportować go na czystej, testowej instancji wspieranej wersji Moodle.
3. Zweryfikować kurs, sekcje, kolejność, aktywności, treści, pliki i multimedia.
4. Sprawdzić logi Moodle oraz błędy importu.
5. Wykonać ponowny eksport/import i sprawdzić stabilność wyniku.
6. Zachować raport i artefakt testowy.

W CI należy uruchamiać testy jednostkowe i integracyjne, a test importu przeprowadzać na kontrolowanej instancji Moodle. Wersja Moodle i środowisko testowe muszą być jawne.

## 6. Plan realizacji

### Etap 0 — inwentaryzacja
- ustalić faktyczną zawartość i wykorzystanie skryptów PHP, C i Python;
- odnaleźć wszystkie wejścia, wyjścia i punkty wywołania;
- przeanalizować PR #101 oraz zależności;
- uruchomić istniejące testy i zapisać stan bazowy;
- nie scalać PR ani nie usuwać historycznych skryptów przed oceną ich użycia.

### Etap 1 — parser i HTML
- wybrać bibliotekę Markdown;
- zdefiniować rozszerzenia i politykę sanitacji;
- przygotować zestaw plików wzorcowych i testy porównawcze;
- zapewnić prawidłowy HTML i zachowanie zasobów.

### Etap 2 — model pośredni i aktywności
- zdefiniować schemat IR;
- opracować walidację;
- zdefiniować jawne mapowanie sekcji i aktywności;
- przygotować testy dla wszystkich wspieranych typów.

### Etap 3 — generator MBZ
- wybrać i udokumentować strategię zgodności z Moodle;
- wdrożyć strukturę backupu i obsługę plików;
- walidować archiwum przed uznaniem eksportu za udany.

### Etap 4 — import testowy i CI
- uruchomić testową instancję Moodle;
- automatyzować import i weryfikację;
- raportować błędy i zachowywać artefakty.

### Etap 5 — GitHub i publikacja
- przygotować manifest, raport i sumy kontrolne;
- zintegrować eksport z GitHub Actions;
- rozdzielić artefakty testowe, wydania i źródła;
- udokumentować sposób ręcznego i automatycznego uruchamiania.

## 7. Kryteria akceptacji

Prace można uznać za zakończone dopiero, gdy:
- jeden kanoniczny proces obsługuje cały przepływ MD → HTML → IR → aktywności → MBZ;
- wszystkie wspierane elementy Markdown są objęte testami;
- hierarchia i kolejność kursu są zachowane;
- typy aktywności są tworzone zgodnie z jawną konfiguracją;
- pytania testowe nie są generowane przez zgadywanie odpowiedzi;
- multimedia i pliki są dostępne po imporcie;
- MBZ przechodzi walidację i import na wspieranej wersji Moodle;
- raport potwierdza wynik testu end-to-end;
- proces jest powtarzalny i nie ujawnia sekretów;
- dokumentacja opisuje ograniczenia i wspierane wersje.

## 8. Zasady prowadzenia prac

- Zmiany wykonywać na osobnej gałęzi roboczej i przedstawiać w PR.
- Nie scalać do `main` przed przejściem wymaganych testów.
- Nie deklarować poprawności MBZ na podstawie samego utworzenia ZIP/XML.
- Nie usuwać istniejących funkcji bez analizy użycia i testów regresji.
- Każdy etap kończyć raportem: zmienione pliki, testy, wyniki, znane ograniczenia i następny krok.
- Przy niepowodzeniu testu nie maskować błędu ani nie oznaczać etapu jako ukończonego.

## 9. Wstępne obserwacje z audytu

Wstępny przegląd repozytorium wskazał na rozdzielenie eksportu manifestu JSON, publikacji przez Moodle REST API i eksportu banku pytań. Nie są to same w sobie mechanizmy pełnego backupu kursu MBZ.

Wskazano również ograniczenia uproszczonej konwersji Markdown oraz brak potwierdzonego testu pełnej ścieżki MD → MBZ → import Moodle. PR #101 wymaga ponownej, aktualnej analizy przed wykorzystaniem lub scaleniem.

Powyższe obserwacje należy zweryfikować podczas Etapu 0 na aktualnym stanie gałęzi i testów. Niniejszy dokument zapisuje wymagania i plan prac, a nie deklaruje, że implementacja została już wykonana lub że wszystkie ustalenia zostały potwierdzone testami.

## 10. Pierwsze zadanie do wykonania

Rozpocząć od Etapu 0: sporządzić inwentarz skryptów, modułów, workflow, testów i PR #101; ustalić rzeczywiste wywołania oraz aktualny stan testów. Na tej podstawie przygotować listę konkretnych zmian w kolejności zależności, bez przedwczesnego przepisywania lub usuwania kodu.

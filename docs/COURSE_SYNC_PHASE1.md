# Etap 1 — synchronizacja treści aktywności Moodle

## Zakres tej zmiany

Ponowna publikacja aktywności Page, Label i URL działa jako aktualizacja istniejącego obiektu, a nie jako operacja „znaleziono, więc pomiń”.

- Dopasowanie odbywa się po stabilnym idnumber; dotychczasowa ścieżka awaryjna po nazwie i sekcji pozostaje objęta kontrolą konfliktów.
- Aktualizacja zachowuje identyfikator modułu kursu (cmid) oraz identyfikator instancji modułu (instanceid).
- Zmiana nazwy i treści Page/Label/URL trafia do istniejącego modułu.
- URL nadal wymaga bezwzględnego adresu HTTP/HTTPS bez danych logowania.
- Zapis i przebudowa cache kursu odbywają się w transakcji delegowanej.
- Nie są tworzone nowe moduły przy ponownej publikacji istniejącej aktywności.

## Zakres jeszcze nieobjęty aktualizacją

W wersji 0.1.11 endpointy Book, Glossary, Quiz, Assignment i Resource nadal zapewniają rozpoznawanie obiektów i brak duplikatów, ale nie synchronizują jeszcze ich treści. Szczególnie ostrożnie należy potraktować Quiz: zastąpienie banku pytań musi uwzględniać próby quizu, użycie pytań w innych kontekstach, identyfikatory pytań i historię ocen. Nie wolno usuwać i odtwarzać pytań bez sprawdzenia tych zależności.

## Kontrakt docelowej synchronizacji

Dla każdej aktywności publikator powinien otrzymać jeden z wyników:

- created — utworzono nowy obiekt;
- updated — zaktualizowano istniejący obiekt, zachowując jego identyfikatory;
- unchanged — zdalny stan odpowiada lokalnemu;
- conflict — wykryto zmianę po obu stronach lub niejednoznaczne dopasowanie;
- failed — operacja nie została zatwierdzona.

Manifest wznowienia powinien przechowywać identyfikatory zdalne i skróty stanu źródłowego oraz zdalnego. Nie może sam w sobie być traktowany jako dowód, że zdalna treść nadal odpowiada lokalnej. Po awarii publikator ponownie odczytuje stan z Moodle, oblicza różnicę i dopiero wtedy podejmuje zapis.

## Kryteria bezpieczeństwa

1. Nie zmieniać cmid, instanceid ani idnumber istniejącej aktywności.
2. Nie usuwać ręcznie dodanych aktywności, pytań, rozdziałów, haseł ani plików.
3. Nie nadpisywać pól Moodle, których lokalny model nie definiuje.
4. Przy niejednoznacznym dopasowaniu lub konflikcie zatrzymać daną aktywność przed zapisem.
5. Każdy endpoint aktualizacji musi mieć uprawnienia, walidację kontekstu, blokadę Moodle i transakcję.
6. Testować wycofanie po błędzie pośrednim na instancji Moodle, a nie wyłącznie na atrapach HTTP.

## Kolejne podetapy

1. Book — aktualizacja metadanych i rozdziałów przez API modułu; bez bezpośredniego SQL do tabel modułu.
2. Glossary — synchronizacja haseł przez API modułu, stabilne mapowanie wpisów i zachowanie ręcznych wpisów.
3. Assignment i Resource — aktualizacja ustawień i plików przez API modułów oraz File API.
4. Quiz — porównanie pytań i ustawień, z ochroną prób, historii ocen i współdzielonych pytań.
5. Odczyt zdalnego stanu, raport różnic i kontrolowana polityka konfliktów.
6. Testy integracyjne i współbieżności na Moodle 4.1 oraz wersji docelowej.

## Ograniczenia walidacji

Testy jednostkowe i kontrola składni nie potwierdzają zachowania update_moduleinfo na konkretnej instalacji Moodle. Weryfikacja transakcji, blokad, zdarzeń modułów, zachowania File API oraz aktualizacji treści wymaga integracyjnego środowiska Moodle.
## Weryfikacja API Book i Glossary — Moodle 4.1

### Book

- Oficjalny interfejs modułu udostępnia book_add_instance() i book_update_instance() dla rekordu aktywności oraz funkcje odczytu rozdziałów. Lista funkcji Book w dokumentacji Moodle 4.1 nie udostępnia publicznego API CRUD rozdziałów.
- Aktualny endpoint tworzy rozdziały przez Moodle DML (insert_record do book_chapters), emituje zdarzenie mod_book\\event\\chapter_created i wywołuje book_preload_chapters(). Jest to obejście braku publicznego API rozdziałów, a nie wywołanie nieistniejącego endpointu.
- Przed implementacją aktualizacji trzeba dodać stabilny source_id dla każdego rozdziału i zapisać mapowanie source_id → chapter id w manifeście. Tytuł i kolejność nie są stabilnymi kluczami. Nie wolno usuwać rozdziałów spoza mapowania ani kasować załączników/plików bez jawnej reguły.
- Aktualizacja metadanych samej książki powinna przechodzić przez update_moduleinfo() / book_update_instance(); synchronizacja rozdziałów musi używać transakcyjnego DML, zdarzeń modułu i odświeżenia TOC. Konieczny jest test integracyjny na Moodle 4.1.8.

### Glossary

- Moodle 4.1 udostępnia natywną klasę mod_glossary\\external\\update_entry z metodą execute(entryid, concept, definition, definitionformat, options). Jest to właściwa ścieżka aktualizacji istniejącego hasła; moduł ma również glossary_edit_entry() do tworzenia i aktualizacji wpisu.
- Aktualny endpoint tworzenia używa mod_glossary_external::add_entry(), a więc tworzenie korzysta z natywnego interfejsu modułu zamiast bezpośredniego INSERT do glossary_entries.
- Wpisy nie mają stabilnego idnumber odpowiadającego lokalnemu źródłu. Synchronizacja powinna wprowadzić jawny source_id i manifest source_id → entryid; przed aktualizacją należy potwierdzić, że wpis nadal należy do oczekiwanego glossaryid. Nie należy identyfikować wpisu wyłącznie po koncepcie, bo koncept jest edytowalny.
- Usuwanie wpisów musi być ograniczone do wpisów zarządzanych przez manifest; wpisy ręczne i wpisy bez mapowania pozostają nietknięte. Kategorie, aliasy, załączniki, zatwierdzenie i autorstwo wymagają zachowania, jeśli lokalny model ich nie definiuje.

### Źródła API

- Moodle 4.1 — Book: https://phpdoc.moodledev.io/4.1/dd/d03/group__mod__book.html
- Moodle 4.1 — Glossary: https://phpdoc.moodledev.io/4.1/d4/d48/group__mod__glossary.html
- Moodle 4.1 — Glossary update_entry: https://phpdoc.moodledev.io/4.1/d3/dcd/classmod__glossary_1_1external_1_1update__entry.html
- Moodle 4.1 — update_moduleinfo/get_moduleinfo_data: https://wimski.org/api/4.1/dc/da2/modlib_8php.html

## Etap 2 — Glossary (wdrażany)

### Zakres implementacji

- Każde hasło otrzymuje stabilny `sourceid`. Preferowane pole w lokalnym YAML to `source_id` (akceptowane jest również `id`).
- Dla zgodności ze starszymi kursami bez `source_id` publikator generuje identyfikator na podstawie znormalizowanego terminu. Taki identyfikator pozostaje stabilny tylko dopóki termin się nie zmienia; przy planowanej zmianie terminu należy jawnie ustawić `source_id`.
- Manifest w wersji 2 przechowuje mapowanie `sourceid → entryid` w rekordzie aktywności Glossary.
- Zmiana terminu lub definicji aktualizuje wpis przez natywne `\\mod_glossary\\external\\update_entry::execute`, zachowując `entryid`.
- Nowe hasła są dodawane przez `mod_glossary_external::add_entry()`; zwrócone identyfikatory są zapisywane w manifeście.
- Wpisy usunięte ze źródła nie są automatycznie kasowane w Moodle. Ich mapowania pozostają w manifeście, aby późniejsze przywrócenie źródłowego `source_id` nie utworzyło duplikatu.
- Jeśli istniejący słownik zawiera hasła, ale nie ma mapowania w manifeście, endpoint odmawia synchronizacji zamiast dopisywać duplikaty.
- Jeśli mapowany wpis ma załączniki lub pliki osadzone, endpoint odmawia automatycznej aktualizacji do czasu wdrożenia pełnej obsługi zachowania tych plików.
- Aktualizacja zachowuje aliasy, kategorie oraz ustawienia automatycznego linkowania, jeśli są włączone.

### Manifest i zmiany treści

Manifest v2 wiąże się z witryną Moodle, nazwą skróconą kursu i skrótem tożsamości aktywności (typ, stabilny `idnumber`, sekcja). Skrót treści jest aktualizowany po pomyślnym odnalezieniu tego samego kursu. Dzięki temu można ponownie opublikować zmienioną treść przy zachowaniu mapowań elementów podrzędnych. Zmiana tożsamości kursu lub aktywności nadal powoduje odrzucenie manifestu.

Manifest v1 jest migrowany do v2 tylko wtedy, gdy jego dotychczasowy skrót pełnego planu nadal pasuje. Starszy manifest bez mapowania haseł nie jest automatycznie uzupełniany przez zgadywanie.

### Zakres nadal otwarty

Book jest teraz synchronizowany w miejscu przez mapowanie `source_id → chapter id`. Aktualizacja zachowuje identyfikator rozdziału, pole `hidden`, `timecreated` i `importsrc`, a także ustawia nową kolejność, tytuł, treść i relację podrozdziału. Zmiana rozdziału zawierającego pliki osadzone jest odrzucana do czasu wdrożenia pełnej obsługi File API. Rozdziały usunięte ze źródła pozostają w Moodle i w mapowaniu manifestu — publikator nie kasuje danych automatycznie.

### Ograniczenia testów

Testy statyczne i jednostkowe nie potwierdzają jeszcze aktualizacji wpisów w działającym Moodle 4.1. W szczególności wymagane są testy rzeczywistego API `update_entry`, wycofania transakcji po błędzie pośrednim, aliasów/kategorii, załączników oraz współbieżności.


## Etap 3 — Book (wdrażany)

- Każdy rozdział ma stabilny `sourceid`; preferowane jest jawne pole `source_id` (akceptowane jest również `id`). W kursach starszych bez takiego pola publikator generuje identyfikator z tytułu. Zmiana tytułu wymaga jawnego `source_id`, jeśli ma zachować istniejący `chapterid`.
- Manifest v2 przechowuje mapowanie `sourceid → chapterid` w rekordzie aktywności Book.
- Istniejące rozdziały są aktualizowane przez Moodle DML w transakcji, z zachowaniem ich identyfikatorów i pól niezdefiniowanych lokalnie; emitowane jest zdarzenie `mod_book\\event\\chapter_updated`.
- Nowe rozdziały są dodawane, a mapowania zwracane i zapisywane w manifeście.
- Rozdziały usunięte ze źródła nie są automatycznie usuwane. Ich mapowania są zachowywane, aby późniejsze przywrócenie `source_id` ponownie wykorzystało ten sam obiekt.
- Jeśli istniejący Book zawiera rozdziały, ale nie ma mapowania w manifeście, endpoint odmawia synchronizacji zamiast tworzyć duplikaty.
- Jeśli mapowany rozdział ma pliki w obszarze `mod_book/chapter`, aktualizacja jest odrzucana. Wymagana jest obsługa edytora i File API dla plików osadzonych.

### Walidacja integracyjna Book

Wymagane testy na Moodle 4.1: aktualizacja treści i zmiana kolejności bez zmiany `chapterid`, zachowanie ukrycia rozdziału, zdarzenia `chapter_updated`, wycofanie po błędzie w drugim rozdziale, zachowanie plików (obecnie testowane przez fail-closed), oraz ponowienie publikacji po awarii z zachowaniem mapowania.


## Etap 4 — Assignment i Resource (wdrażany)

### Assignment

- Istniejące zadanie jest odnajdywane po stabilnym `idnumber` i aktualizowane przez `get_moduleinfo_data()` oraz `update_moduleinfo()`.
- Adapter używa maski `syncfields`, dzięki czemu aktualizuje wyłącznie pola jawnie zdefiniowane w źródle. Pozostałe ustawienia Moodle są pobierane z istniejącego modułu i zachowywane.
- Obsługiwane pola źródłowe: nazwa, opis, daty, ocena, typ przesyłania, limity plików, przycisk zatwierdzenia, oświadczenie o samodzielności i ukończenie aktywności.
- Adapter nigdy nie usuwa zgłoszeń ani ocen. Jeśli istnieją zgłoszenia studentów, zmiana aktywnych wtyczek przesyłania lub limitów plików jest odrzucana, gdy zmieniałaby konfigurację. Pozostałe jawnie zarządzane ustawienia mogą być aktualizowane.

### Resource

- Manifest przechowuje nazwę pliku i SHA-256 ostatnio opublikowanego pliku źródłowego.
- Przed aktualizacją endpoint weryfikuje, czy plik w Moodle nadal ma poprzedni skrót. Ręczna zmiana pliku, brak mapowania starszego zasobu albo konflikt nazwy pliku zatrzymują synchronizację.
- Podmiana odbywa się przez Moodle File API: bieżący obszar plików jest kopiowany do draft area, usuwany jest wyłącznie plik zarządzany przez źródło, a pozostałe pliki są zachowywane. Nowy plik zostaje ustawiony jako główny.
- Ustawienia wyświetlania i inne pola, których źródło nie definiuje, są zachowywane przez pobranie kanonicznych danych modułu przed aktualizacją.

### Ograniczenia i testy wymagane na Moodle 4.1

- Assignment: sprawdzić zmianę opisu, terminów, oceny i completion przy istniejących zgłoszeniach; potwierdzić, że próby, zgłoszenia i oceny pozostają nietknięte. Zweryfikować blokadę zmiany wtyczek i limitów po pojawieniu się zgłoszeń.
- Resource: sprawdzić podmianę pliku o tej samej i innej nazwie, zachowanie dodatkowych plików, sortowanie pliku głównego, konflikt po ręcznej zmianie pliku oraz rollback po błędzie zapisu.
- Testy CI kontrolują kontrakt, walidację, składnię PHP i logikę manifestu, ale nie zastępują integracyjnej instancji Moodle.

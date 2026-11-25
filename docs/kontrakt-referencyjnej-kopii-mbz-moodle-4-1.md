# Kontrakt referencyjnej kopii MBZ i testu odtworzenia — Moodle 4.1

**Status:** projekt techniczny do weryfikacji implementacyjnej  
**Zakres:** eksport kursu z modelu `Course → Section → Activity` do kopii Moodle `.mbz`  
**Wersja referencyjna:** Moodle 4.1 (`MOODLE_401_STABLE`)  
**Powiązany audyt:** [raport PR #101](raport-audytu-pr-101-md-do-mbz-2026-11-25.md)

## 1. Decyzja architektoniczna

Plik `.mbz` jest kopią zapasową utworzoną przez mechanizm kopii zapasowych Moodle. Zależnie od konfiguracji Moodle może być archiwum ZIP albo archiwum TAR skompresowanym gzip; rozszerzenie `.mbz` samo w sobie nie określa kontenera.

Nie należy rozwijać generatora z PR #101 jako niezależnego, ręcznego serializatora całego formatu backupu. Źródłem prawdy dla struktury, metadanych, identyfikatorów, obszarów plików i zależności aktywności ma być kod Moodle w konkretnej wspieranej wersji.

Docelowy przepływ:

1. Markdown → wspólny renderer → model pośredni kursu.
2. Walidacja modelu oraz jawnych zasobów (bez dopowiadania odpowiedzi quizu).
3. Utworzenie lub aktualizacja kursu i aktywności w Moodle przez obsługiwaną ścieżkę publikacji.
4. Uruchomienie oficjalnego mechanizmu backupu Moodle dla tego kursu.
5. Kontrola archiwum, raportu i sum kontrolnych.
6. Przywrócenie kopii w odizolowanym, czystym środowisku Moodle tej samej wersji.
7. Porównanie odtworzonego kursu z modelem źródłowym.

REST publish, neutralny model kursu i MBZ pozostają odrębnymi warstwami. Sam eksport banku pytań Moodle XML nie jest eksportem aktywności Quiz.

## 2. Wzorzec referencyjny — fixture z prawdziwego Moodle

Nie wolno ręcznie konstruować fixture MBZ na podstawie domysłów. Fixture musi powstać w CI z uruchomionej instancji Moodle 4.1, z użyciem jej mechanizmu backupu.

Minimalny kurs wzorcowy powinien zawierać:

- co najmniej jedną sekcję kursu;
- aktywność Book z minimum dwoma rozdziałami;
- aktywność Page;
- etykietę/Label, jeżeli obsługuje ją aktualny publikator;
- co najmniej jeden plik osadzony w treści Book lub Page;
- co najmniej jeden obraz z obszaru plików Moodle;
- quiz z pytaniem pochodzącym z jawnego źródła GIFT — tylko jeśli publikator obsługuje pełną instancję Quiz.

Fixture musi być syntetyczny: bez danych osobowych, sekretów, rzeczywistych kont i treści objętych ograniczeniami. W repozytorium należy przechowywać mały, odchudzony zestaw metadanych/oczekiwań, a nie pełny backup z danymi środowiska. Pełny MBZ może być artefaktem CI z ograniczoną retencją.

## 3. Ustalenie kontraktu strukturalnego

W pierwszym przebiegu testu CI należy:

1. utworzyć kurs wzorcowy w Moodle 4.1;
2. uruchomić oficjalny backup kursu;
3. rozpoznać kontener (ZIP lub gzip/TAR), sprawdzić jego integralność i odczytywalność wszystkich wpisów;
4. wypisać wszystkie ścieżki archiwum i zapisać je jako artefakt;
5. odczytać `moodle_backup.xml` oraz wszystkie pliki XML;
6. zebrać nazwy katalogów aktywności, identyfikatory instancji, identyfikatory modułów kursu i manifest plików;
7. sprawdzić, jak Moodle zapisuje treści Book/Page, pliki i pytania;
8. wykonać odtworzenie kopii do nowego kursu;
9. odczytać odtworzony kurs przez API Moodle i porównać jego semantyczną zawartość z kursem wzorcowym.

Dokładny zestaw wpisów MBZ, wymagane pola XML, nazwy katalogów i relacje identyfikatorów należy ustalić z wygenerowanego archiwum Moodle 4.1. Nie przyjmować listy plików z dokumentacji ani z tego dokumentu jako kompletnego schematu.

## 4. Wariant implementacji do rozstrzygnięcia

Preferowany jest mechanizm Moodle, nie ręczne składanie MBZ.

Należy porównać dwa warianty:

### A. Backup po publikacji

- Python publikuje model kursu przez istniejącą ścieżkę integracji.
- Zaufana część serwerowa Moodle uruchamia API backupu dla wskazanego kursu.
- Wynik MBZ jest zapisywany w kontrolowanym obszarze danych i udostępniany wyłącznie uprawnionemu użytkownikowi.
- Tokeny i uprawnienia nie mogą być przekazywane do pliku ani logów.

### B. Osobny komponent Moodle

- Dedykowany, minimalny komponent po stronie Moodle przyjmuje autoryzowane żądanie eksportu.
- Komponent waliduje uprawnienia, identyfikator kursu, docelową lokalizację i limity.
- Sam wywołuje oficjalne API backupu.
- Komponent nie implementuje własnego formatu MBZ.

Wybór wariantu wymaga sprawdzenia istniejącego endpointu `local_magicmoodle`, modelu uprawnień i sposobu identyfikacji kursu. Nie należy dodawać publicznego endpointu backupu bez autoryzacji i kontroli dostępu.

## 5. Testy obowiązkowe

| Warstwa | Test | Kryterium zaliczenia |
|---|---|---|
| Model | Walidacja Course/Section/Activity | brak błędów krytycznych i nieznanych typów |
| Publikacja | Utworzenie aktywności w Moodle | aktywności istnieją i mają oczekiwane powiązania |
| Backup | Oficjalny backup Moodle | proces kończy się powodzeniem |
| Kontener MBZ | Integralność archiwum ZIP lub gzip/TAR | wszystkie wpisy można odczytać bez błędów |
| XML | Parsowanie wszystkich plików XML | wszystkie dokumenty są poprawne składniowo |
| Pliki | Manifest i zawartość plików | każdy wpis ma odpowiadający plik i zgodny hash |
| Restore | Przywrócenie do nowego kursu | Moodle kończy restore bez błędów |
| Semantyka | Porównanie po restore | zgodne sekcje, aktywności, kolejność i treści |
| Book | Rozdziały i podrozdziały | zgodna liczba, tytuły, kolejność i HTML |
| Zasoby | Obrazy i załączniki | pliki otwierają się i odwołania są poprawne |
| Quiz | Pytania i odpowiedzi | zachowane są wyłącznie jawne pytania i klucze |
| Powtarzalność | Dwa eksporty tego samego kursu | semantycznie równoważny wynik, bez osieroconych danych |

Test restore jest warunkiem akceptacji. Samo utworzenie archiwum, poprawność XML albo zielone testy jednostkowe nie wystarczają.

## 6. Bezpieczeństwo i niezawodność

- Ograniczyć eksport do kursów, do których żądający ma uprawnienia.
- Nie ufać ścieżkom, nazwom plików ani identyfikatorom przekazanym przez klienta.
- Nie umieszczać haseł, tokenów, kluczy ani danych osobowych w MBZ, logach i artefaktach testowych.
- Ograniczyć rozmiar backupu, czas wykonania i retencję artefaktów.
- Przerwać proces, jeśli model zawiera nierozpoznany typ aktywności lub brak wymaganych zasobów.
- Raportować błędy z etapem procesu i identyfikatorem korelacyjnym, bez ujawniania sekretów.
- Nie usuwać ani nie nadpisywać istniejącego backupu bez jawnej polityki retencji.

## 7. Zakres pierwszego wdrożenia

Pierwsza wersja powinna obejmować tylko typy aktywności potwierdzone w aktualnym modelu i publikatorze. Zalecana kolejność:

1. kurs i sekcje;
2. Book i jego rozdziały;
3. pliki osadzone w Book;
4. Page i Label;
5. Quiz dopiero po potwierdzeniu pełnego mapowania instancji quizu i banku pytań.

Nie wolno deklarować obsługi typu aktywności, którego nie obejmuje test odtworzenia.

## 8. Kryteria zamknięcia PR #101

PR #101 pozostaje otwarty wyłącznie jako historyczny materiał do zastąpienia. Nie scalać go.

Można go zamknąć jako zastąpiony dopiero wtedy, gdy nowa implementacja:

- działa na aktualnym `main`;
- korzysta z oficjalnego mechanizmu backupu Moodle albo udowodnionej zgodnej implementacji;
- ma testy automatyczne i test odtworzenia na Moodle 4.1;
- zachowuje Book, treści, pliki i jawnie obsługiwane aktywności;
- ma zielone wymagane workflow;
- publikuje raport z testu restore.

## 9. Stan prac

Ten dokument ustanawia kontrakt i plan weryfikacji. Nie oznacza jeszcze, że powstał fixture MBZ, działa nowy eksporter ani że wykonano restore. Następny krok implementacyjny to rozszerzenie workflow Moodle 4.1 o generowanie kursu wzorcowego, oficjalny backup i odtworzenie do nowego kursu.

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
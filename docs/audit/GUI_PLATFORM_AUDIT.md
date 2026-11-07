# Audyt interfejsów użytkownika (GUI/TUI)

Data audytu: 2026-11-07  
Zakres: rewizja `main` `09641decf1e53c5347770d18f6c3bbfe1c8fda68`  
Status: audyt statyczny; bez zmian w `main`

## 1. Streszczenie

Repozytorium ma dojrzały funkcjonalnie rdzeń Python obejmujący modele kursu, ładowanie danych, walidację, eksporty, obsługę GIFT i publikację przez Moodle REST. Dostępny jest lokalny, przeglądarkowy panel inspekcji kursów. Nie znaleziono jednak odrębnych aplikacji TUI, DesktopGUI ani AndroidGUI.

| Obszar | Stan potwierdzony w rewizji audytowanej | Ocena |
|---|---|---|
| CLI | `magic_moodle/cli.py`, polecenie `magic-moodle` | Dostępny interfejs poleceń, nie pełne TUI |
| TUI | Brak odrębnej aplikacji terminalowej i zależności TUI | Do zaprojektowania |
| WebUI | `webui/server.py` oraz statyczne HTML/CSS/JS | Lokalny panel tylko do odczytu |
| DesktopGUI | Brak modułu aplikacji desktopowej i konfiguracji Qt | Niezaimplementowany |
| AndroidGUI | Brak projektu Gradle/Kotlin/Compose | Niezaimplementowany |

Ocena dotyczy wskazanej rewizji i przeglądu statycznego. Nie stanowi potwierdzenia działania wszystkich funkcji na systemach docelowych.

## 2. CLI a TUI

CLI udostępnia polecenia:
- `inspect`, `validate`;
- `course-export-json`;
- `moodle-publish`;
- `gift-validate`, `gift-to-xml`;
- `bank-validate`, `bank-to-xml`.

To użyteczny interfejs automatyzacji i pracy skryptowej. Nie zapewnia jednak typowych cech TUI: stałej nawigacji, widoków tabelarycznych, formularzy, panelu szczegółów, kontekstowej pomocy, obsługi skrótów i interaktywnego przepływu pracy.

Wniosek: zachować CLI jako stabilny interfejs automatyzacji; TUI zbudować jako osobnego klienta usług rdzenia, bez kopiowania logiki biznesowej.

## 3. WebUI

Potwierdzone funkcje:
- lokalny serwer HTTP uruchamiany przez `python -m webui.server` lub `magic-moodle-webui`;
- domyślne nasłuchiwanie na `127.0.0.1:8765`;
- lista kursów z katalogu konfigurowanego przez `MAGIC_MOODLE_COURSES`;
- podsumowanie liczby sekcji i aktywności;
- walidacja kursu oraz prezentacja błędów i ostrzeżeń;
- statyczne zasoby HTML/CSS/JavaScript;
- kontrola ścieżek, nagłówka Host i nagłówki bezpieczeństwa;
- brak operacji zapisu oraz publikacji Moodle.

Ograniczenia:
1. WebUI jest panelem inspekcyjnym, nie edytorem.
2. Serwer używa wbudowanego `http.server`; należy utrzymać go jako lokalne narzędzie, a przed udostępnieniem sieciowym zastąpić lub osłonić produkcyjnym serwerem aplikacyjnym.
3. Brak uwierzytelniania i autoryzacji użytkowników jest akceptowalny wyłącznie przy obecnym ograniczeniu do loopback i trybie tylko do odczytu.
4. Brak kontraktu API wersjonowanego niezależnie od implementacji serwera.
5. Brak testów przeglądarkowych, dostępności WCAG i testów end-to-end.
6. W JavaScript należy zachować bezpieczne renderowanie tekstu przez `textContent` i `createElement`; nie wprowadzać niezaufanych treści kursu do `innerHTML`.

Wniosek: rozwijać WebUI etapami, wprowadzając najpierw jawne przypadki użycia i kontrakty, następnie bezpieczny zapis z walidacją i kontrolą wersji. Nie wystawiać obecnego serwera bezpośrednio do sieci.

## 4. DesktopGUI

Nie znaleziono osobnego projektu desktopowego, manifestu pakietowania ani warstwy prezentacji Qt.

Rekomendacja: PySide6 / Qt 6. Aplikacja powinna wykorzystywać te same przypadki użycia co TUI i WebUI. Zadania długotrwałe (generowanie, walidacja dużych kursów, eksport i publikacja) muszą działać poza wątkiem interfejsu. Wymagane są: obsługa błędów, anulowanie tam, gdzie bezpieczne, postęp zadań, automatyczny zapis wersji roboczej i odzyskiwanie po awarii.

## 5. AndroidGUI

Nie znaleziono projektu Gradle, modułu Kotlin ani aplikacji Compose.

Rekomendacja: Kotlin, Jetpack Compose, MVVM, repozytoria danych i warstwa synchronizacji. Room może przechowywać lokalny stan roboczy, a WorkManager wykonywać zadania odroczone. Aplikacja mobilna powinna korzystać z uwierzytelnionego API; nie może otrzymywać tokenu administratora Moodle ani bezpośrednio przechowywać poświadczeń serwera w kodzie aplikacji.

Pierwszy zakres mobilny: przegląd kursów, podgląd, komentarze/uwagi, zatwierdzanie zaplanowanych operacji, status publikacji i ograniczona edycja. Pełny edytor rozbudowanych kursów pozostaje funkcją WebUI/DesktopGUI.

## 6. Ustalenia architektoniczne

1. Istnieje jeden model domenowy kursu w `magic_moodle/models.py`; nie należy tworzyć odrębnych modeli biznesowych dla każdego interfejsu.
2. `magic_moodle/cli.py` zawiera orkiestrację poleceń i powinien stopniowo delegować do jawnych przypadków użycia.
3. `webui/server.py` bezpośrednio importuje loader i walidator. To właściwe dla małego panelu, ale nie jest jeszcze wspólną warstwą aplikacyjną.
4. Integracja Moodle, manifest wznowienia i walidacja należą do usług rdzenia, nie do klientów.
5. Kontrakty API powinny przenosić identyfikatory, wersje, wyniki i kody błędów; nie powinny ujawniać ścieżek lokalnych ani tokenów.
6. Wszystkie operacje zapisu muszą być jawne, walidowane i audytowalne. Publikacja Moodle wymaga podglądu planu i świadomego potwierdzenia.

## 7. Rejestr priorytetów

### P0 — warunki architektoniczne przed edycją wielointerfejsową
- [ ] Zdefiniować wspólne przypadki użycia i granice odpowiedzialności warstw.
- [ ] Ustanowić kontrakt błędów, identyfikatorów i wersjonowania API.
- [ ] Określić zasady zapisu, wersjonowania, blokad i konfliktów zmian.
- [ ] Zachować CLI jako interfejs zgodności wstecznej.

### P1 — pierwsze wdrożenia
- [ ] Dodać warstwę aplikacyjną bez zależności od frameworka GUI.
- [ ] Dodać testy kontraktowe przypadków użycia.
- [ ] Zbudować TUI jako klienta warstwy aplikacyjnej.
- [ ] Rozwinąć WebUI z trybu inspekcji do kontrolowanej edycji.
- [ ] Przygotować szkielety DesktopGUI i AndroidGUI dopiero po ustabilizowaniu kontraktu.

### P2 — jakość i wydanie
- [ ] Testy end-to-end dla czterech interfejsów.
- [ ] Testy dostępności WCAG 2.2 AA dla WebUI.
- [ ] Testy klawiatury, skalowania, lokalizacji i czytników ekranu.
- [ ] Testy bezpieczeństwa API, sesji, CSRF, CORS i kontroli uprawnień.
- [ ] Pakietowanie, aktualizacje i polityka migracji danych.

## 8. Kryteria zamknięcia audytu

Audyt można uznać za zamknięty dopiero po:
- przyjęciu architektury i kontraktów;
- potwierdzeniu testami, że interfejsy korzystają ze wspólnych przypadków użycia;
- przejściu testów regresyjnych rdzenia;
- przeprowadzeniu osobnych przeglądów bezpieczeństwa i dostępności;
- udokumentowaniu ograniczeń każdej platformy.

## 9. Ograniczenia

To audyt statyczny kodu i konfiguracji repozytorium w określonej rewizji. Nie przeprowadzono uruchomienia aplikacji na Windows/macOS/Linux/Android, testów przeglądarkowych, testów obciążeniowych ani testów penetracyjnych. Wnioski o braku aplikacji wynikają z przeglądu drzewa repozytorium i plików konfiguracyjnych, nie z inspekcji urządzeń użytkowników.

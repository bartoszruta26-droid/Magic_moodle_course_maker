# AndroidGUI — Kotlin i Jetpack Compose

## Status

Pierwszy szkielet natywnego klienta Android. Projekt zapisuje konfigurację adresu API i udostępnia podstawowy ekran mobilny. Nie pobiera jeszcze kursów, ponieważ serwer API v1 nie został jeszcze wdrożony.

## Wymagania

- JDK 17;
- Android SDK z platformą 35;
- Android Gradle Plugin 8.7.3;
- Kotlin 2.0.21.

## Budowanie

```bash
cd android
gradle :app:assembleDebug
gradle :app:testDebugUnitTest
```

## Konfiguracja

Aplikacja przechowuje adres bazowy API w prywatnych preferencjach aplikacji. Dopuszczone są adresy HTTP/HTTPS z hostem, bez danych logowania, parametrów zapytania i fragmentów.

Dla środowiska produkcyjnego należy używać HTTPS. Ruch HTTP może być dopuszczony wyłącznie w kontrolowanym środowisku deweloperskim i wymaga jawnej konfiguracji bezpieczeństwa Androida.

## Granice obecnego etapu

- brak danych demonstracyjnych udających prawdziwe kursy;
- brak tokenów Moodle w aplikacji;
- brak bezpośredniej integracji z Moodle REST;
- brak synchronizacji i edycji offline;
- brak publikacji kursu.

## Kolejny etap

Po wdrożeniu i zabezpieczeniu API v1:
1. klient HTTP i obsługa sesji;
2. lista kursów i podgląd;
3. walidacja oraz raporty;
4. lokalna pamięć podręczna Room;
5. synchronizacja WorkManager;
6. jawne potwierdzanie operacji publikacji.

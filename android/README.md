# AndroidGUI — Kotlin i Jetpack Compose

## Status

Klient natywny Android oparty na Kotlinie i Jetpack Compose. Aplikacja zapisuje adres API v1, pobiera listę kursów przez HTTPS i obsługuje opcjonalny token Bearer.

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
1. szczegóły kursu i raporty walidacji;
2. bezpieczne przechowywanie tokenu API w Android Keystore;
3. lokalna pamięć podręczna Room;
4. synchronizacja WorkManager;
5. jawne potwierdzanie operacji publikacji.

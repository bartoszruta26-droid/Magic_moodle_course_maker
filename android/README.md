# AndroidGUI — Kotlin i Jetpack Compose

## Status

Klient natywny Android oparty na Kotlinie i Jetpack Compose. Aplikacja zapisuje adres API v1, pobiera listę kursów, szczegóły i raporty walidacji oraz obsługuje wersje robocze kursów.

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
- token Bearer jest wymagany do zapisu wersji roboczych i pozostaje wyłącznie w pamięci bieżącej sesji;
- edycja obejmuje nazwę kursu, nazwę skróconą, opis i nazwy sekcji;
- zapis wersji roboczej nie modyfikuje plików źródłowych kursu;
- brak synchronizacji offline i publikacji kursu.

## Kolejny etap

1. bezpieczne przechowywanie tokenu API w Android Keystore;
2. lokalna pamięć podręczna Room;
3. synchronizacja WorkManager;
4. edycja nazw aktywności i historii wersji roboczych;
5. jawne potwierdzanie operacji publikacji.

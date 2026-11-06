# Manifest wznowienia publikacji Moodle

Manifest jest opcjonalnym, lokalnym dziennikiem postępu publikacji. Nie zastępuje kopii zapasowej Moodle ani mechanizmu transakcji po stronie serwera.

## Użycie

```bash
python -m magic_moodle moodle-publish courses/03-kurs-masazysta-med10 \
  --category-id 2 \
  --state-file .local-state/med10-publish.json
```

W razie przerwania publikacji uruchom to samo polecenie z tym samym plikiem stanu. Klient ponownie sprawdza sekcje i aktywności w Moodle. Endpointy rozpoznają już utworzone aktywności po stabilnym identyfikatorze źródłowym, więc ponowienie nie powinno tworzyć duplikatów.

## Co zapisuje manifest

- wersję formatu;
- nazwę skróconą kursu;
- skrót planu publikacji;
- skrót adresu witryny Moodle;
- identyfikator kursu po stronie Moodle;
- listę zaktualizowanych sekcji;
- identyfikatory i wyniki obsłużonych aktywności;
- etap przerwania i typ wyjątku.

Manifest **nie zapisuje tokenu Moodle, hasła, treści pytań ani treści aktywności**. Zawiera identyfikatory Moodle i dane operacyjne, dlatego należy traktować go jako plik administracyjny i nie publikować w repozytorium.

## Zasady bezpieczeństwa

- Nie używaj tego samego pliku stanu dla różnych kursów, planów ani serwerów Moodle.
- Jeśli plan lub serwer się zmieni, publikacja zostanie zatrzymana przed zapisem.
- Jeśli zapisany kurs zniknie lub jego identyfikator przestanie pasować do nazwy skróconej, narzędzie nie utworzy automatycznie nowego kursu.
- Manifest jest zapisywany atomowo. Pliki będące dowiązaniami symbolicznymi są odrzucane.
- Zapisany postęp jest informacyjny. Przy wznowieniu operacje są ponownie weryfikowane w Moodle, a nie pomijane wyłącznie na podstawie lokalnego pliku.

## Ograniczenia

Manifest ułatwia wznowienie i audyt postępu, ale nie zapewnia atomowości całej publikacji kursu. Awaria może pozostawić częściowo opublikowany kurs. Wznowienie jest bezpieczne tylko w zakresie idempotencji endpointów. Aktualizacja istniejącej treści aktywności i trwała synchronizacja wersji źródłowej wymagają osobnych endpointów aktualizacji.
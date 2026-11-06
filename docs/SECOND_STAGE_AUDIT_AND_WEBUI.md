# Drugi etap audytu i plan techniczny

## Zakres przeglądu

Przejrzano implementację rdzenia Python oraz pluginu Moodle:
- `magic_moodle/cli.py`, `models.py`, `loader.py`, `validation.py`;
- `gift.py`, `question_bank.py`, `moodle_xml.py`, `course_export.py`;
- `moodle_api.py`, `moodle_publish.py`;
- funkcje zewnętrzne pluginu `local_magicmoodle`, deklaracje usług i metadane wersji.

Przegląd repozytorium nie zastępuje uruchomienia na instancji Moodle. W szczególności nie potwierdza zgodności zachowania wszystkich funkcji z konkretnymi wydaniami Moodle ani bezpieczeństwa wdrożenia produkcyjnego.

## Ustalenia i działania

### Wysoki priorytet
1. **Synchronizacja aktywności** — część funkcji pluginu rozpoznaje istniejące aktywności po nazwie lub idnumber i zwraca istniejący element. To chroni przed częścią duplikatów, ale nie jest aktualizacją treści. Potrzebny jest jawny tryb create/update/reconcile oraz testy po przerwaniu procesu.
2. **Publikacja częściowa** — proces tworzy kurs i aktywności sekwencyjnie. Należy utrzymywać manifest stanu publikacji, aby bezpiecznie wznowić operację i raportować pominięte elementy.
3. **Zgodność pluginu Moodle** — wymagane testy instalacji i wykonania funkcji na każdej wspieranej wersji Moodle; testy statyczne nie wystarczą.
4. **Walidacja kompletności** — walidator kursu powinien mieć jawny katalog obsługiwanych typów aktywności i zgłaszać nieznane typy jako błąd lub wyraźne ostrzeżenie przed publikacją.

### Średni priorytet
1. Ujednolicić wersjonowanie pakietu Python i pluginu Moodle.
2. Rozdzielić walidację schematu danych od walidacji zasobów na dysku.
3. Zdefiniować politykę HTML/Markdown i testować wynik konwersji.
4. Dodać testy zgodności GIFT z natywnym importerem Moodle, w tym przypadki brzegowe.
5. Uporządkować puste pliki pomocnicze i nieaktualne instrukcje.

## WebUI — zakres pierwszej iteracji

Dodano lokalny interfejs przeglądarkowy:
- lista kursów z katalogu wskazanego przez `MAGIC_MOODLE_COURSES`;
- podsumowanie liczby sekcji i aktywności;
- walidacja kursu oraz raport błędów i ostrzeżeń;
- lokalne zasoby statyczne;
- interfejs tylko do odczytu, bez możliwości publikacji.

Bezpieczeństwo:
- serwer domyślnie nasłuchuje na `127.0.0.1`;
- serwer odrzuca adresy nasłuchu inne niż loopback;
- API nie ujawnia pełnej ścieżki katalogu kursów;
- identyfikatory kursów są dekodowane i sprawdzane pod kątem wyjścia poza katalog bazowy;
- brak tokenów Moodle i operacji zapisu w WebUI;
- brak zewnętrznych zasobów fontów.

Uruchomienie:

```bash
pip install -e ".[dev]"
python -m webui.server
```

Następnie otwórz `http://127.0.0.1:8765`.

## Plan kolejnych iteracji

1. Testy jednostkowe i regresyjne rdzenia oraz WebUI.
2. Test integracyjny z Moodle w środowisku testowym (tworzenie, ponowienie, przerwanie, wznowienie).
3. Bezpieczna synchronizacja aktualizacji aktywności.
4. Edytor struktury kursu i podgląd treści.
5. Generator materiałów oraz quizów z wersjonowaniem zmian.
6. Eksporty HTML/PDF/DOCX i pakiet kursu Moodle.
7. Publikacja REST z planem, potwierdzeniem użytkownika, dziennikiem i możliwością wznowienia.
8. Kontrola ról, uprawnień, dostępności WCAG i audyt bezpieczeństwa przed wdrożeniem zdalnym.

## Ograniczenia

Pierwsza iteracja WebUI jest lokalnym panelem przeglądowym, nie pełnym edytorem kursów. Nie wykonuje publikacji Moodle. Do wdrożenia sieciowego wymagane będą uwierzytelnianie, autoryzacja, ochrona CSRF, HTTPS, audyt zdarzeń i testy penetracyjne.

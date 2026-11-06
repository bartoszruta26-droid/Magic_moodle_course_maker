# Uniwersalny rdzeń Magic Moodle Course Maker

## Cel pierwszego przyrostu

Rdzeń odczytuje istniejący układ katalogów kursu, buduje neutralny model danych
i wykonuje ogólną walidację. Nie modyfikuje kursów, nie nadpisuje materiałów
i nie deklaruje jeszcze generowania plików MBZ ani publikowania do Moodle.

## Zgodność z dotychczasowym formatem

- Metadane kursu: `course.yaml`, w szczególności `course.full_name` i
  `course.short_name`.
- Sekcje: katalogi w `sections/*/` z plikiem `section.yaml`.
- Aktywności: elementy listy `modules` z polami `type`, `ref` i `name`.
- Opis kursu: opcjonalny plik wskazany przez `description.markdown_file`.

Dotychczasowe generatory w katalogu `scripts/` pozostają bez zmian i mogą
być uruchamiane niezależnie od nowego rdzenia.

## Użycie

```bash
python -m pip install -e ".[dev]"
python -m magic_moodle inspect courses/03-kurs-masazysta-med10
python -m magic_moodle validate courses/03-kurs-masazysta-med10
pytest -q
```

## Kontrakt bezpieczeństwa

Walidator odczytuje dane przez `yaml.safe_load`. Odwołania aktywności są
sprawdzane pod kątem istnienia i pozostawania wewnątrz katalogu sekcji.
Wyniki kontroli mają poziom błędu lub ostrzeżenia. Walidacja nie naprawia
plików automatycznie i nie usuwa danych.

## Następne przyrosty

1. Rozszerzenie modelu o quizy, pytania, Book i zasoby multimedialne.
2. Adaptery eksportowe Moodle XML i GIFT.
3. Budowanie kopii zapasowej przez mechanizm zgodny z Moodle.
4. Testy integracyjne na instancji Moodle o jawnie określonej wersji.

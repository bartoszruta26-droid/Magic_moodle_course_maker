# Uniwersalny rdzeń Magic Moodle Course Maker

## Cel i zakres

Rdzeń odczytuje istniejący układ katalogów kursu, buduje neutralny model
danych i wykonuje ogólną walidację. Nie modyfikuje kursów ani nie deklaruje
jeszcze generowania plików MBZ lub publikowania do Moodle.

## Zgodność z formatem repozytorium

- Metadane kursu: `course.yaml`, w szczególności `course.full_name` i
  `course.short_name`.
- Sekcje: katalogi w `sections/*/` z plikiem `section.yaml`.
- Aktywności: elementy listy `modules` z polami `type`, `ref` i `name`.
- Opis kursu: opcjonalny plik wskazany przez `description.markdown_file`.
- Book: `book.yaml`, lista `book.chapters` i pliki wskazane przez
  `content_file`.
- Assignment: `assignment.yaml` oraz opcjonalny plik instrukcji
  wskazany przez `markdown_file`.
- Glossary: `glossary.yaml` z listą wpisów `term` / `definition`.
- Quiz: rozpoznawana jest konfiguracja `quiz.yaml`; jej pełna walidacja
  i mapowanie pytań będą osobnym przyrostem.
- Page i label: treść pliku wskazanego przez `ref`.

Wczytane metadane aktywności są dostępne w `Activity.resource`, a treści
plików w `Activity.content`. Pierwotny wpis modułu pozostaje w
`Activity.config`, co zachowuje zgodność wsteczną.

## Użycie

```bash
python -m pip install -e ".[dev]"
python -m magic_moodle inspect courses/03-kurs-masazysta-med10
python -m magic_moodle inspect courses/03-kurs-masazysta-med10 --json
python -m magic_moodle validate courses/03-kurs-masazysta-med10
pytest -q
```

## Bezpieczeństwo i walidacja

YAML jest odczytywany przez `yaml.safe_load`. Ścieżki opisu kursu,
zasobów i rozdziałów są rozwiązywane i sprawdzane pod kątem wyjścia poza
dozwolony katalog. Walidator sprawdza referencje aktywności, treści
rozdziałów Book, instrukcje Assignment, strukturę wpisów Glossary oraz
składnię plików YAML. Walidacja nie naprawia plików automatycznie i nie
usuwa danych.

## Następne przyrosty

1. Pełny model Quiz i banku pytań (GIFT/YAML) wraz z walidacją typów pytań.
2. Adaptery eksportowe Moodle XML i GIFT.
3. Budowanie kopii zapasowej przez mechanizm zgodny z Moodle.
4. Testy integracyjne na instancji Moodle o jawnie określonej wersji.

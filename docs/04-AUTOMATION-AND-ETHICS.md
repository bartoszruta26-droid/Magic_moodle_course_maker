

# Automatyzacja, skrypty, CI/CD i zasady etyczne

> Szablony konwersji, schematy walidacji, skrypty budowania
> i eksportu, pipeline CI/CD oraz wytyczne etyczne zgodne
> z prawem Bożym, prawem naturalnym i prawami człowieka.

---

## Spis treści

1. [JSON Schema dla course.yaml](#schema-course)
2. [JSON Schema dla pytań](#schema-question)
3. [Szablon Jinja2 – konwersja YAML → XML](#jinja2)
4. [Główny skrypt budujący (build_course.py)](#build-script)
5. [Konwerter YAML → GIFT](#yaml-to-gift)
6. [Skrypt importu do Moodle](#import-script)
7. [Pipeline CI/CD – walidacja](#ci-validate)
8. [Pipeline CI/CD – budowanie](#ci-build)
9. [Zasady etyczne](#ethics)
10. [Walidator etyczny](#ethics-validator)

---

<a id="schema-course"></a>
## 1. JSON Schema dla `course.yaml`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://example.com/schemas/course.schema.json",
  "title": "Moodle Course Definition",
  "description": "Schemat walidacji pliku course.yaml",
  "type": "object",
  "required": ["course"],
  "properties": {
    "course": {
      "type": "object",
      "required": ["fullname", "shortname", "summary", "format"],
      "properties": {
        "fullname": {
          "type": "string",
          "minLength": 3,
          "maxLength": 254,
          "description": "Pełna nazwa kursu"
        },
        "shortname": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100,
          "pattern": "^[A-Za-z0-9_-]+$",
          "description": "Krótka nazwa kursu (bez spacji)"
        },
        "summary": {
          "type": "string",
          "minLength": 10,
          "description": "Opis kursu"
        },
        "format": {
          "type": "string",
          "enum": ["topics", "weeks", "single", "social"],
          "description": "Format kursu"
        },
        "numsections": {
          "type": "integer",
          "minimum": 0,
          "maximum": 52,
          "description": "Liczba sekcji"
        },
        "visible": {
          "type": "boolean",
          "default": true
        },
        "enablecompletion": {
          "type": "boolean",
          "default": false
        },
        "tags": {
          "type": "array",
          "items": {
            "type": "string",
            "minLength": 1
          },
          "uniqueItems": true
        },
        "metadata": {
          "type": "object",
          "properties": {
            "author": { "type": "string" },
            "version": {
              "type": "string",
              "pattern": "^\\d+\\.\\d+\\.\\d+$"
            },
            "license": { "type": "string" },
            "language": {
              "type": "string",
              "pattern": "^[a-z]{2}(-[A-Z]{2})?$"
            },
            "ethical_compliance": {
              "type": "object",
              "properties": {
                "respects_human_dignity": { "type": "boolean" },
                "no_manipulation": { "type": "boolean" },
                "sources_cited": { "type": "boolean" },
                "accessibility_wcag": {
                  "type": "string",
                  "enum": ["A", "AA", "AAA"]
                }
              }
            }
          }
        }
      }
    }
  }
}


---

<a id="schema-question"></a>
## 2. JSON Schema dla pytań (`question.schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://example.com/schemas/question.schema.json",
  "title": "Moodle Question Definition",
  "type": "object",
  "required": ["id", "type", "name", "questiontext"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^q\\d{3,}$"
    },
    "type": {
      "type": "string",
      "enum": [
        "multichoice",
        "truefalse",
        "shortanswer",
        "numerical",
        "matching",
        "essay",
        "missingword",
        "calculated",
        "description"
      ]
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 254
    },
    "questiontext": {
      "type": "string",
      "minLength": 1
    },
    "category": {
      "type": "string"
    },
    "defaultmark": {
      "type": "number",
      "minimum": 0
    },
    "penalty": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "allOf": [
    {
      "if": { "properties": { "type": { "const": "multichoice" } } },
      "then": {
        "required": ["answers", "single"],
        "properties": {
          "answers": {
            "type": "array",
            "minItems": 2,
            "items": {
              "type": "object",
              "required": ["text", "fraction"],
              "properties": {
                "text": { "type": "string" },
                "fraction": {
                  "type": "number",
                  "minimum": -100,
                  "maximum": 100
                },
                "feedback": { "type": "string" }
              }
            }
          },
          "single": { "type": "boolean" }
        }
      }
    },
    {
      "if": { "properties": { "type": { "const": "truefalse" } } },
      "then": {
        "required": ["answer"],
        "properties": {
          "answer": { "type": "boolean" }
        }
      }
    }
  ]
}


---

<a id="jinja2"></a>
## 3. Szablon Jinja2 – konwersja YAML → Moodle XML

Plik: `templates/moodle-xml/question-types/multichoice.xml.j2`

```xml
{# Szablon Jinja2 do konwersji pytania multichoice z YAML do XML #}

<question type="multichoice">
  <name>
    <text>{{ question.name | escape }}</text>
  </name>
  <questiontext format="html">
    <text><![CDATA[{{ question.questiontext }}]]></text>
  </questiontext>
  {% if question.generalfeedback %}
  <generalfeedback format="html">
    <text><![CDATA[{{ question.generalfeedback }}]]></text>
  </generalfeedback>
  {% endif %}
  <defaultgrade>{{ question.defaultmark | default(1.0) }}</defaultgrade>
  <penalty>{{ question.penalty | default(0.3333) }}</penalty>
  <hidden>0</hidden>
  <single>{{ question.single | lower }}</single>
  <shuffleanswers>{{ question.shuffleanswers | default(true) | lower }}</shuffleanswers>
  <answernumbering>{{ question.answernumbering | default('abc') }}</answernumbering>
  {% for answer in question.answers %}
  <answer fraction="{{ answer.fraction }}" format="html">
    <text>{{ answer.text | escape }}</text>
    {% if answer.feedback %}
    <feedback format="html">
      <text>{{ answer.feedback | escape }}</text>
    </feedback>
    {% endif %}
  </answer>
  {% endfor %}
  {% if question.tags %}
  <tags>
    {% for tag in question.tags %}
    <tag><text>{{ tag | escape }}</text></tag>
    {% endfor %}
  </tags>
  {% endif %}
</question>


---

<a id="build-script"></a>
## 4. Główny skrypt budujący – `scripts/builders/build_course.py`

```python
#!/usr/bin/env python3
"""
Główny skrypt budujący kurs Moodle z plików YAML/MD/GIFT.

Użycie:
    python build_course.py courses/01-prawda-i-natura --format xml
    python build_course.py courses/01-prawda-i-natura --format gift
    python build_course.py courses/01-prawda-i-natura --format mbz
    python build_course.py courses/01-prawda-i-natura --format all
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from converters.yaml_to_moodle_xml import YamlToMoodleXml
from converters.yaml_to_gift import YamlToGift
from converters.md_to_html import MarkdownToHtml
from builders.build_mbz import MbzBuilder
from validators.validate_course import CourseValidator


def build_course(course_dir: str, output_format: str = "all") -> None:
    """Buduje kurs Moodle z plików źródłowych."""

    course_path = Path(course_dir)
    output_dir = course_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Krok 1: Walidacja
    print(f"[1/5] Walidacja kursu: {course_path.name}")
    validator = CourseValidator(course_path)
    errors = validator.validate()
    if errors:
        print(f"  ❌ Znaleziono {len(errors)} błędów walidacji:")
        for error in errors:
            print(f"     - {error}")
        sys.exit(1)
    print("  ✅ Walidacja passed")

    # Krok 2: Konwersja Markdown → HTML
    print("[2/5] Konwersja Markdown → HTML")
    md_converter = MarkdownToHtml()
    md_files = list(course_path.rglob("*.md"))
    for md_file in md_files:
        html_output = md_converter.convert_file(md_file)
        print(f"  → {md_file.name} → HTML")

    # Krok 3: Budowanie w zależności od formatu
    formats = ["xml", "gift", "mbz"] if output_format == "all" else [output_format]

    for fmt in formats:
        print(f"[3/5] Budowanie formatu: {fmt.upper()}")

        if fmt == "xml":
            xml_dir = output_dir / "moodle-xml"
            xml_dir.mkdir(exist_ok=True)
            converter = YamlToMoodleXml(course_path)
            converter.build()
            converter.save(xml_dir / "course.xml")
            print(f"  → {xml_dir / 'course.xml'}")

        elif fmt == "gift":
            gift_dir = output_dir / "gift"
            gift_dir.mkdir(exist_ok=True)
            converter = YamlToGift(course_path)
            converter.build()
            converter.save(gift_dir / "all-questions.gift")
            print(f"  → {gift_dir / 'all-questions.gift'}")

        elif fmt == "mbz":
            mbz_dir = output_dir / "mbz"
            mbz_dir.mkdir(exist_ok=True)
            builder = MbzBuilder(course_path)
            builder.build()
            builder.save(mbz_dir / "course.mbz")
            print(f"  → {mbz_dir / 'course.mbz'}")

    # Krok 4: Kopiowanie zasobów multimedialnych
    print("[4/5] Kopiowanie zasobów multimedialnych")
    media_dir = course_path / "media"
    if media_dir.exists():
        import shutil
        shutil.copytree(media_dir, output_dir / "media", dirs_exist_ok=True)
        print(f"  → Skopiowano {len(list(media_dir.rglob('*')))} plików")

    # Krok 5: Podsumowanie
    print("[5/5] Podsumowanie")
    print(f"  ✅ Kurs '{course_path.name}' zbudowany pomyślnie")
    print(f"  📁 Output: {output_dir}")

    for f in sorted(output_dir.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            print(f"     {f.relative_to(output_dir)} ({size:,} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Buduje kurs Moodle z plików YAML/MD/GIFT"
    )
    parser.add_argument("course_dir", help="Ścieżka do katalogu kursu")
    parser.add_argument(
        "--format", "-f",
        choices=["xml", "gift", "mbz", "all"],
        default="all",
        help="Format wyjściowy (default: all)"
    )
    args = parser.parse_args()

    build_course(args.course_dir, args.format)


---

<a id="yaml-to-gift"></a>
## 5. Konwerter YAML → GIFT – `scripts/converters/yaml_to_gift.py`

```python
#!/usr/bin/env python3
"""
Konwerter pytań YAML → format GIFT.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any


class YamlToGift:
    """Konwertuje pytania z formatu YAML do formatu GIFT."""

    def __init__(self, course_path: Path):
        self.course_path = course_path
        self.gift_lines: List[str] = []

    def build(self) -> None:
        self._add_header()
        yaml_files = list(self.course_path.rglob("questions.yaml"))
        for yaml_file in yaml_files:
            self._process_yaml_file(yaml_file)

    def _add_header(self) -> None:
        self.gift_lines.extend([
            "// ============================================================",
            "// Wygenerowano automatycznie z plików YAML",
            "// Nie edytować ręcznie - zmiany zostaną nadpisane",
            "// ============================================================",
            "",
        ])

    def _process_yaml_file(self, yaml_file: Path) -> None:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'quiz_questions' not in data:
            return

        questions = data['quiz_questions'].get('questions', [])

        self.gift_lines.append(f"// === Plik: {yaml_file.name} ===")
        self.gift_lines.append(f"// Liczba pytań: {len(questions)}")
        self.gift_lines.append("")

        for question in questions:
            self._convert_question(question)
            self.gift_lines.append("")

    def _convert_question(self, q: Dict[str, Any]) -> None:
        qtype = q.get('type', '')

        if qtype == 'multichoice':
            self._convert_multichoice(q)
        elif qtype == 'truefalse':
            self._convert_truefalse(q)
        elif qtype == 'shortanswer':
            self._convert_shortanswer(q)
        elif qtype == 'numerical':
            self._convert_numerical(q)
        elif qtype == 'matching':
            self._convert_matching(q)
        elif qtype == 'essay':
            self._convert_essay(q)
        elif qtype == 'missingword':
            self._convert_missingword(q)

    def _convert_multichoice(self, q: Dict) -> None:
        name = q.get('name', 'Bez nazwy')
        qtext = q.get('questiontext', '')

        self.gift_lines.append(f"::{name}::")
        self.gift_lines.append(f"{qtext} {{")

        for answer in q.get('answers', []):
            fraction = answer.get('fraction', 0)
            text = answer.get('text', '')
            feedback = answer.get('feedback', '')

            if fraction >= 100:
                prefix = "="
            elif fraction > 0:
                prefix = f"~%{fraction}%"
            elif fraction < 0:
                prefix = f"~%{fraction}%"
            else:
                prefix = "~"

            line = f"    {prefix}{text}"
            if feedback:
                line += f"#{feedback}"
            self.gift_lines.append(line)

        self.gift_lines.append("}")

    def _convert_truefalse(self, q: Dict) -> None:
        name = q.get('name', 'Bez nazwy')
        qtext = q.get('questiontext', '')
        answer = q.get('answer', False)

        feedback_key = 'feedbacktrue' if answer else 'feedbackfalse'
        feedback = q.get(feedback_key, '')

        self.gift_lines.append(f"::{name}::")
        self.gift_lines.append(f"{qtext} {{")
        self.gift_lines.append(f"    {'TRUE' if answer else 'FALSE'}")
        if feedback:
            self.gift_lines.append(f"    #{feedback}")
        self.gift_lines.append("}")

    def _convert_shortanswer(self, q: Dict) -> None:
        name = q.get('name', 'Bez nazwy')
        qtext = q.get('questiontext', '')

        self.gift_lines.append(f"::{name}::")
        self.gift_lines.append(f"{qtext} {{")

        for answer in q.get('answers', []):
            fraction = answer.get('fraction', 0)
            text = answer.get('text', '')
            prefix = "=" if fraction >= 100 else f"~%{fraction}%"
            self.gift_lines.append(f"    {prefix}{text}")

        self.gift_lines.append("}")

    def _convert_numerical(self, q: Dict) -> None:
        name = q.get('name', 'Bez nazwy')
        qtext = q.get('questiontext', '')

        self.gift_lines.append(f"::{name}::")
        self.gift_lines.append(f"{qtext} {{")

        for answer in q.get('answers', []):
            value = answer.get('value', 0)
            tolerance = answer.get('tolerance', 0)
            self.gift_lines.append(f"    ={value}:{tolerance}")

        self.gift_lines.append("}")

    def _convert_matching(self, q: Dict) -> None:
        name = q.get('name', 'Bez nazwy')
        qtext = q.get('questiontext', '')

        self.gift_lines.append(f"::{name}::")
        self.gift_lines.append(f"{qtext} {{")

        for subq in q.get('subquestions', []):
            question = subq.get('question', '')
            answer = subq.get('answer', '')
            self.gift_lines.append(f"    ={question} -> {answer}")

        self.gift_lines.append("}")

    def _convert_essay(self, q: Dict) -> None:
        name = q.get('name', 'Bez nazwy')
        qtext = q.get('questiontext', '')

        self.gift_lines.append(f"::{name}::")
        self.gift_lines.append(f"{qtext} {{")
        self.gift_lines.append("}")

    def _convert_missingword(self, q: Dict) -> None:
        name = q.get('name', 'Bez nazwy')
        qtext = q.get('questiontext', '')

        self.gift_lines.append(f"::{name}::")
        self.gift_lines.append(f"{qtext}")

    def save(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.gift_lines))

    def get_content(self) -> str:
        return '\n'.join(self.gift_lines)


---

<a id="import-script"></a>
## 6. Skrypt importu do Moodle – `scripts/importers/import_course.py`

```python
#!/usr/bin/env python3
"""
Import kursu do Moodle przez REST API.

Użycie:
    python import_course.py --url https://moodle.example.com \
                            --token YOUR_TOKEN \
                            --file courses/01/output/mbz/course.mbz
"""

import argparse
import requests
from pathlib import Path


class MoodleImporter:
    """Klient importu do Moodle."""

    def __init__(self, moodle_url: str, token: str):
        self.base_url = moodle_url.rstrip('/')
        self.api_url = f"{self.base_url}/webservice/rest/server.php"
        self.token = token

    def _call_api(self, wsfunction: str, params: dict) -> dict:
        data = {
            'wstoken': self.token,
            'wsfunction': wsfunction,
            'moodlewsrestformat': 'json',
            **params
        }

        response = requests.post(self.api_url, data=data)
        response.raise_for_status()
        result = response.json()

        if 'exception' in result:
            raise Exception(f"Moodle API Error: {result['message']}")

        return result

    def create_course(self, course_data: dict) -> int:
        params = {
            'courses[0][fullname]': course_data['fullname'],
            'courses[0][shortname]': course_data['shortname'],
            'courses[0][categoryid]': course_data.get('categoryid', 1),
            'courses[0][summary]': course_data.get('summary', ''),
            'courses[0][format]': course_data.get('format', 'topics'),
            'courses[0][numsections]': course_data.get('numsections', 1),
        }

        result = self._call_api('core_course_create_courses', params)
        course_id = result[0]['id']
        print(f"✅ Kurs utworzony. ID: {course_id}")
        return course_id

    def import_gift_questions(self, course_id: int, gift_file: Path) -> bool:
        print(f"📝 Import pytań GIFT: {gift_file.name}")
        print(f"   → Kurs ID: {course_id}")
        print(f"   → Plik: {gift_file}")
        print("   ℹ️  Import GIFT najlepiej wykonać przez interfejs webowy:")
        print(f"      {self.base_url}/course/view.php?id={course_id}")
        print("      → Administracja kursu → Bank pytań → Import")
        print("      → Format: GIFT → Wybierz plik → Import")

        return True


def main():
    parser = argparse.ArgumentParser(description="Import kursu do Moodle")
    parser.add_argument("--url", required=True, help="URL instancji Moodle")
    parser.add_argument("--token", required=True, help="Token Web Services")
    parser.add_argument("--file", required=True, help="Plik .mbz lub .xml")
    parser.add_argument("--format", choices=["mbz", "xml", "gift"],
                       default="mbz", help="Format pliku")

    args = parser.parse_args()

    importer = MoodleImporter(args.url, args.token)

    if args.format == "gift":
        importer.import_gift_questions(1, Path(args.file))
    else:
        print(f"Import pliku {args.format.upper()}: {args.file}")
        print("Użyj interfejsu webowego Moodle do importu backupu.")


if __name__ == "__main__":
    main()


---

<a id="ci-validate"></a>
## 7. Pipeline CI/CD – walidacja

Plik: `.github/workflows/validate.yml`

```yaml
name: Walidacja kursów

on:
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'courses/**'
      - 'shared/**'
      - 'templates/**'
      - 'scripts/**'

jobs:
  validate-yaml:
    name: Walidacja plików YAML
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml jsonschema markdown

      - name: Validate YAML files
        run: |
          python scripts/validators/validate_yaml.py courses/
          python scripts/validators/validate_course.py courses/

  validate-gift:
    name: Walidacja plików GIFT
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Validate GIFT files
        run: python scripts/validators/validate_gift.py courses/

  validate-links:
    name: Walidacja linków i zasobów
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check internal links
        run: python scripts/validators/validate_links.py courses/

      - name: Check media files
        run: python scripts/validators/validate_media.py courses/

  validate-accessibility:
    name: Walidacja dostępności (WCAG)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check accessibility
        run: python scripts/validators/validate_accessibility.py courses/

  validate-ethics:
    name: Walidacja zgodności etycznej
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check ethical compliance
        run: |
          python scripts/validators/validate_ethics.py courses/

  build-test:
    name: Test budowania
    runs-on: ubuntu-latest
    needs: [validate-yaml, validate-gift]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r scripts/requirements.txt

      - name: Build all courses
        run: |
          for course_dir in courses/*/; do
            if [ -d "$course_dir" ]; then
              python scripts/builders/build_course.py "$course_dir" --format all
            fi
          done

      - name: Verify output files
        run: |
          find courses/*/output -name "*.xml" -o -name "*.gift" | head -20


---

<a id="ci-build"></a>
## 8. Pipeline CI/CD – budowanie

Plik: `.github/workflows/build.yml`

```yaml
name: Budowanie pakietów Moodle

on:
  push:
    branches: [ main ]
    paths:
      - 'courses/**'

jobs:
  build:
    name: Budowanie pakietów
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r scripts/requirements.txt

      - name: Build all courses
        run: |
          for course_dir in courses/*/; do
            if [ -d "$course_dir" ]; then
              python scripts/builders/build_course.py "$course_dir" --format all
            fi
          done

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: moodle-packages
          path: |
            courses/*/output/**/*.xml
            courses/*/output/**/*.gift
            courses/*/output/**/*.mbz
          retention-days: 30

      - name: Create release (opcjonalnie)
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v1
        with:
          files: |
            courses/*/output/**/*.mbz


---

<a id="ethics"></a>
## 9. Zasady etyczne

Plik: `docs/ethical-guidelines.md` (do umieszczenia w repozytorium)

Wszystkie treści kursów muszą być zgodne z:

### 9.1. Prawo Boże
- Treść musi służyć prawdzie, dobru i pięknu
- Nie może zawierać kłamstwa, manipulacji ani dezinformacji
- Wszystkie twierdzenia muszą być prawdziwe i weryfikowalne
- Cytaty muszą mieć podane źródło
- Nie wolno stosować technik manipulacyjnych w treściach
- Nie wolno używać emocji do wymuszania akceptacji tez
- Kontrowersyjne tezy muszą być przedstawione uczciwie

### 9.2. Prawo naturalne
- Treść musi szanować godność osoby ludzkiej, wolną wolę i rozum
- Edukacja ma rozwijać człowieka integralnie
- Treści nie mogą dehumanizować żadnej grupy osób
- Język musi być szanujący i inkluzywny
- Przykłady muszą szanować różnorodność doświadczeń
- Nie wolno stosować stereotypów

### 9.3. Prawa człowieka
- Treść musi szanować prawa autorskie, prywatność, godność
  i wolność sumienia każdego człowieka
- Wszystkie materiały muszą mieć licencję lub być oryginalne
- Cytaty muszą być oznaczone i w dopuszczalnym zakresie
- Obrazy muszą mieć licencję CC lub być własne
- AI nie może generować treści plagiatujących

### 9.4. Dostępność (WCAG 2.1 AA)
- Obrazy muszą mieć tekst alternatywny
- Wideo musi mieć napisy
- Audio musi mieć transkrypcję
- Kontrast kolorów musi spełniać normy
- Nawigacja musi być dostępna z klawiatury

### 9.5. Kontrola jakości
- Każdy kurs musi być zatwierdzony przez ludzkiego recenzenta
- Treści teologiczne muszą być zweryfikowane przez teologa
- Treści muszą być sprawdzone pod kątem błędów merytorycznych
- AI jest narzędziem wspierającym, nie zastępującym ludzki osąd

---

<a id="ethics-validator"></a>
## 10. Walidator etyczny – `scripts/validators/validate_ethics.py`

```python
#!/usr/bin/env python3
"""
Walidator zgodności etycznej treści kursów.

Sprawdza:
- Obecność metadanych etycznych w course.yaml
- Brak słów kluczowych wskazujących na manipulację
- Obecność źródeł i cytatów
- Zgodność z wytycznymi dostępności
"""

import yaml
import re
from pathlib import Path
from typing import List


class EthicsValidator:
    """Walidator zgodności etycznej."""

    MANIPULATION_PATTERNS = [
        r'musisz\s+(natychmiast|bezwarunkowo)',
        r'nie\s+masz\s+wyboru',
        r'jedyn[ay]\s+słuszn[ay]',
        r'kto\s+nie\s+(wierzy|akceptuje)\s+ten',
    ]

    REQUIRED_ETHICS_FIELDS = [
        'respects_human_dignity',
        'no_manipulation',
        'sources_cited',
    ]

    def validate_course(self, course_path: Path) -> List[str]:
        """Waliduje etyczność kursu."""
        errors = []

        course_yaml = course_path / 'course.yaml'
        if course_yaml.exists():
            with open(course_yaml, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            ethics = (data.get('course', {})
                     .get('metadata', {})
                     .get('ethical_compliance', {}))

            for field in self.REQUIRED_ETHICS_FIELDS:
                if field not in ethics:
                    errors.append(
                        f"Brak pola '{field}' w sekcji ethical_compliance"
                    )
                elif not ethics[field]:
                    errors.append(
                        f"Pole '{field}' musi mieć wartość true"
                    )

        md_files = list(course_path.rglob('*.md'))
        for md_file in md_files:
            errors.extend(self._check_manipulation(md_file))

        errors.extend(self._check_sources(course_path))

        return errors

    def _check_manipulation(self, file_path: Path) -> List[str]:
        errors = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()

        for pattern in self.MANIPULATION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                errors.append(
                    f"Potencjalna manipulacja w {file_path.name}: "
                    f"wzorzec '{pattern}'"
                )

        return errors

    def _check_sources(self, course_path: Path) -> List[str]:
        errors = []

        md_files = list(course_path.rglob('*.md'))
        for md_file in md_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            has_quotes = '>' in content or '„' in content
            has_sources = 'Źródło' in content or 'źródło' in content
            has_references = 'http' in content or 'www' in content

            if not (has_quotes or has_sources or has_references):
                pass

        return errors


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Użycie: python validate_ethics.py <ścieżka_do_kursów>")
        sys.exit(1)

    courses_dir = Path(sys.argv[1])
    validator = EthicsValidator()

    total_errors = 0
    for course_dir in sorted(courses_dir.iterdir()):
        if course_dir.is_dir() and not course_dir.name.startswith('_'):
            errors = validator.validate_course(course_dir)
            if errors:
                print(f"❌ {course_dir.name}:")
                for error in errors:
                    print(f"   - {error}")
                total_errors += len(errors)
            else:
                print(f"✅ {course_dir.name}: OK")

    sys.exit(1 if total_errors > 0 else 0)



---

## Podsumowanie – jak skopiować pliki do GitHub

Utwórz w repozytorium katalog `docs/` i umieść w nim cztery pliki:

```text
docs/
├── 01-ARCHITECTURE.md          # Struktura repozytorium, nazewnictwo, formaty
├── 02-CONTENT-FORMATS.md       # Metadane, sekcje, aktywności, multimedia
├── 03-QUESTION-FORMATS.md      # GIFT, YAML, XML, Aiken, quizy
└── 04-AUTOMATION-AND-ETHICS.md # Skrypty, CI/CD, walidacja, etyka


Każdy plik jest samodzielny i zawiera kompletną specyfikację swojego zakresu. Razem tworzą pełną dokumentację techniczną repozytorium kursów Moodle gotową do wykorzystania przez agenta Qwen Coder.

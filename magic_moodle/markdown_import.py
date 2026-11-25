"""Import konspektu Markdown do jawnego modelu katalogowego kursu."""
from __future__ import annotations

import json
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml


MODULE_RE = re.compile(r"^##\s+Moduł\s+(\d+)\.\s*(.+?)\s*$", re.IGNORECASE)
TOPIC_RE = re.compile(r"^###\s+(\d+)\.(\d+)\.\s*(.+?)\s*$")
SOURCE_RE = re.compile(r"^(\d+)_(\d+)_.*\.md$", re.IGNORECASE)
MAX_SOURCE_BYTES = 10 * 1024 * 1024


class MarkdownImportError(ValueError):
    """Błąd wejściowego konspektu lub bezpiecznego importu."""


@dataclass(frozen=True)
class Topic:
    module_number: int
    number: str
    title: str
    source: Path | None


@dataclass(frozen=True)
class Module:
    number: int
    title: str
    topics: tuple[Topic, ...]


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-") or "kurs"


def _read_source(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            raise MarkdownImportError(f"Plik {path.name} przekracza limit 10 MiB.")
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise MarkdownImportError(f"Nie można odczytać {path}: {exc}") from exc


def parse_outline(source: Path) -> tuple[Module, ...]:
    """Odczytuje wyłącznie jawne nagłówki modułów i tematów z course.md."""
    outline = _read_source(source)
    modules: list[dict] = []
    current_module: dict | None = None

    for line in outline.splitlines():
        module_match = MODULE_RE.match(line.strip())
        if module_match:
            current_module = {
                "number": int(module_match.group(1)),
                "title": module_match.group(2).strip(),
                "topics": [],
            }
            modules.append(current_module)
            continue

        topic_match = TOPIC_RE.match(line.strip())
        if topic_match and current_module is not None:
            module_number = int(topic_match.group(1))
            if module_number != current_module["number"]:
                raise MarkdownImportError(
                    f"Temat {topic_match.group(1)}.{topic_match.group(2)} "
                    f"znajduje się pod modułem {current_module['number']}."
                )
            current_module["topics"].append({
                "number": f"{module_number}.{int(topic_match.group(2))}",
                "title": topic_match.group(3).strip(),
            })

    if not modules:
        raise MarkdownImportError("Nie znaleziono nagłówków '## Moduł N.' w konspekcie.")
    if not any(module["topics"] for module in modules):
        raise MarkdownImportError("Konspekt nie zawiera tematów w formacie '### N.N. Tytuł'.")

    source_by_topic: dict[str, Path] = {}
    for path in source.parent.glob("*.md"):
        match = SOURCE_RE.match(path.name)
        if match:
            key = f"{int(match.group(1))}.{int(match.group(2))}"
            if key in source_by_topic:
                raise MarkdownImportError(f"Więcej niż jeden plik źródłowy dla tematu {key}.")
            source_by_topic[key] = path

    result: list[Module] = []
    seen: set[str] = set()
    for module in modules:
        topics: list[Topic] = []
        for item in module["topics"]:
            if item["number"] in seen:
                raise MarkdownImportError(f"Powtórzony temat w konspekcie: {item['number']}.")
            seen.add(item["number"])
            topics.append(Topic(
                module_number=module["number"],
                number=item["number"],
                title=item["title"],
                source=source_by_topic.get(item["number"]),
            ))
        result.append(Module(module["number"], module["title"], tuple(topics)))
    return tuple(result)



def split_markdown_chapters(markdown_text: str, root_title: str) -> list[tuple[str, str, bool]]:
    """Dzieli treść na rozdział główny i podrozdziały wyznaczone nagłówkami H2.

    Nagłówki H2 wewnątrz ogrodzonych bloków kodu pozostają zwykłą treścią.
    H3 i niższe poziomy nie dzielą książki, dzięki czemu zachowują hierarchię
    semantyczną wewnątrz podrozdziału. Fragmenty są zapisywane bez przepisywania
    treści; ich konkatenacja jest identyczna z wejściem.
    """
    lines = markdown_text.splitlines(keepends=True)
    boundaries: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_length = 0
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence_match:
            marker = fence_match.group(1)
            char = marker[0]
            if fence_char is None:
                fence_char, fence_length = char, len(marker)
            elif char == fence_char and len(marker) >= fence_length:
                fence_char, fence_length = None, 0
            continue
        if fence_char is not None:
            continue
        heading = re.match(r"^##[ \t]+(.+?)\s*#*\s*(?:\r?\n)?$", line)
        if heading:
            boundaries.append((index, heading.group(1).strip()))
    if not boundaries:
        return [(root_title, markdown_text, False)]

    parts: list[tuple[str, str, bool]] = []
    first_start = 0
    first_end = boundaries[0][0]
    root_content = "".join(lines[first_start:first_end])
    parts.append((root_title, root_content, False))
    for position, (start, heading_title) in enumerate(boundaries):
        end = boundaries[position + 1][0] if position + 1 < len(boundaries) else len(lines)
        parts.append((heading_title, "".join(lines[start:end]), True))
    return parts

def import_markdown_course(
    source: str | Path,
    destination: str | Path,
    *,
    title: str | None = None,
    short_name: str | None = None,
) -> dict:
    """Tworzy kurs w formacie loadera; nie nadpisuje istniejących danych."""
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    if not source_path.is_file() or source_path.name != "course.md":
        raise MarkdownImportError("Źródłem musi być istniejący plik course.md.")
    if destination_path == source_path.parent or source_path.parent in destination_path.parents:
        raise MarkdownImportError("Katalog docelowy nie może znajdować się wewnątrz źródeł.")
    if destination_path.exists() and any(destination_path.iterdir()):
        raise MarkdownImportError(
            f"Katalog docelowy {destination_path} nie jest pusty; import przerwany bez nadpisywania."
        )

    modules = parse_outline(source_path)
    course_title = (title or " ".join(source_path.parent.name.split("-"))).strip()
    course_short = (short_name or _slug(source_path.parent.name)[:40]).strip()
    if not course_title or not course_short:
        raise MarkdownImportError("Tytuł i nazwa skrócona kursu nie mogą być puste.")

    destination_path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination_path / "course.md")

    course_config = {
        "format_version": "1.0",
        "course": {
            "full_name": course_title,
            "short_name": course_short,
            "visible": 1,
            "format": "topics",
            "lang": "pl",
        },
        "description": {"format": "markdown", "markdown_file": "course.md"},
        "metadata": {
            "source_format": "markdown-outline",
            "source_file": source_path.name,
            "importer": "magic_moodle.markdown_import",
        },
    }
    (destination_path / "course.yaml").write_text(
        yaml.safe_dump(course_config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    section_summaries: list[dict] = []
    missing: list[dict] = []
    imported: list[dict] = []
    sections_root = destination_path / "sections"
    sections_root.mkdir()

    for module in modules:
        section_name = f"{module.number:02d}-modul-{_slug(module.title)[:48]}"
        section_path = sections_root / section_name
        section_path.mkdir()
        activities: list[dict] = []
        summary_lines = [f"# {module.number}. {module.title}", "", "## Tematy ujęte w konspekcie", ""]
        for topic in module.topics:
            if topic.source is None:
                missing.append({
                    "module": module.number,
                    "topic": topic.number,
                    "title": topic.title,
                    "status": "missing_source_file",
                })
                summary_lines.append(f"- {topic.number}. {topic.title} — brak pliku treści")
                continue

            activity_ref = f"book-{topic.number.replace('.', '-')}-{_slug(topic.title)[:42]}"
            activity_path = section_path / activity_ref
            chapters_path = activity_path / "chapters"
            chapters_path.mkdir(parents=True)
            source_text = _read_source(topic.source)
            chapter_parts = split_markdown_chapters(source_text, f"{topic.number}. {topic.title}")
            chapter_entries: list[dict] = []
            for chapter_index, (chapter_title, chapter_text, is_subchapter) in enumerate(chapter_parts, start=1):
                chapter_name = f"{chapter_index:02d}-{_slug(chapter_title)[:52]}.md"
                (chapters_path / chapter_name).write_text(chapter_text, encoding="utf-8")
                chapter_entries.append({
                    "title": chapter_title,
                    "subchapter": is_subchapter,
                    "content_file": f"chapters/{chapter_name}",
                    "hidden": False,
                })
            book_config = {
                "book": {
                    "name": f"{topic.number}. {topic.title}",
                    "intro": f"Materiał źródłowy zaimportowany z pliku {topic.source.name}.",
                    "intro_format": "markdown",
                    "numbering": 1,
                    "customtitles": 0,
                    "chapters": chapter_entries,
                }
            }
            (activity_path / "book.yaml").write_text(
                yaml.safe_dump(book_config, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            activities.append({
                "type": "book",
                "ref": activity_ref,
                "name": f"{topic.number}. {topic.title}",
            })
            imported.append({
                "module": module.number,
                "topic": topic.number,
                "title": topic.title,
                "source_file": topic.source.name,
                "activity_ref": activity_ref,
            })
            summary_lines.append(f"- {topic.number}. {topic.title}")

        section_config = {
            "id": module.number,
            "name": f"Moduł {module.number}: {module.title}",
            "visible": 1,
            "summary": {"format": "markdown", "markdown_file": "section.md"},
            "modules": activities,
        }
        (section_path / "section.yaml").write_text(
            yaml.safe_dump(section_config, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        (section_path / "section.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
        section_summaries.append({
            "module": module.number,
            "title": module.title,
            "topics_in_outline": len(module.topics),
            "activities_created": len(activities),
        })

    report = {
        "source": str(source_path),
        "destination": str(destination_path),
        "modules": len(modules),
        "topics_in_outline": sum(len(module.topics) for module in modules),
        "activities_created": len(imported),
        "missing_topics": missing,
        "sections": section_summaries,
        "activities": imported,
        "quiz_policy": "No quizzes or answer keys are generated from headings or prose.",
        "mbz_status": "not_generated",
    }
    (destination_path / "import-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report

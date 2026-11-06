"""Wczytywanie istniejącego formatu katalogów kursu z repozytorium."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import base64
import yaml

from .models import Activity, Course, Section


class CourseLoadError(ValueError):
    """Błąd odczytu lub struktury danych kursu."""


def _read_text(path: Path, *, max_bytes: int = 10 * 1024 * 1024) -> str:
    """Read bounded UTF-8 text to avoid unbounded local-file memory use."""
    try:
        if path.stat().st_size > max_bytes:
            raise CourseLoadError(f"{path}: plik przekracza limit {max_bytes} B.")
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CourseLoadError(f"Nie można odczytać {path}: {exc}") from exc


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(_read_text(path, max_bytes=2 * 1024 * 1024))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise CourseLoadError(f"Nie można odczytać {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CourseLoadError(f"{path}: oczekiwano dokumentu YAML będącego mapą.")
    return data


def _safe_path(base: Path, relative: str, label: str) -> Path:
    """Resolve a relative path and reject absolute paths and symlink escapes."""
    if not isinstance(relative, str) or not relative or "\\x00" in relative:
        raise CourseLoadError(f"{label}: ścieżka musi być niepustym tekstem.")
    supplied = Path(relative)
    if supplied.is_absolute():
        raise CourseLoadError(f"{label}: ścieżka bezwzględna jest niedozwolona: {relative}")
    base_resolved = base.resolve()
    candidate = (base_resolved / supplied).resolve()
    if not candidate.is_relative_to(base_resolved):
        raise CourseLoadError(f"{label}: ścieżka wychodzi poza dozwolony katalog: {relative}")
    return candidate


def _load_activity_resource(section_path: Path, kind: str, ref: str) -> tuple[dict[str, Any], dict[str, str]]:
    target = _safe_path(section_path, ref, "Aktywność")
    resource: dict[str, Any] = {}
    content: dict[str, str] = {}

    config_names = {
        "book": ("book.yaml", "book"),
        "assignment": ("assignment.yaml", None),
        "glossary": ("glossary.yaml", "glossary"),
        "quiz": ("quiz.yaml", None),
        "url": ("url.yaml", "url"),
    }
    if kind in config_names and target.is_dir():
        filename, root_key = config_names[kind]
        config_path = _safe_path(target, filename, "Konfiguracja aktywności")
        if config_path.is_file():
            raw = _read_yaml(config_path)
            nested = raw.get(root_key) if root_key else raw
            if kind == "url" and isinstance(nested, str):
                resource = {"url": nested}
                nested = None
            if nested is None and kind == "url":
                pass
            elif not isinstance(nested, dict):
                raise CourseLoadError(
                    f"{config_path}: oczekiwano mapy"
                    + (f" w polu '{root_key}'." if root_key else ".")
                )
            else:
                resource = nested

            if kind == "book":
                chapters = resource.get("chapters", [])
                if not isinstance(chapters, list):
                    raise CourseLoadError(f"{config_path}: 'chapters' musi być listą.")
                for index, chapter in enumerate(chapters):
                    if not isinstance(chapter, dict):
                        raise CourseLoadError(f"{config_path}: chapters[{index}] musi być mapą.")
                    chapter_file = chapter.get("content_file")
                    if chapter_file:
                        if not isinstance(chapter_file, str):
                            raise CourseLoadError(
                                f"{config_path}: chapters[{index}].content_file musi być tekstem."
                            )
                        path = _safe_path(target, chapter_file, str(config_path))
                        if path.is_file():
                            content[chapter_file] = _read_text(path)
            elif kind == "assignment":
                markdown_file = resource.get("markdown_file")
                if isinstance(markdown_file, str):
                    path = _safe_path(target, markdown_file, str(config_path))
                    if path.is_file():
                        content[markdown_file] = _read_text(path)
            elif kind == "quiz":
                questions_file = resource.get("questions_file")
                if isinstance(questions_file, str):
                    path = _safe_path(target, questions_file, str(config_path))
                    if path.is_file():
                        content[questions_file] = _read_text(path, max_bytes=2 * 1024 * 1024)

    elif kind == "file" and target.is_file():
        if target.stat().st_size > 5 * 1024 * 1024:
            raise CourseLoadError(f"{target}: plik przekracza limit 5 MiB.")
        content[target.name] = base64.b64encode(target.read_bytes()).decode("ascii")

    elif kind == "url" and target.is_file():
        raw = _read_yaml(target)
        nested = raw.get("url", raw)
        if isinstance(nested, str):
            resource = {"url": nested}
        elif isinstance(nested, dict):
            resource = nested
        else:
            raise CourseLoadError(f"{target}: konfiguracja URL musi zawierać tekstowy adres URL lub mapę.")

    elif kind in {"page", "label"} and target.is_file():
        content[target.name] = _read_text(target)

    return resource, content


def load_course(root: str | Path) -> Course:
    """Wczytuje course.yaml, sekcje i rozpoznane zasoby aktywności."""
    root = Path(root).resolve()
    course_file = _safe_path(root, "course.yaml", "Konfiguracja kursu")
    if not course_file.is_file():
        raise CourseLoadError(f"Brak pliku {course_file}")

    raw = _read_yaml(course_file)
    course_data = raw.get("course")
    if not isinstance(course_data, dict):
        raise CourseLoadError("course.yaml: wymagany jest obiekt 'course'.")

    full_name = course_data.get("full_name")
    short_name = course_data.get("short_name")
    if not isinstance(full_name, str) or not full_name.strip():
        raise CourseLoadError("course.full_name musi być niepustym tekstem.")
    if not isinstance(short_name, str) or not short_name.strip():
        raise CourseLoadError("course.short_name musi być niepustym tekstem.")

    sections_root = _safe_path(root, "sections", "Katalog sekcji")
    sections: list[Section] = []
    if sections_root.exists():
        if not sections_root.is_dir():
            raise CourseLoadError("Katalog sections musi być katalogiem.")
        for section_entry in sorted(p for p in sections_root.iterdir() if p.is_dir()):
            section_path = section_entry.resolve()
            if not section_path.is_relative_to(sections_root):
                raise CourseLoadError(f"Sekcja {section_entry.name}: dowiązanie symboliczne wychodzi poza katalog sections.")
            config_path = _safe_path(section_path, "section.yaml", "Konfiguracja sekcji")
            if not config_path.is_file():
                continue
            section_raw = _read_yaml(config_path)
            section_id = str(section_raw.get("id", section_path.name))
            section_name = section_raw.get("name", section_path.name)
            if not isinstance(section_name, str) or not section_name.strip():
                raise CourseLoadError(f"{config_path}: pole 'name' musi być tekstem.")
            modules = section_raw.get("modules", [])
            if modules is None:
                modules = []
            if not isinstance(modules, list):
                raise CourseLoadError(f"{config_path}: 'modules' musi być listą.")
            activities: list[Activity] = []
            for index, item in enumerate(modules):
                if not isinstance(item, dict):
                    raise CourseLoadError(f"{config_path}: modules[{index}] musi być mapą.")
                kind, ref, name = item.get("type"), item.get("ref"), item.get("name")
                if not all(isinstance(v, str) and v.strip() for v in (kind, ref, name)):
                    raise CourseLoadError(
                        f"{config_path}: modules[{index}] wymaga niepustych pól type, ref i name."
                    )
                resource, activity_content = _load_activity_resource(section_path, kind, ref)
                activities.append(Activity(
                    kind=kind, ref=ref, name=name, config=item,
                    resource=resource, content=activity_content,
                ))
            sections.append(Section(
                id=section_id, name=section_name, path=section_path,
                activities=tuple(activities),
            ))

    description = ""
    description_config = raw.get("description", {})
    if isinstance(description_config, dict):
        markdown_file = description_config.get("markdown_file")
        if isinstance(markdown_file, str):
            description_path = _safe_path(root, markdown_file, "description.markdown_file")
            if description_path.is_file():
                description = _read_text(description_path)

    return Course(
        root=root, full_name=full_name.strip(), short_name=short_name.strip(),
        metadata=raw, sections=tuple(sections), description=description,
    )

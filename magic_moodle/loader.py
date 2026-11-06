"""Wczytywanie istniejącego formatu katalogów kursów z repozytorium."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Activity, Course, Section


class CourseLoadError(ValueError):
    """Błąd odczytu lub struktury danych kursu."""


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CourseLoadError(f"Nie można odczytać {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CourseLoadError(f"{path}: oczekiwano dokumentu YAML będącego mapą.")
    return data


def load_course(root: str | Path) -> Course:
    """Wczytuje course.yaml i sekcje wskazane w katalogu sections/."""
    root = Path(root).resolve()
    course_file = root / "course.yaml"
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

    sections_root = root / "sections"
    sections: list[Section] = []
    if sections_root.exists():
        for section_path in sorted(p for p in sections_root.iterdir() if p.is_dir()):
            config_path = section_path / "section.yaml"
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
                activities.append(Activity(kind=kind, ref=ref, name=name, config=item))
            sections.append(Section(
                id=section_id, name=section_name, path=section_path,
                activities=tuple(activities),
            ))

    description = ""
    description_config = raw.get("description", {})
    if isinstance(description_config, dict):
        markdown_file = description_config.get("markdown_file")
        if isinstance(markdown_file, str):
            description_path = root / markdown_file
            if description_path.is_file():
                description = description_path.read_text(encoding="utf-8")

    return Course(
        root=root, full_name=full_name.strip(), short_name=short_name.strip(),
        metadata=raw, sections=tuple(sections), description=description,
    )

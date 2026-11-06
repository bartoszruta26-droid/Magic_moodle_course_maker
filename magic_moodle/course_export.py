"""Portable, lossless JSON representation of a loaded course.

This is an interchange/debugging format, not a Moodle MBZ backup.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .models import Activity, Course


FORMAT = "magic-moodle-course-manifest"
FORMAT_VERSION = 1


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Nieobsługiwany typ danych w manifeście: {type(value).__name__}")


def _activity_manifest(activity: Activity) -> dict[str, Any]:
    return {
        "type": activity.kind,
        "ref": activity.ref,
        "name": activity.name,
        "config": _json_value(activity.config),
        "resource": _json_value(activity.resource),
        "content": dict(sorted(activity.content.items())),
    }


def course_manifest(course: Course) -> dict[str, Any]:
    """Build a deterministic manifest without exposing absolute filesystem paths."""
    return {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "course": {
            "full_name": course.full_name,
            "short_name": course.short_name,
            "description": course.description,
            "metadata": _json_value(course.metadata),
        },
        "sections": [
            {
                "id": section.id,
                "name": section.name,
                "activities": [_activity_manifest(item) for item in section.activities],
            }
            for section in course.sections
        ],
        "statistics": {
            "section_count": course.section_count,
            "activity_count": course.activity_count,
            "activity_types": course.activity_types,
        },
        "compatibility": {
            "target": "intermediate representation",
            "moodle_importable": False,
            "note": "Manifest nie jest kopią zapasową Moodle (MBZ) ani plikiem importu kursu.",
        },
    }


def to_course_json(course: Course) -> str:
    """Serialize a course manifest as stable UTF-8 JSON."""
    return json.dumps(
        course_manifest(course),
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    ) + "\n"


def export_course_json(course: Course, destination: str | Path) -> Path:
    """Write a course manifest, creating the destination directory if needed."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_course_json(course), encoding="utf-8")
    return path

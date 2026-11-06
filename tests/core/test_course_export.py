from __future__ import annotations

import json
from pathlib import Path

from magic_moodle.course_export import FORMAT, course_manifest, export_course_json, to_course_json
from magic_moodle.loader import load_course


def _course(tmp_path: Path):
    (tmp_path / "sections" / "01").mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs testowy\n  short_name: TEST\n"
        "description:\n  markdown_file: description.md\n",
        encoding="utf-8",
    )
    (tmp_path / "description.md").write_text("Opis kursu", encoding="utf-8")
    (tmp_path / "sections" / "01" / "section.yaml").write_text(
        "id: s1\nname: Sekcja 1\nmodules:\n"
        "  - type: page\n    ref: page.md\n    name: Strona\n",
        encoding="utf-8",
    )
    (tmp_path / "sections" / "01" / "page.md").write_text("# Treść", encoding="utf-8")
    return load_course(tmp_path)


def test_manifest_contains_sections_activities_and_content(tmp_path):
    course = _course(tmp_path)
    manifest = course_manifest(course)
    assert manifest["format"] == FORMAT
    assert manifest["statistics"]["section_count"] == 1
    assert manifest["statistics"]["activity_count"] == 1
    activity = manifest["sections"][0]["activities"][0]
    assert activity["type"] == "page"
    assert activity["content"]["page.md"] == "# Treść"
    assert manifest["compatibility"]["moodle_importable"] is False
    assert str(tmp_path) not in to_course_json(course)


def test_export_is_valid_utf8_json_and_creates_parent(tmp_path):
    destination = tmp_path / "nested" / "manifest.json"
    export_course_json(_course(tmp_path), destination)
    data = json.loads(destination.read_text(encoding="utf-8"))
    assert data["course"]["full_name"] == "Kurs testowy"
    assert data["course"]["description"] == "Opis kursu"


def test_manifest_rejects_unserializable_metadata(tmp_path):
    course = _course(tmp_path)
    # Replace the metadata with a value that YAML cannot normally produce.
    from dataclasses import replace
    broken = replace(course, metadata={"custom": object()})
    import pytest
    with pytest.raises(TypeError, match="Nieobsługiwany typ"):
        course_manifest(broken)

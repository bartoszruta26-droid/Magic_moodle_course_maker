from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs

import pytest

from magic_moodle.loader import load_course
from magic_moodle.moodle_api import (
    MoodleAPIError, MoodleClient, MoodleConfig, _flatten,
)
from magic_moodle.moodle_publish import build_publish_plan, publish_course


def test_flatten_moodle_nested_parameters():
    assert _flatten({"courses": [{"fullname": "A", "visible": True}]}) == [
        ("courses[0][fullname]", "A"),
        ("courses[0][visible]", "1"),
    ]


def test_reject_insecure_remote_url():
    with pytest.raises(MoodleAPIError, match="HTTPS"):
        MoodleClient(MoodleConfig("http://moodle.example", "secret"))


def test_moodle_client_posts_token_and_function():
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size=-1):
            return b'{"sitename":"Test Moodle","functions":[]}'

    captured = {}
    def fake_urlopen(request, **kwargs):
        captured["url"] = request.full_url
        captured["body"] = parse_qs(request.data.decode())
        return Response()

    client = MoodleClient(MoodleConfig("https://moodle.example/moodle", "secret"))
    with patch("urllib.request.urlopen", fake_urlopen):
        result = client.site_info()
    assert result["sitename"] == "Test Moodle"
    assert captured["url"].endswith("/moodle/webservice/rest/server.php")
    assert captured["body"]["wstoken"] == ["secret"]
    assert captured["body"]["wsfunction"] == ["core_webservice_get_site_info"]


def test_moodle_error_payload_is_raised():
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size=-1): return b'{"exception":"moodle_exception","errorcode":"invalidtoken","message":"Bad token"}'

    client = MoodleClient(MoodleConfig("https://moodle.example", "secret"))
    with patch("urllib.request.urlopen", lambda *a, **k: Response()):
        with pytest.raises(MoodleAPIError, match="invalidtoken"):
            client.call("core_webservice_get_site_info")


def _sample_course(tmp_path: Path):
    section = tmp_path / "sections" / "01"
    section.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs testowy\n  short_name: TEST\n"
        "  format: topics\n  visible: 1\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Wprowadzenie\nmodules:\n"
        "  - type: page\n    ref: page.md\n    name: Pierwsza strona\n",
        encoding="utf-8",
    )
    (section / "page.md").write_text("# Tytuł\n\nTreść **ważna**.", encoding="utf-8")
    return load_course(tmp_path)


def test_build_publish_plan_converts_markdown_and_has_no_side_effects(tmp_path):
    plan = build_publish_plan(_sample_course(tmp_path), 2)
    assert plan.course["categoryid"] == 2
    assert plan.activities[0]["content"] == "<h2>Tytuł</h2>\n<p>Treść <strong>ważna</strong>.</p>"
    assert not plan.warnings


def test_publish_dry_run_does_not_call_moodle(tmp_path):
    course = _sample_course(tmp_path)
    class NoNetwork:
        def __getattr__(self, name):
            raise AssertionError("dry-run must not call Moodle")
    result = publish_course(NoNetwork(), course, 2, dry_run=True)
    assert result["dry_run"] is True
    assert result["activity_count"] == 1


def test_publish_stops_before_writes_for_unsupported_activity(tmp_path):
    course = _sample_course(tmp_path)
    from dataclasses import replace
    from magic_moodle.models import Activity, Section
    old = course.sections[0]
    changed = replace(course, sections=(replace(old, activities=(
        Activity("quiz", "quiz", "Test"),)),))
    with pytest.raises(MoodleAPIError, match="zatrzymana przed zmianami"):
        publish_course(object(), changed, 2, dry_run=False)


def test_publish_plan_uses_moodle_general_section_numbering_and_html_summary(tmp_path):
    section = tmp_path / "sections" / "00"
    section.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs\n  short_name: KURS\n"
        "  format: topics\n",
        encoding="utf-8",
    )
    (tmp_path / "course.md").write_text("# Opis\n\nTreść kursu.", encoding="utf-8")
    (tmp_path / "sections" / "00" / "section.yaml").write_text(
        "id: '00'\nname: Ogólne\nmodules: []\n", encoding="utf-8"
    )
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs\n  short_name: KURS\n  format: topics\n"
        "description:\n  markdown_file: course.md\n",
        encoding="utf-8",
    )
    plan = build_publish_plan(load_course(tmp_path), 4)
    assert plan.course["numsections"] == 0
    assert plan.course["summary"] == "<h2>Opis</h2>\n<p>Treść kursu.</p>"


def test_ensure_course_reuses_existing_shortname():
    client = MoodleClient(MoodleConfig("https://moodle.example", "secret"))
    with patch.object(client, "get_course_by_shortname", return_value={"id": 42, "shortname": "KURS"}):
        with patch.object(client, "create_course") as create:
            course, created = client.ensure_course({"shortname": "KURS"})
    assert course["id"] == 42
    assert created is False
    create.assert_not_called()


def test_url_activity_is_loaded_and_added_to_publish_plan(tmp_path):
    section = tmp_path / "sections" / "01"
    section.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\\n  full_name: Kurs URL\\n  short_name: KURL\\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\\nname: Zasoby\\nmodules:\\n"
        "  - type: url\\n    ref: source.yaml\\n    name: Dokumentacja\\n",
        encoding="utf-8",
    )
    (section / "source.yaml").write_text(
        "url: https://docs.moodle.org/401/\\n",
        encoding="utf-8",
    )
    plan = build_publish_plan(load_course(tmp_path), 2)
    assert not plan.warnings
    assert plan.activities[0]["type"] == "url"
    assert plan.activities[0]["externalurl"] == "https://docs.moodle.org/401/"


def test_url_activity_without_target_stops_preflight(tmp_path):
    section = tmp_path / "sections" / "01"
    section.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\\n  full_name: Kurs URL\\n  short_name: KURL\\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\\nname: Zasoby\\nmodules:\\n"
        "  - type: url\\n    ref: source.yaml\\n    name: Brak adresu\\n",
        encoding="utf-8",
    )
    (section / "source.yaml").write_text("title: Bez adresu\\n", encoding="utf-8")
    plan = build_publish_plan(load_course(tmp_path), 2)
    assert any("nie zawiera pola externalurl/url" in warning for warning in plan.warnings)


def test_create_url_activity_sends_target_url_to_plugin():
    client = MoodleClient(MoodleConfig("https://moodle.example", "secret"))
    with patch.object(client, "call", return_value={"created": True}) as call:
        client.create_activity(7, 1, {
            "type": "url",
            "name": "Dokumentacja",
            "content": "",
            "externalurl": "https://docs.moodle.org/401/",
        })
    assert call.call_args.args[0] == "local_magicmoodle_create_activity"
    assert call.call_args.args[1]["modname"] == "url"
    assert call.call_args.args[1]["externalurl"] == "https://docs.moodle.org/401/"

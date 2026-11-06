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
        """course:
  full_name: Kurs URL
  short_name: KURL
""",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        """id: '01'
name: Zasoby
modules:
  - type: url
    ref: source.yaml
    name: Dokumentacja
""",
        encoding="utf-8",
    )
    (section / "source.yaml").write_text(
        """url: https://docs.moodle.org/401/""",
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
        """course:
  full_name: Kurs URL
  short_name: KURL
""",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        """id: '01'
name: Zasoby
modules:
  - type: url
    ref: source.yaml
    name: Brak adresu
""",
        encoding="utf-8",
    )
    (section / "source.yaml").write_text("""title: Bez adresu""", encoding="utf-8")
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


def test_invalid_url_is_rejected_during_preflight(tmp_path):
    section = tmp_path / "sections" / "01"
    section.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        """course:
  full_name: Kurs URL
  short_name: KURL
""",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        """id: '01'
name: Zasoby
modules:
  - type: url
    ref: source.yaml
    name: Niebezpieczny adres
""",
        encoding="utf-8",
    )
    (section / "source.yaml").write_text(
        """url: javascript:alert(1)
""",
        encoding="utf-8",
    )
    plan = build_publish_plan(load_course(tmp_path), 2)
    assert any("nieprawidłowy adres" in warning for warning in plan.warnings)
    with pytest.raises(MoodleAPIError, match="zatrzymana przed zmianami"):
        publish_course(object(), load_course(tmp_path), 2)


def test_book_activity_is_loaded_and_prepared_for_moodle(tmp_path):
    section = tmp_path / "sections" / "01"
    bookdir = section / "book"
    bookdir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs książka\n  short_name: KBOOK\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Materiały\nmodules:\n"
        "  - type: book\n    ref: book\n    name: Podręcznik\n",
        encoding="utf-8",
    )
    (bookdir / "book.yaml").write_text(
        "book:\n  numbering: 1\n  chapters:\n"
        "    - title: Wprowadzenie\n      content_file: intro.md\n"
        "    - title: Podstawy\n      content_file: basics.md\n      subchapter: true\n",
        encoding="utf-8",
    )
    (bookdir / "intro.md").write_text("# Start\n\nTreść pierwsza.", encoding="utf-8")
    (bookdir / "basics.md").write_text("Treść **drugiego** rozdziału.", encoding="utf-8")

    plan = build_publish_plan(load_course(tmp_path), 2)
    assert not plan.warnings
    book = plan.activities[0]
    assert book["type"] == "book"
    assert book["numbering"] == 1
    assert book["chapters"][0]["content"] == "<h2>Start</h2>\n<p>Treść pierwsza.</p>"
    assert book["chapters"][1]["subchapter"] is True
    assert "<strong>drugiego</strong>" in book["chapters"][1]["content"]


def test_book_preflight_rejects_missing_chapter_file(tmp_path):
    section = tmp_path / "sections" / "01"
    bookdir = section / "book"
    bookdir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs książka\n  short_name: KBOOK\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Materiały\nmodules:\n"
        "  - type: book\n    ref: book\n    name: Podręcznik\n",
        encoding="utf-8",
    )
    (bookdir / "book.yaml").write_text(
        "book:\n  chapters:\n    - title: Brak\n      content_file: missing.md\n",
        encoding="utf-8",
    )
    plan = build_publish_plan(load_course(tmp_path), 2)
    assert any("brak pliku rozdziału" in warning for warning in plan.warnings)


def test_create_book_calls_registered_moodle_service():
    client = MoodleClient(MoodleConfig("https://moodle.example", "secret"))
    chapters = [{"title": "Start", "content": "<p>Treść</p>", "subchapter": False}]
    with patch.object(client, "call", return_value={"created": True}) as call:
        client.create_book(7, 1, {
            "name": "Podręcznik",
            "chapters": chapters,
            "numbering": 1,
        })
    assert call.call_args.args[0] == "local_magicmoodle_create_book"
    assert call.call_args.args[1]["chapters"] == chapters
    assert call.call_args.args[1]["numbering"] == 1


def test_moodle_book_plugin_exposes_secure_moodle_41_endpoint():
    plugin = (
        Path(__file__).parents[2]
        / "moodle-plugin/local/magicmoodle/classes/external/create_book.php"
    ).read_text(encoding="utf-8")
    services = (
        Path(__file__).parents[2]
        / "moodle-plugin/local/magicmoodle/db/services.php"
    ).read_text(encoding="utf-8")
    assert "class create_book extends \\external_api" in plugin
    assert "require_capability('mod/book:edit', $modulecontext)" in plugin
    assert "5 * 1024 * 1024" in plugin
    assert "'local_magicmoodle_create_book'" in services


def test_publish_routes_book_activity_to_book_endpoint(tmp_path):
    section = tmp_path / "sections" / "01"
    bookdir = section / "book"
    bookdir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs książka\n  short_name: KBOOK\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Materiały\nmodules:\n"
        "  - type: book\n    ref: book\n    name: Podręcznik\n",
        encoding="utf-8",
    )
    (bookdir / "book.yaml").write_text(
        "book:\n  chapters:\n    - title: Start\n      content: Treść rozdziału.\n",
        encoding="utf-8",
    )
    course = load_course(tmp_path)

    class FakeClient:
        def site_info(self):
            return {"functions": [
                {"name": "core_course_get_courses_by_field"},
                {"name": "core_course_create_courses"},
                {"name": "local_magicmoodle_update_section"},
                {"name": "local_magicmoodle_create_activity"},
                {"name": "local_magicmoodle_create_book"},
            ]}

        def ensure_course(self, payload):
            return ({"id": 42, "shortname": "KBOOK"}, True)

        def update_section(self, courseid, sectionnum, name):
            return {"section": sectionnum}

        def create_book(self, courseid, sectionnum, activity):
            return {"modname": "book", "name": activity["name"], "created": True}

        def create_activity(self, *args):
            raise AssertionError("Book must use create_book, not create_activity")

    result = publish_course(FakeClient(), course, 2)
    assert result["activities_created"][0]["modname"] == "book"


def _sample_quiz_course(tmp_path: Path):
    section = tmp_path / "sections" / "01"
    quizdir = section / "quiz-01"
    quizdir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs testowy\n  short_name: QUIZTEST\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Testowanie\nmodules:\n"
        "  - type: quiz\n    ref: quiz-01\n    name: Test wiedzy\n",
        encoding="utf-8",
    )
    (quizdir / "quiz.yaml").write_text(
        "name: Test wiedzy\nintro: Weryfikacja podstaw.\n"
        "time_limit: 600\nattempts: 2\ngrade_passing: 60\n"
        "shuffle_answers: true\nquestions_file: questions.gift\n"
        "completion:\n  enabled: true\n  type: grade\n  min_score: 60\n",
        encoding="utf-8",
    )
    (quizdir / "questions.gift").write_text(
        "::q1:: Czy Moodle obsługuje import GIFT? {TRUE}\n\n"
        "::q2:: Wybierz właściwy protokół. {=HTTPS ~HTTP}\n",
        encoding="utf-8",
    )
    return load_course(tmp_path)


def test_quiz_activity_is_preflighted_with_gift_and_settings(tmp_path):
    plan = build_publish_plan(_sample_quiz_course(tmp_path), 2)
    assert not plan.warnings
    quiz = plan.activities[0]
    assert quiz["type"] == "quiz"
    assert quiz["questioncount"] == 2
    assert quiz["timelimit"] == 600
    assert quiz["attempts"] == 2
    assert quiz["passingpercent"] == 60
    assert quiz["shuffleanswers"] is True
    assert quiz["completionenabled"] is True
    assert quiz["completiontype"] == "grade"
    assert "<p>Weryfikacja podstaw.</p>" == quiz["intro"]


def test_quiz_preflight_rejects_missing_gift_file(tmp_path):
    course = _sample_quiz_course(tmp_path)
    from dataclasses import replace
    old = course.sections[0]
    activity = old.activities[0]
    changed = replace(activity, content={})
    course = replace(course, sections=(replace(old, activities=(changed,)),))
    plan = build_publish_plan(course, 2)
    assert any("brak pliku pytań" in warning for warning in plan.warnings)


def test_quiz_preflight_rejects_invalid_gift(tmp_path):
    course = _sample_quiz_course(tmp_path)
    from dataclasses import replace
    old = course.sections[0]
    activity = old.activities[0]
    changed = replace(activity, content={"questions.gift": "::broken:: Brak odpowiedzi"})
    course = replace(course, sections=(replace(old, activities=(changed,)),))
    plan = build_publish_plan(course, 2)
    assert any("błąd GIFT" in warning for warning in plan.warnings)


def test_create_quiz_calls_registered_moodle_service():
    client = MoodleClient(MoodleConfig("https://moodle.example", "secret"))
    gift = "::q1:: Pytanie testowe? {TRUE}"
    with patch.object(client, "call", return_value={"created": True}) as call:
        client.create_quiz(7, 1, {
            "name": "Test wiedzy",
            "intro": "<p>Wprowadzenie</p>",
            "gift": gift,
            "timelimit": 600,
            "attempts": 2,
            "grade": 10,
            "passingpercent": 60,
            "shuffleanswers": True,
            "questionsperpage": 1,
            "completionenabled": True,
            "completiontype": "grade",
        })
    assert call.call_args.args[0] == "local_magicmoodle_create_quiz"
    assert call.call_args.args[1]["gift"] == gift
    assert call.call_args.args[1]["passingpercent"] == 60
    assert call.call_args.args[1]["completionenabled"] is True
    assert call.call_args.args[1]["completiontype"] == "grade"


def test_publish_routes_quiz_to_native_gift_import_endpoint(tmp_path):
    course = _sample_quiz_course(tmp_path)

    class FakeClient:
        def site_info(self):
            return {"functions": [
                {"name": "core_course_get_courses_by_field"},
                {"name": "core_course_create_courses"},
                {"name": "local_magicmoodle_update_section"},
                {"name": "local_magicmoodle_create_quiz"},
            ]}

        def ensure_course(self, payload):
            return ({"id": 42, "shortname": "QUIZTEST"}, True)

        def update_section(self, courseid, sectionnum, name):
            return {"section": sectionnum}

        def create_quiz(self, courseid, sectionnum, activity):
            assert activity["questioncount"] == 2
            return {"modname": "quiz", "name": activity["name"], "questioncount": 2}

        def create_activity(self, *args):
            raise AssertionError("Quiz must use create_quiz")

    result = publish_course(FakeClient(), course, 2)
    assert result["activities_created"][0]["modname"] == "quiz"


def test_quiz_endpoint_uses_native_gift_import_and_quiz_slot_api():
    plugin = (
        Path(__file__).parents[2]
        / "moodle-plugin/local/magicmoodle/classes/external/create_quiz.php"
    ).read_text(encoding="utf-8")
    services = (
        Path(__file__).parents[2]
        / "moodle-plugin/local/magicmoodle/db/services.php"
    ).read_text(encoding="utf-8")
    assert "new \\qformat_gift()" in plugin
    assert "importprocess()" in plugin
    assert "quiz_add_quiz_question" in plugin
    assert "quiz_update_sumgrades" in plugin
    assert "completionusegrade" in plugin
    assert "completionpassgrade" in plugin
    assert "'local_magicmoodle_create_quiz'" in services


def test_existing_med10_quiz_gift_is_accepted_by_preflight_parser():
    from magic_moodle.gift import parse_gift, validate_question_bank
    giftfile = (
        Path(__file__).parents[2]
        / "courses/03-kurs-masazysta-med10/sections/"
          "01-med-10-1-bezpieczenstwo-i-higiena-pracy/quiz-01/questions.gift"
    )
    bank = parse_gift(giftfile.read_text(encoding="utf-8"), source_name=str(giftfile))
    assert bank.questions
    assert not validate_question_bank(bank)


def test_existing_med10_quiz_config_builds_a_valid_publish_plan():
    root = Path(__file__).parents[2] / "courses/03-kurs-masazysta-med10"
    course = load_course(root)
    selected = next(
        (activity, section)
        for section in course.sections
        for activity in section.activities
        if activity.kind == "quiz"
    )
    activity, section = selected
    from dataclasses import replace
    isolated = replace(
        course,
        sections=(replace(section, activities=(activity,)),),
    )
    plan = build_publish_plan(isolated, 2)
    assert not plan.warnings
    assert plan.activities[0]["type"] == "quiz"
    assert plan.activities[0]["completionenabled"] is True
    assert plan.activities[0]["passingpercent"] == 60
    assert plan.activities[0]["questioncount"] > 0


def test_book_preflight_rejects_combined_chapter_content_over_five_mib(tmp_path):
    section = tmp_path / "sections" / "01"
    bookdir = section / "book"
    bookdir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs książka\n  short_name: KBOOK\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Materiały\nmodules:\n"
        "  - type: book\n    ref: book\n    name: Podręcznik\n",
        encoding="utf-8",
    )
    (bookdir / "book.yaml").write_text(
        "book:\n  chapters:\n"
        "    - title: Duży rozdział\n      content_file: large.md\n",
        encoding="utf-8",
    )
    (bookdir / "large.md").write_text("x" * (5 * 1024 * 1024 + 1), encoding="utf-8")
    plan = build_publish_plan(load_course(tmp_path), 2)
    assert any("przekracza limit 5 MiB" in warning for warning in plan.warnings)
    with pytest.raises(MoodleAPIError, match="zatrzymana przed zmianami"):
        publish_course(object(), load_course(tmp_path), 2)


def test_book_preflight_rejects_non_boolean_subchapter(tmp_path):
    section = tmp_path / "sections" / "01"
    bookdir = section / "book"
    bookdir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs książka\n  short_name: KBOOK\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Materiały\nmodules:\n"
        "  - type: book\n    ref: book\n    name: Podręcznik\n",
        encoding="utf-8",
    )
    (bookdir / "book.yaml").write_text(
        "book:\n  chapters:\n"
        "    - title: Start\n      content: Treść\n"
        "    - title: Błędny podrozdział\n      content: Treść\n"
        "      subchapter: 'false'\n",
        encoding="utf-8",
    )
    plan = build_publish_plan(load_course(tmp_path), 2)
    assert any("subchapter musi być wartością logiczną" in warning for warning in plan.warnings)

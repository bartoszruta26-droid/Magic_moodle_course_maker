from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs

import pytest

from magic_moodle.loader import load_course
from magic_moodle.moodle_api import (
    MoodleAPIError, MoodleClient, MoodleConfig, _NoRedirectHandler, _flatten,
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
    class Opener:
        def open(self, request, **kwargs):
            captured["url"] = request.full_url
            captured["body"] = parse_qs(request.data.decode())
            return Response()

    def fake_build_opener(*handlers):
        captured["redirect_handler"] = handlers[0]
        return Opener()

    client = MoodleClient(MoodleConfig("https://moodle.example/moodle", "secret"))
    with patch("urllib.request.build_opener", fake_build_opener):
        result = client.site_info()
    assert result["sitename"] == "Test Moodle"
    assert captured["url"].endswith("/moodle/webservice/rest/server.php")
    assert captured["body"]["wstoken"] == ["secret"]
    assert captured["body"]["wsfunction"] == ["core_webservice_get_site_info"]
    assert isinstance(captured["redirect_handler"], _NoRedirectHandler)


def test_moodle_error_payload_is_raised():
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size=-1): return b'{"exception":"moodle_exception","errorcode":"invalidtoken","message":"Bad token"}'

    client = MoodleClient(MoodleConfig("https://moodle.example", "secret"))
    class Opener:
        def open(self, *args, **kwargs): return Response()
    with patch("urllib.request.build_opener", lambda *a, **k: Opener()):
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
    chapters = [{"sourceid": "chapter-001", "title": "Start", "content": "<p>Treść</p>", "subchapter": False}]
    with patch.object(client, "call", return_value={"created": True}) as call:
        client.create_book(7, 1, {
            "name": "Podręcznik",
            "chapters": chapters,
            "chapterids": [{"sourceid": "chapter-001", "chapterid": 77}],
            "numbering": 1,
        })
    assert call.call_args.args[0] == "local_magicmoodle_create_book"
    assert call.call_args.args[1]["chapters"] == chapters
    assert call.call_args.args[1]["chapterids"] == [{"sourceid": "chapter-001", "chapterid": 77}]
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
    assert "\\mod_book\\event\\chapter_updated::create_from_chapter" in plugin
    assert "'sourceid'" in plugin and "'chapterids'" in plugin
    assert "get_moduleinfo_data($cm, $course);" in plugin
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
    sourceid = build_publish_plan(course, 2).activities[0]["chapters"][0]["sourceid"]

    class FakeClient:
        def site_info(self):
            return {"siteurl": "https://moodle.example", "functions": [
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
            return {"modname": "book", "name": activity["name"], "created": True,
                    "chapterids": [{"sourceid": activity["chapters"][0]["sourceid"], "chapterid": 55}]}

        def create_activity(self, *args):
            raise AssertionError("Book must use create_book, not create_activity")

    result = publish_course(FakeClient(), course, 2, state_file=tmp_path / "publish.json")
    assert result["activities_created"][0]["modname"] == "book"
    import json
    state = json.loads((tmp_path / "publish.json").read_text(encoding="utf-8"))
    record = next(iter(state["activities_completed"].values()))
    assert record["chapterids"] == [{"sourceid": sourceid, "chapterid": 55}]


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


def _sample_assignment_course(tmp_path: Path):
    section = tmp_path / "sections" / "01"
    assignmentdir = section / "assignment-01"
    assignmentdir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs testowy\n  short_name: ASSIGNTEST\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Prace\nmodules:\n"
        "  - type: assignment\n    ref: assignment-01\n    name: Praca zaliczeniowa\n",
        encoding="utf-8",
    )
    (assignmentdir / "assignment.yaml").write_text(
        "intro: Opis zadania.\nsubmission_type: both\n"
        "grade: 100\nmax_files: 3\nmax_file_size: 10485760\n"
        "completion:\n  enabled: true\n"
        "submission_drafts: true\nrequire_submission_statement: false\n",
        encoding="utf-8",
    )
    return load_course(tmp_path)


def test_assignment_is_preflighted_with_submission_settings(tmp_path):
    plan = build_publish_plan(_sample_assignment_course(tmp_path), 2)
    assert not plan.warnings
    assignment = plan.activities[0]
    assert assignment["type"] == "assignment"
    assert assignment["submissiontype"] == "both"
    assert assignment["grade"] == 100
    assert assignment["maxfiles"] == 3
    assert assignment["maxbytes"] == 10485760
    assert assignment["submissiondrafts"] is True
    assert assignment["completionenabled"] is True
    assert assignment["intro"] == "<p>Opis zadania.</p>"


def test_assignment_preflight_rejects_invalid_submission_type(tmp_path):
    course = _sample_assignment_course(tmp_path)
    from dataclasses import replace
    section = course.sections[0]
    activity = section.activities[0]
    changed = replace(activity, resource={**activity.resource, "submission_type": "shell"})
    course = replace(course, sections=(replace(section, activities=(changed,)),))
    plan = build_publish_plan(course, 2)
    assert any("submission_type" in warning for warning in plan.warnings)


def test_assignment_preflight_rejects_dates_out_of_order(tmp_path):
    course = _sample_assignment_course(tmp_path)
    from dataclasses import replace
    section = course.sections[0]
    activity = section.activities[0]
    changed = replace(activity, resource={
        **activity.resource, "allowsubmissionsfromdate": 200,
        "duedate": 100, "cutoffdate": 300,
    })
    course = replace(course, sections=(replace(section, activities=(changed,)),))
    plan = build_publish_plan(course, 2)
    assert any("daty otwarcia" in warning for warning in plan.warnings)


def test_create_assignment_calls_registered_moodle_service():
    client = MoodleClient(MoodleConfig("https://moodle.example", "secret"))
    with patch.object(client, "call", return_value={"created": True}) as call:
        client.create_assignment(7, 1, {
            "name": "Praca zaliczeniowa",
            "intro": "<p>Opis</p>",
            "submissiontype": "both",
            "grade": 100,
            "maxfiles": 3,
            "maxbytes": 10485760,
            "completionenabled": True,
        })
    assert call.call_args.args[0] == "local_magicmoodle_create_assignment"
    assert call.call_args.args[1]["submissiontype"] == "both"
    assert call.call_args.args[1]["maxfiles"] == 3
    assert call.call_args.args[1]["completionenabled"] is True


def test_publish_routes_assignment_to_assignment_endpoint(tmp_path):
    course = _sample_assignment_course(tmp_path)

    class FakeClient:
        def site_info(self):
            return {"functions": [
                {"name": "core_course_get_courses_by_field"},
                {"name": "core_course_create_courses"},
                {"name": "local_magicmoodle_update_section"},
                {"name": "local_magicmoodle_create_assignment"},
            ]}

        def ensure_course(self, payload):
            return ({"id": 42, "shortname": "ASSIGNTEST"}, True)

        def update_section(self, courseid, sectionnum, name):
            return {"section": sectionnum}

        def create_assignment(self, courseid, sectionnum, activity):
            assert activity["submissiontype"] == "both"
            return {"modname": "assign", "name": activity["name"], "created": True}

        def create_activity(self, *args):
            raise AssertionError("Assignment must use create_assignment")

    result = publish_course(FakeClient(), course, 2)
    assert result["activities_created"][0]["modname"] == "assign"


def test_assignment_endpoint_is_registered_for_moodle_41():
    root = Path(__file__).parents[2] / "moodle-plugin/local/magicmoodle"
    plugin = (root / "classes/external/create_assignment.php").read_text(encoding="utf-8")
    services = (root / "db/services.php").read_text(encoding="utf-8")
    version = (root / "version.php").read_text(encoding="utf-8")
    assert "class create_assignment extends \\external_api" in plugin
    assert "add_moduleinfo($moduleinfo, $course)" in plugin
    assert "assignsubmission_onlinetext_enabled" in plugin
    assert "assignsubmission_file_enabled" in plugin
    assert "'local_magicmoodle_create_assignment'" in services
    assert "$plugin->version = 2026110613;" in version


def _sample_file_course(tmp_path: Path):
    section = tmp_path / "sections" / "01"
    filesdir = section / "files"
    filesdir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs plików\n  short_name: FILETEST\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Materiały\nmodules:\n"
        "  - type: file\n    ref: files/manual.pdf\n    name: Instrukcja PDF\n",
        encoding="utf-8",
    )
    (filesdir / "manual.pdf").write_bytes(b"%PDF-1.4\x00sample binary content")
    return load_course(tmp_path)


def test_file_resource_is_loaded_as_base64_and_preflighted(tmp_path):
    import base64
    plan = build_publish_plan(_sample_file_course(tmp_path), 2)
    assert not plan.warnings
    item = plan.activities[0]
    assert item["type"] == "file"
    assert item["filename"] == "manual.pdf"
    assert base64.b64decode(item["contentbase64"]) == b"%PDF-1.4\x00sample binary content"
    assert item["filesize"] == len(b"%PDF-1.4\x00sample binary content")


def test_file_resource_preflight_rejects_path_like_filename(tmp_path):
    course = _sample_file_course(tmp_path)
    from dataclasses import replace
    section = course.sections[0]
    activity = section.activities[0]
    changed = replace(activity, content={"../manual.pdf": activity.content["manual.pdf"]})
    course = replace(course, sections=(replace(section, activities=(changed,)),))
    plan = build_publish_plan(course, 2)
    assert any("nieprawidłowa nazwa pliku" in warning for warning in plan.warnings)


def test_file_resource_preflight_rejects_invalid_base64(tmp_path):
    course = _sample_file_course(tmp_path)
    from dataclasses import replace
    section = course.sections[0]
    activity = section.activities[0]
    changed = replace(activity, content={"manual.pdf": "%%%not-base64%%%"})
    course = replace(course, sections=(replace(section, activities=(changed,)),))
    plan = build_publish_plan(course, 2)
    assert any("nieprawidłowe kodowanie base64" in warning for warning in plan.warnings)


def test_create_resource_calls_registered_moodle_service():
    client = MoodleClient(MoodleConfig("https://moodle.example", "secret"))
    with patch.object(client, "call", return_value={"created": True}) as call:
        client.create_resource(7, 1, {
            "name": "Instrukcja PDF",
            "filename": "manual.pdf",
            "contentbase64": "JVBERi0xLjQ=",
            "intro": "<p>Dokument</p>",
        })
    assert call.call_args.args[0] == "local_magicmoodle_create_resource"
    assert call.call_args.args[1]["filename"] == "manual.pdf"
    assert call.call_args.args[1]["contentbase64"] == "JVBERi0xLjQ="


def test_publish_routes_file_to_moodle_resource_endpoint(tmp_path):
    course = _sample_file_course(tmp_path)

    class FakeClient:
        def site_info(self):
            return {"functions": [
                {"name": "core_course_get_courses_by_field"},
                {"name": "core_course_create_courses"},
                {"name": "local_magicmoodle_update_section"},
                {"name": "local_magicmoodle_create_resource"},
            ]}

        def ensure_course(self, payload):
            return ({"id": 42, "shortname": "FILETEST"}, True)

        def update_section(self, courseid, sectionnum, name):
            return {"section": sectionnum}

        def create_resource(self, courseid, sectionnum, activity):
            assert activity["filename"] == "manual.pdf"
            return {"modname": "resource", "name": activity["name"], "created": True}

        def create_activity(self, *args):
            raise AssertionError("File must use create_resource")

    result = publish_course(FakeClient(), course, 2)
    assert result["activities_created"][0]["modname"] == "resource"


def test_file_resource_endpoint_is_registered_and_limited():
    root = Path(__file__).parents[2] / "moodle-plugin/local/magicmoodle"
    plugin = (root / "classes/external/create_resource.php").read_text(encoding="utf-8")
    services = (root / "db/services.php").read_text(encoding="utf-8")
    version = (root / "version.php").read_text(encoding="utf-8")
    assert "class create_resource extends \\external_api" in plugin
    assert "base64_decode($params['contentbase64'], true)" in plugin
    assert "5 * 1024 * 1024" in plugin
    assert "file_get_unused_draft_itemid()" in plugin
    assert "'local_magicmoodle_create_resource'" in services
    assert "$plugin->version = 2026110613;" in version


def test_existing_med10_assignment_yaml_is_supported_by_publisher():
    root = Path(__file__).parents[2] / "courses/03-kurs-masazysta-med10"
    course = load_course(root)
    selected = next(
        (activity, section)
        for section in course.sections
        for activity in section.activities
        if activity.kind == "assignment"
    )
    activity, section = selected
    from dataclasses import replace
    isolated = replace(course, sections=(replace(section, activities=(activity,)),))
    plan = build_publish_plan(isolated, 2)
    assert not plan.warnings
    assignment = plan.activities[0]
    assert assignment["submissiontype"] == "both"
    assert assignment["maxfiles"] == 3
    assert assignment["grade"] == 100
    assert assignment["intro"]


def test_full_med10_course_has_no_moodle_publish_preflight_warnings():
    root = Path(__file__).parents[2] / "courses/03-kurs-masazysta-med10"
    course = load_course(root)
    plan = build_publish_plan(course, 2)
    assert not plan.warnings, "\n".join(plan.warnings[:30])
    assert len(plan.activities) > 300
    assert {item["type"] for item in plan.activities} >= {"book", "quiz", "assignment"}


def test_existing_med10_glossary_yaml_builds_valid_publish_plan():
    root = Path(__file__).parents[2] / "courses/03-kurs-masazysta-med10"
    course = load_course(root)
    selected = next(
        (activity, section)
        for section in course.sections
        for activity in section.activities
        if activity.kind == "glossary"
    )
    activity, section = selected
    from dataclasses import replace
    isolated = replace(course, sections=(replace(section, activities=(activity,)),))
    plan = build_publish_plan(isolated, 2)
    assert not plan.warnings
    glossary = plan.activities[0]
    assert glossary["type"] == "glossary"
    assert glossary["entrycount"] >= 50
    assert glossary["entries"][0]["term"]
    assert glossary["entries"][0]["sourceid"].startswith("term-")


def test_glossary_preflight_rejects_duplicate_terms(tmp_path):
    section = tmp_path / "sections" / "01"
    glossarydir = section / "glossary"
    glossarydir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs słownikowy\n  short_name: GLOSSARYTEST\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Słownik\nmodules:\n"
        "  - type: glossary\n    ref: glossary\n    name: Słownik\n",
        encoding="utf-8",
    )
    (glossarydir / "glossary.yaml").write_text(
        "glossary:\n  entries:\n"
        "    - term: Masaż\n      definition: Definicja pierwsza\n"
        "    - term: masaż\n      definition: Definicja druga\n",
        encoding="utf-8",
    )
    plan = build_publish_plan(load_course(tmp_path), 2)
    assert any("powtórzone hasło" in warning for warning in plan.warnings)


def test_create_glossary_calls_registered_moodle_service():
    client = MoodleClient(MoodleConfig("https://moodle.example", "secret"))
    entries = [{"sourceid": "term-001", "term": "Masaż", "definition": "<p>Definicja</p>"}]
    with patch.object(client, "call", return_value={"created": True}) as call:
        client.create_glossary(7, 1, {
            "name": "Słownik",
            "intro": "<p>Wprowadzenie</p>",
            "entries": entries,
            "entryids": [{"sourceid": "term-001", "entryid": 77}],
        })
    assert call.call_args.args[0] == "local_magicmoodle_create_glossary"
    assert call.call_args.args[1]["entries"] == entries
    assert call.call_args.args[1]["entryids"] == [{"sourceid": "term-001", "entryid": 77}]


def test_publish_routes_glossary_to_native_glossary_endpoint(tmp_path):
    section = tmp_path / "sections" / "01"
    glossarydir = section / "glossary"
    glossarydir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs słownikowy\n  short_name: GLOSSARYTEST\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Słownik\nmodules:\n"
        "  - type: glossary\n    ref: glossary\n    name: Słownik\n",
        encoding="utf-8",
    )
    (glossarydir / "glossary.yaml").write_text(
        "glossary:\n  entries:\n"
        "    - term: Masaż\n      definition: Definicja\n",
        encoding="utf-8",
    )
    course = load_course(tmp_path)

    class FakeClient:
        def site_info(self):
            return {"siteurl": "https://moodle.example", "functions": [
                {"name": "core_course_get_courses_by_field"},
                {"name": "core_course_create_courses"},
                {"name": "local_magicmoodle_update_section"},
                {"name": "local_magicmoodle_create_glossary"},
            ]}

        def ensure_course(self, payload):
            return ({"id": 42, "shortname": "GLOSSARYTEST"}, True)

        def update_section(self, courseid, sectionnum, name):
            return {"section": sectionnum}

        def create_glossary(self, courseid, sectionnum, activity):
            assert activity["entrycount"] == 1
            return {"modname": "glossary", "name": activity["name"], "created": True,
                    "entryids": [{"sourceid": activity["entries"][0]["sourceid"], "entryid": 88}]}

        def create_activity(self, *args):
            raise AssertionError("Glossary must use create_glossary")

    result = publish_course(FakeClient(), course, 2, state_file=tmp_path / "publish.json")
    assert result["activities_created"][0]["modname"] == "glossary"
    import json
    state = json.loads((tmp_path / "publish.json").read_text(encoding="utf-8"))
    record = next(iter(state["activities_completed"].values()))
    assert record["entryids"] == [{"sourceid": "term-" + __import__("hashlib").sha256("masaż".encode()).hexdigest()[:32], "entryid": 88}]


def test_glossary_endpoint_uses_moodle_native_entry_api():
    root = Path(__file__).parents[2] / "moodle-plugin/local/magicmoodle"
    plugin = (root / "classes/external/create_glossary.php").read_text(encoding="utf-8")
    services = (root / "db/services.php").read_text(encoding="utf-8")
    version = (root / "version.php").read_text(encoding="utf-8")
    assert "class create_glossary extends \\external_api" in plugin
    assert "\\mod_glossary_external::add_entry" in plugin
    assert "\\mod_glossary\\external\\update_entry::execute" in plugin
    assert "'sourceid'" in plugin
    assert "'entryids'" in plugin
    assert "500" in plugin
    assert "'local_magicmoodle_create_glossary'" in services
    assert "$plugin->version = 2026110613;" in version


def test_publish_plan_assigns_stable_source_idnumbers(tmp_path):
    course = _sample_course(tmp_path)
    plan = build_publish_plan(course, 2)
    original = plan.activities[0]["idnumber"]
    assert original.startswith("mm-")
    assert len(original) == 35

    from dataclasses import replace
    section = course.sections[0]
    activity = section.activities[0]
    renamed = replace(activity, name="Zmieniona nazwa")
    renamed_course = replace(course, sections=(replace(section, activities=(renamed,)),))
    renamed_plan = build_publish_plan(renamed_course, 2)
    assert renamed_plan.activities[0]["idnumber"] == original


def test_moodle_plugin_endpoints_accept_and_persist_stable_idnumbers():
    root = Path(__file__).parents[2] / "moodle-plugin/local/magicmoodle/classes/external"
    names = [
        "create_activity.php", "create_book.php", "create_quiz.php",
        "create_assignment.php", "create_resource.php", "create_glossary.php",
    ]
    for name in names:
        source = (root / name).read_text(encoding="utf-8")
        assert "'idnumber' => new " in source
        assert "$moduleinfo->cmidnumber = $params['idnumber'];" in source
        assert "->idnumber === $params['idnumber']" in source
        assert (
            "course_modules', 'idnumber'" in source
            or ("get_moduleinfo_data($coursemodule, $course);" in source
                and "update_moduleinfo($coursemodule, $moduleinfo, $course);" in source)
            or ("get_moduleinfo_data($cm, $course);" in source
                and "update_moduleinfo($cm, $moduleinfo, $course);" in source)
        )


def test_stable_idnumber_is_last_external_parameter_for_all_moodle_modules():
    root = Path(__file__).parents[2] / "moodle-plugin/local/magicmoodle/classes/external"
    names = [
        "create_activity.php", "create_book.php", "create_quiz.php",
        "create_assignment.php", "create_resource.php", "create_glossary.php",
    ]
    for name in names:
        source = (root / name).read_text(encoding="utf-8")
        start = source.index("public static function execute_parameters()")
        end = source.index("public static function execute(", start)
        params = source[start:end]
        assert params.rfind("'idnumber'") > params.rfind("'sectionnum'")
        signature = source[end:source.index("{", end)]
        assert "$idnumber = ''" in signature


def test_partial_publish_failure_reports_resume_identity_and_progress(tmp_path):
    course = _sample_course(tmp_path)
    from dataclasses import replace
    from magic_moodle.models import Activity
    section = course.sections[0]
    second = Activity("page", "second.md", "Druga strona")
    changed = replace(section, activities=(section.activities[0], second))
    course = replace(course, sections=(changed,))

    class FailingClient:
        def __init__(self):
            self.calls = 0

        def site_info(self):
            return {"functions": [
                {"name": "core_course_get_courses_by_field"},
                {"name": "core_course_create_courses"},
                {"name": "local_magicmoodle_update_section"},
                {"name": "local_magicmoodle_create_activity"},
            ]}

        def ensure_course(self, payload):
            return ({"id": 42, "shortname": "TEST"}, True)

        def update_section(self, courseid, sectionnum, name):
            return {"section": sectionnum}

        def create_activity(self, courseid, sectionnum, activity):
            self.calls += 1
            if self.calls == 2:
                raise MoodleAPIError("symulowany błąd Moodle")
            return {"created": True}

    with pytest.raises(MoodleAPIError) as error:
        publish_course(FailingClient(), course, 2)
    message = str(error.value)
    assert "2/2" in message
    assert "idnumber mm-" in message
    assert "Poprzednio obsłużono 1 aktywności" in message
    assert "bezpiecznie ponowić" in message


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_moodle_client_rejects_invalid_timeout(timeout):
    with pytest.raises(MoodleAPIError, match="MOODLE_TIMEOUT"):
        MoodleClient(MoodleConfig("https://moodle.example", "secret", timeout=timeout))


def test_redirect_handler_refuses_redirects():
    handler = _NoRedirectHandler()
    assert handler.redirect_request(None, None, 307, "Temporary Redirect", {}, "https://attacker.example/") is None



def test_disabling_tls_verification_is_rejected_for_remote_hosts():
    with pytest.raises(MoodleAPIError, match="localhost"):
        MoodleClient(MoodleConfig("https://moodle.example", "secret", verify_tls=False))


def test_disabling_tls_verification_remains_available_for_local_development():
    client = MoodleClient(MoodleConfig("https://localhost", "secret", verify_tls=False))
    assert client.endpoint.startswith("https://localhost/")


def test_http_error_body_redacts_moodle_token():
    client = MoodleClient(MoodleConfig("https://moodle.example", "sensitive-token"))
    error = __import__("urllib.error").error.HTTPError(
        client.endpoint, 500, "Server Error", {}, __import__("io").BytesIO(
            b"failure sensitive-token detail"
        )
    )
    with patch("urllib.request.build_opener", side_effect=error):
        with pytest.raises(MoodleAPIError) as caught:
            client.call("core_webservice_get_site_info")
    assert "sensitive-token" not in str(caught.value)
    assert "[REDACTED]" in str(caught.value)


def test_moodle_json_error_message_redacts_token():
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size=-1):
            return b'{"exception":"moodle_exception","errorcode":"bad","message":"token sensitive-token rejected"}'

    client = MoodleClient(MoodleConfig("https://moodle.example", "sensitive-token"))
    class Opener:
        def open(self, *args, **kwargs): return Response()
    with patch("urllib.request.build_opener", lambda *a, **k: Opener()):
        with pytest.raises(MoodleAPIError) as caught:
            client.call("core_webservice_get_site_info")
    assert "sensitive-token" not in str(caught.value)
    assert "[REDACTED]" in str(caught.value)



class _StatefulPublishClient:
    def __init__(self, *, fail_activity=False):
        self.fail_activity = fail_activity
        self.ensure_calls = 0
        self.lookup_calls = 0
        self.activity_calls = 0

    def site_info(self):
        return {
            "siteurl": "https://moodle.example",
            "functions": [
                {"name": "core_course_get_courses_by_field"},
                {"name": "core_course_create_courses"},
                {"name": "local_magicmoodle_update_section"},
                {"name": "local_magicmoodle_create_activity"},
            ],
        }

    def ensure_course(self, payload):
        self.ensure_calls += 1
        return ({"id": 42, "shortname": payload["shortname"]}, True)

    def get_course_by_shortname(self, shortname):
        self.lookup_calls += 1
        return {"id": 42, "shortname": shortname}

    def update_section(self, courseid, sectionnum, name):
        return {"section": sectionnum}

    def create_activity(self, courseid, sectionnum, activity):
        self.activity_calls += 1
        if self.fail_activity:
            raise MoodleAPIError("symulowana awaria")
        return {
            "cmid": 100 + self.activity_calls,
            "instanceid": 200 + self.activity_calls,
            "created": self.activity_calls == 1,
        }


def test_publish_state_manifest_records_progress_without_secrets(tmp_path):
    course = _sample_course(tmp_path / "course")
    state_file = tmp_path / "state" / "publish.json"
    client = _StatefulPublishClient()
    result = publish_course(client, course, 2, state_file=state_file)

    import json
    state_text = state_file.read_text(encoding="utf-8")
    state = json.loads(state_text)
    assert result["state_file"] == str(state_file)
    assert state["format"] == "magic-moodle-publish-state"
    assert state["version"] == 2
    assert state["identity_sha256"]
    assert state["status"] == "complete"
    assert state["course_id"] == 42
    assert state["sections_completed"] == [0]
    assert len(state["activities_completed"]) == 1
    assert "token" not in state_text.lower()


def test_publish_state_manifest_resumes_only_against_same_remote_course(tmp_path):
    from dataclasses import replace
    import json

    course = _sample_course(tmp_path / "course")
    state_file = tmp_path / "publish.json"
    first = _StatefulPublishClient()
    publish_course(first, course, 2, state_file=state_file)
    resumed = _StatefulPublishClient()
    result = publish_course(resumed, course, 2, state_file=state_file)

    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert resumed.lookup_calls == 1
    assert resumed.ensure_calls == 0
    assert result["course_created"] is False
    assert state["status"] == "complete"


def test_publish_state_manifest_rejects_changed_course_identity_before_remote_writes(tmp_path):
    from dataclasses import replace

    course = _sample_course(tmp_path / "course")
    state_file = tmp_path / "publish.json"
    publish_course(_StatefulPublishClient(), course, 2, state_file=state_file)
    changed = replace(course, short_name="INNY_KURS")
    client = _StatefulPublishClient()
    with pytest.raises(MoodleAPIError, match="innego kursu, planu lub serwera"):
        publish_course(client, changed, 2, state_file=state_file)
    assert client.ensure_calls == 0
    assert client.lookup_calls == 0
    assert client.activity_calls == 0


def test_publish_state_manifest_persists_partial_failure_for_safe_retry(tmp_path):
    import json

    course = _sample_course(tmp_path / "course")
    state_file = tmp_path / "publish.json"
    client = _StatefulPublishClient(fail_activity=True)
    with pytest.raises(MoodleAPIError, match="bezpiecznie ponowić"):
        publish_course(client, course, 2, state_file=state_file)
    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["status"] == "partial"
    assert state["failed_step"] == "activity:1"
    assert state["course_id"] == 42
    assert state["last_error_type"] == "MoodleAPIError"



def test_publish_state_manifest_allows_section_content_updates_with_same_identity(tmp_path):
    from dataclasses import replace

    course = _sample_course(tmp_path / "course")
    state_file = tmp_path / "publish.json"
    publish_course(_StatefulPublishClient(), course, 2, state_file=state_file)
    section = course.sections[0]
    changed = replace(course, sections=(replace(section, name="Zmieniona sekcja"),))
    client = _StatefulPublishClient()
    result = publish_course(client, changed, 2, state_file=state_file)
    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert client.ensure_calls == 0
    assert client.lookup_calls == 1
    assert result["course_created"] is False
    assert state["status"] == "complete"



@pytest.mark.parametrize("value", [2, -1, "yes", None])
def test_course_payload_rejects_invalid_visibility_values(tmp_path, value):
    from dataclasses import replace

    course = _sample_course(tmp_path)
    metadata = dict(course.metadata)
    metadata["course"] = {**metadata.get("course", {}), "visible": value}
    with pytest.raises(MoodleAPIError, match="course.visible"):
        build_publish_plan(replace(course, metadata=metadata), 2)


@pytest.mark.parametrize("category_id", [True, False, 0, -1, 2.5, "x"])
def test_course_payload_rejects_invalid_category_ids(tmp_path, category_id):
    course = _sample_course(tmp_path)
    with pytest.raises(MoodleAPIError, match="categoryid"):
        build_publish_plan(course, category_id)


@pytest.mark.parametrize("news_items", [-1, 11, True, "5"])
def test_course_payload_rejects_invalid_news_item_counts(tmp_path, news_items):
    from dataclasses import replace

    course = _sample_course(tmp_path)
    metadata = dict(course.metadata)
    metadata["course"] = {**metadata.get("course", {}), "news_items": news_items}
    with pytest.raises(MoodleAPIError, match="news_items"):
        build_publish_plan(replace(course, metadata=metadata), 2)


def test_course_payload_rejects_overlong_course_names(tmp_path):
    from dataclasses import replace

    course = _sample_course(tmp_path)
    with pytest.raises(MoodleAPIError, match="short_name"):
        build_publish_plan(replace(course, short_name="X" * 101), 2)


def test_create_activity_sends_stable_idnumber_for_repeatable_sync():
    client = MoodleClient(MoodleConfig("https://moodle.example", "secret"))
    with patch.object(client, "call", return_value={"created": False, "cmid": 91}) as call:
        result = client.create_activity(7, 1, {
            "type": "page",
            "name": "Zmieniona nazwa strony",
            "content": "<p>Zmieniona treść</p>",
            "idnumber": "mm-source-identity",
        })
    assert result["created"] is False
    assert call.call_args.args[0] == "local_magicmoodle_create_activity"
    assert call.call_args.args[1]["idnumber"] == "mm-source-identity"
    assert call.call_args.args[1]["content"] == "<p>Zmieniona treść</p>"


def test_page_label_url_plugin_updates_existing_module_in_place():
    plugin = (
        Path(__file__).parents[2]
        / "moodle-plugin/local/magicmoodle/classes/external/create_activity.php"
    ).read_text(encoding="utf-8")
    assert "update_moduleinfo($coursemodule, $moduleinfo, $course);" in plugin
    assert "This source idnumber already belongs to an activity with a different name" not in plugin
    assert "file_prepare_standard_editor(" in plugin
    assert "$moduleinfo->content = $moduleinfo->content_editor;" in plugin
    assert "'itemid' => file_get_unused_draft_itemid()" in plugin
    assert "get_moduleinfo_data($coursemodule, $course);" in plugin
    assert "$coursemodule = $DB->get_record('course_modules'" in plugin
    assert "$transaction->allow_commit();" in plugin
    assert "get_moduleinfo_data($coursemodule, $course);" in plugin
    assert "file_prepare_standard_editor(" in plugin
    assert "$moduleinfo->visible = 1;" not in plugin[plugin.index("// Re-publishing a source activity is an update"):plugin.index("update_moduleinfo($coursemodule, $moduleinfo, $course);")]


def test_publish_reports_existing_basic_activity_as_updated(tmp_path):
    course = _sample_course(tmp_path)

    class FakeClient:
        def site_info(self):
            return {"functions": [
                {"name": "core_course_get_courses_by_field"},
                {"name": "core_course_create_courses"},
                {"name": "local_magicmoodle_update_section"},
                {"name": "local_magicmoodle_create_activity"},
            ]}

        def ensure_course(self, payload):
            return ({"id": 42, "shortname": "TEST"}, False)

        def update_section(self, courseid, sectionnum, name):
            return {"section": sectionnum}

        def create_activity(self, courseid, sectionnum, activity):
            return {
                "cmid": 91, "instanceid": 81, "modname": "page",
                "name": activity["name"], "created": False, "updated": True,
            }

    result = publish_course(FakeClient(), course, 2)
    assert len(result["activities_processed"]) == 1
    assert result["activities_updated"][0]["cmid"] == 91


def test_basic_activity_endpoint_exposes_update_outcome():
    plugin = (
        Path(__file__).parents[2]
        / "moodle-plugin/local/magicmoodle/classes/external/create_activity.php"
    ).read_text(encoding="utf-8")
    assert "'updated' => true" in plugin
    assert "'updated' => false" in plugin
    assert "'updated' => new \\external_value(PARAM_BOOL" in plugin


def test_glossary_publish_requires_manifest_for_entry_identity(tmp_path):
    section = tmp_path / "sections" / "01"
    glossarydir = section / "glossary"
    glossarydir.mkdir(parents=True)
    (tmp_path / "course.yaml").write_text(
        "course:\n  full_name: Kurs słownikowy\n  short_name: GLOSSARYSAFE\n",
        encoding="utf-8",
    )
    (section / "section.yaml").write_text(
        "id: '01'\nname: Słownik\nmodules:\n"
        "  - type: glossary\n    ref: glossary\n    name: Słownik\n",
        encoding="utf-8",
    )
    (glossarydir / "glossary.yaml").write_text(
        "glossary:\n  entries:\n    - term: Masaż\n      definition: Definicja\n",
        encoding="utf-8",
    )
    course = load_course(tmp_path)
    with pytest.raises(MoodleAPIError, match="wymaga --state-file"):
        publish_course(object(), course, 2)


def test_publish_manifest_allows_content_change_with_stable_course_and_activity_identity(tmp_path):
    from dataclasses import replace
    import json
    course = _sample_course(tmp_path / "course")
    state_file = tmp_path / "publish.json"
    publish_course(_StatefulPublishClient(), course, 2, state_file=state_file)
    original_state = json.loads(state_file.read_text(encoding="utf-8"))
    section = course.sections[0]
    activity = section.activities[0]
    changed_activity = replace(activity, name="Zmieniona nazwa strony")
    changed_course = replace(
        course,
        sections=(replace(section, activities=(changed_activity,)),),
    )
    client = _StatefulPublishClient()
    publish_course(client, changed_course, 2, state_file=state_file)
    updated_state = json.loads(state_file.read_text(encoding="utf-8"))
    assert client.lookup_calls == 1
    assert updated_state["identity_sha256"] == original_state["identity_sha256"]
    assert updated_state["plan_sha256"] != original_state["plan_sha256"]

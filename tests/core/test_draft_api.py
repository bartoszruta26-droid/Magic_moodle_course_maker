from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from api.server import create_server
from magic_moodle.application import CourseApplicationService


def make_course(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "course.yaml").write_text(
        "course:\n  full_name: Kurs API\n  short_name: API\n",
        encoding="utf-8",
    )
    section = root / "sections" / "01-intro"
    section.mkdir(parents=True)
    (section / "section.yaml").write_text(
        "id: intro\nname: Wprowadzenie\nmodules: []\n",
        encoding="utf-8",
    )


@contextmanager
def running_server(service: CourseApplicationService, token: str = ""):
    server = create_server(service, host="127.0.0.1", port=0, token=token)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    token: str = "",
) -> tuple[int, dict]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def test_api_draft_create_update_and_preview(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    course_path = courses / "sample"
    make_course(course_path)
    source = (course_path / "course.yaml").read_text(encoding="utf-8")

    with running_server(CourseApplicationService(courses), token="draft-secret") as base:
        status, created = request_json(
            f"{base}/api/v1/courses/sample/drafts",
            method="POST",
            payload={},
            token="draft-secret",
        )
        assert status == 201
        draft_id = created["data"]["draft_id"]
        assert created["data"]["revision"] == 1

        status, updated = request_json(
            f"{base}/api/v1/drafts/{draft_id}",
            method="PATCH",
            payload={
                "expected_revision": 1,
                "changes": {"full_name": "Kurs roboczy", "section_names": {"intro": "Podstawy"}},
            },
            token="draft-secret",
        )
        assert status == 200
        assert updated["data"]["revision"] == 2

        status, preview = request_json(f"{base}/api/v1/drafts/{draft_id}/preview", token="draft-secret")
        assert status == 200
        assert preview["data"]["course"]["course"]["full_name"] == "Kurs roboczy"
        assert preview["data"]["course"]["sections"][0]["name"] == "Podstawy"
        assert preview["data"]["source_modified"] is False
        assert (course_path / "course.yaml").read_text(encoding="utf-8") == source


def test_api_draft_write_requires_configured_bearer_token(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")

    with running_server(CourseApplicationService(courses)) as base:
        status, payload = request_json(
            f"{base}/api/v1/courses/sample/drafts",
            method="POST",
            payload={},
        )
        assert status == 503
        assert payload["error"]["code"] == "WRITE_AUTH_NOT_CONFIGURED"


def test_api_draft_update_reports_stale_revision(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")

    with running_server(CourseApplicationService(courses), token="draft-secret") as base:
        _, created = request_json(
            f"{base}/api/v1/courses/sample/drafts",
            method="POST",
            payload={},
            token="draft-secret",
        )
        draft_id = created["data"]["draft_id"]
        request_json(
            f"{base}/api/v1/drafts/{draft_id}",
            method="PATCH",
            payload={"expected_revision": 1, "changes": {"full_name": "Nowa nazwa"}},
            token="draft-secret",
        )
        status, conflict = request_json(
            f"{base}/api/v1/drafts/{draft_id}",
            method="PATCH",
            payload={"expected_revision": 1, "changes": {"full_name": "Stara rewizja"}},
            token="draft-secret",
        )
        assert status == 409
        assert conflict["error"]["code"] == "DRAFT_CONFLICT"


def test_api_read_only_validation_still_works_without_write_token(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")

    with running_server(CourseApplicationService(courses)) as base:
        status, report = request_json(
            f"{base}/api/v1/courses/sample/validation",
            method="POST",
        )
        assert status == 200
        assert report["data"]["ok"] is True


def test_api_post_draft_update_alias_supports_android_clients(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")

    with running_server(CourseApplicationService(courses), token="draft-secret") as base:
        _, created = request_json(
            f"{base}/api/v1/courses/sample/drafts",
            method="POST",
            payload={},
            token="draft-secret",
        )
        draft_id = created["data"]["draft_id"]
        status, updated = request_json(
            f"{base}/api/v1/drafts/{draft_id}/update",
            method="POST",
            payload={"expected_revision": 1, "changes": {"full_name": "Kurs Android"}},
            token="draft-secret",
        )
        assert status == 200
        assert updated["data"]["revision"] == 2


def test_api_lists_draft_history_and_restores_revision(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")

    with running_server(CourseApplicationService(courses), token="draft-secret") as base:
        _, created = request_json(
            f"{base}/api/v1/courses/sample/drafts",
            method="POST",
            payload={},
            token="draft-secret",
        )
        draft_id = created["data"]["draft_id"]
        request_json(
            f"{base}/api/v1/drafts/{draft_id}/update",
            method="POST",
            payload={"expected_revision": 1, "changes": {"full_name": "Kurs druga rewizja"}},
            token="draft-secret",
        )

        status, listing = request_json(
            f"{base}/api/v1/courses/sample/drafts",
            token="draft-secret",
        )
        assert status == 200
        assert listing["data"][0]["draft_id"] == draft_id
        assert listing["data"][0]["revision"] == 2

        status, history = request_json(
            f"{base}/api/v1/drafts/{draft_id}/history",
            token="draft-secret",
        )
        assert status == 200
        assert [item["revision"] for item in history["data"]] == [1, 2]

        status, restored = request_json(
            f"{base}/api/v1/drafts/{draft_id}/restore",
            method="POST",
            payload={"expected_revision": 2, "target_revision": 1},
            token="draft-secret",
        )
        assert status == 200
        assert restored["data"]["revision"] == 3

        status, preview = request_json(
            f"{base}/api/v1/drafts/{draft_id}/preview",
            token="draft-secret",
        )
        assert status == 200
        assert preview["data"]["course"]["course"]["full_name"] == "Kurs API"

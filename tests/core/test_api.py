from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

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


def get_json(url: str, token: str = "") -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with urlopen(Request(url, headers=headers), timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def test_api_health_courses_detail_and_validation(tmp_path: Path) -> None:
    courses = tmp_path / "courses"
    make_course(courses / "sample")
    service = CourseApplicationService(courses)

    with running_server(service, token="test-secret") as base:
        with pytest.raises(HTTPError) as unauthorized:
            urlopen(f"{base}/api/v1/health", timeout=5)
        assert unauthorized.value.code == 401

        health = get_json(f"{base}/api/v1/health", token="test-secret")
        assert health["data"]["status"] == "ok"

        listing = get_json(f"{base}/api/v1/courses", token="test-secret")
        assert listing["data"][0]["id"] == "sample"
        assert listing["data"][0]["name"] == "Kurs API"

        detail = get_json(f"{base}/api/v1/courses/sample", token="test-secret")
        assert detail["data"]["short_name"] == "API"
        assert detail["data"]["sections"][0]["id"] == "intro"
        assert str(courses) not in json.dumps(detail)

        request = Request(
            f"{base}/api/v1/courses/sample/validation",
            headers={"Authorization": "Bearer test-secret"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            report = json.loads(response.read().decode("utf-8"))
        assert report["data"]["ok"] is True
        assert report["meta"]["api_version"] == "1"


def test_api_returns_404_for_unknown_course(tmp_path: Path) -> None:
    service = CourseApplicationService(tmp_path / "courses")
    with running_server(service) as base:
        with pytest.raises(HTTPError) as missing:
            urlopen(f"{base}/api/v1/courses/absent", timeout=5)
        assert missing.value.code == 404


def test_api_refuses_non_loopback_bind_without_exposing_http(tmp_path: Path) -> None:
    service = CourseApplicationService(tmp_path / "courses")
    with pytest.raises(ValueError, match="reverse proxy HTTPS"):
        create_server(service, host="0.0.0.0", port=0)

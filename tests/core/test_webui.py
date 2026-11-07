from pathlib import Path

from webui import server


def test_inside_rejects_parent_traversal(tmp_path: Path):
    base = tmp_path / "courses"
    base.mkdir()
    assert server._inside(base / "course", base)
    assert not server._inside(base.parent / "outside", base)


def test_allowed_host_blocks_dns_rebinding():
    assert server._is_allowed_host("127.0.0.1:8765")
    assert server._is_allowed_host("localhost:8765")
    assert server._is_allowed_host("[::1]:8765")
    assert not server._is_allowed_host("attacker.example:8765")
    assert not server._is_allowed_host("127.0.0.1.evil.example:8765")
    assert not server._is_allowed_host(None)


def test_list_courses_reads_course_metadata(tmp_path: Path, monkeypatch):
    course = tmp_path / "sample"
    course.mkdir()
    (course / "course.yaml").write_text(
        "course:\n  full_name: Kurs testowy\n  short_name: TEST\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(server, "ROOT", tmp_path)
    result = server.list_courses()
    assert result == [{
        "id": "sample",
        "name": "Kurs testowy",
        "short_name": "TEST",
        "sections": "0",
        "activities": "0",
    }]


def test_list_courses_handles_invalid_course(tmp_path: Path, monkeypatch):
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "course.yaml").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(server, "ROOT", tmp_path)
    result = server.list_courses()
    assert len(result) == 1
    assert result[0]["id"] == "broken"
    assert result[0]["sections"] == "—"


def _running_webui(monkeypatch, courses_root: Path, token: str = ""):
    import threading
    from http.server import ThreadingHTTPServer

    monkeypatch.setattr(server, "ROOT", courses_root)
    monkeypatch.setattr(server, "API_TOKEN", token)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread, f"http://127.0.0.1:{httpd.server_port}"


def _webui_request(url: str, *, method: str = "GET", payload=None, token: str = ""):
    import json
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    headers = {"Host": "127.0.0.1:8765"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
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


def test_webui_can_create_update_and_preview_course_draft(tmp_path: Path, monkeypatch):
    courses = tmp_path / "courses"
    course = courses / "sample"
    course.mkdir(parents=True)
    (course / "course.yaml").write_text(
        "course:\n  full_name: Kurs bazowy\n  short_name: BASE\n",
        encoding="utf-8",
    )
    section = course / "sections" / "intro"
    section.mkdir(parents=True)
    (section / "section.yaml").write_text(
        "id: intro\nname: Wprowadzenie\nmodules: []\n",
        encoding="utf-8",
    )
    source = (course / "course.yaml").read_text(encoding="utf-8")
    httpd, thread, base = _running_webui(monkeypatch, courses, "webui-secret")
    try:
        status, created = _webui_request(
            f"{base}/api/courses/sample/drafts",
            method="POST",
            payload={},
            token="webui-secret",
        )
        assert status == 201
        draft_id = created["data"]["draft_id"]

        status, updated = _webui_request(
            f"{base}/api/drafts/{draft_id}",
            method="PATCH",
            payload={"expected_revision": 1, "changes": {"full_name": "Kurs roboczy"}},
            token="webui-secret",
        )
        assert status == 200
        assert updated["data"]["revision"] == 2

        status, preview = _webui_request(
            f"{base}/api/drafts/{draft_id}/preview",
            token="webui-secret",
        )
        assert status == 200
        assert preview["data"]["course"]["course"]["full_name"] == "Kurs roboczy"
        assert (course / "course.yaml").read_text(encoding="utf-8") == source
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


def test_webui_requires_configured_token_for_draft_writes(tmp_path: Path, monkeypatch):
    courses = tmp_path / "courses"
    courses.mkdir()
    httpd, thread, base = _running_webui(monkeypatch, courses)
    try:
        status, payload = _webui_request(
            f"{base}/api/courses/sample/drafts",
            method="POST",
            payload={},
        )
        assert status == 503
        assert payload["code"] == "WRITE_AUTH_NOT_CONFIGURED"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)

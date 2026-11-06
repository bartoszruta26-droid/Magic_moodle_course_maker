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
}
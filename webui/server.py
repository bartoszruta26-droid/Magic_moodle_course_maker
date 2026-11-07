"""Read-only local WebUI for inspecting and validating course projects.

Run with: python -m webui.server
The interface binds to localhost by default and never publishes to Moodle.
"""
from __future__ import annotations

import ipaddress
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from magic_moodle.application import CourseApplicationService, CourseNotFoundError
from magic_moodle.loader import CourseLoadError

ROOT = Path(os.environ.get("MAGIC_MOODLE_COURSES", "courses")).resolve()
STATIC = Path(__file__).with_name("static").resolve()
HOST = os.environ.get("MAGIC_MOODLE_WEBUI_HOST", "127.0.0.1")
PORT = int(os.environ.get("MAGIC_MOODLE_WEBUI_PORT", "8765"))


def _inside(path: Path, base: Path) -> bool:
    return path.resolve().is_relative_to(base.resolve())


def _allowed_hosts(host: str = HOST, port: int = PORT) -> set[str]:
    """Return strict loopback Host authorities to mitigate DNS-rebinding access."""
    port_text = str(port)
    configured = f"[{host}]:{port_text}" if ":" in host else f"{host}:{port_text}"
    return {
        configured.lower(),
        f"127.0.0.1:{port_text}",
        f"localhost:{port_text}",
        f"[::1]:{port_text}",
    }


def _is_allowed_host(value: str | None, host: str = HOST, port: int = PORT) -> bool:
    return bool(value) and value.strip().lower() in _allowed_hosts(host, port)


def list_courses() -> list[dict[str, str]]:
    """Keep the existing WebUI response shape while delegating to the app core."""
    summaries = CourseApplicationService(ROOT).list_courses()
    return [
        {
            "id": item.id,
            "name": item.name,
            "short_name": item.short_name,
            "sections": str(item.sections) if item.sections is not None else "—",
            "activities": str(item.activities) if item.activities is not None else "—",
        }
        for item in summaries
    ]


class Handler(BaseHTTPRequestHandler):
    server_version = "MagicMoodleWebUI/0.2"

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.send_header("Cache-Control", "no-store")

    def _json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if not _is_allowed_host(self.headers.get("Host")):
            return self._json({"error": "Niedozwolony nagłówek Host."}, 403)

        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self._json({"ok": True})
        if parsed.path == "/api/courses":
            return self._json({"courses": list_courses()})
        if parsed.path.startswith("/api/courses/") and parsed.path.endswith("/validate"):
            course_id = unquote(parsed.path[len("/api/courses/"):-len("/validate")]).strip("/")
            if not course_id or course_id in {".", ".."} or "/" in course_id or "\\" in course_id:
                return self._json({"error": "Nieprawidłowy identyfikator kursu."}, 400)
            try:
                course, report = CourseApplicationService(ROOT).validate(course_id)
            except CourseNotFoundError:
                return self._json({"error": "Nie znaleziono kursu."}, 404)
            except (CourseLoadError, OSError, ValueError):
                return self._json({"error": "Nie udało się wczytać lub zwalidować kursu."}, 422)
            return self._json({
                "course": {
                    "name": course.full_name,
                    "short_name": course.short_name,
                    "sections": course.section_count,
                    "activities": course.activity_count,
                    "activity_types": course.activity_types,
                },
                "ok": report.ok,
                "errors": [item.__dict__ for item in report.errors],
                "warnings": [item.__dict__ for item in report.warnings],
            })
        if parsed.path == "/" or parsed.path == "/index.html":
            return self._static("index.html", "text/html; charset=utf-8")
        if parsed.path in {"/app.js", "/styles.css"}:
            kind = "text/javascript; charset=utf-8" if parsed.path.endswith(".js") else "text/css; charset=utf-8"
            return self._static(parsed.path.lstrip("/"), kind)
        return self._json({"error": "Nie znaleziono zasobu."}, 404)

    def _static(self, name: str, content_type: str) -> None:
        path = (STATIC / name).resolve()
        if not _inside(path, STATIC) or not path.is_file():
            return self._json({"error": "Nie znaleziono zasobu."}, 404)
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[WebUI] {self.address_string()} - {fmt % args}")


def main() -> None:
    try:
        if not ipaddress.ip_address(HOST).is_loopback:
            raise SystemExit("WebUI jest lokalny i może nasłuchiwać wyłącznie na adresie loopback.")
    except ValueError as exc:
        raise SystemExit("MAGIC_MOODLE_WEBUI_HOST musi być adresem IP loopback.") from exc
    if not 1 <= PORT <= 65535:
        raise SystemExit("MAGIC_MOODLE_WEBUI_PORT musi mieścić się w zakresie 1–65535.")
    if not ROOT.is_dir():
        raise SystemExit(f"Katalog kursów nie istnieje: {ROOT}")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Magic Moodle WebUI: http://{HOST}:{PORT}")
    print(f"Katalog kursów: {ROOT}")
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

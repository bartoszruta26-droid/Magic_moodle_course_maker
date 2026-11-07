"""Local, read-only HTTP API for native and browser clients."""

from __future__ import annotations

import hmac
import ipaddress
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any
from urllib.parse import unquote, urlsplit

from magic_moodle.application import CourseApplicationService, CourseNotFoundError
from magic_moodle.loader import CourseLoadError


API_PREFIX = "/api/v1"


def _finding_payload(finding: Any) -> dict[str, str]:
    return {
        "severity": finding.severity,
        "code": finding.code,
        "path": finding.path,
        "message": finding.message,
    }


def create_server(
    service: CourseApplicationService,
    *,
    host: str = "127.0.0.1",
    port: int = 8766,
    token: str = "",
) -> ThreadingHTTPServer:
    """Create an API server bound to loopback; remote access belongs behind TLS proxy."""
    normalized_host = host.strip().lower()
    if normalized_host != "localhost":
        try:
            address = ipaddress.ip_address(normalized_host)
        except ValueError as exc:
            raise ValueError("API może nasłuchiwać wyłącznie na localhost lub adresie loopback.") from exc
        if not address.is_loopback:
            raise ValueError(
                "API jest serwerem lokalnym. Dostęp zdalny skonfiguruj przez reverse proxy HTTPS."
            )
    if not 0 <= port <= 65535:
        raise ValueError("Port API musi należeć do zakresu 0–65535.")

    class Handler(BaseHTTPRequestHandler):
        server_version = "MagicMoodleAPI/1"
        sys_version = ""

        def log_message(self, format: str, *args: Any) -> None:
            # Do not log authorization headers or request bodies.
            super().log_message(format, *args)

        def _send(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _error(self, status: int, code: str, message: str) -> None:
            self._send(status, {"error": {"code": code, "message": message}})

        def _authorized(self) -> bool:
            if not token:
                return True
            header = self.headers.get("Authorization", "")
            scheme, separator, supplied = header.partition(" ")
            return (
                bool(separator)
                and scheme.lower() == "bearer"
                and hmac.compare_digest(supplied, token)
            )

        def _request_path(self) -> str | None:
            if len(self.path) > 2048:
                self._error(414, "URI_TOO_LONG", "Adres żądania jest zbyt długi.")
                return None
            parsed = urlsplit(self.path)
            if parsed.query or parsed.fragment:
                self._error(400, "UNEXPECTED_QUERY", "Ta wersja API nie przyjmuje parametrów zapytania.")
                return None
            return unquote(parsed.path)

        def do_GET(self) -> None:
            if not self._authorized():
                self._error(401, "UNAUTHORIZED", "Wymagany jest prawidłowy token Bearer.")
                return
            path = self._request_path()
            if path is None:
                return
            if path == f"{API_PREFIX}/health":
                self._send(200, {"data": {"status": "ok"}, "meta": {"api_version": "1"}})
                return
            if path == f"{API_PREFIX}/courses":
                courses = [
                    {
                        "id": item.id,
                        "name": item.name,
                        "short_name": item.short_name,
                        "sections": item.sections,
                        "activities": item.activities,
                        "load_error": item.load_error,
                    }
                    for item in service.list_courses()
                ]
                self._send(200, {"data": courses, "meta": {"api_version": "1"}})
                return
            prefix = f"{API_PREFIX}/courses/"
            if path.startswith(prefix):
                course_id = path[len(prefix):]
                if not course_id or "/" in course_id:
                    self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                    return
                try:
                    course = service.get_course(course_id)
                except CourseNotFoundError:
                    self._error(404, "COURSE_NOT_FOUND", "Nie znaleziono kursu.")
                    return
                except (CourseLoadError, OSError, ValueError):
                    self._error(422, "COURSE_LOAD_FAILED", "Nie udało się wczytać kursu.")
                    return
                sections = [
                    {
                        "id": section.id,
                        "name": section.name,
                        "activity_count": len(section.activities),
                        "activities": [
                            {"type": activity.kind, "ref": activity.ref, "name": activity.name}
                            for activity in section.activities
                        ],
                    }
                    for section in course.sections
                ]
                self._send(
                    200,
                    {
                        "data": {
                            "id": course_id,
                            "name": course.full_name,
                            "short_name": course.short_name,
                            "description": course.description,
                            "sections": sections,
                            "statistics": {
                                "section_count": course.section_count,
                                "activity_count": course.activity_count,
                                "activity_types": course.activity_types,
                            },
                        },
                        "meta": {"api_version": "1"},
                    },
                )
                return
            self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")

        def do_POST(self) -> None:
            if not self._authorized():
                self._error(401, "UNAUTHORIZED", "Wymagany jest prawidłowy token Bearer.")
                return
            path = self._request_path()
            if path is None:
                return
            try:
                body_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._error(400, "INVALID_CONTENT_LENGTH", "Nieprawidłowy Content-Length.")
                return
            if body_length != 0:
                self._error(400, "BODY_NOT_ALLOWED", "To żądanie nie przyjmuje treści.")
                return
            prefix = f"{API_PREFIX}/courses/"
            suffix = "/validation"
            if not path.startswith(prefix) or not path.endswith(suffix):
                self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                return
            course_id = path[len(prefix):-len(suffix)]
            if not course_id or "/" in course_id:
                self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                return
            try:
                _, report = service.validate(course_id)
            except CourseNotFoundError:
                self._error(404, "COURSE_NOT_FOUND", "Nie znaleziono kursu.")
                return
            except (CourseLoadError, OSError, ValueError):
                self._error(422, "COURSE_VALIDATION_FAILED", "Nie udało się zwalidować kursu.")
                return
            self._send(
                200,
                {
                    "data": {
                        "ok": report.ok,
                        "errors": [_finding_payload(item) for item in report.errors],
                        "warnings": [_finding_payload(item) for item in report.warnings],
                    },
                    "meta": {"api_version": "1"},
                },
            )

    class ApiServer(ThreadingHTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    server = ApiServer((host, port), Handler)
    return server


def main() -> int:
    host = os.environ.get("MAGIC_MOODLE_API_HOST", "127.0.0.1")
    port = int(os.environ.get("MAGIC_MOODLE_API_PORT", "8766"))
    token = os.environ.get("MAGIC_MOODLE_API_TOKEN", "")
    courses_root = os.environ.get("MAGIC_MOODLE_COURSES", "courses")
    service = CourseApplicationService(courses_root)
    server = create_server(service, host=host, port=port, token=token)
    print(f"Magic Moodle API v1 nasłuchuje lokalnie na http://{host}:{server.server_port}{API_PREFIX}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

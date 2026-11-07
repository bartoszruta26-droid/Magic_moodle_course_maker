"""Local HTTP API v1 for course inspection and isolated draft editing."""

from __future__ import annotations

import hmac
import ipaddress
import json
import os
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlsplit

from magic_moodle.application import (
    CourseApplicationService,
    CourseDraftConflictError,
    CourseDraftNotFoundError,
    CourseDraftService,
    CourseDraftValidationError,
    CourseNotFoundError,
)
from magic_moodle.loader import CourseLoadError


API_PREFIX = "/api/v1"
_MAX_REQUEST_BYTES = 256 * 1024


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
    """Create a loopback API; write operations require an explicitly configured token."""
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

    draft_service = CourseDraftService(service.courses_root)

    class Handler(BaseHTTPRequestHandler):
        server_version = "MagicMoodleAPI/1"
        sys_version = ""

        def log_message(self, format: str, *args: Any) -> None:
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

        def _authorized(self, *, write: bool = False) -> bool:
            if write and not token:
                self._error(
                    503,
                    "WRITE_AUTH_NOT_CONFIGURED",
                    "Operacje edycji wymagają skonfigurowania MAGIC_MOODLE_API_TOKEN.",
                )
                return False
            if not token:
                return True
            header = self.headers.get("Authorization", "")
            scheme, separator, supplied = header.partition(" ")
            if not (
                bool(separator)
                and scheme.lower() == "bearer"
                and hmac.compare_digest(supplied, token)
            ):
                self._error(401, "UNAUTHORIZED", "Wymagany jest prawidłowy token Bearer.")
                return False
            return True

        def _request_path(self) -> str | None:
            if len(self.path) > 2048:
                self._error(414, "URI_TOO_LONG", "Adres żądania jest zbyt długi.")
                return None
            parsed = urlsplit(self.path)
            if parsed.query or parsed.fragment:
                self._error(400, "UNEXPECTED_QUERY", "Ta wersja API nie przyjmuje parametrów zapytania.")
                return None
            return unquote(parsed.path)

        def _read_json_body(self, *, allow_empty: bool = False) -> dict[str, Any] | None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._error(400, "INVALID_CONTENT_LENGTH", "Nieprawidłowy Content-Length.")
                return None
            if length < 0 or length > _MAX_REQUEST_BYTES:
                self._error(413, "BODY_TOO_LARGE", "Treść żądania przekracza limit 256 KiB.")
                return None
            if length == 0:
                if allow_empty:
                    return {}
                self._error(400, "BODY_REQUIRED", "Wymagana jest treść JSON.")
                return None
            if self.headers.get_content_type() != "application/json":
                self._error(415, "UNSUPPORTED_MEDIA_TYPE", "Wymagany jest Content-Type: application/json.")
                return None
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError):
                self._error(400, "INVALID_JSON", "Treść żądania nie jest poprawnym JSON.")
                return None
            if not isinstance(payload, dict):
                self._error(400, "INVALID_JSON_SHAPE", "Treść JSON musi być obiektem.")
                return None
            return payload

        def _draft_error(self, error: Exception) -> None:
            if isinstance(error, CourseDraftConflictError):
                self._error(409, "DRAFT_CONFLICT", str(error))
            elif isinstance(error, CourseDraftNotFoundError):
                self._error(404, "DRAFT_NOT_FOUND", "Nie znaleziono wersji roboczej.")
            elif isinstance(error, CourseNotFoundError):
                self._error(404, "COURSE_NOT_FOUND", "Nie znaleziono kursu.")
            elif isinstance(error, CourseDraftValidationError):
                self._error(422, "DRAFT_INVALID", str(error))
            elif isinstance(error, (CourseLoadError, OSError, ValueError)):
                self._error(422, "COURSE_LOAD_FAILED", "Nie udało się wczytać kursu.")
            else:
                self._error(500, "INTERNAL_ERROR", "Wystąpił wewnętrzny błąd API.")

        def do_GET(self) -> None:
            if not self._authorized():
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
            draft_prefix = f"{API_PREFIX}/drafts/"
            if path.startswith(draft_prefix):
                suffix = path[len(draft_prefix):]
                is_preview = suffix.endswith("/preview")
                is_history = suffix.endswith("/history")
                if is_preview:
                    draft_id = suffix[:-len("/preview")]
                elif is_history:
                    draft_id = suffix[:-len("/history")]
                else:
                    draft_id = suffix
                if not draft_id or "/" in draft_id:
                    self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                    return
                try:
                    if is_preview:
                        data = draft_service.preview(draft_id)
                    elif is_history:
                        data = [asdict(item) for item in draft_service.history(draft_id)]
                    else:
                        data = asdict(draft_service.get(draft_id))
                except Exception as error:
                    self._draft_error(error)
                    return
                self._send(200, {"data": data, "meta": {"api_version": "1"}})
                return

            prefix = f"{API_PREFIX}/courses/"
            if path.startswith(prefix):
                suffix = path[len(prefix):]
                if suffix.endswith("/drafts"):
                    course_id = suffix[:-len("/drafts")]
                    if not course_id or "/" in course_id:
                        self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                        return
                    try:
                        drafts = [asdict(item) for item in draft_service.list_for_course(course_id)]
                    except Exception as error:
                        self._draft_error(error)
                        return
                    self._send(200, {"data": drafts, "meta": {"api_version": "1"}})
                    return
                course_id = suffix
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
            path = self._request_path()
            if path is None:
                return
            is_draft_creation = path.startswith(f"{API_PREFIX}/courses/") and path.endswith("/drafts")
            is_draft_update = path.startswith(f"{API_PREFIX}/drafts/") and path.endswith("/update")
            is_draft_restore = path.startswith(f"{API_PREFIX}/drafts/") and path.endswith("/restore")
            if not self._authorized(write=is_draft_creation or is_draft_update or is_draft_restore):
                return
            validation_prefix = f"{API_PREFIX}/courses/"
            validation_suffix = "/validation"
            if path.startswith(validation_prefix) and path.endswith(validation_suffix):
                body = self._read_json_body(allow_empty=True)
                if body is None:
                    return
                course_id = path[len(validation_prefix):-len(validation_suffix)]
                if not course_id or "/" in course_id:
                    self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                    return
                try:
                    _, report = service.validate(course_id)
                except Exception as error:
                    self._draft_error(error)
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
                return

            create_suffix = "/drafts"
            if path.startswith(validation_prefix) and path.endswith(create_suffix):
                body = self._read_json_body(allow_empty=True)
                if body is None:
                    return
                course_id = path[len(validation_prefix):-len(create_suffix)]
                if not course_id or "/" in course_id:
                    self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                    return
                if body:
                    self._error(400, "UNEXPECTED_FIELDS", "Utworzenie wersji roboczej nie przyjmuje pól.")
                    return
                try:
                    draft = draft_service.create(course_id)
                except Exception as error:
                    self._draft_error(error)
                    return
                self._send(201, {"data": asdict(draft), "meta": {"api_version": "1"}})
                return
            update_prefix = f"{API_PREFIX}/drafts/"
            update_suffix = "/update"
            if path.startswith(update_prefix) and path.endswith(update_suffix):
                body = self._read_json_body()
                if body is None:
                    return
                draft_id = path[len(update_prefix):-len(update_suffix)]
                if not draft_id or "/" in draft_id:
                    self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                    return
                if set(body) != {"expected_revision", "changes"}:
                    self._error(
                        400,
                        "INVALID_DRAFT_UPDATE",
                        "Wymagane są wyłącznie pola expected_revision i changes.",
                    )
                    return
                try:
                    updated = draft_service.update(
                        draft_id,
                        expected_revision=body["expected_revision"],
                        changes=body["changes"],
                    )
                except Exception as error:
                    self._draft_error(error)
                    return
                self._send(200, {"data": asdict(updated), "meta": {"api_version": "1"}})
                return
            restore_prefix = f"{API_PREFIX}/drafts/"
            restore_suffix = "/restore"
            if path.startswith(restore_prefix) and path.endswith(restore_suffix):
                body = self._read_json_body()
                if body is None:
                    return
                draft_id = path[len(restore_prefix):-len(restore_suffix)]
                if not draft_id or "/" in draft_id:
                    self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                    return
                if set(body) != {"expected_revision", "target_revision"}:
                    self._error(
                        400,
                        "INVALID_DRAFT_RESTORE",
                        "Wymagane są wyłącznie pola expected_revision i target_revision.",
                    )
                    return
                try:
                    restored = draft_service.restore(
                        draft_id,
                        expected_revision=body["expected_revision"],
                        target_revision=body["target_revision"],
                    )
                except Exception as error:
                    self._draft_error(error)
                    return
                self._send(200, {"data": asdict(restored), "meta": {"api_version": "1"}})
                return
            self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")

        def do_PATCH(self) -> None:
            if not self._authorized(write=True):
                return
            path = self._request_path()
            if path is None:
                return
            prefix = f"{API_PREFIX}/drafts/"
            if not path.startswith(prefix):
                self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                return
            draft_id = path[len(prefix):]
            if not draft_id or "/" in draft_id:
                self._error(404, "NOT_FOUND", "Nie znaleziono zasobu.")
                return
            body = self._read_json_body()
            if body is None:
                return
            if set(body) != {"expected_revision", "changes"}:
                self._error(
                    400,
                    "INVALID_DRAFT_UPDATE",
                    "Wymagane są wyłącznie pola expected_revision i changes.",
                )
                return
            try:
                updated = draft_service.update(
                    draft_id,
                    expected_revision=body["expected_revision"],
                    changes=body["changes"],
                )
            except Exception as error:
                self._draft_error(error)
                return
            self._send(200, {"data": asdict(updated), "meta": {"api_version": "1"}})

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

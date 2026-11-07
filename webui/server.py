"""Local WebUI for course inspection and isolated draft editing."""

from __future__ import annotations

import hmac
import ipaddress
import json
import os
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import unquote, urlparse

from magic_moodle.application import (
    CourseApplicationService,
    CourseDraftConflictError,
    CourseDraftNotFoundError,
    CourseDraftService,
    CourseDraftValidationError,
    CourseNotFoundError,
)
from magic_moodle.loader import CourseLoadError

ROOT = Path(os.environ.get("MAGIC_MOODLE_COURSES", "courses")).resolve()
STATIC = Path(__file__).with_name("static").resolve()
HOST = os.environ.get("MAGIC_MOODLE_WEBUI_HOST", "127.0.0.1")
PORT = int(os.environ.get("MAGIC_MOODLE_WEBUI_PORT", "8765"))
API_TOKEN = os.environ.get("MAGIC_MOODLE_API_TOKEN", "")
MAX_REQUEST_BYTES = 256 * 1024


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


_DRAFT_SERVICES: dict[Path, CourseDraftService] = {}
_DRAFT_SERVICES_LOCK = Lock()


def _draft_service() -> CourseDraftService:
    root = ROOT.resolve()
    with _DRAFT_SERVICES_LOCK:
        if root not in _DRAFT_SERVICES:
            _DRAFT_SERVICES[root] = CourseDraftService(root)
        return _DRAFT_SERVICES[root]


class Handler(BaseHTTPRequestHandler):
    server_version = "MagicMoodleWebUI/0.3"

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

    def _error(self, message: str, status: int, code: str | None = None) -> None:
        payload: dict[str, object] = {"error": message}
        if code:
            payload["code"] = code
        self._json(payload, status)

    def _check_host(self) -> bool:
        if _is_allowed_host(self.headers.get("Host")):
            return True
        self._error("Niedozwolony nagłówek Host.", 403, "HOST_FORBIDDEN")
        return False

    def _authorize_draft(self, *, write: bool = False) -> bool:
        if write and not API_TOKEN:
            self._error(
                "Edycja wymaga skonfigurowania MAGIC_MOODLE_API_TOKEN.",
                503,
                "WRITE_AUTH_NOT_CONFIGURED",
            )
            return False
        if API_TOKEN:
            header = self.headers.get("Authorization", "")
            scheme, separator, supplied = header.partition(" ")
            if not (
                separator
                and scheme.lower() == "bearer"
                and hmac.compare_digest(supplied, API_TOKEN)
            ):
                self._error("Wymagany jest prawidłowy token Bearer.", 401, "UNAUTHORIZED")
                return False
        return True

    def _read_json_body(self, *, allow_empty: bool = False) -> dict[str, object] | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._error("Nieprawidłowy Content-Length.", 400, "INVALID_CONTENT_LENGTH")
            return None
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._error("Treść żądania przekracza limit 256 KiB.", 413, "BODY_TOO_LARGE")
            return None
        if length == 0:
            if allow_empty:
                return {}
            self._error("Wymagana jest treść JSON.", 400, "BODY_REQUIRED")
            return None
        if self.headers.get_content_type() != "application/json":
            self._error("Wymagany jest Content-Type: application/json.", 415, "UNSUPPORTED_MEDIA_TYPE")
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            self._error("Treść żądania nie jest poprawnym JSON.", 400, "INVALID_JSON")
            return None
        if not isinstance(payload, dict):
            self._error("Treść JSON musi być obiektem.", 400, "INVALID_JSON_SHAPE")
            return None
        return payload

    def _draft_error(self, error: Exception) -> None:
        if isinstance(error, CourseDraftConflictError):
            self._error(str(error), 409, "DRAFT_CONFLICT")
        elif isinstance(error, CourseDraftNotFoundError):
            self._error("Nie znaleziono wersji roboczej.", 404, "DRAFT_NOT_FOUND")
        elif isinstance(error, CourseNotFoundError):
            self._error("Nie znaleziono kursu.", 404, "COURSE_NOT_FOUND")
        elif isinstance(error, CourseDraftValidationError):
            self._error(str(error), 422, "DRAFT_INVALID")
        elif isinstance(error, (CourseLoadError, OSError, ValueError)):
            self._error("Nie udało się wczytać kursu.", 422, "COURSE_LOAD_FAILED")
        else:
            self._error("Wystąpił wewnętrzny błąd WebUI.", 500, "INTERNAL_ERROR")

    def do_GET(self) -> None:  # noqa: N802
        if not self._check_host():
            return
        parsed = urlparse(self.path)
        if parsed.query or parsed.fragment:
            return self._error("Parametry zapytania nie są obsługiwane.", 400, "UNEXPECTED_QUERY")
        if parsed.path == "/api/health":
            return self._json({"ok": True})
        if parsed.path == "/api/courses":
            return self._json({"courses": list_courses()})
        draft_prefix = "/api/drafts/"
        if parsed.path.startswith(draft_prefix):
            if not self._authorize_draft():
                return
            suffix = parsed.path[len(draft_prefix):]
            is_preview = suffix.endswith("/preview")
            is_history = suffix.endswith("/history")
            if is_preview:
                draft_id = suffix[:-len("/preview")]
            elif is_history:
                draft_id = suffix[:-len("/history")]
            else:
                draft_id = suffix
            if not draft_id or "/" in draft_id:
                return self._error("Nie znaleziono wersji roboczej.", 404, "DRAFT_NOT_FOUND")
            try:
                if is_preview:
                    result = _draft_service().preview(draft_id)
                elif is_history:
                    result = [asdict(item) for item in _draft_service().history(draft_id)]
                else:
                    result = asdict(_draft_service().get(draft_id))
            except Exception as error:
                return self._draft_error(error)
            return self._json({"data": result})
        courses_prefix = "/api/courses/"
        drafts_suffix = "/drafts"
        if parsed.path.startswith(courses_prefix) and parsed.path.endswith(drafts_suffix):
            if not self._authorize_draft():
                return
            course_id = unquote(parsed.path[len(courses_prefix):-len(drafts_suffix)])
            if not course_id or "/" in course_id or "\\" in course_id:
                return self._error("Nieprawidłowy identyfikator kursu.", 400, "INVALID_COURSE_ID")
            try:
                drafts = [asdict(item) for item in _draft_service().list_for_course(course_id)]
            except Exception as error:
                return self._draft_error(error)
            return self._json({"data": drafts})

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

    def do_POST(self) -> None:  # noqa: N802
        if not self._check_host():
            return
        parsed = urlparse(self.path)
        if parsed.query or parsed.fragment:
            return self._error("Parametry zapytania nie są obsługiwane.", 400, "UNEXPECTED_QUERY")
        create_prefix, create_suffix = "/api/courses/", "/drafts"
        restore_prefix, restore_suffix = "/api/drafts/", "/restore"
        is_create = parsed.path.startswith(create_prefix) and parsed.path.endswith(create_suffix)
        is_restore = parsed.path.startswith(restore_prefix) and parsed.path.endswith(restore_suffix)
        if not (is_create or is_restore):
            return self._error("Nie znaleziono zasobu.", 404, "NOT_FOUND")
        if not self._authorize_draft(write=True):
            return
        body = self._read_json_body(allow_empty=is_create)
        if body is None:
            return
        if is_create:
            course_id = unquote(parsed.path[len(create_prefix):-len(create_suffix)])
            if not course_id or "/" in course_id or "\\" in course_id:
                return self._error("Nieprawidłowy identyfikator kursu.", 400, "INVALID_COURSE_ID")
            if body:
                return self._error("Utworzenie wersji roboczej nie przyjmuje pól.", 400, "UNEXPECTED_FIELDS")
            try:
                draft = _draft_service().create(course_id)
            except Exception as error:
                return self._draft_error(error)
            return self._json({"data": asdict(draft)}, 201)

        draft_id = parsed.path[len(restore_prefix):-len(restore_suffix)]
        if not draft_id or "/" in draft_id:
            return self._error("Nie znaleziono wersji roboczej.", 404, "DRAFT_NOT_FOUND")
        if set(body) != {"expected_revision", "target_revision"}:
            return self._error(
                "Wymagane są wyłącznie pola expected_revision i target_revision.",
                400,
                "INVALID_DRAFT_RESTORE",
            )
        try:
            restored = _draft_service().restore(
                draft_id,
                expected_revision=body["expected_revision"],  # type: ignore[arg-type]
                target_revision=body["target_revision"],  # type: ignore[arg-type]
            )
        except Exception as error:
            return self._draft_error(error)
        return self._json({"data": asdict(restored)})

    def do_PATCH(self) -> None:  # noqa: N802
        if not self._check_host():
            return
        parsed = urlparse(self.path)
        if parsed.query or parsed.fragment:
            return self._error("Parametry zapytania nie są obsługiwane.", 400, "UNEXPECTED_QUERY")
        prefix = "/api/drafts/"
        if not parsed.path.startswith(prefix):
            return self._error("Nie znaleziono zasobu.", 404, "NOT_FOUND")
        if not self._authorize_draft(write=True):
            return
        draft_id = parsed.path[len(prefix):]
        if not draft_id or "/" in draft_id:
            return self._error("Nie znaleziono wersji roboczej.", 404, "DRAFT_NOT_FOUND")
        body = self._read_json_body()
        if body is None:
            return
        if set(body) != {"expected_revision", "changes"}:
            return self._error(
                "Wymagane są wyłącznie pola expected_revision i changes.",
                400,
                "INVALID_DRAFT_UPDATE",
            )
        try:
            updated = _draft_service().update(
                draft_id,
                expected_revision=body["expected_revision"],  # type: ignore[arg-type]
                changes=body["changes"],  # type: ignore[arg-type]
            )
        except Exception as error:
            return self._draft_error(error)
        return self._json({"data": asdict(updated)})

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

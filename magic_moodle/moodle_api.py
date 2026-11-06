"""Moodle REST web-service client (standard REST endpoint, JSON responses)."""
from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit


class MoodleAPIError(RuntimeError):
    """Transport, authentication or Moodle application-level error."""


def _flatten(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    """Flatten mappings/sequences into Moodle's bracketed form parameters."""
    pairs: list[tuple[str, str]] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = f"{prefix}[{key}]" if prefix else str(key)
            pairs.extend(_flatten(item, name))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            name = f"{prefix}[{index}]"
            pairs.extend(_flatten(item, name))
    elif value is None:
        return pairs
    elif isinstance(value, bool):
        pairs.append((prefix, "1" if value else "0"))
    else:
        pairs.append((prefix, str(value)))
    return pairs


@dataclass(frozen=True)
class MoodleConfig:
    base_url: str
    token: str
    timeout: float = 30.0
    verify_tls: bool = True

    @classmethod
    def from_env(cls) -> "MoodleConfig":
        base_url = os.environ.get("MOODLE_URL", "").strip()
        token = os.environ.get("MOODLE_TOKEN", "").strip()
        if not base_url or not token:
            raise MoodleAPIError(
                "Ustaw zmienne MOODLE_URL i MOODLE_TOKEN. Token przechowuj poza repozytorium."
            )
        verify = os.environ.get("MOODLE_VERIFY_TLS", "true").lower() not in {
            "0", "false", "no"
        }
        try:
            timeout = float(os.environ.get("MOODLE_TIMEOUT", "30"))
        except ValueError as exc:
            raise MoodleAPIError("MOODLE_TIMEOUT musi być liczbą.") from exc
        return cls(base_url=base_url, token=token, timeout=timeout, verify_tls=verify)


class MoodleClient:
    """Small stdlib-only client for Moodle's /webservice/rest/server.php."""

    def __init__(self, config: MoodleConfig):
        parts = urlsplit(config.base_url)
        if parts.scheme not in {"https", "http"} or not parts.netloc:
            raise MoodleAPIError("MOODLE_URL musi być pełnym adresem http(s).")
        if parts.username or parts.password or parts.query or parts.fragment:
            raise MoodleAPIError("MOODLE_URL nie może zawierać danych logowania, query ani fragmentu.")
        if parts.scheme != "https" and parts.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise MoodleAPIError("Wymagane jest HTTPS dla hostów zdalnych; HTTP jest dozwolone wyłącznie dla localhost.")
        if not config.token:
            raise MoodleAPIError("Brak tokenu Moodle.")
        self.config = config
        base_path = parts.path.rstrip("/")
        endpoint = base_path + "/webservice/rest/server.php"
        self.endpoint = urlunsplit((parts.scheme, parts.netloc, endpoint, "", ""))

    def call(self, function: str, params: Mapping[str, Any] | None = None) -> Any:
        if not function or not function.replace("_", "").isalnum():
            raise MoodleAPIError("Niepoprawna nazwa funkcji Moodle.")
        payload = {
            "wstoken": self.config.token,
            "wsfunction": function,
            "moodlewsrestformat": "json",
        }
        if params:
            payload.update(dict(_flatten(params)))
        body = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": "MagicMoodleCourseMaker/0.2",
            },
            method="POST",
        )
        context = None
        if self.endpoint.startswith("https://") and not self.config.verify_tls:
            context = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(
                request, timeout=self.config.timeout, context=context
            ) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
        except urllib.error.HTTPError as exc:
            detail = exc.read(4096).decode("utf-8", errors="replace")
            raise MoodleAPIError(
                f"Moodle zwrócił HTTP {exc.code}; odpowiedź: {detail[:1000]}"
            ) from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise MoodleAPIError(f"Nie udało się połączyć z Moodle: {exc}") from None
        if len(raw) > 8 * 1024 * 1024:
            raise MoodleAPIError("Odpowiedź Moodle przekracza limit 8 MiB.")
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            preview = raw[:300].decode("utf-8", errors="replace")
            raise MoodleAPIError(
                f"Moodle nie zwrócił poprawnego JSON (możliwy błąd endpointu): {preview}"
            ) from None
        if isinstance(result, dict) and (
            result.get("exception") or result.get("errorcode")
        ):
            code = result.get("errorcode", "MOODLE_ERROR")
            message = result.get("message", "Nieznany błąd Moodle.")
            raise MoodleAPIError(f"{code}: {message}")
        return result

    def site_info(self) -> dict[str, Any]:
        result = self.call("core_webservice_get_site_info")
        if not isinstance(result, dict):
            raise MoodleAPIError("Nieoczekiwany wynik core_webservice_get_site_info.")
        return result

    def get_course_by_shortname(self, shortname: str) -> dict[str, Any] | None:
        result = self.call(
            "core_course_get_courses_by_field",
            {"field": "shortname", "value": shortname},
        )
        courses = result.get("courses", []) if isinstance(result, dict) else result
        if not isinstance(courses, list):
            raise MoodleAPIError("Nieoczekiwany wynik wyszukiwania kursu.")
        return courses[0] if courses else None

    def create_course(self, course: Mapping[str, Any]) -> dict[str, Any]:
        result = self.call("core_course_create_courses", {"courses": [dict(course)]})
        if not isinstance(result, list) or not result or not isinstance(result[0], dict):
            raise MoodleAPIError("Moodle nie zwrócił identyfikatora utworzonego kursu.")
        return result[0]

    def ensure_course(self, course: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
        shortname = str(course.get("shortname", "")).strip()
        if not shortname:
            raise MoodleAPIError("Do utworzenia kursu wymagane jest shortname.")
        existing = self.get_course_by_shortname(shortname)
        if existing:
            return existing, False
        return self.create_course(course), True

    def create_activity(
        self, courseid: int, sectionnum: int, activity: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Create page, label or URL through the companion local_magicmoodle plugin."""
        kind = str(activity.get("type", "")).lower()
        if kind not in {"page", "label", "url"}:
            raise MoodleAPIError(
                f"Aktywność '{kind}' wymaga osobnego adaptera Moodle; nie zostanie pominięta."
            )
        return self.call(
            "local_magicmoodle_create_activity",
            {
                "courseid": courseid,
                "sectionnum": sectionnum,
                "modname": kind,
                "name": activity["name"],
                "content": activity.get("content", ""),
                "externalurl": activity.get("externalurl", ""),
            },
        )

    def update_section(
        self, courseid: int, sectionnum: int, name: str
    ) -> dict[str, Any]:
        return self.call(
            "local_magicmoodle_update_section",
            {"courseid": courseid, "sectionnum": sectionnum, "name": name},
        )

    def create_assignment(
        self, courseid: int, sectionnum: int, activity: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Create an Assignment with configured submission plugins and deadlines."""
        return self.call(
            "local_magicmoodle_create_assignment",
            {
                "courseid": courseid,
                "sectionnum": sectionnum,
                "name": activity["name"],
                "intro": activity.get("intro", ""),
                "allowsubmissionsfromdate": activity.get("allowsubmissionsfromdate", 0),
                "duedate": activity.get("duedate", 0),
                "cutoffdate": activity.get("cutoffdate", 0),
                "grade": activity.get("grade", 100),
                "submissiontype": activity.get("submissiontype", "both"),
                "maxfiles": activity.get("maxfiles", 5),
                "maxbytes": activity.get("maxbytes", 10485760),
                "submissiondrafts": activity.get("submissiondrafts", False),
                "requiresubmissionstatement": activity.get("requiresubmissionstatement", False),
                "completionenabled": activity.get("completionenabled", False),
            },
        )

    def create_book(
        self, courseid: int, sectionnum: int, activity: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Create a Moodle Book activity with ordered chapters."""
        chapters = activity.get("chapters")
        if not isinstance(chapters, list) or not chapters:
            raise MoodleAPIError("Aktywność Book wymaga co najmniej jednego rozdziału.")
        return self.call(
            "local_magicmoodle_create_book",
            {
                "courseid": courseid,
                "sectionnum": sectionnum,
                "name": activity["name"],
                "chapters": chapters,
                "numbering": activity.get("numbering", 1),
            },
        )

    def create_quiz(
        self, courseid: int, sectionnum: int, activity: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Create a Moodle Quiz and import its GIFT questions through Moodle's importer."""
        gift = activity.get("gift")
        if not isinstance(gift, str) or not gift.strip():
            raise MoodleAPIError("Quiz wymaga niepustego źródła GIFT.")
        return self.call(
            "local_magicmoodle_create_quiz",
            {
                "courseid": courseid,
                "sectionnum": sectionnum,
                "name": activity["name"],
                "intro": activity.get("intro", ""),
                "gift": gift,
                "timelimit": activity.get("timelimit", 0),
                "attempts": activity.get("attempts", 1),
                "grade": activity.get("grade", 10),
                "passingpercent": activity.get("passingpercent", 0),
                "shuffleanswers": activity.get("shuffleanswers", True),
                "questionsperpage": activity.get("questionsperpage", 1),
                "completionenabled": activity.get("completionenabled", False),
                "completiontype": activity.get("completiontype", "grade"),
            },
        )

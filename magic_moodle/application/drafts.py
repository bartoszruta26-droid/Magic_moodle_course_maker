"""Persistent, optimistic-concurrency course drafts shared by every UI adapter."""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from magic_moodle.course_export import course_manifest, to_course_json
from magic_moodle.io_utils import atomic_write_text
from magic_moodle.models import Course
from magic_moodle.validation import validate_course

_DRAFT_FORMAT = "magic-moodle-course-draft"
_DRAFT_VERSION = 1
_MAX_DRAFT_BYTES = 512 * 1024
_MAX_DESCRIPTION_LENGTH = 100_000
_MAX_NAME_LENGTH = 250
_ACTIVITY_KEY_SEPARATOR = "|"


class CourseDraftError(Exception):
    """Base class for safe, user-correctable draft errors."""


class CourseDraftNotFoundError(CourseDraftError):
    """The requested draft does not exist or is malformed."""


class CourseDraftConflictError(CourseDraftError):
    """The supplied revision is stale or the source course changed."""


class CourseDraftValidationError(CourseDraftError):
    """A draft contains unsupported or invalid changes."""


@dataclass(frozen=True)
class CourseDraft:
    draft_id: str
    course_id: str
    revision: int
    created_at: str
    updated_at: str
    base_digest: str
    changes: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _course_digest(course: Course) -> str:
    return hashlib.sha256(to_course_json(course).encode("utf-8")).hexdigest()


def _validate_text(value: Any, field: str, *, maximum: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise CourseDraftValidationError(f"Pole {field} musi być tekstem.")
    if len(value) > maximum:
        raise CourseDraftValidationError(f"Pole {field} przekracza limit {maximum} znaków.")
    if not allow_empty and not value.strip():
        raise CourseDraftValidationError(f"Pole {field} nie może być puste.")
    return value


class CourseDraftService:
    """Store editable overlays without modifying the source course files.

    Draft updates require an expected revision. Preview applies the overlay to
    the canonical immutable model and runs the existing validator. The source
    course is never rewritten by this service.
    """

    def __init__(self, courses_root: str | Path) -> None:
        self.courses_root = Path(courses_root).expanduser().resolve()
        self._lock = threading.RLock()

    def _drafts_dir(self) -> Path:
        candidate = self.courses_root / ".magic_moodle" / "drafts"
        candidate.mkdir(parents=True, exist_ok=True)
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.courses_root):
            raise CourseDraftValidationError("Katalog wersji roboczych wychodzi poza katalog kursów.")
        return resolved

    @staticmethod
    def _validate_draft_id(draft_id: str) -> str:
        try:
            return str(uuid.UUID(draft_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise CourseDraftNotFoundError("Nie znaleziono wersji roboczej.") from exc

    def _draft_path(self, draft_id: str) -> Path:
        normalized = self._validate_draft_id(draft_id)
        directory = self._drafts_dir()
        path = directory / f"{normalized}.json"
        if not path.resolve().is_relative_to(directory):
            raise CourseDraftNotFoundError("Nie znaleziono wersji roboczej.")
        return path

    @staticmethod
    def _serialize(draft: CourseDraft) -> str:
        payload = {"format": _DRAFT_FORMAT, "format_version": _DRAFT_VERSION, **asdict(draft)}
        return json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"

    @staticmethod
    def _deserialize_payload(payload: Any, expected_draft_id: str) -> CourseDraft:
        if not isinstance(payload, dict):
            raise ValueError("invalid draft document")
        if payload.get("format") != _DRAFT_FORMAT or payload.get("format_version") != _DRAFT_VERSION:
            raise ValueError("unsupported draft format")
        draft = CourseDraft(
            draft_id=CourseDraftService._validate_draft_id(payload["draft_id"]),
            course_id=payload["course_id"],
            revision=payload["revision"],
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
            base_digest=payload["base_digest"],
            changes=payload["changes"],
        )
        if (
            draft.draft_id != CourseDraftService._validate_draft_id(expected_draft_id)
            or not isinstance(draft.course_id, str)
            or not draft.course_id
            or type(draft.revision) is not int
            or draft.revision < 1
            or not isinstance(draft.created_at, str)
            or not isinstance(draft.updated_at, str)
            or not isinstance(draft.base_digest, str)
            or len(draft.base_digest) != 64
            or not isinstance(draft.changes, dict)
        ):
            raise ValueError("invalid draft fields")
        return draft

    def _read(self, draft_id: str) -> CourseDraft:
        path = self._draft_path(draft_id)
        try:
            if path.stat().st_size > _MAX_DRAFT_BYTES:
                raise CourseDraftNotFoundError("Plik wersji roboczej przekracza dopuszczalny rozmiar.")
            payload = json.loads(path.read_text(encoding="utf-8"))
            return self._deserialize_payload(payload, draft_id)
        except CourseDraftError:
            raise
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
            raise CourseDraftNotFoundError("Nie znaleziono poprawnej wersji roboczej.") from exc

    def _history_dir(self, draft_id: str) -> Path:
        normalized = self._validate_draft_id(draft_id)
        root = self._drafts_dir()
        candidate = root / f"{normalized}.history"
        candidate.mkdir(parents=True, exist_ok=True)
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            raise CourseDraftValidationError("Katalog historii wychodzi poza katalog wersji roboczych.")
        return resolved

    def _snapshot_path(self, draft_id: str, revision: int) -> Path:
        if type(revision) is not int or revision < 1:
            raise CourseDraftNotFoundError("Nie znaleziono rewizji wersji roboczej.")
        directory = self._history_dir(draft_id)
        path = directory / f"{revision:08d}.json"
        if not path.resolve().is_relative_to(directory):
            raise CourseDraftNotFoundError("Nie znaleziono rewizji wersji roboczej.")
        return path

    def _write_snapshot(self, draft: CourseDraft) -> None:
        atomic_write_text(
            self._snapshot_path(draft.draft_id, draft.revision),
            self._serialize(draft),
        )

    def _read_snapshot(self, draft_id: str, revision: int) -> CourseDraft:
        path = self._snapshot_path(draft_id, revision)
        try:
            if path.stat().st_size > _MAX_DRAFT_BYTES:
                raise CourseDraftNotFoundError("Migawka rewizji przekracza dopuszczalny rozmiar.")
            payload = json.loads(path.read_text(encoding="utf-8"))
            draft = self._deserialize_payload(payload, draft_id)
            if draft.revision != revision:
                raise ValueError("snapshot revision mismatch")
            return draft
        except CourseDraftError:
            raise
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
            raise CourseDraftNotFoundError("Nie znaleziono rewizji wersji roboczej.") from exc

    def create(self, course_id: str) -> CourseDraft:
        from magic_moodle.application.queries import CourseApplicationService

        course = CourseApplicationService(self.courses_root).get_course(course_id)
        now = _utc_now()
        draft = CourseDraft(
            draft_id=str(uuid.uuid4()),
            course_id=course_id,
            revision=1,
            created_at=now,
            updated_at=now,
            base_digest=_course_digest(course),
            changes={},
        )
        with self._lock:
            self._write_snapshot(draft)
            atomic_write_text(self._draft_path(draft.draft_id), self._serialize(draft))
        return draft

    def get(self, draft_id: str) -> CourseDraft:
        with self._lock:
            return self._read(draft_id)

    def update(
        self,
        draft_id: str,
        *,
        expected_revision: int,
        changes: dict[str, Any],
    ) -> CourseDraft:
        if type(expected_revision) is not int or expected_revision < 1:
            raise CourseDraftValidationError("Wymagana jest dodatnia rewizja wersji roboczej.")
        if not isinstance(changes, dict) or not changes:
            raise CourseDraftValidationError("Zmiany muszą być niepustym obiektem JSON.")

        if any(not isinstance(key, str) for key in changes):
            raise CourseDraftValidationError("Nazwy pól zmian muszą być tekstem.")
        allowed = {"full_name", "short_name", "description", "section_names", "activity_names"}
        unknown = set(changes) - allowed
        if unknown:
            raise CourseDraftValidationError(
                "Nieobsługiwane pola wersji roboczej: " + ", ".join(sorted(unknown))
            )

        normalized: dict[str, Any] = {}
        if "full_name" in changes:
            normalized["full_name"] = _validate_text(
                changes["full_name"], "full_name", maximum=_MAX_NAME_LENGTH
            )
        if "short_name" in changes:
            normalized["short_name"] = _validate_text(
                changes["short_name"], "short_name", maximum=100
            )
        if "description" in changes:
            normalized["description"] = _validate_text(
                changes["description"], "description",
                maximum=_MAX_DESCRIPTION_LENGTH, allow_empty=True,
            )
        for mapping_name in ("section_names", "activity_names"):
            if mapping_name not in changes:
                continue
            mapping = changes[mapping_name]
            if not isinstance(mapping, dict) or len(mapping) > 500:
                raise CourseDraftValidationError(f"Pole {mapping_name} musi być mapą do 500 wpisów.")
            clean: dict[str, str] = {}
            for key, value in mapping.items():
                if not isinstance(key, str) or not key or len(key) > 500:
                    raise CourseDraftValidationError(f"Nieprawidłowy identyfikator w {mapping_name}.")
                clean[key] = _validate_text(value, f"{mapping_name}.{key}", maximum=_MAX_NAME_LENGTH)
            normalized[mapping_name] = clean

        with self._lock:
            current = self._read(draft_id)
            if current.revision != expected_revision:
                raise CourseDraftConflictError(
                    f"Nieaktualna rewizja. Bieżąca rewizja: {current.revision}."
                )
            merged = dict(current.changes)
            for key, value in normalized.items():
                if key in {"section_names", "activity_names"}:
                    merged[key] = {**merged.get(key, {}), **value}
                else:
                    merged[key] = value
            from magic_moodle.application.queries import CourseApplicationService

            source_course = CourseApplicationService(self.courses_root).get_course(current.course_id)
            if _course_digest(source_course) != current.base_digest:
                raise CourseDraftConflictError(
                    "Kurs źródłowy zmienił się od utworzenia wersji roboczej. Utwórz nową wersję."
                )
            updated = replace(
                current,
                revision=current.revision + 1,
                updated_at=_utc_now(),
                changes=merged,
            )
            # Validate section/activity identifiers before persisting the new revision.
            self._apply(source_course, updated)
            self._write_snapshot(updated)
            atomic_write_text(self._draft_path(updated.draft_id), self._serialize(updated))
            return updated

    def list_for_course(self, course_id: str) -> list[CourseDraft]:
        """List current drafts for a course, newest update first."""
        drafts: list[CourseDraft] = []
        with self._lock:
            for path in self._drafts_dir().glob("*.json"):
                try:
                    draft = self._read(path.stem)
                except CourseDraftNotFoundError:
                    continue
                if draft.course_id == course_id:
                    drafts.append(draft)
        return sorted(drafts, key=lambda item: item.updated_at, reverse=True)

    def history(self, draft_id: str) -> list[CourseDraft]:
        """Return immutable snapshots in ascending revision order."""
        with self._lock:
            current = self._read(draft_id)
            directory = self._history_dir(current.draft_id)
            snapshots: dict[int, CourseDraft] = {}
            for path in directory.glob("*.json"):
                try:
                    revision = int(path.stem)
                    if revision > current.revision:
                        continue
                    snapshot = self._read_snapshot(current.draft_id, revision)
                    if snapshot.course_id == current.course_id and snapshot.base_digest == current.base_digest:
                        snapshots[revision] = snapshot
                except (ValueError, CourseDraftNotFoundError):
                    continue
            if current.revision not in snapshots:
                # Backfill the current revision for drafts created before history support.
                self._write_snapshot(current)
                snapshots[current.revision] = current
            return [snapshots[number] for number in sorted(snapshots)]

    def restore(
        self,
        draft_id: str,
        *,
        expected_revision: int,
        target_revision: int,
    ) -> CourseDraft:
        """Restore a prior snapshot as a new revision; never rewind the revision counter."""
        if type(target_revision) is not int or target_revision < 1:
            raise CourseDraftValidationError("Rewizja docelowa musi być dodatnią liczbą całkowitą.")
        current = self.get(draft_id)
        if current.revision != expected_revision:
            raise CourseDraftConflictError(
                f"Nieaktualna rewizja. Bieżąca rewizja: {current.revision}."
            )
        if target_revision > current.revision:
            raise CourseDraftNotFoundError("Nie znaleziono rewizji wersji roboczej.")
        target = self._read_snapshot(draft_id, target_revision)
        if target.course_id != current.course_id or target.base_digest != current.base_digest:
            raise CourseDraftConflictError("Rewizja docelowa pochodzi z innej wersji bazowej kursu.")

        from magic_moodle.application.queries import CourseApplicationService

        source_course = CourseApplicationService(self.courses_root).get_course(current.course_id)
        if _course_digest(source_course) != current.base_digest:
            raise CourseDraftConflictError(
                "Kurs źródłowy zmienił się od utworzenia wersji roboczej. Utwórz nową wersję."
            )
        target_course = self._apply(source_course, target)
        current_section_keys = set(current.changes.get("section_names", {}))
        target_section_keys = set(target.changes.get("section_names", {}))
        current_activity_keys = set(current.changes.get("activity_names", {}))
        target_activity_keys = set(target.changes.get("activity_names", {}))
        section_keys = current_section_keys | target_section_keys
        activity_keys = current_activity_keys | target_activity_keys
        section_names = {
            section.id: section.name
            for section in target_course.sections
            if section.id in section_keys
        }
        activity_names = {
            f"{section.id}{_ACTIVITY_KEY_SEPARATOR}{activity.ref}": activity.name
            for section in target_course.sections
            for activity in section.activities
            if f"{section.id}{_ACTIVITY_KEY_SEPARATOR}{activity.ref}" in activity_keys
        }
        return self.update(
            draft_id,
            expected_revision=expected_revision,
            changes={
                "full_name": target_course.full_name,
                "short_name": target_course.short_name,
                "description": target_course.description,
                "section_names": section_names,
                "activity_names": activity_names,
            },
        )

    def _apply(self, course: Course, draft: CourseDraft) -> Course:
        changes = draft.changes
        section_names = changes.get("section_names", {})
        activity_names = changes.get("activity_names", {})
        if not isinstance(section_names, dict) or not isinstance(activity_names, dict):
            raise CourseDraftValidationError("Nieprawidłowa mapa zmian wersji roboczej.")

        known_sections = {section.id for section in course.sections}
        unknown_sections = set(section_names) - known_sections
        if unknown_sections:
            raise CourseDraftValidationError(
                "Nie znaleziono sekcji: " + ", ".join(sorted(unknown_sections))
            )

        known_activities: set[str] = set()
        for section in course.sections:
            for activity in section.activities:
                known_activities.add(f"{section.id}{_ACTIVITY_KEY_SEPARATOR}{activity.ref}")
        unknown_activities = set(activity_names) - known_activities
        if unknown_activities:
            raise CourseDraftValidationError(
                "Nie znaleziono aktywności: " + ", ".join(sorted(unknown_activities))
            )

        sections = []
        for section in course.sections:
            activities = tuple(
                replace(
                    activity,
                    name=activity_names.get(
                        f"{section.id}{_ACTIVITY_KEY_SEPARATOR}{activity.ref}", activity.name
                    ),
                )
                for activity in section.activities
            )
            sections.append(
                replace(section, name=section_names.get(section.id, section.name), activities=activities)
            )
        return replace(
            course,
            full_name=changes.get("full_name", course.full_name),
            short_name=changes.get("short_name", course.short_name),
            description=changes.get("description", course.description),
            sections=tuple(sections),
        )

    def preview(self, draft_id: str) -> dict[str, Any]:
        from magic_moodle.application.queries import CourseApplicationService

        draft = self.get(draft_id)
        course = CourseApplicationService(self.courses_root).get_course(draft.course_id)
        if _course_digest(course) != draft.base_digest:
            raise CourseDraftConflictError(
                "Kurs źródłowy zmienił się od utworzenia wersji roboczej. Utwórz nową wersję."
            )
        preview_course = self._apply(course, draft)
        report = validate_course(preview_course)
        return {
            "draft": asdict(draft),
            "course": course_manifest(preview_course),
            "validation": {
                "ok": report.ok,
                "errors": [
                    {"severity": item.severity, "code": item.code, "path": item.path, "message": item.message}
                    for item in report.errors
                ],
                "warnings": [
                    {"severity": item.severity, "code": item.code, "path": item.path, "message": item.message}
                    for item in report.warnings
                ],
            },
            "source_modified": False,
        }

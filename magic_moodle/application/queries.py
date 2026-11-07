"""Read-only course use cases shared by CLI, TUI, desktop and HTTP adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from magic_moodle.course_export import export_course_json
from magic_moodle.loader import CourseLoadError, load_course
from magic_moodle.gift import GiftParseError, QuestionBank
from magic_moodle.models import Course
from magic_moodle.moodle_xml import export_moodle_xml
from magic_moodle.question_bank import load_question_bank
from magic_moodle.validation import ValidationReport, validate_course


class CourseNotFoundError(LookupError):
    """Raised when a course identifier is invalid or unavailable."""


@dataclass(frozen=True)
class CourseSummary:
    """Stable, presentation-neutral summary of a course."""

    id: str
    name: str
    short_name: str
    sections: int | None
    activities: int | None
    load_error: bool = False


class CourseApplicationService:
    """Application boundary for course discovery, retrieval and validation.

    The service owns path resolution and delegates parsing/validation to the
    existing core. It has no dependency on a UI framework or HTTP server.
    """

    def __init__(self, courses_root: str | Path) -> None:
        self.courses_root = Path(courses_root).expanduser().resolve()

    @staticmethod
    def _valid_identifier(course_id: str) -> bool:
        return (
            isinstance(course_id, str)
            and bool(course_id)
            and course_id not in {".", ".."}
            and "/" not in course_id
            and "\\" not in course_id
            and "\x00" not in course_id
        )

    def _course_path(self, course_id: str) -> Path:
        if not self._valid_identifier(course_id):
            raise CourseNotFoundError("Nieprawidłowy identyfikator kursu.")

        candidate = (self.courses_root / course_id).resolve()
        if not candidate.is_relative_to(self.courses_root):
            raise CourseNotFoundError("Nie znaleziono kursu.")
        if not (candidate / "course.yaml").is_file():
            raise CourseNotFoundError("Nie znaleziono kursu.")
        return candidate

    def list_courses(self) -> list[CourseSummary]:
        """List direct child course folders; malformed courses remain visible."""
        if not self.courses_root.is_dir():
            return []

        summaries: list[CourseSummary] = []
        for config in sorted(self.courses_root.glob("*/course.yaml")):
            if not config.resolve().is_relative_to(self.courses_root):
                continue
            course_id = config.parent.name
            try:
                course = load_course(config.parent)
            except (CourseLoadError, OSError, ValueError):
                summaries.append(
                    CourseSummary(
                        id=course_id,
                        name=course_id,
                        short_name="",
                        sections=None,
                        activities=None,
                        load_error=True,
                    )
                )
                continue

            summaries.append(
                CourseSummary(
                    id=course_id,
                    name=course.full_name,
                    short_name=course.short_name,
                    sections=course.section_count,
                    activities=course.activity_count,
                )
            )
        return summaries

    def get_course(self, course_id: str) -> Course:
        """Load a course by opaque directory identifier, never by user path."""
        try:
            return load_course(self._course_path(course_id))
        except CourseLoadError:
            raise
        except (OSError, ValueError) as exc:
            raise CourseLoadError("Nie udało się wczytać kursu.") from exc

    def validate(self, course_id: str) -> tuple[Course, ValidationReport]:
        """Return the course and its canonical core validation report."""
        course = self.get_course(course_id)
        return course, validate_course(course)

    def export_json(self, course_id: str, destination: str | Path) -> Path:
        """Export a course to the documented intermediate JSON manifest format."""
        course = self.get_course(course_id)
        return export_course_json(course, destination)

    def get_question_bank(self, course_id: str) -> QuestionBank:
        """Load and validate the course-level GIFT question bank."""
        bank_path = self._course_path(course_id) / "question-bank"
        if not bank_path.is_dir():
            raise FileNotFoundError("Kurs nie zawiera katalogu question-bank.")
        return load_question_bank(bank_path)

    def export_question_bank_xml(
        self,
        course_id: str,
        destination: str | Path,
        *,
        category: str = "$course$/top",
    ) -> Path:
        """Export the validated course question bank to Moodle XML."""
        bank = self.get_question_bank(course_id)
        return export_moodle_xml(bank, destination, category=category)

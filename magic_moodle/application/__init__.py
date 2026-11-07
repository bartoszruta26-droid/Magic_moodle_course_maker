"""Framework-neutral application services shared by all user interfaces."""

from .queries import (
    CourseApplicationService,
    CourseNotFoundError,
    CourseSummary,
)

__all__ = [
    "CourseApplicationService",
    "CourseNotFoundError",
    "CourseSummary",
]

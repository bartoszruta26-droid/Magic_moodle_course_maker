"""Neutralny model danych kursu, niezależny od konkretnego formatu LMS."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Activity:
    kind: str
    ref: str
    name: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Section:
    id: str
    name: str
    path: Path
    activities: tuple[Activity, ...] = ()


@dataclass(frozen=True)
class Course:
    root: Path
    full_name: str
    short_name: str
    metadata: dict[str, Any]
    sections: tuple[Section, ...] = ()
    description: str = ""

    @property
    def activity_count(self) -> int:
        return sum(len(section.activities) for section in self.sections)

    @property
    def section_count(self) -> int:
        return len(self.sections)

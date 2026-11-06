"""Preflight and publish supported course content to a Moodle site."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from .models import Course
from .moodle_api import MoodleAPIError, MoodleClient


@dataclass(frozen=True)
class PublishPlan:
    course: dict[str, Any]
    activities: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]


def _course_payload(course: Course, category_id: int) -> dict[str, Any]:
    config = course.metadata.get("course", {})
    if not isinstance(config, dict):
        raise MoodleAPIError("course.yaml: pole course musi być mapą.")
    try:
        category_id = int(category_id)
    except (TypeError, ValueError) as exc:
        raise MoodleAPIError("categoryid musi być dodatnim identyfikatorem liczbowym Moodle.") from exc
    if category_id < 1:
        raise MoodleAPIError("categoryid musi być dodatni.")
    visible = config.get("visible", 1)
    payload = {
        "fullname": course.full_name,
        "shortname": course.short_name,
        "categoryid": category_id,
        "summary": _markdown_to_html(course.description),
        "summaryformat": 1,
        "format": config.get("format", "topics"),
        "numsections": max(course.section_count - 1, 0),
        "visible": int(visible),
        "lang": config.get("lang", "pl"),
        "showgrades": int(config.get("show_grades", 1)),
        "newsitems": int(config.get("news_items", 5)),
    }
    idnumber = config.get("idnumber")
    if idnumber:
        payload["idnumber"] = str(idnumber)
    return payload


def _markdown_to_html(source: str) -> str:
    """Convert a safe Markdown subset without adding a third-party dependency."""
    import html
    import re

    def inline(value: str) -> str:
        value = html.escape(value, quote=False)
        value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
        value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
        value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
        return value

    output: list[str] = []
    paragraph: list[str] = []
    in_list = False

    def flush() -> None:
        if paragraph:
            output.append("<p>" + "<br>".join(inline(line) for line in paragraph) + "</p>")
            paragraph.clear()

    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            if in_list:
                output.append("</ul>")
                in_list = False
            continue
        if line.startswith("### "):
            flush()
            output.append("<h3>" + inline(line[4:]) + "</h3>")
        elif line.startswith("## "):
            flush()
            output.append("<h2>" + inline(line[3:]) + "</h2>")
        elif line.startswith("# "):
            flush()
            output.append("<h2>" + inline(line[2:]) + "</h2>")
        elif line.startswith("- ") or line.startswith("* "):
            flush()
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append("<li>" + inline(line[2:]) + "</li>")
        else:
            if in_list:
                output.append("</ul>")
                in_list = False
            paragraph.append(line)
    flush()
    if in_list:
        output.append("</ul>")
    return "\n".join(output)


def build_publish_plan(course: Course, category_id: int) -> PublishPlan:
    payload = _course_payload(course, category_id)
    activities: list[dict[str, Any]] = []
    warnings: list[str] = []
    for section_index, section in enumerate(course.sections):
        for activity in section.activities:
            if activity.kind not in {"page", "label", "url"}:
                warnings.append(
                    f"Sekcja {section_index}, '{activity.name}': typ '{activity.kind}' "
                    "nie jest jeszcze obsługiwany przez wbudowany adapter REST."
                )
                continue
            source = "\n\n".join(activity.content.values())
            item = {
                "sectionnum": section_index,
                "type": activity.kind,
                "name": activity.name,
                "content": _markdown_to_html(source),
            }
            if activity.kind == "url":
                target_url = (
                    activity.resource.get("externalurl")
                    or activity.resource.get("url")
                    or activity.config.get("externalurl")
                    or activity.config.get("url")
                )
                if not isinstance(target_url, str) or not target_url.strip():
                    warnings.append(
                        f"Aktywność URL '{activity.name}' nie zawiera pola externalurl/url."
                    )
                    continue
                normalized_url = target_url.strip()
                try:
                    parsed_url = urlsplit(normalized_url)
                    valid_url = (
                        parsed_url.scheme.lower() in {"http", "https"}
                        and bool(parsed_url.hostname)
                        and not any(character.isspace() for character in normalized_url)
                    )
                    if parsed_url.port is not None:
                        valid_url = valid_url and 1 <= parsed_url.port <= 65535
                except ValueError:
                    valid_url = False
                if not valid_url:
                    warnings.append(
                        f"Aktywność URL '{activity.name}' ma nieprawidłowy adres: "
                        "wymagany jest bezwzględny adres HTTP lub HTTPS."
                    )
                    continue
                item["externalurl"] = normalized_url
            activities.append(item)
    return PublishPlan(payload, tuple(activities), tuple(warnings))


def publish_course(
    client: MoodleClient,
    course: Course,
    category_id: int,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create/reuse a course, then publish page/label modules in section order.

    All activity types are checked before any remote write to avoid partial
    publication caused by an unsupported module type.
    """
    plan = build_publish_plan(course, category_id)
    if plan.warnings:
        raise MoodleAPIError(
            "Publikacja zatrzymana przed zmianami: " + " ".join(plan.warnings)
        )
    if dry_run:
        return {
            "dry_run": True,
            "course": plan.course,
            "activity_count": len(plan.activities),
            "activities": list(plan.activities),
        }

    site = client.site_info()
    functions = {
        item.get("name")
        for item in site.get("functions", [])
        if isinstance(item, dict)
    }
    required = {
        "core_course_get_courses_by_field",
        "core_course_create_courses",
        "local_magicmoodle_update_section",
        "local_magicmoodle_create_activity",
    }
    missing = sorted(required - functions)
    if missing:
        raise MoodleAPIError(
            "Token nie udostępnia wymaganych funkcji: " + ", ".join(missing)
            + ". Sprawdź konfigurację usługi zewnętrznej Moodle."
        )

    remote_course, created = client.ensure_course(plan.course)
    course_id = int(remote_course["id"])
    section_results = []
    for index, section in enumerate(course.sections):
        section_results.append(
            client.update_section(course_id, index, section.name)
        )
    activity_results = []
    for activity in plan.activities:
        activity_results.append(
            client.create_activity(course_id, activity["sectionnum"], activity)
        )
    return {
        "dry_run": False,
        "course": remote_course,
        "course_created": created,
        "sections_updated": len(section_results),
        "activities_created": activity_results,
    }

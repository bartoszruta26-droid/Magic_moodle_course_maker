"""Preflight and publish supported course content to a Moodle site."""
from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from .gift import GiftParseError, parse_gift, validate_question_bank
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
            if activity.kind not in {"page", "label", "url", "book", "quiz", "assignment", "file", "glossary"}:
                warnings.append(
                    f"Sekcja {section_index}, '{activity.name}': typ '{activity.kind}' "
                    "nie jest jeszcze obsługiwany przez wbudowany adapter REST."
                )
                continue
            source_identity = f"{course.short_name}\\0{section.id}\\0{activity.kind}\\0{activity.ref}"
            source_idnumber = "mm-" + hashlib.sha256(source_identity.encode("utf-8")).hexdigest()[:32]
            item = {
                "sectionnum": section_index,
                "type": activity.kind,
                "name": activity.name,
                "idnumber": source_idnumber,
                "content": "" if activity.kind == "file" else _markdown_to_html("\n\n".join(activity.content.values())),
            }
            if activity.kind == "quiz":
                questions_file = activity.resource.get("questions_file", "questions.gift")
                if not isinstance(questions_file, str) or not questions_file.strip():
                    warnings.append(f"Quiz '{activity.name}': questions_file musi wskazywać plik GIFT.")
                    continue
                gift_source = activity.content.get(questions_file)
                if not isinstance(gift_source, str) or not gift_source.strip():
                    warnings.append(f"Quiz '{activity.name}': brak pliku pytań '{questions_file}'.")
                    continue
                if len(gift_source.encode("utf-8")) > 2 * 1024 * 1024:
                    warnings.append(f"Quiz '{activity.name}': plik GIFT przekracza limit 2 MiB.")
                    continue
                try:
                    bank = parse_gift(gift_source, source_name=questions_file)
                    bank_errors = validate_question_bank(bank)
                except GiftParseError as exc:
                    warnings.append(f"Quiz '{activity.name}': błąd GIFT: {exc}")
                    continue
                if bank_errors:
                    warnings.extend(f"Quiz '{activity.name}': {error}" for error in bank_errors)
                    continue
                if not bank.questions or len(bank.questions) > 250:
                    warnings.append(f"Quiz '{activity.name}' musi zawierać od 1 do 250 pytań.")
                    continue
                intro = activity.resource.get("intro", "")
                if not isinstance(intro, str) or len(intro) > 20000:
                    warnings.append(f"Quiz '{activity.name}': intro musi być tekstem do 20 000 znaków.")
                    continue
                timelimit = activity.resource.get("time_limit", 0)
                attempts = activity.resource.get("attempts", 1)
                grade = activity.resource.get("grade", 10)
                completion = activity.resource.get("completion", {})
                passingpercent = activity.resource.get("grade_passing", completion.get("min_score", 0) if isinstance(completion, dict) else 0)
                questionsperpage = activity.resource.get("questions_per_page", 1)
                shuffleanswers = activity.resource.get("shuffle_answers", True)
                if isinstance(timelimit, bool) or not isinstance(timelimit, int) or not 0 <= timelimit <= 86400:
                    warnings.append(f"Quiz '{activity.name}': time_limit musi mieścić się w zakresie 0–86400 sekund.")
                    continue
                if isinstance(attempts, bool) or not isinstance(attempts, int) or not 0 <= attempts <= 10:
                    warnings.append(f"Quiz '{activity.name}': attempts musi być liczbą całkowitą 0–10.")
                    continue
                if isinstance(grade, bool) or not isinstance(grade, (int, float)) or not 0 < grade <= 1000:
                    warnings.append(f"Quiz '{activity.name}': grade musi być większe od 0 i nie większe niż 1000.")
                    continue
                if isinstance(passingpercent, bool) or not isinstance(passingpercent, (int, float)) or not 0 <= passingpercent <= 100:
                    warnings.append(f"Quiz '{activity.name}': grade_passing musi być procentem 0–100.")
                    continue
                if isinstance(questionsperpage, bool) or not isinstance(questionsperpage, int) or not 0 <= questionsperpage <= 50:
                    warnings.append(f"Quiz '{activity.name}': questions_per_page musi być liczbą całkowitą 0–50.")
                    continue
                if not isinstance(shuffleanswers, (bool, int)) or shuffleanswers not in (0, 1, False, True):
                    warnings.append(f"Quiz '{activity.name}': shuffle_answers musi być wartością logiczną.")
                    continue
                completion = activity.resource.get("completion", {})
                if not isinstance(completion, dict):
                    warnings.append(f"Quiz '{activity.name}': completion musi być mapą.")
                    continue
                completionenabled = completion.get("enabled", False)
                completiontype = completion.get("type", "grade")
                if not isinstance(completionenabled, bool):
                    warnings.append(f"Quiz '{activity.name}': completion.enabled musi być wartością logiczną.")
                    continue
                if completiontype not in {"grade", "view"}:
                    warnings.append(f"Quiz '{activity.name}': completion.type musi mieć wartość grade lub view.")
                    continue
                if completionenabled and completiontype == "grade" and passingpercent <= 0:
                    warnings.append(f"Quiz '{activity.name}': ukończenie według oceny wymaga dodatniego grade_passing lub completion.min_score.")
                    continue
                if "grade_passing" in activity.resource and "min_score" in completion:
                    if float(activity.resource["grade_passing"]) != float(completion["min_score"]):
                        warnings.append(f"Quiz '{activity.name}': grade_passing i completion.min_score muszą być zgodne.")
                        continue
                item.update({
                    "intro": _markdown_to_html(intro),
                    "gift": gift_source,
                    "timelimit": timelimit,
                    "attempts": attempts,
                    "grade": float(grade),
                    "passingpercent": float(passingpercent),
                    "shuffleanswers": bool(shuffleanswers),
                    "questionsperpage": questionsperpage,
                    "completionenabled": completionenabled,
                    "completiontype": completiontype,
                    "questioncount": len(bank.questions),
                    "questiontypes": bank.by_type(),
                })
            if activity.kind == "glossary":
                entries = activity.resource.get("entries", [])
                if not isinstance(entries, list) or not entries or len(entries) > 500:
                    warnings.append(f"Słownik '{activity.name}' musi zawierać od 1 do 500 haseł.")
                    continue
                planned_entries = []
                seen_terms = set()
                total_entry_bytes = 0
                entries_invalid = False
                for entry_index, entry in enumerate(entries):
                    if not isinstance(entry, dict):
                        warnings.append(f"Słownik '{activity.name}': entries[{entry_index}] musi być mapą.")
                        entries_invalid = True
                        continue
                    term = entry.get("term")
                    definition = entry.get("definition")
                    entry_format = entry.get("format", "html")
                    if (not isinstance(term, str) or not term.strip() or len(term.strip()) > 255
                            or not isinstance(definition, str) or not definition.strip()):
                        warnings.append(f"Słownik '{activity.name}': hasło {entry_index + 1} wymaga term i definition.")
                        entries_invalid = True
                        continue
                    if entry_format not in {"html", "markdown", "plain"}:
                        warnings.append(f"Słownik '{activity.name}': entries[{entry_index}].format musi być html, markdown lub plain.")
                        entries_invalid = True
                        continue
                    term_key = term.strip().casefold()
                    if term_key in seen_terms:
                        warnings.append(f"Słownik '{activity.name}': powtórzone hasło '{term.strip()}'.")
                        entries_invalid = True
                        continue
                    seen_terms.add(term_key)
                    definition_html = (
                        definition if entry_format == "html"
                        else _markdown_to_html(definition)
                    )
                    total_entry_bytes += len(term.strip().encode("utf-8")) + len(definition_html.encode("utf-8"))
                    if len(definition_html) > 100000 or total_entry_bytes > 5 * 1024 * 1024:
                        warnings.append(f"Słownik '{activity.name}': treść haseł przekracza limit 5 MiB lub 100 000 znaków na definicję.")
                        entries_invalid = True
                        break
                    planned_entries.append({
                        "term": term.strip(),
                        "definition": definition_html,
                    })
                if entries_invalid or len(planned_entries) != len(entries):
                    continue
                intro_source = activity.resource.get("intro", "")
                if not isinstance(intro_source, str) or len(intro_source) > 20000:
                    warnings.append(f"Słownik '{activity.name}': intro musi być tekstem do 20 000 znaków.")
                    continue
                item.update({
                    "intro": _markdown_to_html(intro_source),
                    "entries": planned_entries,
                    "entrycount": len(planned_entries),
                })
            if activity.kind == "file":
                if len(activity.content) != 1:
                    warnings.append(f"Plik '{activity.name}': aktywność musi wskazywać dokładnie jeden plik.")
                    continue
                filename, encoded = next(iter(activity.content.items()))
                if (not isinstance(filename, str) or not filename.strip()
                        or filename in {".", ".."} or "/" in filename or chr(92) in filename
                        or len(filename) > 255):
                    warnings.append(f"Plik '{activity.name}': nieprawidłowa nazwa pliku.")
                    continue
                if not isinstance(encoded, str):
                    warnings.append(f"Plik '{activity.name}': zawartość pliku musi być zakodowana base64.")
                    continue
                try:
                    filebytes = base64.b64decode(encoded, validate=True)
                except (ValueError, base64.binascii.Error):
                    warnings.append(f"Plik '{activity.name}': nieprawidłowe kodowanie base64.")
                    continue
                if not filebytes or len(filebytes) > 5 * 1024 * 1024:
                    warnings.append(f"Plik '{activity.name}': rozmiar musi mieścić się w zakresie 1 B–5 MiB.")
                    continue
                intro_source = activity.resource.get("intro", "")
                if not isinstance(intro_source, str) or len(intro_source) > 20000:
                    warnings.append(f"Plik '{activity.name}': intro musi być tekstem do 20 000 znaków.")
                    continue
                item.update({
                    "filename": filename,
                    "contentbase64": encoded,
                    "intro": _markdown_to_html(intro_source),
                    "filesize": len(filebytes),
                })
            if activity.kind == "assignment":
                intro_source = activity.resource.get("intro", "")
                markdown_file = activity.resource.get("markdown_file")
                if markdown_file:
                    intro_source = activity.content.get(markdown_file, intro_source)
                if not isinstance(intro_source, str) or len(intro_source) > 100000:
                    warnings.append(f"Zadanie '{activity.name}': intro musi być tekstem do 100 000 znaków.")
                    continue
                submissiontype = activity.resource.get("submission_type")
                if submissiontype is None:
                    configured_types = activity.resource.get("submission_types", ["file", "onlinetext"])
                    if (not isinstance(configured_types, list) or not configured_types
                            or any(value not in {"onlinetext", "file"} for value in configured_types)):
                        warnings.append(f"Zadanie '{activity.name}': submission_types musi być niepustą listą wartości file/onlinetext.")
                        continue
                    submissiontype = "both" if set(configured_types) == {"file", "onlinetext"} else configured_types[0]
                if submissiontype not in {"onlinetext", "file", "both"}:
                    warnings.append(f"Zadanie '{activity.name}': submission_type musi mieć wartość onlinetext, file lub both.")
                    continue
                grade = activity.resource.get("grade", activity.resource.get("grademax", 100))
                maxfiles = activity.resource.get("max_files", activity.resource.get("max_attachments", 5))
                maxbytes = activity.resource.get("max_file_size", 10 * 1024 * 1024)
                if isinstance(grade, bool) or not isinstance(grade, (int, float)) or not 0 < grade <= 10000:
                    warnings.append(f"Zadanie '{activity.name}': grade musi być większe od 0 i nie większe niż 10000.")
                    continue
                if isinstance(maxfiles, bool) or not isinstance(maxfiles, int) or not 1 <= maxfiles <= 20:
                    warnings.append(f"Zadanie '{activity.name}': max_files musi mieścić się w zakresie 1–20.")
                    continue
                if isinstance(maxbytes, bool) or not isinstance(maxbytes, int) or not 1 <= maxbytes <= 100 * 1024 * 1024:
                    warnings.append(f"Zadanie '{activity.name}': max_file_size musi mieścić się w zakresie 1 B–100 MiB.")
                    continue
                date_fields = {}
                date_invalid = False
                for source_key, target_key in (
                    ("allowsubmissionsfromdate", "allowsubmissionsfromdate"),
                    ("duedate", "duedate"),
                    ("cutoffdate", "cutoffdate"),
                ):
                    value = activity.resource.get(source_key, 0)
                    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                        warnings.append(f"Zadanie '{activity.name}': {source_key} musi być nieujemnym znacznikiem czasu Unix.")
                        date_invalid = True
                        break
                    date_fields[target_key] = value
                if date_invalid:
                    continue
                start = date_fields["allowsubmissionsfromdate"]
                due = date_fields["duedate"]
                cutoff = date_fields["cutoffdate"]
                if ((start and due and due <= start) or (due and cutoff and cutoff < due)
                        or (start and cutoff and cutoff < start)):
                    warnings.append(f"Zadanie '{activity.name}': daty otwarcia, terminu i zamknięcia są w nieprawidłowej kolejności.")
                    continue
                completion = activity.resource.get("completion", {})
                if not isinstance(completion, dict):
                    warnings.append(f"Zadanie '{activity.name}': completion musi być mapą.")
                    continue
                completionenabled = completion.get("enabled", False)
                if not isinstance(completionenabled, bool):
                    warnings.append(f"Zadanie '{activity.name}': completion.enabled musi być wartością logiczną.")
                    continue
                submissiondrafts = activity.resource.get("submission_drafts", False)
                requiresstatement = activity.resource.get("require_submission_statement", False)
                if not isinstance(submissiondrafts, bool) or not isinstance(requiresstatement, bool):
                    warnings.append(f"Zadanie '{activity.name}': submission_drafts i require_submission_statement muszą być wartościami logicznymi.")
                    continue
                item.update({
                    "intro": _markdown_to_html(intro_source),
                    "submissiontype": submissiontype,
                    "grade": float(grade),
                    "maxfiles": maxfiles,
                    "maxbytes": maxbytes,
                    "submissiondrafts": submissiondrafts,
                    "requiresubmissionstatement": requiresstatement,
                    "completionenabled": completionenabled,
                    **date_fields,
                })
            if activity.kind == "book":
                chapters = activity.resource.get("chapters", [])
                if not isinstance(chapters, list) or not chapters or len(chapters) > 200:
                    warnings.append(f"Książka '{activity.name}' musi zawierać od 1 do 200 rozdziałów.")
                    continue
                planned_chapters = []
                total_chapter_bytes = 0
                for chapter_index, chapter in enumerate(chapters):
                    if not isinstance(chapter, dict):
                        warnings.append(f"Książka '{activity.name}': chapters[{chapter_index}] musi być mapą.")
                        continue
                    title = chapter.get("title")
                    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 255:
                        warnings.append(f"Książka '{activity.name}': rozdział {chapter_index + 1} ma nieprawidłowy tytuł.")
                        continue
                    content_file = chapter.get("content_file")
                    if content_file:
                        chapter_source = activity.content.get(content_file)
                        if chapter_source is None:
                            warnings.append(f"Książka '{activity.name}': brak pliku rozdziału '{content_file}'.")
                            continue
                    else:
                        chapter_source = chapter.get("content", "")
                    if not isinstance(chapter_source, str):
                        warnings.append(f"Książka '{activity.name}': treść rozdziału '{title}' musi być tekstem.")
                        continue
                    subchapter_value = chapter.get("subchapter", False)
                    if not isinstance(subchapter_value, bool):
                        warnings.append(
                            f"Książka '{activity.name}': chapters[{chapter_index}].subchapter musi być wartością logiczną."
                        )
                        continue
                    subchapter = subchapter_value
                    total_chapter_bytes += len(_markdown_to_html(chapter_source).encode("utf-8"))
                    if total_chapter_bytes > 5 * 1024 * 1024:
                        warnings.append(
                            f"Książka '{activity.name}': łączny rozmiar treści rozdziałów przekracza limit 5 MiB."
                        )
                        break
                    if chapter_index == 0 and subchapter:
                        warnings.append(f"Książka '{activity.name}': pierwszy rozdział nie może być podrozdziałem.")
                        continue
                    planned_chapters.append({
                        "title": title.strip(),
                        "content": _markdown_to_html(chapter_source),
                        "subchapter": subchapter,
                    })
                numbering = activity.resource.get("numbering", 1)
                if isinstance(numbering, bool) or not isinstance(numbering, int) or numbering not in {0, 1, 2, 3}:
                    warnings.append(f"Książka '{activity.name}': numbering musi mieć wartość 0, 1, 2 lub 3.")
                    continue
                if len(planned_chapters) != len(chapters):
                    continue
                item["chapters"] = planned_chapters
                item["numbering"] = numbering
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
    }
    for activity in plan.activities:
        if activity["type"] in {"page", "label", "url"}:
            required.add("local_magicmoodle_create_activity")
        elif activity["type"] == "book":
            required.add("local_magicmoodle_create_book")
        elif activity["type"] == "quiz":
            required.add("local_magicmoodle_create_quiz")
        elif activity["type"] == "assignment":
            required.add("local_magicmoodle_create_assignment")
        elif activity["type"] == "file":
            required.add("local_magicmoodle_create_resource")
        elif activity["type"] == "glossary":
            required.add("local_magicmoodle_create_glossary")
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
        if activity["type"] == "book":
            result = client.create_book(course_id, activity["sectionnum"], activity)
        elif activity["type"] == "quiz":
            result = client.create_quiz(course_id, activity["sectionnum"], activity)
        elif activity["type"] == "assignment":
            result = client.create_assignment(course_id, activity["sectionnum"], activity)
        elif activity["type"] == "file":
            result = client.create_resource(course_id, activity["sectionnum"], activity)
        elif activity["type"] == "glossary":
            result = client.create_glossary(course_id, activity["sectionnum"], activity)
        else:
            result = client.create_activity(course_id, activity["sectionnum"], activity)
        activity_results.append(result)
    return {
        "dry_run": False,
        "course": remote_course,
        "course_created": created,
        "sections_updated": len(section_results),
        "activities_created": activity_results,
    }

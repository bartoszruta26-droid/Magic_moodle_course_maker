"""Parser GIFT do neutralnego modelu pytań."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


class GiftParseError(ValueError):
    """Błąd składni GIFT z numerem linii."""


@dataclass(frozen=True)
class Answer:
    text: str
    fraction: float
    feedback: str = ""


@dataclass(frozen=True)
class MatchPair:
    question: str
    answer: str


@dataclass(frozen=True)
class Question:
    name: str
    qtype: str
    text: str
    answers: tuple[Answer, ...] = ()
    pairs: tuple[MatchPair, ...] = ()
    general_feedback: str = ""
    tolerance: float | None = None
    source_line: int = 1
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class QuestionBank:
    questions: tuple[Question, ...]
    source: str = "<memory>"

    def by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for question in self.questions:
            counts[question.qtype] = counts.get(question.qtype, 0) + 1
        return dict(sorted(counts.items()))


_HEADER = re.compile(r"(?m)^\s*::([^\n]*?)::")
_WEIGHT = re.compile(r"^%([+-]?(?:\d+(?:\.\d*)?|\.\d+))%(.*)$", re.S)


def _strip_comments(source: str) -> str:
    # Komentarze // są ignorowane tylko poza blokami pytań, jak w GIFT.
    return source


def _extract_questions(source: str) -> list[tuple[str, str, int, str]]:
    """Wydziela pytania po nagłówkach ::name::, respektując klamry i ucieczki."""
    matches = list(_HEADER.finditer(source))
    if not matches:
        if not source.strip():
            return []
        raise GiftParseError("Brak nagłówków pytań ::nazwa::; parser wymaga nazwanych pytań.")
    result: list[tuple[str, str, int, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end_limit = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        fragment = source[start:end_limit]
        opening = None
        escaped = False
        depth = 0
        closing = None
        for pos, char in enumerate(fragment):
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == "{":
                if depth == 0:
                    opening = pos
                depth += 1
            elif char == "}" and depth:
                depth -= 1
                if depth == 0:
                    closing = pos
                    break
        if opening is None or closing is None:
            line = source.count("\n", 0, match.start()) + 1
            raise GiftParseError(f"Linia {line}: pytanie '{match.group(1)}' nie ma zamkniętego bloku odpowiedzi.")
        prefix = fragment[:opening].strip()
        body = fragment[opening + 1:closing].strip()
        suffix = fragment[closing + 1:].strip()
        if suffix and not suffix.startswith("//"):
            # GIFT missingword/cloze: odpowiedzi są osadzone w treści pytania.
            prefix = fragment.strip()
            body = "__CLOZE__"
        line = source.count("\n", 0, match.start()) + 1
        result.append((match.group(1).strip(), prefix, line, body))
    return result


def _split_feedback(value: str) -> tuple[str, str]:
    if "#" not in value:
        return value.strip(), ""
    text, feedback = value.split("#", 1)
    return text.strip(), feedback.strip()


def _parse_answers(body: str) -> tuple[Answer, ...]:
    markers = list(re.finditer(r"(?<!\\)([=~])", body))
    answers: list[Answer] = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(body)
        raw = body[marker.end():end].strip()
        fraction = 100.0 if marker.group(1) == "=" else 0.0
        weighted = _WEIGHT.match(raw)
        if weighted:
            fraction = float(weighted.group(1))
            raw = weighted.group(2).strip()
        else:
            # Zgodność z historycznymi plikami MED.10: ~0.5#treść oznacza
            # odpowiedź z wagą 0.5 (czyli 50%) i treścią po znaku #.
            legacy_weight = re.match(
                r"^([+-]?(?:\d+(?:\.\d*)?|\.\d+))#\s*(.+)$", raw, re.S
            )
            if marker.group(1) == "~" and legacy_weight:
                fraction = float(legacy_weight.group(1))
                if -1.0 <= fraction <= 1.0:
                    fraction *= 100.0
                raw = legacy_weight.group(2).strip()
        text, feedback = _split_feedback(raw)
        if text:
            answers.append(Answer(text=text, fraction=fraction, feedback=feedback))
    return tuple(answers)


def _parse_one(name: str, text: str, body: str, line: int) -> Question:
    if body.strip() == "__CLOZE__":
        return Question(name, "multianswer", text, source_line=line)
    if re.search(r"\{[a-zA-Z][a-zA-Z0-9_]*\}", body) and body.strip().startswith("="):
        raise GiftParseError(
            f"Linia {line}: pytanie obliczeniowe z zestawem danych nie jest jeszcze obsługiwane."
        )
    normalized = body.strip()
    upper = normalized.upper()
    if upper.startswith("TRUE") or upper.startswith("FALSE"):
        correct = upper.startswith("TRUE")
        feedback = normalized[4 if correct else 5:].lstrip("#").strip()
        return Question(name, "truefalse", text, (
            Answer("true", 100.0 if correct else 0.0),
            Answer("false", 0.0 if correct else 100.0),
        ), general_feedback=feedback, source_line=line)

    if upper.startswith("#MANUAL") or upper.startswith("#ESSAY"):
        return Question(name, "essay", text, source_line=line)

    if upper.startswith("#"):
        match = re.match(r"#\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))(?:\s*:\s*([\d.]+))?", normalized)
        if not match:
            raise GiftParseError(f"Linia {line}: niepoprawna odpowiedź numeryczna.")
        value = float(match.group(1))
        tolerance = float(match.group(2)) if match.group(2) else 0.0
        return Question(name, "numerical", text, (
            Answer(str(value), 100.0),
        ), tolerance=tolerance, source_line=line)

    numeric = re.match(
        r"^=\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))(?:\s*:\s*([\d.]+)|\s*\.\.\s*([+-]?[\d.]+))?\s*$",
        normalized,
    )
    if numeric:
        value = float(numeric.group(1))
        tolerance = float(numeric.group(2)) if numeric.group(2) else (
            abs(float(numeric.group(3)) - value) if numeric.group(3) else 0.0
        )
        return Question(name, "numerical", text, (
            Answer(str(value), 100.0),
        ), tolerance=tolerance, source_line=line)

    lines = [item.strip() for item in normalized.splitlines() if item.strip()]
    if any(item.startswith("-=") for item in lines):
        left = [item[1:].strip() for item in lines if item.startswith("=") and not item.startswith("==")]
        right = [item[2:].strip() for item in lines if item.startswith("-=")]
        if len(left) < 2 or len(left) != len(right):
            raise GiftParseError(
                f"Linia {line}: niestandardowy zestaw dopasowań wymaga równej liczby elementów po obu stronach."
            )
        return Question(
            name, "matching", text,
            pairs=tuple(MatchPair(a, b) for a, b in zip(left, right)),
            source_line=line,
        )

    short = re.match(r"(?i)^(SHORTANSWER|SA|SHORTANSWER_C|SAC)\s*:\s*(.*)$", normalized, re.S)
    if short:
        raw_answers = short.group(2).strip()
        if "|" in raw_answers:
            # Repozytorium zawiera listę odpowiedzi rozdzielonych pionową kreską.
            values = [part.strip().lstrip("~=# ").strip() for part in raw_answers.split("|")]
            answers = tuple(Answer(value, 100.0) for value in values if value)
        else:
            answers = _parse_answers(raw_answers)
            if not answers and raw_answers.startswith("#"):
                value = raw_answers[1:].strip()
                answers = (Answer(value, 100.0),) if value else ()
        return Question(name, "shortanswer", text, answers, source_line=line)

    if normalized in {"", "}"}:
        return Question(name, "description", text, source_line=line)

    answers = _parse_answers(normalized)
    if not answers:
        raise GiftParseError(f"Linia {line}: nie rozpoznano typu pytania ani odpowiedzi.")
    if any("->" in answer.text for answer in answers):
        pairs = []
        for answer in answers:
            if "->" not in answer.text:
                continue
            left, right = answer.text.split("->", 1)
            pairs.append(MatchPair(left.strip(), right.strip()))
        if len(pairs) < 2:
            raise GiftParseError(f"Linia {line}: pytanie dopasowujące wymaga co najmniej dwóch par.")
        return Question(name, "matching", text, pairs=tuple(pairs), source_line=line)
    if answers and all(answer.fraction == 100.0 for answer in answers):
        return Question(name, "shortanswer", text, answers, source_line=line)
    return Question(name, "multichoice", text, answers, source_line=line)


def parse_gift(source: str, *, source_name: str = "<memory>") -> QuestionBank:
    """Parsuje GIFT: multichoice, true/false, shortanswer, numerical, matching, essay, description."""
    questions = []
    for name, text, line, body in _extract_questions(_strip_comments(source)):
        questions.append(_parse_one(name or f"question-{len(questions) + 1}", text, body, line))
    return QuestionBank(tuple(questions), source_name)


def validate_question_bank(bank: QuestionBank) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for question in bank.questions:
        prefix = f"{bank.source}:{question.source_line} [{question.name}]"
        if not question.name:
            errors.append(f"{prefix}: brak nazwy pytania.")
        if question.name in seen:
            errors.append(f"{prefix}: powtórzona nazwa pytania.")
        seen.add(question.name)
        if not question.text.strip():
            errors.append(f"{prefix}: brak treści pytania.")
        if question.qtype in {"multichoice", "truefalse"}:
            if len(question.answers) < 2:
                errors.append(f"{prefix}: wymagane są co najmniej dwie odpowiedzi.")
            if not any(answer.fraction > 0 for answer in question.answers):
                errors.append(f"{prefix}: brak poprawnej odpowiedzi.")
            if question.qtype == "multichoice" and sum(
                answer.fraction for answer in question.answers if answer.fraction > 0
            ) <= 0:
                errors.append(f"{prefix}: suma punktacji poprawnych odpowiedzi musi być dodatnia.")
            if any(answer.fraction > 100 or answer.fraction < -100 for answer in question.answers):
                errors.append(f"{prefix}: udział punktowy odpowiedzi musi mieścić się w przedziale -100..100.")
        elif question.qtype == "shortanswer":
            if not question.answers or not any(a.fraction > 0 for a in question.answers):
                errors.append(f"{prefix}: krótka odpowiedź wymaga co najmniej jednej odpowiedzi poprawnej.")
        elif question.qtype == "matching":
            if len(question.pairs) < 2 or any(not p.question or not p.answer for p in question.pairs):
                errors.append(f"{prefix}: dopasowanie wymaga co najmniej dwóch kompletnych par.")
        elif question.qtype == "numerical":
            if not question.answers:
                errors.append(f"{prefix}: brak wartości numerycznej.")
            if question.tolerance is not None and question.tolerance < 0:
                errors.append(f"{prefix}: tolerancja nie może być ujemna.")
    return errors

"""Eksport neutralnego banku pytań do formatu Moodle XML."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .gift import Question, QuestionBank


def _element(parent: ET.Element, name: str, text: str | None = None, **attrs: str) -> ET.Element:
    node = ET.SubElement(parent, name, attrs)
    if text is not None:
        node.text = text
    return node


def _text_field(parent: ET.Element, name: str, value: str, fmt: str = "html") -> ET.Element:
    field = _element(parent, name, format=fmt)
    _element(field, "text", value)
    return field


def _answer(parent: ET.Element, text: str, fraction: float, feedback: str = "", tolerance: float | None = None) -> None:
    node = _element(parent, "answer", fraction=f"{fraction:g}", format="html")
    _element(node, "text", text)
    if feedback:
        _text_field(node, "feedback", feedback)


def _append_question(root: ET.Element, question: Question) -> None:
    node = _element(root, "question", type=question.qtype)
    _element(node, "name").append(ET.Element("text"))
    node.find("./name/text").text = question.name
    _text_field(node, "questiontext", question.text)
    _text_field(node, "generalfeedback", question.general_feedback)
    _element(node, "defaultgrade", "1.0000000")
    _element(node, "penalty", "0.3333333")
    _element(node, "hidden", "0")

    if question.qtype == "multichoice":
        correct_count = sum(1 for answer in question.answers if answer.fraction > 0)
        _element(node, "single", "true" if correct_count == 1 else "false")
        _element(node, "shuffleanswers", "true")
        _element(node, "answernumbering", "abc")
        _text_field(node, "correctfeedback", "")
        _text_field(node, "partiallycorrectfeedback", "")
        _text_field(node, "incorrectfeedback", "")
        for answer in question.answers:
            _answer(node, answer.text, answer.fraction, answer.feedback)
    elif question.qtype == "truefalse":
        for answer in question.answers:
            _answer(node, answer.text, answer.fraction, answer.feedback)
    elif question.qtype == "shortanswer":
        _element(node, "usecase", "0")
        for answer in question.answers:
            _answer(node, answer.text, answer.fraction, answer.feedback)
    elif question.qtype == "numerical":
        for answer in question.answers:
            _answer(node, answer.text, answer.fraction, answer.feedback)
        tolerance = question.tolerance or 0.0
        _element(node, "tolerance", f"{tolerance:g}")
    elif question.qtype == "matching":
        _element(node, "shuffleanswers", "true")
        for pair in question.pairs:
            sub = _element(node, "subquestion", format="html")
            _element(sub, "text", pair.question)
            answer = _element(sub, "answer")
            _element(answer, "text", pair.answer)
    elif question.qtype == "essay":
        _element(node, "responseformat", "editor")
        _element(node, "responserequired", "1")
        _element(node, "responsefieldlines", "15")
        _element(node, "attachments", "0")
        _element(node, "attachmentsrequired", "0")
        _element(node, "graderinfo", format="html").append(ET.Element("text"))
        _element(node, "responsetemplate", format="html").append(ET.Element("text"))
    elif question.qtype == "description":
        pass
    else:
        raise ValueError(f"Nieobsługiwany typ pytania Moodle XML: {question.qtype}")


def to_moodle_xml(bank: QuestionBank, *, category: str = "$course$/top") -> str:
    """Zwraca poprawnie zbudowany dokument Moodle XML dla obsługiwanych typów."""
    root = ET.Element("quiz")
    category_node = _element(root, "question", type="category")
    category_name = _element(category_node, "category")
    _element(category_name, "text", category)
    for question in bank.questions:
        _append_question(root, question)
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        root, encoding="unicode", short_empty_elements=True
    ) + "\n"


def export_moodle_xml(
    bank: QuestionBank, destination: str | Path, *, category: str = "$course$/top"
) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_moodle_xml(bank, category=category), encoding="utf-8")
    return path

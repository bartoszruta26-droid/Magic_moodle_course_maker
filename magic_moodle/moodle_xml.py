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


def _answer(
    parent: ET.Element, text: str, fraction: float, feedback: str = "",
    tolerance: float | None = None,
) -> None:
    node = _element(parent, "answer", fraction=f"{fraction:g}", format="html")
    _element(node, "text", text)
    if feedback:
        _text_field(node, "feedback", feedback)
    if tolerance is not None:
        _element(node, "tolerance", f"{tolerance:g}")
    elif question.qtype == "numerical":
        for answer in question.answers:
            _answer(node, answer.text, answer.fraction, answer.feedback, question.tolerance or 0.0)


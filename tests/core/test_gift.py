from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from magic_moodle.gift import GiftParseError, parse_gift, validate_question_bank
from magic_moodle.moodle_xml import to_moodle_xml


def test_parses_multiple_choice_single_and_multi_select() -> None:
    bank = parse_gift(
        """::single:: Wybierz jedną odpowiedź. {
=Poprawna
~Błędna
~%0%Także błędna
}
::multi:: Wybierz dwie odpowiedzi. {
~%50%Pierwsza
~%50%Druga
~%-50%Trzecia
}"""
    )
    assert bank.by_type() == {"multichoice": 2}
    assert [a.fraction for a in bank.questions[1].answers] == [50, 50, -50]
    assert validate_question_bank(bank) == []


def test_parses_true_false_and_feedback() -> None:
    bank = parse_gift("::tf:: Zdanie jest prawdziwe. {TRUE#Dobra odpowiedź.}")
    question = bank.questions[0]
    assert question.qtype == "truefalse"
    assert question.answers[0].fraction == 100
    assert question.general_feedback == "Dobra odpowiedź."


def test_parses_shortanswer_and_repository_pipe_syntax() -> None:
    bank = parse_gift(
        """::standard:: Kto? {=Jan =Jan Paweł II}
::repo:: Wymień pojęcia. {SHORTANSWER:~#ergonomia | higiena pracy | bezpieczeństwo}"""
    )
    assert bank.questions[0].qtype == "shortanswer"
    assert [a.text for a in bank.questions[0].answers] == ["Jan", "Jan Paweł II"]
    assert [a.text for a in bank.questions[1].answers] == [
        "ergonomia", "higiena pracy", "bezpieczeństwo"
    ]
    assert validate_question_bank(bank) == []


def test_parses_numerical_question_with_tolerance() -> None:
    question = parse_gift("::number:: Ile? {#12.5:0.25}").questions[0]
    assert question.qtype == "numerical"
    assert question.answers[0].text == "12.5"
    assert question.tolerance == 0.25


def test_parses_matching_question() -> None:
    question = parse_gift(
        """::pairs:: Połącz pojęcia. {
=Serce -> Narząd
=Płuco -> Narząd
=Wątroba -> Narząd
}"""
    ).questions[0]
    assert question.qtype == "matching"
    assert len(question.pairs) == 3


def test_parses_essay_and_description() -> None:
    bank = parse_gift(
        """::essay:: Omów zagadnienie. {#MANUAL}
::info:: Przeczytaj tekst przed kolejnym pytaniem. {}"""
    )
    assert [q.qtype for q in bank.questions] == ["essay", "description"]


def test_reports_malformed_question_without_closing_brace() -> None:
    with pytest.raises(GiftParseError, match="nie ma zamkniętego bloku"):
        parse_gift("::broken:: Pytanie {=odpowiedź")


def test_validates_duplicate_names_and_missing_correct_answer() -> None:
    bank = parse_gift(
        """::same:: Pytanie A. {~Błędna ~Także błędna}
::same:: Pytanie B. {=Poprawna ~Błędna}"""
    )
    errors = validate_question_bank(bank)
    assert any("brak poprawnej odpowiedzi" in error for error in errors)
    assert any("powtórzona nazwa" in error for error in errors)


def test_exports_moodle_xml_for_supported_question_types() -> None:
    bank = parse_gift(
        """::mc:: Wybierz. {=Tak ~Nie}
::tf:: Prawda? {TRUE}
::sa:: Odpowiedz. {=Jan}
::num:: Wynik. {#2:0.1}
::match:: Dopasuj. {
=A -> 1
=B -> 2
}
::essay:: Opisz. {#MANUAL}
::desc:: Informacja. {}"""
    )
    xml = to_moodle_xml(bank, category="$course$/MED.10")
    root = ET.fromstring(xml)
    questions = root.findall("question")
    assert len(questions) == 8  # kategoria + siedem pytań
    assert [node.attrib["type"] for node in questions[1:]] == [
        "multichoice", "truefalse", "shortanswer", "numerical",
        "matching", "essay", "description"
    ]
    numerical_answer = questions[4].find("answer")
    assert numerical_answer is not None
    assert numerical_answer.findtext("tolerance") == "0.1"


def test_xml_escapes_question_text_and_answer_content() -> None:
    bank = parse_gift("::html:: Czy 2 < 3? {=Tak & oczywiście ~Nie}")
    root = ET.fromstring(to_moodle_xml(bank))
    assert "2 < 3" in root.findtext(".//questiontext/text")
    assert "Tak & oczywiście" in root.findtext(".//answer/text")


def test_loads_real_med10_question_bank() -> None:
    from pathlib import Path

    from magic_moodle.question_bank import load_question_bank

    repository = Path(__file__).resolve().parents[2]
    bank = load_question_bank(repository / "courses" / "03-kurs-masazysta-med10" / "question-bank")
    assert len(bank.questions) > 20
    assert {"essay", "matching", "multichoice", "shortanswer", "truefalse"} <= set(bank.by_type())

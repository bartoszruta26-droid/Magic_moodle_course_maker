"""Ładowanie banków pytań GIFT z katalogu kursu."""
from __future__ import annotations

from pathlib import Path

from .gift import GiftParseError, QuestionBank, parse_gift, validate_question_bank


def load_question_bank(source: str | Path) -> QuestionBank:
    """Wczytuje plik GIFT albo łączy wszystkie pliki .gift z katalogu."""
    path = Path(source).resolve()
    files = [path] if path.is_file() else sorted(path.rglob("*.gift"))
    if not files:
        raise FileNotFoundError(f"Nie znaleziono plików GIFT w: {path}")
    questions = []
    for file in files:
        try:
            parsed = parse_gift(file.read_text(encoding="utf-8-sig"), source_name=str(file))
        except (OSError, UnicodeError, GiftParseError) as exc:
            raise GiftParseError(f"{file}: {exc}") from exc
        questions.extend(parsed.questions)
    bank = QuestionBank(tuple(questions), source=str(path))
    errors = validate_question_bank(bank)
    if errors:
        raise GiftParseError("\n".join(errors))
    return bank


def validate_question_bank_path(source: str | Path) -> tuple[QuestionBank, list[str]]:
    """Wczytuje bank i zwraca wszystkie błędy walidacji bez eksportu."""
    path = Path(source).resolve()
    files = [path] if path.is_file() else sorted(path.rglob("*.gift"))
    if not files:
        raise FileNotFoundError(f"Nie znaleziono plików GIFT w: {path}")
    questions = []
    for file in files:
        parsed = parse_gift(file.read_text(encoding="utf-8-sig"), source_name=str(file))
        questions.extend(parsed.questions)
    bank = QuestionBank(tuple(questions), source=str(path))
    return bank, validate_question_bank(bank)

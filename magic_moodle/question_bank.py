"""Ładowanie banków pytań GIFT z katalogu kursu."""
from __future__ import annotations

from pathlib import Path

from .gift import GiftParseError, QuestionBank, parse_gift, validate_question_bank

MAX_GIFT_FILE_BYTES = 5 * 1024 * 1024
MAX_BANK_BYTES = 25 * 1024 * 1024
MAX_GIFT_FILES = 500


def _collect_gift_files(path: Path) -> list[Path]:
    if path.is_file():
        files = [path]
        base = path.parent.resolve()
    elif path.is_dir():
        base = path.resolve()
        files = sorted(item for item in path.rglob("*.gift") if item.is_file())
    else:
        files = []
        base = path.resolve()
    if not files:
        raise FileNotFoundError(f"Nie znaleziono plików GIFT w: {path}")
    if len(files) > MAX_GIFT_FILES:
        raise GiftParseError(f"Bank zawiera więcej niż {MAX_GIFT_FILES} plików GIFT.")
    total = 0
    for file in files:
        resolved = file.resolve()
        if not resolved.is_relative_to(base):
            raise GiftParseError(f"{file}: dowiązanie symboliczne wychodzi poza katalog banku.")
        try:
            size = resolved.stat().st_size
        except OSError as exc:
            raise GiftParseError(f"{file}: nie można odczytać metadanych pliku: {exc}") from exc
        if size > MAX_GIFT_FILE_BYTES:
            raise GiftParseError(f"{file}: plik GIFT przekracza limit 5 MiB.")
        total += size
        if total > MAX_BANK_BYTES:
            raise GiftParseError("Łączny rozmiar banku GIFT przekracza limit 25 MiB.")
    return files


def _read_bank(path: Path) -> QuestionBank:
    files = _collect_gift_files(path)
    questions = []
    for file in files:
        try:
            parsed = parse_gift(file.read_text(encoding="utf-8-sig"), source_name=str(file))
        except (OSError, UnicodeError, GiftParseError) as exc:
            raise GiftParseError(f"{file}: {exc}") from exc
        questions.extend(parsed.questions)
    return QuestionBank(tuple(questions), source=str(path))


def load_question_bank(source: str | Path) -> QuestionBank:
    """Wczytuje plik GIFT albo łączy wszystkie pliki .gift z katalogu."""
    path = Path(source).resolve()
    bank = _read_bank(path)
    errors = validate_question_bank(bank)
    if errors:
        raise GiftParseError("\n".join(errors))
    return bank


def validate_question_bank_path(source: str | Path) -> tuple[QuestionBank, list[str]]:
    """Wczytuje bank i zwraca wszystkie błędy walidacji bez eksportu."""
    bank = _read_bank(Path(source).resolve())
    return bank, validate_question_bank(bank)

"""Atomic UTF-8 text writes for generated course artifacts."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(destination: str | Path, content: str) -> Path:
    """Write beside the destination and atomically replace it after fsync."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        return path
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

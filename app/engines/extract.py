from __future__ import annotations

from pathlib import Path
from typing import Any

from ..utils import Progress

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".json",
    ".jsonl",
    ".xml",
    ".yaml",
    ".yml",
    ".html",
    ".htm",
    ".log",
    ".rtf",
}


def read_text_safely(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def extract_markdown(path: Path, progress: Progress) -> tuple[str, dict[str, Any]]:
    progress(0.12, "Lettura locale con Microsoft MarkItDown")
    if path.suffix.lower() in TEXT_EXTENSIONS:
        text = read_text_safely(path)
        return text, {"engine": "lettura diretta", "characters": len(text)}

    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise RuntimeError(
            "Microsoft MarkItDown non è installato. Esegui scripts/install.sh."
        ) from exc

    converter = MarkItDown(enable_plugins=False)
    try:
        if hasattr(converter, "convert_local"):
            result = converter.convert_local(str(path))
        else:
            result = converter.convert(str(path))
    except Exception as exc:
        raise RuntimeError(f"MarkItDown non ha potuto leggere il file: {exc}") from exc

    text = getattr(result, "markdown", None) or getattr(result, "text_content", None)
    if not isinstance(text, str):
        raise RuntimeError("MarkItDown non ha restituito contenuto testuale.")
    progress(0.82, "Documento convertito in Markdown")
    return text, {
        "engine": "Microsoft MarkItDown",
        "characters": len(text),
        "source_extension": path.suffix.lower(),
    }

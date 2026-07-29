from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import unicodedata
import zipfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import PATHS

Progress = Callable[[float, str], None]


def safe_name(name: str, fallback: str = "documento") -> str:
    name = Path(name).name
    normalized = unicodedata.normalize("NFKC", name)
    normalized = re.sub(r"[\x00-\x1f\x7f/\\]+", "_", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip(" .")
    return normalized[:180] or fallback


def slug_stem(name: str) -> str:
    stem = Path(name).stem
    stem = unicodedata.normalize("NFKD", stem)
    stem = "".join(ch for ch in stem if not unicodedata.combining(ch))
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", stem).strip("-._")
    return stem[:100] or "documento"


def job_output_dir(job: dict[str, Any]) -> Path:
    day = datetime.now().strftime("%Y-%m-%d")
    folder = PATHS.outputs / day / f"{slug_stem(job['input_name'])}-{job['id'][:8]}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def make_bundle(folder: Path, *, name: str = "risultati.zip") -> Path:
    bundle = folder.parent / f"{folder.name}-{name}"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(folder))
    return bundle


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def file_kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {
        ".wav",
        ".mp3",
        ".m4a",
        ".flac",
        ".ogg",
        ".aac",
        ".opus",
        ".mp4",
        ".mov",
        ".mkv",
        ".webm",
    }:
        return "audio"
    if ext in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}:
        return "image"
    if ext == ".pdf":
        return "pdf"
    return "document"


def content_type(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def run_checked(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        timeout=timeout,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout or "errore sconosciuto").strip()
        raise RuntimeError(detail[-3000:])
    return result


def remove_tree(path: Path) -> None:
    if path.is_dir() and PATHS.work in path.parents:
        shutil.rmtree(path, ignore_errors=True)

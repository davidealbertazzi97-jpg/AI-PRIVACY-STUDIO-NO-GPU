from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from ..config import PATHS
from ..utils import Progress, run_checked


def _duration(path: Path) -> float:
    result = run_checked(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        timeout=60,
    )
    try:
        return max(0.0, float(result.stdout.strip()))
    except ValueError:
        return 0.0


def _split_audio(
    path: Path,
    target: Path,
    progress: Progress,
    *,
    chunk_seconds: int,
) -> tuple[list[Path], float]:
    target.mkdir(parents=True, exist_ok=True)
    duration = _duration(path)
    progress(0.03, "Normalizzazione audio con FFmpeg")
    pattern = target / "blocco-%05d.wav"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-reset_timestamps",
        "1",
        str(pattern),
    ]
    run_checked(command, timeout=None)
    chunks = sorted(target.glob("blocco-*.wav"))
    if not chunks:
        raise RuntimeError("FFmpeg non ha trovato una traccia audio utilizzabile.")
    return chunks, duration


def transcribe_parakeet(
    path: Path,
    work_dir: Path,
    progress: Progress,
    *,
    chunk_minutes: int = 10,
) -> tuple[str, dict[str, Any]]:
    if not PATHS.ai_python.is_file():
        raise RuntimeError(
            "Parakeet v3 non è installato. Esegui scripts/install-ai.sh."
        )
    chunks, duration = _split_audio(
        path,
        work_dir / "audio-chunks",
        progress,
        chunk_seconds=max(120, min(chunk_minutes, 20) * 60),
    )
    manifest = work_dir / "transcription-result.json"
    worker_progress = work_dir / "transcription-progress.json"
    command = [
        str(PATHS.ai_python),
        str(PATHS.app / "workers" / "ai_worker.py"),
        "transcribe",
        "--input-dir",
        str(chunks[0].parent),
        "--output",
        str(manifest),
        "--progress",
        str(worker_progress),
    ]
    log_path = work_dir / "parakeet-worker.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=log,
            text=True,
        )
        while process.poll() is None:
            if worker_progress.is_file():
                try:
                    state = json.loads(worker_progress.read_text(encoding="utf-8"))
                    progress(
                        0.1 + float(state.get("progress", 0)) * 0.82,
                        str(state.get("stage", "Trascrizione Parakeet v3")),
                    )
                except (OSError, ValueError):
                    pass
            time.sleep(0.5)
    stderr = log_path.read_text(encoding="utf-8", errors="replace").strip()
    if process.returncode:
        raise RuntimeError(
            "Parakeet v3 non ha completato la trascrizione. "
            + (stderr[-3000:] or "Errore del motore locale.")
        )
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    text = str(payload.get("text", ""))
    payload["duration_seconds"] = duration
    payload["chunks"] = len(chunks)
    progress(0.94, "Trascrizione completata")
    return text, payload


def seconds_to_srt(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def make_srt(segments: list[dict[str, Any]]) -> str:
    entries: list[str] = []
    for index, segment in enumerate(segments, start=1):
        entries.append(
            "\n".join(
                [
                    str(index),
                    f"{seconds_to_srt(float(segment['start']))} --> "
                    f"{seconds_to_srt(float(segment['end']))}",
                    str(segment.get("text", "")).strip(),
                ]
            )
        )
    return "\n\n".join(entries) + ("\n" if entries else "")

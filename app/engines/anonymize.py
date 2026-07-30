from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from ..config import PATHS
from ..utils import Progress


def anonymize_text(
    text: str,
    work_dir: Path,
    progress: Progress,
    *,
    engine: str = "privacy_filter",
    include_dates: bool = True,
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    if not PATHS.ai_python.is_file():
        raise RuntimeError(
            "Il motore AI di privacy non è installato. Riesegui l’installer completo."
        )
    source = work_dir / "testo-estratto.md"
    output = work_dir / "privacy-result.json"
    worker_progress = work_dir / "privacy-progress.json"
    source.write_text(text, encoding="utf-8")
    command = [
        str(PATHS.ai_python),
        str(PATHS.app / "workers" / "ai_worker.py"),
        "anonymize",
        "--engine",
        engine,
        "--input",
        str(source),
        "--output",
        str(output),
        "--progress",
        str(worker_progress),
    ]
    if include_dates:
        command.append("--include-dates")
    log_path = work_dir / "privacy-filter-worker.log"
    engine_title = (
        "Rizzo PII 0.3B"
        if engine == "privacy_filter_rizzo"
        else "OpenAI Privacy Filter"
    )
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
                        0.35 + float(state.get("progress", 0)) * 0.55,
                        str(state.get("stage", engine_title)),
                    )
                except (OSError, ValueError):
                    pass
            time.sleep(0.5)
    stderr = log_path.read_text(encoding="utf-8", errors="replace").strip()
    if process.returncode:
        raise RuntimeError(
            f"{engine_title} non ha completato il lavoro. "
            + (stderr[-3000:] or "Errore del motore locale.")
        )
    payload = json.loads(output.read_text(encoding="utf-8"))
    redacted = str(payload.pop("redacted_text"))
    private_spans = payload.pop("_private_spans", [])
    progress(0.92, f"Anonimizzazione locale ({engine_title}) completata")
    return redacted, payload, private_spans

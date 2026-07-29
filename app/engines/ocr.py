from __future__ import annotations

import base64
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

from ..config import PATHS
from ..utils import Progress, file_kind

GLM_MODEL_DIGEST = "2a5a0f1a93017fc9db321ec196efb4b9bbba97c4d890df8e39429ed771f2ed25"


def _prepare_glm_image(path: Path, target: Path) -> Path:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError("Pillow non è installato.") from exc

    output = target / f"{path.stem}-glm.jpg"
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((1440, 1440), Image.Resampling.LANCZOS)
        image.save(output, format="JPEG", quality=92, optimize=True)
    return output


def _render_pages(path: Path, target: Path, progress: Progress) -> list[Path]:
    kind = file_kind(path)
    if kind == "image":
        progress(0.08, "Preparazione immagine per GLM-OCR")
        return [_prepare_glm_image(path, target)]
    if kind != "pdf":
        raise RuntimeError("GLM-OCR locale accetta immagini e PDF.")
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise RuntimeError("pypdfium2 non è installato.") from exc

    pages: list[Path] = []
    document = pdfium.PdfDocument(path)
    try:
        total = max(1, len(document))
        for index in range(len(document)):
            output = target / f"pagina-{index + 1:05d}.jpg"
            page = document[index]
            try:
                bitmap = page.render(scale=120 / 72)
                try:
                    bitmap.to_pil().convert("RGB").save(
                        output,
                        format="JPEG",
                        quality=92,
                        optimize=True,
                    )
                finally:
                    bitmap.close()
            finally:
                page.close()
            pages.append(_prepare_glm_image(output, target))
            output.unlink(missing_ok=True)
            progress(
                0.05 + (index + 1) / total * 0.15,
                f"Preparazione pagina {index + 1}/{total}",
            )
    finally:
        document.close()
    if not pages:
        raise RuntimeError("Il PDF non contiene pagine elaborabili.")
    return pages


def ocr_glm(
    path: Path,
    work_dir: Path,
    progress: Progress,
    *,
    model: str = "glm-ocr:q8_0",
) -> tuple[str, dict[str, Any]]:
    pages_dir = work_dir / "glm-pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    pages = _render_pages(path, pages_dir, progress)
    parts: list[str] = []
    endpoint = "http://127.0.0.1:11434/api/generate"

    try:
        tags = httpx.get("http://127.0.0.1:11434/api/tags", timeout=3.0).json()
        installed = {
            entry.get("name") or entry.get("model"): entry.get("digest")
            for entry in tags.get("models", [])
        }
    except Exception as exc:
        raise RuntimeError(
            "Ollama non risponde su 127.0.0.1:11434. Avvialo e riprova."
        ) from exc
    if model not in installed:
        raise RuntimeError(
            f"Il modello locale {model} non è installato. "
            "Riesegui l’installer senza l’opzione --without-glm."
        )
    if model == "glm-ocr:q8_0" and installed[model] != GLM_MODEL_DIGEST:
        raise RuntimeError(
            "Il digest del modello GLM-OCR non corrisponde alla release "
            "verificata. Riesegui l’installer."
        )

    total = max(1, len(pages))
    with httpx.Client(timeout=httpx.Timeout(900.0, connect=10.0)) as client:
        for index, page in enumerate(pages):
            progress(
                0.2 + index / total * 0.7,
                f"GLM-OCR: pagina {index + 1}/{total}",
            )
            image = base64.b64encode(page.read_bytes()).decode("ascii")
            response = client.post(
                endpoint,
                json={
                    "model": model,
                    "prompt": (
                        "Text Recognition:\n"
                        "Trascrivi tutto il testo visibile rispettando ordine di "
                        "lettura, titoli, elenchi e tabelle. Restituisci solo Markdown."
                    ),
                    "images": [image],
                    "stream": False,
                    "keep_alive": "10m",
                    "options": {
                        "temperature": 0,
                        "num_ctx": 8192,
                        "num_predict": 2048,
                    },
                },
            )
            if response.status_code >= 400:
                raise RuntimeError(
                    f"GLM-OCR ha risposto {response.status_code}: {response.text[:500]}"
                )
            page_text = str(response.json().get("response", "")).strip()
            parts.append(f"<!-- pagina {index + 1} -->\n\n{page_text}")
    progress(0.94, "GLM-OCR completato")
    return "\n\n---\n\n".join(parts), {
        "engine": "GLM-OCR via Ollama locale",
        "model": model,
        "pages": len(pages),
        "characters": sum(len(part) for part in parts),
    }


def ocr_paddle(
    path: Path,
    work_dir: Path,
    progress: Progress,
    *,
    structured: bool = False,
) -> tuple[str, dict[str, Any]]:
    if not PATHS.paddle_python.is_file():
        raise RuntimeError("PaddleOCR non è installato. Riesegui l’installer completo.")
    result_path = work_dir / "paddle-result.json"
    progress_path = work_dir / "paddle-progress.json"
    command = [
        str(PATHS.paddle_python),
        str(PATHS.app / "workers" / "paddle_worker.py"),
        "--input",
        str(path),
        "--output",
        str(result_path),
        "--progress",
        str(progress_path),
        "--mode",
        "structure" if structured else "ocr",
    ]
    log_path = work_dir / "paddle-worker.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=log,
            text=True,
        )
        while process.poll() is None:
            if progress_path.is_file():
                try:
                    state = json.loads(progress_path.read_text(encoding="utf-8"))
                    stage = str(state.get("stage", "PaddleOCR in esecuzione"))
                    progress(
                        0.08 + float(state.get("progress", 0)) * 0.84,
                        stage,
                    )
                except (OSError, ValueError):
                    pass
            time.sleep(0.5)
    stderr = log_path.read_text(encoding="utf-8", errors="replace").strip()
    if process.returncode:
        raise RuntimeError(
            "PaddleOCR non ha completato il lavoro. "
            + (stderr[-2500:] or "Controlla l’installazione del motore.")
        )
    if not result_path.is_file():
        raise RuntimeError("PaddleOCR non ha prodotto il file risultato.")
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    text = str(payload.pop("text", ""))
    progress(0.94, "PaddleOCR completato")
    return text, payload

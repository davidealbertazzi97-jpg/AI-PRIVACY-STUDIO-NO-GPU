from __future__ import annotations

import json
import queue
import threading
import traceback
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

from .config import PATHS
from .db import STORE
from .engines.anonymize import anonymize_text
from .engines.extract import extract_markdown
from .engines.ocr import ocr_glm, ocr_paddle
from .engines.transcribe import make_srt, transcribe_parakeet
from .engines.vault import decrypt_from_vault, encrypt_to_vault
from .utils import (
    file_kind,
    job_output_dir,
    make_bundle,
    remove_tree,
    sha256,
    slug_stem,
)


class SecretStore:
    """Passwords live in RAM only and are removed as soon as a job consumes them."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}
        self._lock = threading.Lock()

    def put(self, job_id: str, secret: str) -> None:
        with self._lock:
            self._values[job_id] = secret

    def pop(self, job_id: str) -> str | None:
        with self._lock:
            return self._values.pop(job_id, None)


SECRETS = SecretStore()


class JobRunner:
    def __init__(self) -> None:
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stopping = threading.Event()
        self._queued: set[str] = set()
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        STORE.recover_interrupted()
        self._stopping.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="privacy-studio-worker",
            daemon=True,
        )
        self._thread.start()
        for job_id in STORE.queued_ids():
            self.submit(job_id)

    def stop(self) -> None:
        self._stopping.set()
        self._queue.put(None)
        if self._thread:
            self._thread.join(timeout=8)

    def submit(self, job_id: str) -> None:
        with self._lock:
            if job_id in self._queued:
                return
            self._queued.add(job_id)
        self._queue.put(job_id)

    def _loop(self) -> None:
        while not self._stopping.is_set():
            job_id = self._queue.get()
            if job_id is None:
                break
            with self._lock:
                self._queued.discard(job_id)
            try:
                self._run(job_id)
            except Exception:
                # A malformed database row must not kill the persistent worker.
                traceback.print_exc()
            finally:
                self._queue.task_done()

    def _run(self, job_id: str) -> None:
        job = STORE.get(job_id)
        work_dir = PATHS.work / job_id
        work_dir.mkdir(parents=True, exist_ok=True)

        def update(value: float, stage: str) -> None:
            STORE.update(
                job_id,
                status="running",
                progress=max(0.0, min(0.99, value)),
                stage=stage,
            )

        try:
            update(0.01, "Avvio elaborazione locale")
            output, bundle, result = self._dispatch(job, work_dir, update)
            STORE.update(
                job_id,
                status="completed",
                progress=1.0,
                stage="Completato",
                output_path=str(output) if output else None,
                bundle_path=str(bundle) if bundle else None,
                result_json=result,
                error=None,
            )
        except Exception as exc:
            STORE.update(
                job_id,
                status="failed",
                stage="Operazione non completata",
                error=str(exc)[:4000],
                result_json={
                    "exception": type(exc).__name__,
                    "local_only": True,
                },
            )
            traceback.print_exc()
        finally:
            SECRETS.pop(job_id)
            remove_tree(work_dir)
            input_path = Path(job["input_path"])
            if input_path.is_file() and PATHS.inbox in input_path.parents:
                input_path.unlink(missing_ok=True)
                with suppress(OSError):
                    input_path.parent.rmdir()

    def _dispatch(
        self,
        job: dict[str, Any],
        work_dir: Path,
        progress: Callable[[float, str], None],
    ) -> tuple[Path | None, Path | None, dict[str, Any]]:
        operation = job["operation"]
        source = Path(job["input_path"])
        options = job["options"]
        if not source.is_file():
            raise RuntimeError("Il file di ingresso non è più disponibile.")

        if operation == "vault_encrypt":
            password = SECRETS.pop(job["id"])
            if password is None:
                raise RuntimeError("La password non è più in memoria: reinvia il file.")
            target, result = encrypt_to_vault(
                source,
                password,
                progress,
                paranoid=bool(options.get("paranoid")),
                recovery=bool(options.get("recovery")),
            )
            result["source_sha256"] = sha256(source)
            return target, None, result

        output_dir = job_output_dir(job)

        if operation == "vault_decrypt":
            password = SECRETS.pop(job["id"])
            if password is None:
                raise RuntimeError(
                    "La password non è più in memoria: ripeti la decifratura."
                )
            target, result = decrypt_from_vault(source, password, output_dir, progress)
            bundle = make_bundle(output_dir)
            return target, bundle, result

        if operation == "transcribe":
            text, result = transcribe_parakeet(
                source,
                work_dir,
                progress,
                chunk_minutes=int(options.get("chunk_minutes", 10)),
            )
            stem = slug_stem(job["input_name"])
            text_path = output_dir / f"{stem}-trascrizione.txt"
            md_path = output_dir / f"{stem}-trascrizione.md"
            srt_path = output_dir / f"{stem}-sottotitoli.srt"
            text_path.write_text(text, encoding="utf-8")
            md_path.write_text(
                f"# Trascrizione — {job['input_name']}\n\n{text}\n",
                encoding="utf-8",
            )
            srt_path.write_text(make_srt(result.get("segments", [])), encoding="utf-8")
            result["outputs"] = [text_path.name, md_path.name, srt_path.name]
            result["source_sha256"] = sha256(source)
            self._write_metadata(output_dir, result)
            bundle = make_bundle(output_dir)
            return md_path, bundle, result

        if operation == "ocr":
            text, result = self._extract_with_engine(
                source,
                job["engine"],
                work_dir,
                progress,
                start=0.02,
                span=0.9,
            )
            stem = slug_stem(job["input_name"])
            md_path = output_dir / f"{stem}-ocr.md"
            txt_path = output_dir / f"{stem}-ocr.txt"
            md_path.write_text(text, encoding="utf-8")
            txt_path.write_text(text, encoding="utf-8")
            result["outputs"] = [md_path.name, txt_path.name]
            result["source_sha256"] = sha256(source)
            self._write_metadata(output_dir, result)
            bundle = make_bundle(output_dir)
            return md_path, bundle, result

        if operation == "convert":
            text, result = extract_markdown(
                source,
                lambda value, stage: progress(0.04 + value * 0.9, stage),
            )
            stem = slug_stem(job["input_name"])
            md_path = output_dir / f"{stem}.md"
            md_path.write_text(text, encoding="utf-8")
            result["outputs"] = [md_path.name]
            result["source_sha256"] = sha256(source)
            self._write_metadata(output_dir, result)
            bundle = make_bundle(output_dir)
            return md_path, bundle, result

        if operation == "anonymize":
            if job["engine"] == "privacy_filter":
                text, extraction = self._extract_for_privacy(
                    source,
                    work_dir,
                    progress,
                )
            else:
                # Compatibilità con eventuali lavori creati dalle versioni
                # precedenti, dove il campo engine indicava l’estrattore.
                text, extraction = self._extract_with_engine(
                    source,
                    job["engine"],
                    work_dir,
                    progress,
                    start=0.02,
                    span=0.3,
                )
            redacted, privacy, _ = anonymize_text(
                text,
                work_dir,
                progress,
                include_dates=bool(options.get("include_dates", True)),
            )
            progress(0.94, "Scrittura copie anonimizzate")
            stem = slug_stem(job["input_name"])
            md_path = output_dir / f"{stem}-anonimizzato.md"
            txt_path = output_dir / f"{stem}-anonimizzato.txt"
            report_path = output_dir / f"{stem}-rapporto-privacy.json"
            warning_path = output_dir / "LEGGIMI-REVISIONE-UMANA.txt"
            md_path.write_text(redacted, encoding="utf-8")
            txt_path.write_text(redacted, encoding="utf-8")
            privacy["extraction"] = extraction
            privacy["source_sha256"] = sha256(source)
            privacy["outputs"] = [md_path.name, txt_path.name, report_path.name]
            report_path.write_text(
                json.dumps(privacy, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            warning_path.write_text(
                "REVISIONE UMANA NECESSARIA\n\n"
                "OpenAI Privacy Filter e le regole italiane riducono il rischio, "
                "ma non garantiscono anonimizzazione completa né conformità legale. "
                "Controlla sempre il testo prima di condividerlo, soprattutto in "
                "ambito sanitario, scolastico, giuridico, finanziario o del lavoro.\n",
                encoding="utf-8",
            )
            bundle = make_bundle(output_dir)
            return md_path, bundle, privacy

        raise RuntimeError(f"Operazione non supportata: {operation}")

    @staticmethod
    def _extract_for_privacy(
        source: Path,
        work_dir: Path,
        progress: Callable[[float, str], None],
    ) -> tuple[str, dict[str, Any]]:
        kind = file_kind(source)
        if kind == "audio":
            raise RuntimeError(
                "Per anonimizzare audio o video, trascrivilo prima con Parakeet."
            )

        if kind == "image":
            text, result = ocr_paddle(
                source,
                work_dir,
                lambda value, stage: progress(0.02 + value * 0.3, stage),
                structured=False,
            )
            result["selected_automatically"] = True
            result["privacy_pipeline"] = "PaddleOCR → OpenAI Privacy Filter"
            return text, result

        if kind == "pdf":
            text, result = extract_markdown(
                source,
                lambda value, stage: progress(0.02 + value * 0.1, stage),
            )
            if len("".join(text.split())) >= 24:
                result["selected_automatically"] = True
                result["privacy_pipeline"] = (
                    "Microsoft MarkItDown → OpenAI Privacy Filter"
                )
                return text, result
            progress(0.12, "PDF senza testo: avvio OCR automatico")
            text, result = ocr_paddle(
                source,
                work_dir,
                lambda value, stage: progress(0.12 + value * 0.2, stage),
                structured=False,
            )
            result["selected_automatically"] = True
            result["privacy_pipeline"] = "PaddleOCR automatico → OpenAI Privacy Filter"
            return text, result

        text, result = extract_markdown(
            source,
            lambda value, stage: progress(0.02 + value * 0.3, stage),
        )
        result["selected_automatically"] = True
        result["privacy_pipeline"] = "Microsoft MarkItDown → OpenAI Privacy Filter"
        return text, result

    @staticmethod
    def _extract_with_engine(
        source: Path,
        engine: str,
        work_dir: Path,
        progress: Callable[[float, str], None],
        *,
        start: float,
        span: float,
    ) -> tuple[str, dict[str, Any]]:
        def scaled(value: float, stage: str) -> None:
            progress(start + value * span, stage)

        if engine == "glm":
            return ocr_glm(source, work_dir, scaled)
        if engine == "paddle":
            return ocr_paddle(source, work_dir, scaled, structured=False)
        if engine == "paddle_structure":
            return ocr_paddle(source, work_dir, scaled, structured=True)
        return extract_markdown(source, scaled)

    @staticmethod
    def _write_metadata(output_dir: Path, result: dict[str, Any]) -> None:
        (output_dir / "metadati-elaborazione.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


RUNNER = JobRunner()

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
from .engines.pdf import redact_pdf
from .engines.transcribe import make_srt, transcribe_parakeet
from .engines.vault import (
    decrypt_from_vault,
    decrypt_group_from_vault,
    encrypt_to_vault,
)
from .utils import (
    file_kind,
    job_output_dir,
    make_bundle,
    public_privacy_report,
    remove_tree,
    sha256,
    slug_stem,
)


def reversible_dictionary(
    input_name: str, spans: list[dict[str, Any]]
) -> dict[str, Any]:
    entries: list[dict[str, str]] = []
    for span in spans:
        placeholder = str(span.get("placeholder") or "")
        original = str(span.get("text") or "")
        if not placeholder or not original:
            continue
        entries.append(
            {
                "placeholder": placeholder,
                "replacement": str(span.get("replacement") or placeholder),
                "original": original,
                "label": str(span.get("label") or "PII"),
            }
        )
    return {
        "version": 1,
        "document": input_name,
        "entries": entries,
        "note": "File sensibile: conservarlo esclusivamente nella cassaforte.",
    }


def preview_cache_path(source: Path) -> Path:
    return source.with_name(f".{source.stem}-privacy-cache.json")


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
        preview_source_kept = False

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
            preview_source_kept = job["operation"] == "anonymize_preview"
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
            cache_value = (job.get("options") or {}).get("preview_cache_path")
            if isinstance(cache_value, str):
                cache_path = Path(cache_value)
                if (
                    cache_path.parent == input_path.parent
                    and cache_path.name.startswith(".")
                    and cache_path.name.endswith("-privacy-cache.json")
                ):
                    cache_path.unlink(missing_ok=True)
            if (
                not preview_source_kept
                and input_path.is_file()
                and PATHS.inbox in input_path.parents
            ):
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

        if operation == "vault_decrypt":
            output_dir = job_output_dir(job)
            password = SECRETS.pop(job["id"])
            if password is None:
                raise RuntimeError(
                    "La password non è più in memoria: ripeti la decifratura."
                )
            target, result = decrypt_from_vault(source, password, output_dir, progress)
            bundle = make_bundle(output_dir)
            return target, bundle, result

        if operation == "vault_group_encrypt":
            password = SECRETS.pop(job["id"])
            if password is None:
                raise RuntimeError(
                    "La password non è più in memoria: reinvia il vault."
                )
            target, result = encrypt_to_vault(
                source,
                password,
                progress,
                paranoid=bool(options.get("paranoid")),
                recovery=bool(options.get("recovery")),
                kind="group",
            )
            result["source_sha256"] = sha256(source)
            return target, None, result

        if operation == "vault_group_decrypt":
            output_dir = job_output_dir(job)
            password = SECRETS.pop(job["id"])
            if password is None:
                raise RuntimeError(
                    "La password non è più in memoria: ripeti la decifratura."
                )
            target, result = decrypt_group_from_vault(
                source,
                password,
                output_dir,
                progress,
            )
            bundle = make_bundle(output_dir)
            return target, bundle, result

        if operation == "transcribe":
            output_dir = job_output_dir(job)
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
            output_dir = job_output_dir(job)
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
            output_dir = job_output_dir(job)
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

        if operation in ("anonymize", "anonymize_preview"):
            dictionary_password = (
                SECRETS.pop(job["id"])
                if bool(options.get("dictionary_vault"))
                else None
            )
            if options.get("dictionary_vault") and dictionary_password is None:
                raise RuntimeError(
                    "La password del dizionario non è più in memoria: "
                    "ripeti la conferma della preview."
                )
            cached_preview = self._load_preview_cache(job, source)
            if cached_preview:
                text = cached_preview["text"]
                extraction = cached_preview["extraction"]
                cached_spans = cached_preview["spans"]
                progress(0.18, "Riutilizzo testo e rilevazioni della preview")
            elif job["engine"] in ("privacy_filter", "privacy_filter_rizzo"):
                text, extraction = self._extract_for_privacy(
                    source,
                    work_dir,
                    progress,
                )
                cached_spans = None
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
                cached_spans = None
            selected_spans = (
                options.get("selected_spans") if operation == "anonymize" else None
            )
            redacted, privacy, private_spans = anonymize_text(
                text,
                work_dir,
                progress,
                engine=job["engine"],
                include_dates=bool(options.get("include_dates", True)),
                selected_spans=selected_spans,
                preview_only=operation == "anonymize_preview",
                cached_spans=cached_spans,
            )
            privacy["extraction"] = extraction
            privacy["source_sha256"] = sha256(source)
            if operation == "anonymize_preview":
                cache_path = preview_cache_path(source)
                cache_path.write_text(
                    json.dumps(
                        {
                            "version": 1,
                            "source_sha256": privacy["source_sha256"],
                            "text": text,
                            "spans": private_spans,
                            "extraction": extraction,
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                cache_path.chmod(0o600)
                if source.suffix.lower() == ".pdf":
                    preview_pdf = source.with_name(
                        f".{source.stem}-privacy-preview.pdf"
                    )
                    try:
                        privacy["pdf_preview"] = redact_pdf(
                            source,
                            preview_pdf,
                            private_spans,
                        )
                        privacy["preview_pdf_path"] = str(preview_pdf)
                    except RuntimeError as exc:
                        privacy["pdf_preview_warning"] = str(exc)
                privacy["preview_only"] = True
                privacy["review_required"] = True
                return None, None, privacy
            # The full source is needed only by the in-memory preview UI; it
            # must never be written into the downloadable final report.
            privacy.pop("original_text", None)
            if dictionary_password and private_spans:
                dictionary_file = (
                    work_dir / f"{slug_stem(job['input_name'])}-dizionario.json"
                )
                try:
                    dictionary_payload = reversible_dictionary(
                        job["input_name"], private_spans
                    )
                    dictionary_file.write_text(
                        json.dumps(
                            dictionary_payload,
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                    dictionary_target, _ = encrypt_to_vault(
                        dictionary_file,
                        dictionary_password,
                        progress,
                        kind="dictionary",
                    )
                    privacy["dictionary_vault_name"] = dictionary_target.name
                    privacy["dictionary_entries"] = len(dictionary_payload["entries"])
                finally:
                    dictionary_file.unlink(missing_ok=True)
            progress(0.94, "Scrittura copie anonimizzate")
            output_dir = job_output_dir(job)
            stem = slug_stem(job["input_name"])
            md_path = output_dir / f"{stem}-anonimizzato.md"
            txt_path = output_dir / f"{stem}-anonimizzato.txt"
            pdf_path = output_dir / f"{stem}-anonimizzato.pdf"
            report_path = output_dir / f"{stem}-rapporto-privacy.json"
            warning_path = output_dir / "LEGGIMI-REVISIONE-UMANA.txt"
            md_path.write_text(redacted, encoding="utf-8")
            txt_path.write_text(redacted, encoding="utf-8")
            outputs = [md_path.name, txt_path.name, report_path.name]
            if source.suffix.lower() == ".pdf":
                try:
                    privacy["pdf_redaction"] = redact_pdf(
                        source,
                        pdf_path,
                        private_spans,
                    )
                    outputs.insert(2, pdf_path.name)
                except RuntimeError as exc:
                    privacy["pdf_redaction_warning"] = str(exc)
            privacy["outputs"] = outputs
            report_path.write_text(
                json.dumps(
                    public_privacy_report(privacy), indent=2, ensure_ascii=False
                ),
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
    def _load_preview_cache(job: dict[str, Any], source: Path) -> dict[str, Any] | None:
        value = (job.get("options") or {}).get("preview_cache_path")
        if not isinstance(value, str):
            return None
        cache = Path(value)
        if (
            cache.parent != source.parent
            or cache != preview_cache_path(source)
            or not cache.is_file()
        ):
            return None
        try:
            payload = json.loads(cache.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return None
            if payload.get("source_sha256") != sha256(source):
                return None
            if not isinstance(payload.get("text"), str):
                return None
            if not isinstance(payload.get("spans"), list):
                return None
            if not isinstance(payload.get("extraction"), dict):
                return None
            return payload
        except (OSError, ValueError, TypeError):
            return None

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

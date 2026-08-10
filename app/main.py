from __future__ import annotations

import hmac
import os
import shutil
import subprocess
import uuid
import zipfile
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask

from . import __version__
from .config import ACCESS_TOKEN, MAX_UPLOAD_BYTES, PATHS, PORT
from .db import STORE
from .engines.permanent_vault import (
    PERMANENT_VAULT,
    VAULT_SESSIONS,
    PermanentVaultError,
    PersistentVault,
)
from .jobs import RUNNER, SECRETS, preview_cache_path
from .utils import safe_name

VALID_OPERATIONS = {
    "convert",
    "ocr",
    "transcribe",
    "anonymize",
    "vault_encrypt",
    "vault_decrypt",
    "vault_group_encrypt",
    "vault_group_decrypt",
}
VALID_ENGINES = {
    "markitdown",
    "paddle",
    "paddle_structure",
    "glm",
    "parakeet",
    "privacy_filter",
    "privacy_filter_rizzo",
    "picocrypt",
}
ENGINES_BY_OPERATION = {
    "convert": {"markitdown"},
    "ocr": {"paddle", "paddle_structure", "glm"},
    "transcribe": {"parakeet"},
    "anonymize": {"privacy_filter", "privacy_filter_rizzo"},
    "vault_encrypt": {"markitdown"},
    "vault_decrypt": {"markitdown"},
    "vault_group_encrypt": {"picocrypt"},
    "vault_group_decrypt": {"picocrypt"},
}


def token_matches(value: str | None) -> bool:
    return bool(
        ACCESS_TOKEN
        and value
        and hmac.compare_digest(value.encode(), ACCESS_TOKEN.encode())
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    RUNNER.start()
    yield
    RUNNER.stop()


app = FastAPI(
    title="AI Privacy Studio",
    version=__version__,
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


@app.middleware("http")
async def local_security(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        supplied = request.cookies.get("ps_token") or request.headers.get(
            "X-Privacy-Studio-Token"
        )
        if not token_matches(supplied):
            return JSONResponse({"detail": "Accesso locale non autorizzato"}, 401)
        origin = request.headers.get("origin")
        allowed = {
            f"http://127.0.0.1:{PORT}",
            f"http://localhost:{PORT}",
        }
        if origin and origin not in allowed:
            return JSONResponse({"detail": "Origine non autorizzata"}, 403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=()"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; connect-src 'self'; object-src 'none'; "
        "base-uri 'none'; frame-ancestors 'none'"
    )
    return response


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "app": "privacy-studio-locale",
        "version": __version__,
        "local": True,
    }


@app.get("/")
def index(request: Request, token: str | None = Query(default=None)):
    if token_matches(token):
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            "ps_token",
            token,
            httponly=True,
            samesite="strict",
            secure=False,
            max_age=60 * 60 * 24 * 30,
        )
        return response
    if not token_matches(request.cookies.get("ps_token")):
        return JSONResponse(
            {
                "detail": (
                    "Apri Privacy Studio dal collegamento sulla Scrivania. "
                    "Il collegamento fornisce la chiave locale in modo sicuro."
                )
            },
            401,
        )
    return FileResponse(PATHS.app / "static" / "index.html")


app.mount(
    "/assets",
    StaticFiles(directory=PATHS.app / "static"),
    name="assets",
)


async def save_upload(upload: UploadFile) -> tuple[Path, int, str]:
    original = safe_name(upload.filename or "documento")
    target_dir = PATHS.inbox / uuid.uuid4().hex
    target_dir.mkdir(parents=True, exist_ok=False)
    os.chmod(target_dir, 0o700)
    target = target_dir / original
    size = 0
    try:
        with target.open("xb") as handle:
            while chunk := await upload.read(8 * 1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        413,
                        "File oltre il limite locale configurato (100 GB).",
                    )
                handle.write(chunk)
        os.chmod(target, 0o600)
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise
    finally:
        await upload.close()
    if size == 0:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise HTTPException(400, f"{original} è vuoto.")
    return target, size, original


@app.post("/api/jobs")
async def create_jobs(
    files: Annotated[list[UploadFile], File()],
    operation: Annotated[str, Form()],
    engine: Annotated[str, Form()] = "markitdown",
    include_dates: Annotated[bool, Form()] = True,
    chunk_minutes: Annotated[int, Form()] = 10,
    password: Annotated[str | None, Form()] = None,
    paranoid: Annotated[bool, Form()] = False,
    recovery: Annotated[bool, Form()] = False,
) -> dict[str, Any]:
    if operation not in VALID_OPERATIONS:
        raise HTTPException(400, "Operazione non valida.")
    if engine not in VALID_ENGINES:
        raise HTTPException(400, "Motore non valido.")
    if engine not in ENGINES_BY_OPERATION[operation]:
        raise HTTPException(400, "Il motore scelto non supporta questa operazione.")
    if operation.startswith("vault_") and not password:
        raise HTTPException(400, "Inserisci la password della cassaforte.")
    if operation.startswith("vault_") and len(password or "") < 10:
        raise HTTPException(400, "Usa una passphrase di almeno 10 caratteri.")
    created: list[dict[str, Any]] = []
    for upload in files:
        path, size, original = await save_upload(upload)
        job_operation = operation
        job_engine = engine
        if operation == "vault_decrypt" and original.lower().endswith(".vault.zip.pcv"):
            job_operation = "vault_group_decrypt"
            job_engine = "picocrypt"
        options = {
            "include_dates": include_dates,
            "chunk_minutes": max(2, min(chunk_minutes, 20)),
            "paranoid": paranoid,
            "recovery": recovery,
        }
        job = STORE.create(
            operation=job_operation,
            engine=job_engine,
            input_name=original,
            input_path=str(path),
            input_size=size,
            options=options,
        )
        if password is not None:
            SECRETS.put(job["id"], password)
        RUNNER.submit(job["id"])
        created.append(job)
    return {"jobs": created}


@app.post("/api/vault/groups")
async def create_vault_group(
    files: Annotated[list[UploadFile], File()],
    group_name: Annotated[str, Form()] = "vault-documenti",
    password: Annotated[str, Form()] = "",
    paranoid: Annotated[bool, Form()] = False,
    recovery: Annotated[bool, Form()] = False,
) -> dict[str, Any]:
    """Pack multiple uploaded documents, then encrypt the archive once."""
    if not files:
        raise HTTPException(400, "Seleziona almeno un documento per il vault.")
    if len(password) < 10:
        raise HTTPException(400, "Usa una passphrase di almeno 10 caratteri.")
    group_label = safe_name(group_name, "vault-documenti")
    saved: list[Path] = []
    archive_dir: Path | None = None
    try:
        for upload in files:
            path, _, _ = await save_upload(upload)
            saved.append(path)
        archive_dir = PATHS.inbox / uuid.uuid4().hex
        archive_dir.mkdir(parents=True, exist_ok=False)
        os.chmod(archive_dir, 0o700)
        archive_path = archive_dir / f"{group_label}.zip"
        used_names: set[str] = set()
        with zipfile.ZipFile(
            archive_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
        ) as archive:
            for path in saved:
                name = safe_name(path.name)
                if name in used_names:
                    name = f"{path.stem}-{uuid.uuid4().hex[:6]}{path.suffix}"
                used_names.add(name)
                archive.write(path, arcname=name)
        os.chmod(archive_path, 0o600)
        size = archive_path.stat().st_size
        job = STORE.create(
            operation="vault_group_encrypt",
            engine="picocrypt",
            input_name=archive_path.name,
            input_path=str(archive_path),
            input_size=size,
            options={"paranoid": paranoid, "recovery": recovery},
        )
        SECRETS.put(job["id"], password)
        RUNNER.submit(job["id"])
        return {"job": job}
    except Exception:
        if archive_dir is not None:
            shutil.rmtree(archive_dir, ignore_errors=True)
        raise
    finally:
        for path in saved:
            shutil.rmtree(path.parent, ignore_errors=True)


def _permanent_vault_session(request: Request):
    token = request.headers.get("X-Privacy-Studio-Vault-Session")
    try:
        return token, VAULT_SESSIONS.get(token)
    except PermanentVaultError as exc:
        raise HTTPException(401, str(exc)) from exc


def _remove_upload(path: Path) -> None:
    shutil.rmtree(path.parent, ignore_errors=True)


@app.get("/api/permanent-vault")
def permanent_vault_status(request: Request) -> dict[str, Any]:
    token = request.headers.get("X-Privacy-Studio-Vault-Session")
    if not PERMANENT_VAULT.exists:
        return {"exists": False, "unlocked": False}
    try:
        session = VAULT_SESSIONS.get(token)
    except PermanentVaultError:
        return {"exists": True, "unlocked": False}
    return {
        "exists": True,
        "unlocked": True,
        "metadata": PERMANENT_VAULT._metadata(session.header),
    }


@app.post("/api/permanent-vault/create")
def create_permanent_vault(password: Annotated[str, Form()]) -> dict[str, Any]:
    try:
        metadata = PERMANENT_VAULT.create(password)
        token, _ = VAULT_SESSIONS.open(password)
    except PermanentVaultError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"session": token, "metadata": metadata}


@app.post("/api/permanent-vault/unlock")
def unlock_permanent_vault(password: Annotated[str, Form()]) -> dict[str, Any]:
    if not PERMANENT_VAULT.exists:
        raise HTTPException(404, "Il vault permanente non è ancora creato.")
    try:
        token, metadata = VAULT_SESSIONS.open(password)
    except PermanentVaultError as exc:
        raise HTTPException(401, str(exc)) from exc
    return {"session": token, "metadata": metadata}


@app.post("/api/permanent-vault/lock")
def lock_permanent_vault(request: Request) -> dict[str, bool]:
    token = request.headers.get("X-Privacy-Studio-Vault-Session")
    VAULT_SESSIONS.clear(token)
    return {"ok": True}


@app.get("/api/permanent-vault/files")
def list_permanent_vault_files(
    request: Request,
    q: str = Query("", max_length=200),
) -> dict[str, Any]:
    _, session = _permanent_vault_session(request)
    try:
        files = PERMANENT_VAULT.list_files(session.key, session.header, q)
    except PermanentVaultError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"files": files}


@app.post("/api/permanent-vault/files")
async def add_permanent_vault_files(
    request: Request,
    files: Annotated[list[UploadFile], File()],
) -> dict[str, Any]:
    _, session = _permanent_vault_session(request)
    if not files:
        raise HTTPException(400, "Seleziona almeno un documento.")
    saved: list[Path] = []
    stored: list[dict[str, Any]] = []
    try:
        for upload in files:
            path, _, original = await save_upload(upload)
            saved.append(path)
            stored.append(
                PERMANENT_VAULT.store_file(
                    session.key,
                    session.header,
                    path,
                    original,
                )
            )
    except PermanentVaultError as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        for path in saved:
            _remove_upload(path)
    return {"files": stored}


@app.get("/api/permanent-vault/files/{file_id}/download")
def download_permanent_vault_file(file_id: str, request: Request):
    _, session = _permanent_vault_session(request)
    temporary_dir = PATHS.work / f"permanent-vault-download-{uuid.uuid4().hex}"
    target = temporary_dir / "documento"
    try:
        metadata = PERMANENT_VAULT.restore_file(
            session.key,
            session.header,
            file_id,
            target,
        )
    except PermanentVaultError as exc:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        raise HTTPException(404, str(exc)) from exc
    return FileResponse(
        target,
        filename=metadata["name"],
        background=BackgroundTask(shutil.rmtree, temporary_dir, ignore_errors=True),
    )


@app.delete("/api/permanent-vault/files/{file_id}")
def delete_permanent_vault_file(file_id: str, request: Request) -> dict[str, bool]:
    _, session = _permanent_vault_session(request)
    try:
        PERMANENT_VAULT.delete_file(session.key, session.header, file_id)
    except PermanentVaultError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"ok": True}


@app.post("/api/permanent-vault/backup")
def backup_permanent_vault(
    request: Request,
    folder: Annotated[str, Form()],
) -> dict[str, Any]:
    _, session = _permanent_vault_session(request)
    if not folder.strip():
        raise HTTPException(400, "Indica una cartella locale di backup.")
    try:
        result = PERMANENT_VAULT.backup(Path(folder), session.header)
    except (OSError, PermanentVaultError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return result


@app.post("/api/permanent-vault/restore")
def restore_permanent_vault(
    backup_path: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> dict[str, Any]:
    if not PERMANENT_VAULT.exists and (
        PERMANENT_VAULT.root.exists() and any(PERMANENT_VAULT.root.iterdir())
    ):
        raise HTTPException(
            409,
            "La cartella locale del vault contiene dati non riconosciuti.",
        )
    candidate = PersistentVault(Path(backup_path))
    try:
        candidate.unlock(password)
        if PERMANENT_VAULT.exists:
            result = PERMANENT_VAULT.merge_backup(candidate.root, password)
            metadata = result["metadata"]
        else:
            metadata = PERMANENT_VAULT.restore_backup(candidate.root)
        VAULT_SESSIONS.clear_all()
        token, _ = VAULT_SESSIONS.open(password)
    except (OSError, PermanentVaultError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"session": token, "metadata": metadata}


@app.post("/api/anonymization-previews")
async def create_anonymization_preview(
    files: Annotated[list[UploadFile], File()],
    engine: Annotated[str, Form()] = "privacy_filter",
    include_dates: Annotated[bool, Form()] = True,
) -> dict[str, Any]:
    """Start a local detection-only pass for the anonymization review step.

    The uploaded source is intentionally kept in the private inbox until the
    user either commits or discards the preview.  No cloud service is involved
    and the final job reuses that exact source file.
    """
    if engine not in ENGINES_BY_OPERATION["anonymize"]:
        raise HTTPException(400, "Il motore scelto non supporta l’anonimizzazione.")
    if len(files) != 1:
        raise HTTPException(
            400,
            "La preview richiede un solo file alla volta per consentire "
            "una revisione precisa.",
        )
    path, size, original = await save_upload(files[0])
    job = STORE.create(
        operation="anonymize_preview",
        engine=engine,
        input_name=original,
        input_path=str(path),
        input_size=size,
        options={"include_dates": include_dates},
    )
    RUNNER.submit(job["id"])
    return {"job": job}


def _preview_job(job_id: str) -> dict[str, Any]:
    try:
        job = STORE.get(job_id)
    except KeyError as exc:
        raise HTTPException(404, "Anteprima non trovata.") from exc
    if job["operation"] != "anonymize_preview":
        raise HTTPException(
            400,
            "Il lavoro indicato non è un’anteprima di anonimizzazione.",
        )
    if job["status"] != "completed":
        raise HTTPException(409, "L’anteprima non è ancora pronta.")
    source = Path(job["input_path"])
    inbox = PATHS.inbox.resolve()
    try:
        inside_inbox = source.resolve(strict=True).parent == inbox / source.parent.name
    except FileNotFoundError as exc:
        raise HTTPException(
            410,
            "Il documento dell’anteprima non è più disponibile.",
        ) from exc
    if not inside_inbox:
        raise HTTPException(403, "Percorso dell’anteprima non consentito.")
    return job


def _selection_key(item: Any) -> tuple[int, int, str] | None:
    if not isinstance(item, dict):
        return None
    try:
        start = int(item["start"])
        end = int(item["end"])
        label = str(item["label"])
    except (KeyError, TypeError, ValueError):
        return None
    if start < 0 or end <= start or not label:
        return None
    return start, end, label


def _remove_preview_artifact(preview: dict[str, Any]) -> None:
    value = (preview.get("result") or {}).get("preview_pdf_path")
    if not value:
        return
    path = Path(value)
    source = Path(preview["input_path"])
    if path.parent == source.parent and path.name.startswith("."):
        path.unlink(missing_ok=True)


def _remove_preview_cache(preview: dict[str, Any]) -> None:
    source = Path(preview["input_path"])
    cache = preview_cache_path(source)
    cache.unlink(missing_ok=True)


@app.post("/api/anonymization-previews/{preview_id}/commit")
async def commit_anonymization_preview(
    preview_id: str,
    request: Request,
) -> dict[str, Any]:
    """Commit only the detections selected in the local preview."""
    preview = _preview_job(preview_id)
    payload = await request.json()
    if not isinstance(payload, dict) or not isinstance(
        payload.get("selected_spans"), list
    ):
        raise HTTPException(400, "La selezione della preview non è valida.")
    raw_selection = payload["selected_spans"]

    available: set[tuple[int, int, str]] = set()
    for span in (preview.get("result") or {}).get("spans", []):
        key = _selection_key(span)
        if key is not None:
            available.add(key)

    original_text = str((preview.get("result") or {}).get("original_text") or "")

    selected: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str]] = set()
    for item in raw_selection:
        key = _selection_key(item)
        if key is None:
            raise HTTPException(
                400,
                "La selezione contiene una rilevazione non valida.",
            )
        is_manual = key[2] == "manual_text"
        valid_manual = is_manual and key[1] <= len(original_text)
        if key not in available and not valid_manual:
            raise HTTPException(
                400,
                "La selezione contiene una rilevazione non valida.",
            )
        replacement = item.get("replacement", "") if isinstance(item, dict) else ""
        if replacement is not None and not isinstance(replacement, str):
            raise HTTPException(400, "La sostituzione personalizzata non è valida.")
        replacement = (replacement or "").strip()
        if len(replacement) > 180 or any(
            ord(char) < 32 and char not in "\t" for char in replacement
        ):
            raise HTTPException(400, "La sostituzione personalizzata non è valida.")
        if key in seen:
            continue
        seen.add(key)
        selected_item = {"start": key[0], "end": key[1], "label": key[2]}
        if replacement:
            selected_item["replacement"] = replacement
        selected.append(selected_item)

    save_dictionary = bool(payload.get("save_dictionary"))
    dictionary_password = payload.get("dictionary_password")
    if save_dictionary and (
        not isinstance(dictionary_password, str) or len(dictionary_password) < 10
    ):
        raise HTTPException(
            400,
            "Per salvare il dizionario usa una passphrase di almeno 10 caratteri.",
        )

    options = dict(preview.get("options") or {})
    options["selected_spans"] = selected
    options["preview_job_id"] = preview_id
    options["dictionary_vault"] = save_dictionary
    cache_path = preview_cache_path(Path(preview["input_path"]))
    if cache_path.is_file():
        options["preview_cache_path"] = str(cache_path)
    final_job = STORE.create(
        operation="anonymize",
        engine=preview["engine"],
        input_name=preview["input_name"],
        input_path=preview["input_path"],
        input_size=preview["input_size"],
        options=options,
    )
    if save_dictionary:
        SECRETS.put(final_job["id"], dictionary_password)
    STORE.update(
        preview_id,
        status="consumed",
        stage="Anteprima confermata: anonimizzazione in coda",
        result_json={"preview_consumed": True, "selected": len(selected)},
    )
    _remove_preview_artifact(preview)
    RUNNER.submit(final_job["id"])
    return {"job": final_job, "selected": len(selected), "available": len(available)}


@app.post("/api/anonymization-previews/{preview_id}/discard")
def discard_anonymization_preview(preview_id: str) -> dict[str, Any]:
    """Release a preview source when the user cancels the review."""
    preview = _preview_job(preview_id)
    source = Path(preview["input_path"])
    source.unlink(missing_ok=True)
    _remove_preview_artifact(preview)
    _remove_preview_cache(preview)
    with suppress(OSError):
        source.parent.rmdir()
    STORE.update(
        preview_id,
        status="discarded",
        stage="Anteprima annullata",
        result_json={"preview_discarded": True},
    )
    return {"ok": True}


@app.get("/api/anonymization-previews/{preview_id}/pdf")
def preview_anonymized_pdf(
    preview_id: str,
    kind: str = Query("original"),
):
    preview = _preview_job(preview_id)
    source = Path(preview["input_path"])
    if source.suffix.lower() != ".pdf":
        raise HTTPException(404, "La preview PDF non è disponibile per questo file.")
    if kind == "original":
        target = source
    elif kind == "redacted":
        target = Path((preview.get("result") or {}).get("preview_pdf_path", ""))
    else:
        raise HTTPException(400, "Vista PDF non valida.")
    if not target.is_file() or target.parent != source.parent:
        raise HTTPException(404, "Vista PDF non disponibile.")
    return FileResponse(target, media_type="application/pdf", filename=target.name)


@app.get("/api/jobs")
def list_jobs(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
    return {"jobs": STORE.list(limit)}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    try:
        return STORE.get(job_id)
    except KeyError as exc:
        raise HTTPException(404, "Lavoro non trovato.") from exc


def allowed_download(path: Path) -> bool:
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        return False
    roots = (PATHS.outputs.resolve(), PATHS.vault.resolve())
    return any(resolved == root or root in resolved.parents for root in roots)


@app.get("/api/jobs/{job_id}/download")
def download_job(job_id: str, kind: str = Query("primary")):
    try:
        job = STORE.get(job_id)
    except KeyError as exc:
        raise HTTPException(404, "Lavoro non trovato.") from exc
    field = "bundle_path" if kind == "bundle" else "output_path"
    value = job.get(field)
    if not value:
        raise HTTPException(404, "Risultato non disponibile.")
    path = Path(value)
    if not allowed_download(path):
        raise HTTPException(403, "Percorso risultato non consentito.")
    return FileResponse(path, filename=path.name)


@app.get("/api/vault")
def list_vault() -> dict[str, Any]:
    volumes = []
    for path in sorted(
        PATHS.vault.glob("*.pcv"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ):
        stat = path.stat()
        if path.name.endswith(".vault.zip.pcv"):
            kind = "group"
        elif path.name.endswith(".dizionario.json.pcv"):
            kind = "dictionary"
        else:
            kind = "file"
        volumes.append(
            {
                "name": path.name,
                "size": stat.st_size,
                "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "kind": kind,
            }
        )
    return {"volumes": volumes}


@app.get("/api/vault/{name}/download")
def download_vault_volume(name: str):
    safe = safe_name(name)
    path = PATHS.vault / safe
    if safe != name or not path.is_file() or path.suffix.lower() != ".pcv":
        raise HTTPException(404, "Volume non trovato.")
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@app.delete("/api/vault/{name}")
def delete_vault_volume(name: str) -> dict[str, Any]:
    safe = safe_name(name)
    path = PATHS.vault / safe
    if safe != name or not path.is_file() or path.suffix.lower() != ".pcv":
        raise HTTPException(404, "Volume non trovato.")
    path.unlink()
    return {"ok": True, "name": name}


@app.post("/api/vault/{name}/decrypt")
def decrypt_vault_volume(
    name: str,
    password: Annotated[str, Form()],
) -> dict[str, Any]:
    safe = safe_name(name)
    path = PATHS.vault / safe
    if safe != name or not path.is_file() or path.suffix.lower() != ".pcv":
        raise HTTPException(404, "Volume non trovato.")
    operation = (
        "vault_group_decrypt"
        if path.name.endswith(".vault.zip.pcv")
        else "vault_decrypt"
    )
    job = STORE.create(
        operation=operation,
        engine="picocrypt",
        input_name=path.name,
        input_path=str(path),
        input_size=path.stat().st_size,
        options={},
    )
    SECRETS.put(job["id"], password)
    RUNNER.submit(job["id"])
    return {"job": job}


def command_ok(command: list[str], timeout: int = 10) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        detail = (result.stdout or result.stderr).strip().splitlines()
        return result.returncode == 0, (detail[-1] if detail else "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)


def model_cached(pattern: str) -> bool:
    cache = Path(
        os.environ.get(
            "HF_HUB_CACHE",
            Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
            / "hub",
        )
    )
    return any(cache.glob(pattern))


@app.get("/api/status")
def status() -> dict[str, Any]:
    core_ok, core_detail = command_ok(
        [
            str(PATHS.core_python),
            "-c",
            "import markitdown, pypdfium2; print('pronto')",
        ]
    )
    ai_ok, ai_detail = command_ok(
        [
            str(PATHS.ai_python),
            "-c",
            "import opf, torch, transformers; print('pronto')",
        ]
    )
    paddle_ok, paddle_detail = command_ok(
        [
            str(PATHS.paddle_python),
            "-c",
            "import paddleocr, paddle; print('pronto')",
        ],
        timeout=25,
    )
    ollama_ok, ollama_detail = command_ok(
        [str(PATHS.ollama), "show", "glm-ocr:q8_0"], timeout=20
    )
    picocrypt_ok = PATHS.picocrypt.is_file() and os.access(PATHS.picocrypt, os.X_OK)
    opf_model = Path(
        os.environ.get(
            "OPF_CHECKPOINT",
            Path.home() / ".opf" / "privacy_filter",
        )
    )
    opf_model_ready = (opf_model / "model.safetensors").is_file()
    parakeet_model = model_cached(
        "models--nvidia--parakeet-tdt-0.6b-v3/snapshots/*/model.safetensors"
    )
    rizzo_model_ready = model_cached(
        "models--rizzoaiacademy--rizzo-pii-0.3B/snapshots/*/config.json"
    )
    return {
        "local_only": True,
        "bind": f"127.0.0.1:{PORT}",
        "outputs": str(PATHS.outputs),
        "engines": {
            "markitdown": {
                "ready": core_ok,
                "model_ready": True,
                "detail": core_detail,
            },
            "privacy_filter": {
                "ready": ai_ok,
                "model_ready": opf_model_ready,
                "detail": (
                    "OpenAI Privacy Filter locale (Tutte le lingue)"
                    if opf_model_ready
                    else "Modello da scaricare al primo uso"
                ),
            },
            "privacy_filter_rizzo": {
                "ready": ai_ok,
                "model_ready": rizzo_model_ready,
                "detail": (
                    "Rizzo PII 0.3B locale (Solo italiano)"
                    if rizzo_model_ready
                    else "Modello da scaricare al primo uso"
                ),
            },
            "parakeet": {
                "ready": ai_ok,
                "model_ready": parakeet_model,
                "detail": (
                    "NVIDIA Parakeet v3 locale"
                    if parakeet_model
                    else "Modello da scaricare al primo uso"
                ),
            },
            "paddle": {
                "ready": paddle_ok,
                "model_ready": paddle_ok,
                "detail": paddle_detail,
            },
            "glm": {
                "ready": ollama_ok,
                "model_ready": ollama_ok,
                "detail": (
                    "Ollama / glm-ocr:q8_0"
                    if ollama_ok
                    else (ollama_detail or "Modello non disponibile")
                ),
            },
            "picocrypt": {
                "ready": picocrypt_ok,
                "model_ready": True,
                "detail": "Picocrypt CLI 1.49" if picocrypt_ok else "Non installato",
            },
        },
    }

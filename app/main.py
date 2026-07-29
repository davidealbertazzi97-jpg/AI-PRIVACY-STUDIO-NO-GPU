from __future__ import annotations

import hmac
import os
import shutil
import subprocess
import uuid
from contextlib import asynccontextmanager
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

from . import __version__
from .config import ACCESS_TOKEN, MAX_UPLOAD_BYTES, PATHS, PORT
from .db import STORE
from .jobs import RUNNER, SECRETS
from .utils import safe_name

VALID_OPERATIONS = {
    "convert",
    "ocr",
    "transcribe",
    "anonymize",
    "vault_encrypt",
    "vault_decrypt",
}
VALID_ENGINES = {
    "markitdown",
    "paddle",
    "paddle_structure",
    "glm",
    "parakeet",
    "privacy_filter",
}
ENGINES_BY_OPERATION = {
    "convert": {"markitdown"},
    "ocr": {"paddle", "paddle_structure", "glm"},
    "transcribe": {"parakeet"},
    "anonymize": {"privacy_filter"},
    "vault_encrypt": {"markitdown"},
    "vault_decrypt": {"markitdown"},
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
        options = {
            "include_dates": include_dates,
            "chunk_minutes": max(2, min(chunk_minutes, 20)),
            "paranoid": paranoid,
            "recovery": recovery,
        }
        job = STORE.create(
            operation=operation,
            engine=engine,
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
        volumes.append(
            {
                "name": path.name,
                "size": stat.st_size,
                "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )
    return {"volumes": volumes}


@app.post("/api/vault/{name}/decrypt")
def decrypt_vault_volume(
    name: str,
    password: Annotated[str, Form()],
) -> dict[str, Any]:
    safe = safe_name(name)
    path = PATHS.vault / safe
    if safe != name or not path.is_file() or path.suffix.lower() != ".pcv":
        raise HTTPException(404, "Volume non trovato.")
    job = STORE.create(
        operation="vault_decrypt",
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
                    "OpenAI Privacy Filter locale"
                    if opf_model_ready
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

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import wave
from contextlib import contextmanager
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

APP_DIR = Path(__file__).resolve().parent.parent
OPF_REVISION = "7ffa9a043d54d1be65afb281eddf0ffbe629385b"


def write_text_pdf(path: Path, lines: list[tuple[str, int]]) -> None:
    """Create a small dependency-free PDF fixture with selectable text."""

    commands = ["BT", "72 752 Td"]
    for index, (line, size) in enumerate(lines):
        if index:
            commands.append("0 -48 Td")
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        commands.extend((f"/F1 {size} Tf", f"({escaped}) Tj"))
    commands.append("ET")
    stream = ("\n".join(commands) + "\n").encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, item in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{number} 0 obj\n".encode("ascii"))
        payload.extend(item)
        payload.extend(b"\nendobj\n")
    xref = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(payload)


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def create_fixtures(root: Path) -> dict[str, Path]:
    fixtures = root / "fixtures"
    fixtures.mkdir()

    private_text = fixtures / "dati-sintetici.txt"
    private_text.write_text(
        "Scheda sintetica di Mario Rossi.\n"
        "Email: mario.rossi@example.test\n"
        "Telefono: 333 1234567\n"
        "Data: 12/03/1985\n"
        "IBAN: IT60X0542811101000000123456\n",
        encoding="utf-8",
    )

    image_path = fixtures / "scansione-sintetica.png"
    image = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(image)
    regular_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if regular_path.is_file() and bold_path.is_file():
        regular = ImageFont.truetype(str(regular_path), 52)
        bold = ImageFont.truetype(str(bold_path), 72)
    else:
        regular = ImageFont.load_default(size=52)
        bold = ImageFont.load_default(size=72)
    draw.text((90, 90), "PRIVACY STUDIO", font=bold, fill="#111111")
    draw.text(
        (90, 250),
        "Documento OCR sintetico",
        font=regular,
        fill="#111111",
    )
    draw.text(
        (90, 350),
        "Questa pagina contiene testo italiano leggibile.",
        font=regular,
        fill="#111111",
    )
    draw.text(
        (90, 450),
        "Numero pratica: 2026-0729",
        font=regular,
        fill="#111111",
    )
    draw.text(
        (90, 550),
        "Email: lucia.bianchi@example.test",
        font=regular,
        fill="#111111",
    )
    draw.text(
        (90, 650),
        "Telefono: 347 7654321",
        font=regular,
        fill="#111111",
    )
    image.save(image_path)

    pdf_path = fixtures / "documento-sintetico.pdf"
    write_text_pdf(
        pdf_path,
        [
            ("DOCUMENTO DI PROVA PRIVACY STUDIO", 20),
            ("Conversione locale con Microsoft MarkItDown.", 12),
            ("Nessun documento personale viene usato in questo test.", 12),
        ],
    )

    audio_path = fixtures / "audio-sintetico.wav"
    sample_rate = 16_000
    duration = 2.5
    samples = int(sample_rate * duration)
    with wave.open(str(audio_path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        frames = bytearray()
        for index in range(samples):
            t = index / sample_rate
            envelope = min(1.0, t * 8, (duration - t) * 8)
            value = int(
                5_000
                * max(0.0, envelope)
                * (
                    math.sin(2 * math.pi * 220 * t)
                    + 0.35 * math.sin(2 * math.pi * 440 * t)
                )
            )
            frames.extend(value.to_bytes(2, "little", signed=True))
        output.writeframes(frames)

    return {
        "private": private_text,
        "image": image_path,
        "pdf": pdf_path,
        "audio": audio_path,
    }


@contextmanager
def test_server(root: Path):
    port = free_port()
    token = secrets.token_urlsafe(48)
    log_path = root / "server.log"
    environment = os.environ.copy()
    environment.update(
        {
            "PRIVACY_STUDIO_TOKEN": token,
            "PRIVACY_STUDIO_PORT": str(port),
            "PRIVACY_STUDIO_DATA": str(root / "data"),
            "PRIVACY_STUDIO_OUTPUTS": str(root / "outputs"),
            "PYTHONUNBUFFERED": "1",
        }
    )
    managed_hf = APP_DIR / "models" / "huggingface"
    managed_opf = (
        managed_hf
        / "hub"
        / "models--openai--privacy-filter"
        / "snapshots"
        / OPF_REVISION
        / "original"
    )
    if managed_hf.is_dir():
        environment["HF_HOME"] = str(managed_hf)
    if (managed_opf / "model.safetensors").is_file():
        environment["OPF_CHECKPOINT"] = str(managed_opf)
    guard = str(APP_DIR / "runtime_guard")
    current_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        guard + os.pathsep + current_pythonpath if current_pythonpath else guard
    )
    native_guard = APP_DIR / "bin" / "libprivacy_studio_netguard.so"
    if sys.platform.startswith("linux") and native_guard.is_file():
        environment["LD_PRELOAD"] = str(native_guard)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-access-log",
            ],
            cwd=APP_DIR,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        base_url = f"http://127.0.0.1:{port}"
        for _ in range(120):
            if process.poll() is not None:
                break
            try:
                if httpx.get(f"{base_url}/health", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.25)
        else:
            process.terminate()
            raise RuntimeError("Timeout durante l’avvio del server di test.")
        if process.poll() is not None:
            raise RuntimeError(
                "Server di test non avviato:\n"
                + log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
            )
        try:
            yield base_url, token, root
        finally:
            process.terminate()
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def submit_job(
    client: httpx.Client,
    base_url: str,
    source: Path,
    operation: str,
    engine: str,
    *,
    timeout_seconds: int,
    extra: dict[str, str] | None = None,
) -> dict:
    data = {"operation": operation, "engine": engine, **(extra or {})}
    with source.open("rb") as handle:
        response = client.post(
            f"{base_url}/api/jobs",
            data=data,
            files={"files": (source.name, handle, "application/octet-stream")},
            timeout=120,
        )
    response.raise_for_status()
    job_id = response.json()["jobs"][0]["id"]
    deadline = time.monotonic() + timeout_seconds
    last_stage = ""
    while time.monotonic() < deadline:
        job = (
            client.get(
                f"{base_url}/api/jobs/{job_id}",
                timeout=30,
            )
            .raise_for_status()
            .json()
        )
        stage = str(job.get("stage", ""))
        if stage != last_stage:
            print(f"[{operation}/{engine}] {stage}", flush=True)
            last_stage = stage
        if job["status"] == "completed":
            return job
        if job["status"] == "failed":
            raise RuntimeError(f"{operation}/{engine} fallito: {job.get('error')}")
        time.sleep(0.75)
    raise TimeoutError(f"Timeout per {operation}/{engine}.")


def require_text(path: Path, needles: tuple[str, ...]) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.casefold()
    if not any(needle.casefold() in lowered for needle in needles):
        raise AssertionError(f"Contenuto inatteso in {path.name}: {text[:400]!r}")
    return text


def run_smoke(
    root: Path,
    *,
    core_only: bool,
    skip_heavy: bool,
    skip_glm: bool,
) -> dict:
    fixtures = create_fixtures(root)
    results: dict[str, dict] = {}
    with (
        test_server(root) as (base_url, token, test_root),
        httpx.Client(
            headers={"X-Privacy-Studio-Token": token},
            timeout=60,
        ) as client,
    ):
        unauthorized = httpx.get(
            f"{base_url}/api/status",
            timeout=10,
        )
        if unauthorized.status_code != 401:
            raise AssertionError("L’API accetta richieste senza chiave.")

        browser = httpx.Client(follow_redirects=False, timeout=30)
        login = browser.get(f"{base_url}/", params={"token": token})
        if login.status_code != 303 or "ps_token=" not in login.headers.get(
            "set-cookie", ""
        ):
            raise AssertionError("Il login locale via launcher non funziona.")
        page = browser.get(f"{base_url}/")
        if (
            page.status_code != 200
            or "Privacy Studio" not in page.text
            or 'data-language="it"' not in page.text
            or 'data-language="en"' not in page.text
        ):
            raise AssertionError("L’interfaccia autenticata non è disponibile.")
        browser.close()

        status = client.get(f"{base_url}/api/status").raise_for_status().json()
        not_ready = [
            name
            for name, details in status["engines"].items()
            if not details["ready"] or not details["model_ready"]
        ]
        if core_only:
            markitdown = status["engines"]["markitdown"]
            if not markitdown["ready"] or not markitdown["model_ready"]:
                raise AssertionError("Microsoft MarkItDown non è pronto.")
        elif not_ready:
            raise AssertionError(f"Motori non pronti: {not_ready}")

        converted = submit_job(
            client,
            base_url,
            fixtures["pdf"],
            "convert",
            "markitdown",
            timeout_seconds=180,
        )
        require_text(
            Path(converted["output_path"]),
            ("DOCUMENTO DI PROVA", "PRIVACY STUDIO"),
        )
        results["markitdown"] = converted

        if core_only:
            return {
                "local_only": status["local_only"],
                "bind": status["bind"],
                "engines": sorted(results),
                "output_root": str(test_root / "outputs"),
            }

        encrypted = submit_job(
            client,
            base_url,
            fixtures["private"],
            "vault_encrypt",
            "markitdown",
            timeout_seconds=180,
            extra={"password": "test-locale-Privacy-Studio-2026"},
        )
        encrypted_path = Path(encrypted["output_path"])
        if not encrypted_path.is_file():
            raise AssertionError("Il volume Picocrypt non è stato creato.")
        results["vault_encrypt"] = encrypted

        decrypted_response = client.post(
            f"{base_url}/api/vault/{encrypted_path.name}/decrypt",
            data={"password": "test-locale-Privacy-Studio-2026"},
        )
        decrypted_response.raise_for_status()
        decrypt_job_id = decrypted_response.json()["job"]["id"]
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            decrypted = (
                client.get(f"{base_url}/api/jobs/{decrypt_job_id}")
                .raise_for_status()
                .json()
            )
            if decrypted["status"] == "completed":
                break
            if decrypted["status"] == "failed":
                raise RuntimeError(f"Decifratura fallita: {decrypted.get('error')}")
            time.sleep(0.5)
        else:
            raise TimeoutError("Timeout decifratura Picocrypt.")
        if file_sha256(Path(decrypted["output_path"])) != file_sha256(
            fixtures["private"]
        ):
            raise AssertionError("Il file decifrato non coincide con l’originale.")
        results["vault_decrypt"] = decrypted

        anonymized = submit_job(
            client,
            base_url,
            fixtures["private"],
            "anonymize",
            "privacy_filter",
            timeout_seconds=900,
            extra={"include_dates": "true"},
        )
        anonymized_text = Path(anonymized["output_path"]).read_text(encoding="utf-8")
        if (
            "mario.rossi@example.test" in anonymized_text
            or "333 1234567" in anonymized_text
            or "[EMAIL_" not in anonymized_text
        ):
            raise AssertionError("L’anonimizzazione sintetica è incompleta.")
        results["privacy_filter"] = anonymized

        anonymized_rizzo = submit_job(
            client,
            base_url,
            fixtures["private"],
            "anonymize",
            "privacy_filter_rizzo",
            timeout_seconds=900,
            extra={"include_dates": "true"},
        )
        rizzo_text = Path(anonymized_rizzo["output_path"]).read_text(encoding="utf-8")
        if (
            "mario.rossi@example.test" in rizzo_text
            or "333 1234567" in rizzo_text
            or "[EMAIL_" not in rizzo_text
        ):
            raise AssertionError("L’anonimizzazione Rizzo PII 0.3B è incompleta.")
        results["privacy_filter_rizzo"] = anonymized_rizzo

        if not skip_heavy:
            paddle = submit_job(
                client,
                base_url,
                fixtures["image"],
                "ocr",
                "paddle",
                timeout_seconds=1200,
            )
            require_text(
                Path(paddle["output_path"]),
                ("PRIVACY STUDIO", "Documento OCR"),
            )
            results["paddle"] = paddle

            private_image = submit_job(
                client,
                base_url,
                fixtures["image"],
                "anonymize",
                "privacy_filter",
                timeout_seconds=1200,
                extra={"include_dates": "true"},
            )
            private_image_text = Path(private_image["output_path"]).read_text(
                encoding="utf-8"
            )
            private_image_pipeline = (
                private_image["result"]
                .get("extraction", {})
                .get("privacy_pipeline", "")
            )
            if (
                "lucia.bianchi@example.test" in private_image_text
                or "[EMAIL_" not in private_image_text
                or "PaddleOCR" not in private_image_pipeline
            ):
                raise AssertionError(
                    "La pipeline automatica immagine -> Privacy Filter è incompleta."
                )
            results["privacy_filter_image"] = private_image

            parakeet = submit_job(
                client,
                base_url,
                fixtures["audio"],
                "transcribe",
                "parakeet",
                timeout_seconds=1200,
                extra={"chunk_minutes": "2"},
            )
            if len(parakeet["result"].get("outputs", [])) != 3:
                raise AssertionError("Parakeet non ha creato i tre risultati.")
            results["parakeet"] = parakeet

            if not skip_glm:
                glm = submit_job(
                    client,
                    base_url,
                    fixtures["image"],
                    "ocr",
                    "glm",
                    timeout_seconds=1200,
                )
                require_text(
                    Path(glm["output_path"]),
                    ("PRIVACY STUDIO", "Documento OCR"),
                )
                results["glm"] = glm

        return {
            "local_only": status["local_only"],
            "bind": status["bind"],
            "engines": sorted(results),
            "output_root": str(test_root / "outputs"),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Testa autenticazione, interfaccia e conversione senza modelli AI.",
    )
    parser.add_argument(
        "--skip-heavy",
        action="store_true",
        help="Salta OCR e trascrizione, ma testa API, conversione, privacy e vault.",
    )
    parser.add_argument(
        "--skip-glm",
        action="store_true",
        help="Testa Paddle e Parakeet ma salta il lento GLM-OCR.",
    )
    args = parser.parse_args()
    try:
        with tempfile.TemporaryDirectory(prefix="privacy-studio-smoke-") as temp:
            report = run_smoke(
                Path(temp),
                core_only=args.core_only,
                skip_heavy=args.skip_heavy,
                skip_glm=args.skip_glm,
            )
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

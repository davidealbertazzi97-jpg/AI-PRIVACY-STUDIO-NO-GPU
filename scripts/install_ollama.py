#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from contextlib import suppress
from pathlib import Path

import zstandard

APP_DIR = Path(__file__).resolve().parent.parent
VERSION = "v0.32.5"
BASE_URL = f"https://github.com/ollama/ollama/releases/download/{VERSION}"
ASSETS = {
    ("Linux", "x86_64"): (
        "ollama-linux-amd64.tar.zst",
        "f7d6bdbcf71b83aa8670c4e7dc4b6936c0952fcf8b114eaf6a11cbadb9684214",
    ),
    ("Darwin", "arm64"): (
        "ollama-darwin.tgz",
        "5789dd037a86adb328c72c11fc45e6c558452d07e5b50814a8bdb7b0fbdbcd81",
    ),
    ("Windows", "AMD64"): (
        "ollama-windows-amd64.zip",
        "7c941ae084569d298062d29f8139163a3187c76dbca0479c70d085e78fd8c7bb",
    ),
}
MODEL = "glm-ocr:q8_0"
MODEL_DIGEST = "2a5a0f1a93017fc9db321ec196efb4b9bbba97c4d890df8e39429ed771f2ed25"


def download(url: str, target: Path, expected: str) -> None:
    digest = hashlib.sha256()
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Privacy-Studio-Installer/1.0"},
    )
    # URL is assembled from a fixed HTTPS release origin and a closed asset map.
    with urllib.request.urlopen(request, timeout=180) as response:  # nosec B310
        total = int(response.headers.get("Content-Length", "0"))
        received = 0
        with target.open("wb") as output:
            while block := response.read(4 * 1024 * 1024):
                output.write(block)
                digest.update(block)
                received += len(block)
                if total:
                    print(
                        f"\rOllama: {received / 1024**2:.0f}/{total / 1024**2:.0f} MiB",
                        end="",
                        flush=True,
                    )
    print()
    actual = digest.hexdigest()
    if actual != expected:
        raise RuntimeError(f"Checksum Ollama non valido: {actual}")


def safe_extract_zip(source: Path, target: Path) -> None:
    target_root = target.resolve()
    with zipfile.ZipFile(source) as archive:
        for entry in archive.infolist():
            destination = (target / entry.filename).resolve()
            if destination != target_root and target_root not in destination.parents:
                raise RuntimeError("Archivio Ollama con percorso non sicuro.")
            unix_type = (entry.external_attr >> 16) & 0o170000
            if unix_type == 0o120000:
                raise RuntimeError("Archivio Ollama con collegamento simbolico.")
            if entry.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source_file, destination.open("xb") as output:
                shutil.copyfileobj(source_file, output)


def extract(source: Path, target: Path) -> None:
    if source.suffix == ".zip":
        safe_extract_zip(source, target)
        return
    if source.name.endswith(".tar.zst"):
        with (
            source.open("rb") as compressed,
            zstandard.ZstdDecompressor().stream_reader(compressed) as reader,
            tarfile.open(fileobj=reader, mode="r|") as archive,
        ):
            archive.extractall(target, filter="data")
        return
    with tarfile.open(source, mode="r:gz") as archive:
        archive.extractall(target, filter="data")


def find_ollama(root: Path) -> Path:
    name = "ollama.exe" if os.name == "nt" else "ollama"
    preferred = (root / name, root / "bin" / name)
    for candidate in preferred:
        if candidate.is_file():
            return candidate
    matches = [path for path in root.rglob(name) if path.is_file()]
    if len(matches) != 1:
        raise RuntimeError("Impossibile individuare l’eseguibile Ollama estratto.")
    return matches[0]


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def api_ready(base_url: str) -> bool:
    try:
        # The endpoint is a fixed numeric loopback address.
        with urllib.request.urlopen(  # nosec B310
            f"{base_url}/api/tags",
            timeout=2,
        ) as response:
            json.load(response)
        return True
    except (OSError, ValueError, urllib.error.URLError):
        return False


def installed_model_digest(base_url: str) -> str | None:
    try:
        # The endpoint is a fixed numeric loopback address.
        with urllib.request.urlopen(  # nosec B310
            f"{base_url}/api/tags",
            timeout=3,
        ) as response:
            payload = json.load(response)
    except (OSError, ValueError, urllib.error.URLError):
        return None
    for entry in payload.get("models", []):
        if entry.get("name") == MODEL or entry.get("model") == MODEL:
            return str(entry.get("digest", ""))
    return None


def pull_model(executable: Path, runtime_root: Path) -> None:
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    environment = os.environ.copy()
    environment.update(
        {
            "OLLAMA_HOST": f"127.0.0.1:{port}",
            "OLLAMA_MODELS": str(APP_DIR / "models" / "ollama"),
            "OLLAMA_NOHISTORY": "1",
        }
    )
    log_path = runtime_root / "ollama-install.log"
    log = log_path.open("wb")
    server = subprocess.Popen(
        [str(executable), "serve"],
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    for _ in range(120):
        if server.poll() is not None:
            log.close()
            detail = log_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(f"Ollama non si è avviato:\n{detail[-2000:]}")
        if api_ready(base_url):
            break
        time.sleep(0.5)
    else:
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()
        raise RuntimeError("Timeout durante l’avvio locale di Ollama.")
    try:
        subprocess.run(
            [str(executable), "pull", MODEL],
            env=environment,
            check=True,
        )
        actual_digest = installed_model_digest(base_url)
        if actual_digest != MODEL_DIGEST:
            raise RuntimeError(
                f"Digest del modello {MODEL} non valido: "
                f"{actual_digest or 'non disponibile'}"
            )
    finally:
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()


def main() -> int:
    key = (platform.system(), platform.machine())
    try:
        asset, expected = ASSETS[key]
    except KeyError:
        supported = ", ".join(f"{system}/{machine}" for system, machine in ASSETS)
        raise SystemExit(
            f"Installazione Ollama non preparata per {key[0]}/{key[1]}. "
            f"Profili completi: {supported}."
        ) from None

    runtime_root = APP_DIR / "bin" / "ollama-runtime"
    existing = None
    if runtime_root.is_dir():
        with suppress(RuntimeError):
            existing = find_ollama(runtime_root)
    if existing is None:
        runtime_root.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="privacy-studio-ollama-"
        ) as temporary_name:
            temporary = Path(temporary_name)
            archive_path = temporary / asset
            extracted = temporary / "extracted"
            extracted.mkdir()
            print(f"Scarico Ollama {VERSION} per {key[0]}/{key[1]}...")
            download(f"{BASE_URL}/{asset}", archive_path, expected)
            print("Estraggo Ollama nella directory privata dell’app...")
            extract(archive_path, extracted)
            find_ollama(extracted)
            if runtime_root.exists():
                shutil.rmtree(runtime_root)
            shutil.move(str(extracted), runtime_root)
        existing = find_ollama(runtime_root)
    if os.name != "nt":
        existing.chmod(0o755)
    print(f"Ollama pronto: {existing}")
    pull_model(existing, runtime_root)
    print(f"Modello {MODEL} pronto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

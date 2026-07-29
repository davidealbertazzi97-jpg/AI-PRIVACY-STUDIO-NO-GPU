#!/usr/bin/env python3
"""Start Privacy Studio with a private local configuration on every supported OS."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PORT = 8765
OPF_REVISION = "7ffa9a043d54d1be65afb281eddf0ffbe629385b"


def config_root() -> Path:
    home = Path.home()
    if os.name == "nt":
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        return local / "Privacy Studio"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Privacy Studio"
    xdg = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")).expanduser()
    return xdg / "privacy-studio"


def model_root() -> Path:
    return APP_DIR / "models" / "ollama"


def huggingface_root() -> Path:
    return APP_DIR / "models" / "huggingface"


def opf_checkpoint() -> Path:
    return (
        huggingface_root()
        / "hub"
        / "models--openai--privacy-filter"
        / "snapshots"
        / OPF_REVISION
        / "original"
    )


def load_config() -> dict[str, Any]:
    root = config_root()
    root.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        root.chmod(0o700)
    path = root / "launcher.json"
    values: dict[str, Any] = {}
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                values = loaded
        except (OSError, ValueError):
            values = {}
    token = values.get("token")
    if not isinstance(token, str) or len(token) < 48:
        token = secrets.token_urlsafe(48)
    port = values.get("port", DEFAULT_PORT)
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        port = DEFAULT_PORT
    clean = {"token": token, "port": port}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(clean, indent=2) + "\n", encoding="utf-8")
    if os.name != "nt":
        temporary.chmod(0o600)
    os.replace(temporary, path)
    if os.name != "nt":
        path.chmod(0o600)
    return clean


def get_json(url: str, timeout: float = 1.0) -> dict[str, Any] | None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
        raise ValueError("Il launcher accetta soltanto endpoint HTTP loopback.")
    try:
        # The URL was constrained to a numeric loopback HTTP endpoint above.
        with urllib.request.urlopen(  # nosec B310
            url,
            timeout=timeout,
        ) as response:
            value = json.load(response)
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, urllib.error.URLError):
        return None


def app_is_ready(port: int) -> bool:
    value = get_json(f"http://127.0.0.1:{port}/health")
    return value is not None and value.get("app") == "privacy-studio-locale"


def token_is_authorized(port: int, token: str) -> bool:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/status",
        headers={"X-Privacy-Studio-Token": token},
    )
    try:
        # The request targets a fixed numeric loopback URL.
        with urllib.request.urlopen(  # nosec B310
            request,
            timeout=1,
        ) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def port_is_available(port: int) -> bool:
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def ollama_executable() -> Path | None:
    name = "ollama.exe" if os.name == "nt" else "ollama"
    runtime = APP_DIR / "bin" / "ollama-runtime"
    candidates = (runtime / name, runtime / "bin" / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    system = shutil.which("ollama")
    return Path(system) if system else None


def ollama_is_ready() -> bool:
    return get_json("http://127.0.0.1:11434/api/tags", timeout=2) is not None


def start_ollama(environment: dict[str, str]) -> subprocess.Popen[bytes] | None:
    executable = ollama_executable()
    if executable is None or ollama_is_ready():
        return None
    log_root = config_root()
    log_path = log_root / "ollama.log"
    log_path.touch(exist_ok=True)
    if os.name != "nt":
        log_path.chmod(0o600)
    log = log_path.open("ab")
    process = subprocess.Popen(
        [str(executable), "serve"],
        cwd=APP_DIR,
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    process._privacy_studio_log = log  # type: ignore[attr-defined]
    for _ in range(60):
        if process.poll() is not None:
            log.close()
            detail = log_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(f"Ollama non si è avviato:\n{detail[-2000:]}")
        if ollama_is_ready():
            return process
        time.sleep(0.25)
    stop_process(process)
    raise RuntimeError("Timeout durante l’avvio del motore GLM-OCR locale.")


def stop_process(process: subprocess.Popen[Any] | None) -> None:
    if process is None:
        return
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=12)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    log = getattr(process, "_privacy_studio_log", None)
    if log is not None and not log.closed:
        log.close()


def guarded_environment(token: str, port: int) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "PRIVACY_STUDIO_TOKEN": token,
            "PRIVACY_STUDIO_PORT": str(port),
            "OLLAMA_HOST": "127.0.0.1:11434",
            "OLLAMA_MODELS": str(model_root()),
            "HF_HOME": str(huggingface_root()),
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "OPF_CHECKPOINT": str(opf_checkpoint()),
            "PYTHONUNBUFFERED": "1",
        }
    )
    guard = str(APP_DIR / "runtime_guard")
    current_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        guard + os.pathsep + current_pythonpath if current_pythonpath else guard
    )
    native_guard = APP_DIR / "bin" / "libprivacy_studio_netguard.so"
    if sys.platform.startswith("linux") and native_guard.is_file():
        current_preload = environment.get("LD_PRELOAD")
        environment["LD_PRELOAD"] = str(native_guard) + (
            f":{current_preload}" if current_preload else ""
        )
    return environment


def open_app(port: int, token: str) -> None:
    url = f"http://127.0.0.1:{port}/?token={token}"
    if not webbrowser.open(url, new=1):
        print(f"Apri nel browser: {url}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Avvia Privacy Studio in locale.")
    root.add_argument(
        "--no-browser",
        action="store_true",
        help="avvia il servizio senza aprire il browser",
    )
    return root


def raise_keyboard_interrupt() -> None:
    raise KeyboardInterrupt


def main() -> int:
    args = parser().parse_args()
    config = load_config()
    token = str(config["token"])
    port = int(config["port"])
    if app_is_ready(port) and token_is_authorized(port, token):
        if not args.no_browser:
            open_app(port, token)
        print(f"Privacy Studio è già attivo su http://127.0.0.1:{port}/")
        return 0
    if not port_is_available(port):
        port = free_port()
        config["port"] = port
        path = config_root() / "launcher.json"
        path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        if os.name != "nt":
            path.chmod(0o600)

    environment = guarded_environment(token, port)
    ollama_process = start_ollama(environment)
    log_path = config_root() / "server.log"
    log_path.touch(exist_ok=True)
    if os.name != "nt":
        log_path.chmod(0o600)
    with log_path.open("ab") as log:
        server = subprocess.Popen(
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
        try:
            for _ in range(120):
                if server.poll() is not None:
                    detail = log_path.read_text(encoding="utf-8", errors="replace")
                    raise RuntimeError(
                        f"Privacy Studio non si è avviato:\n{detail[-3000:]}"
                    )
                if app_is_ready(port):
                    break
                time.sleep(0.25)
            else:
                raise RuntimeError("Timeout durante l’avvio di Privacy Studio.")
            if not args.no_browser:
                open_app(port, token)
            print(
                f"Privacy Studio è attivo su http://127.0.0.1:{port}/\n"
                "Premi Ctrl+C per arrestarlo."
            )
            server.wait()
        except KeyboardInterrupt:
            print("\nArresto Privacy Studio...")
        finally:
            stop_process(server)
            stop_process(ollama_process)
    return 0


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: raise_keyboard_interrupt())
    raise SystemExit(main())

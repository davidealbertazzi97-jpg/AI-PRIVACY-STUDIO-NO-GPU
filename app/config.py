from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent


def _venv_python(name: str) -> Path:
    if os.name == "nt":
        return APP_ROOT / name / "Scripts" / "python.exe"
    return APP_ROOT / name / "bin" / "python"


def _platform_roots() -> tuple[Path, Path, Path]:
    home = Path.home()
    if os.name == "nt":
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        data = local / "Privacy Studio"
        state = data / "state"
    elif sys.platform == "darwin":
        data = home / "Library" / "Application Support" / "Privacy Studio"
        state = home / "Library" / "Caches" / "Privacy Studio"
    else:
        data_home = Path(
            os.environ.get("XDG_DATA_HOME", home / ".local" / "share")
        ).expanduser()
        state_home = Path(
            os.environ.get("XDG_STATE_HOME", home / ".local" / "state")
        ).expanduser()
        data = data_home / "privacy-studio"
        state = state_home / "privacy-studio"
    documents = home / "Documents"
    if not documents.is_dir() and (home / "Documenti").is_dir():
        documents = home / "Documenti"
    return data, state, documents / "Privacy Studio - Results"


def _first_candidate(*paths: Path) -> Path:
    return next((path for path in paths if path.is_file()), paths[0])


@dataclass(frozen=True)
class Paths:
    app: Path
    data: Path
    inbox: Path
    work: Path
    vault: Path
    outputs: Path
    state: Path
    database: Path
    ai_python: Path
    paddle_python: Path
    picocrypt: Path
    ollama: Path

    @classmethod
    def build(cls) -> Paths:
        default_data, default_state, default_outputs = _platform_roots()
        data = Path(
            os.environ.get(
                "PRIVACY_STUDIO_DATA",
                default_data,
            )
        ).expanduser()
        outputs = Path(
            os.environ.get(
                "PRIVACY_STUDIO_OUTPUTS",
                default_outputs,
            )
        ).expanduser()
        state = Path(os.environ.get("PRIVACY_STUDIO_STATE", default_state)).expanduser()
        executable_suffix = ".exe" if os.name == "nt" else ""
        runtime_root = APP_ROOT / "bin" / "ollama-runtime"
        system_ollama = shutil.which("ollama")
        ollama_candidates = [
            runtime_root / f"ollama{executable_suffix}",
            runtime_root / "bin" / f"ollama{executable_suffix}",
        ]
        if system_ollama:
            ollama_candidates.append(Path(system_ollama))
        paths = cls(
            app=APP_ROOT,
            data=data,
            inbox=data / "inbox",
            work=data / "work",
            vault=data / "vault",
            outputs=outputs,
            state=state,
            database=data / "privacy-studio.sqlite3",
            ai_python=_venv_python(".venv-ai"),
            paddle_python=_venv_python(".venv-paddle"),
            picocrypt=APP_ROOT / "bin" / f"picocrypt{executable_suffix}",
            ollama=_first_candidate(*ollama_candidates),
        )
        paths.ensure()
        return paths

    def ensure(self) -> None:
        for path in (
            self.data,
            self.inbox,
            self.work,
            self.vault,
            self.outputs,
            self.state,
            self.picocrypt.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)
        os.chmod(self.data, 0o700)
        os.chmod(self.inbox, 0o700)
        os.chmod(self.work, 0o700)
        os.chmod(self.vault, 0o700)
        os.chmod(self.outputs, 0o700)
        os.chmod(self.state, 0o700)


PATHS = Paths.build()
ACCESS_TOKEN = os.environ.get("PRIVACY_STUDIO_TOKEN", "")
HOST = "127.0.0.1"
PORT = int(os.environ.get("PRIVACY_STUDIO_PORT", "8765"))
MAX_UPLOAD_BYTES = int(
    os.environ.get("PRIVACY_STUDIO_MAX_UPLOAD_BYTES", str(100 * 1024**3))
)

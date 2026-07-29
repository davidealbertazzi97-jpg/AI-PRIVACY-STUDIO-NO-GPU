from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent


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

    @classmethod
    def build(cls) -> Paths:
        home = Path.home()
        data = Path(
            os.environ.get(
                "PRIVACY_STUDIO_DATA",
                home / ".local" / "share" / "privacy-studio",
            )
        ).expanduser()
        outputs = Path(
            os.environ.get(
                "PRIVACY_STUDIO_OUTPUTS",
                home / "Documenti" / "Privacy Studio - Risultati",
            )
        ).expanduser()
        state = home / ".local" / "state" / "privacy-studio"
        paths = cls(
            app=APP_ROOT,
            data=data,
            inbox=data / "inbox",
            work=data / "work",
            vault=data / "vault",
            outputs=outputs,
            state=state,
            database=data / "privacy-studio.sqlite3",
            ai_python=APP_ROOT / ".venv-ai" / "bin" / "python",
            paddle_python=APP_ROOT / ".venv-paddle" / "bin" / "python",
            picocrypt=APP_ROOT / "bin" / "picocrypt",
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

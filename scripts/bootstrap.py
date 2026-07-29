#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PYTHON_VERSION = "3.12"
FULL_PROFILES = {
    ("Linux", "x86_64"): "Linux x86-64",
    ("Darwin", "arm64"): "macOS Apple Silicon",
    ("Windows", "AMD64"): "Windows x86-64",
}


def venv_python(name: str) -> Path:
    if os.name == "nt":
        return APP_DIR / name / "Scripts" / "python.exe"
    return APP_DIR / name / "bin" / "python"


def run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    printable = " ".join(command)
    print(f"\n-> {printable}", flush=True)
    subprocess.run(command, cwd=APP_DIR, env=environment, check=True)


def install_requirements(
    uv: str,
    environment_name: str,
    requirements: str,
) -> Path:
    python = venv_python(environment_name)
    if not python.is_file():
        run([uv, "venv", "--python", PYTHON_VERSION, str(APP_DIR / environment_name)])
    run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(python),
            "--requirement",
            str(APP_DIR / requirements),
        ]
    )
    return python


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Installer versionato multipiattaforma di Privacy Studio."
    )
    root.add_argument(
        "--without-glm",
        action="store_true",
        help="non scaricare Ollama e il modello GLM-OCR opzionale",
    )
    root.add_argument(
        "--core-only",
        action="store_true",
        help="installa soltanto il nucleo leggero, utile per sviluppo e CI",
    )
    root.add_argument(
        "--skip-desktop",
        action="store_true",
        help="non creare il launcher desktop Linux",
    )
    root.add_argument(
        "--dry-run",
        action="store_true",
        help="mostra il piano senza modificare il sistema",
    )
    return root


def installation_plan(
    system: str,
    machine: str,
    *,
    core_only: bool,
    without_glm: bool,
) -> dict[str, object]:
    key = (system, machine)
    return {
        "platform": FULL_PROFILES.get(key, f"{system}/{machine}"),
        "supported_full_profile": key in FULL_PROFILES,
        "python": PYTHON_VERSION,
        "components": [
            "core",
            *(
                []
                if core_only
                else [
                    "picocrypt",
                    "privacy-filter",
                    "parakeet",
                    "paddleocr",
                    *(["ollama-glm-ocr"] if not without_glm else []),
                ]
            ),
        ],
    }


def main() -> int:
    args = parser().parse_args()
    system = platform.system()
    machine = platform.machine()
    plan = installation_plan(
        system,
        machine,
        core_only=args.core_only,
        without_glm=args.without_glm,
    )
    if args.dry_run:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0
    if not args.core_only and (system, machine) not in FULL_PROFILES:
        supported = ", ".join(FULL_PROFILES.values())
        raise SystemExit(
            f"Profilo completo non supportato su {system}/{machine}. "
            f"Combinazioni supportate: {supported}."
        )

    uv = os.environ.get("PRIVACY_STUDIO_UV") or shutil.which("uv")
    if not uv:
        raise SystemExit(
            "uv non è disponibile. Avvia l’installer dalla radice del progetto."
        )

    print(json.dumps(plan, indent=2, ensure_ascii=False))
    core_python = install_requirements(uv, ".venv", "requirements-core.txt")
    expect_import = (
        "from app.wexpect_compat import import_wexpect; import_wexpect()"
        if os.name == "nt"
        else "import pexpect"
    )
    run(
        [
            str(core_python),
            "-c",
            (
                "import fastapi, imageio_ffmpeg, markitdown, pypdfium2, "
                f"uvicorn, zstandard; {expect_import}; print('Nucleo pronto')"
            ),
        ]
    )
    if args.core_only:
        print("\nInstallazione core completata.")
        return 0

    run([str(core_python), str(APP_DIR / "scripts" / "install_picocrypt.py")])

    ai_python = venv_python(".venv-ai")
    if not ai_python.is_file():
        run([uv, "venv", "--python", PYTHON_VERSION, str(APP_DIR / ".venv-ai")])
    torch_command = [
        uv,
        "pip",
        "install",
        "--python",
        str(ai_python),
    ]
    if system == "Darwin":
        torch_command.append("torch==2.13.0")
    else:
        torch_command.extend(
            [
                "torch==2.13.0+cpu",
                "--index-url",
                "https://download.pytorch.org/whl/cpu",
            ]
        )
    run(torch_command)
    run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(ai_python),
            "--requirement",
            str(APP_DIR / "requirements-ai.txt"),
        ]
    )
    run([str(ai_python), str(APP_DIR / "scripts" / "prefetch_models.py")])

    paddle_python = install_requirements(
        uv,
        ".venv-paddle",
        "requirements-paddle.txt",
    )
    run([str(paddle_python), str(APP_DIR / "scripts" / "prefetch_paddle.py")])

    if not args.without_glm:
        run([str(core_python), str(APP_DIR / "scripts" / "install_ollama.py")])

    if system == "Linux" and not args.skip_desktop:
        if shutil.which("cc"):
            run(["bash", str(APP_DIR / "scripts" / "install-netguard.sh")])
        else:
            print(
                "Nota: compilatore C assente; verrà usato il guard Python "
                "multipiattaforma."
            )
        try:
            run(["bash", str(APP_DIR / "scripts" / "install-desktop.sh")])
        except subprocess.CalledProcessError:
            print(
                "Nota: integrazione con il menu applicazioni non disponibile; "
                "usa ./start.sh."
            )

    print("\nPrivacy Studio è pronto.")
    if os.name == "nt":
        print(r"Avvio: .\start.ps1")
    else:
        print("Avvio: ./start.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

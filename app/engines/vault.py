from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from ..config import PATHS
from ..utils import Progress, safe_name


def _run_picocrypt(
    input_path: Path,
    password: str,
    *,
    decrypt: bool,
    paranoid: bool = False,
    recovery: bool = False,
) -> tuple[Path, str]:
    if not PATHS.picocrypt.is_file():
        raise RuntimeError(
            "Picocrypt CLI non è installato. Riesegui l’installer completo."
        )
    if len(password) < 10:
        raise RuntimeError(
            "Usa una password di almeno 10 caratteri; meglio una passphrase lunga."
        )
    try:
        if os.name == "nt":
            from ..wexpect_compat import import_wexpect

            expect = import_wexpect()
        else:
            import pexpect as expect
    except ImportError as exc:
        raise RuntimeError(
            "Manca il componente locale per controllare Picocrypt."
        ) from exc

    arguments: list[str] = []
    if not decrypt and paranoid:
        arguments.append("-p")
    if not decrypt and recovery:
        arguments.append("-r")
    # Prefix with an explicit relative path so a filename beginning with "-"
    # cannot be interpreted as a Picocrypt command-line option.
    arguments.append(os.path.join(".", input_path.name))
    spawn_options: dict[str, Any] = {
        "cwd": str(input_path.parent),
        "timeout": None,
        "echo": False,
    }
    if os.name == "nt":
        # Wexpect uses the Windows console code page instead of Pexpect's
        # encoding argument.
        spawn_options["codepage"] = 65001
    else:
        spawn_options["encoding"] = "utf-8"
    child = expect.spawn(
        str(PATHS.picocrypt),
        arguments,
        **spawn_options,
    )
    log: list[str] = []
    try:
        child.expect_exact("Password: ")
        log.append(child.before or "")
        child.sendline(password)
        if not decrypt:
            child.expect_exact("Confirm: ")
            log.append(child.before or "")
            child.sendline(password)
        child.expect(expect.EOF)
        log.append(child.before or "")
    finally:
        child.close()
    if child.exitstatus not in (0, None):
        detail = " ".join(log)[-1200:]
        if "Incorrect password" in detail:
            raise RuntimeError("Password errata o volume non valido.")
        raise RuntimeError(f"Picocrypt non ha completato l’operazione: {detail}")

    output = (
        input_path.with_suffix("")
        if decrypt
        else input_path.with_name(input_path.name + ".pcv")
    )
    if not output.is_file():
        detail = " ".join(log)[-1200:]
        raise RuntimeError(f"Picocrypt non ha creato il volume: {detail}")
    return output, " ".join(log)


def encrypt_to_vault(
    path: Path,
    password: str,
    progress: Progress,
    *,
    paranoid: bool = False,
    recovery: bool = False,
    kind: str = "file",
) -> tuple[Path, dict[str, Any]]:
    progress(0.08, "Preparazione volume Picocrypt")
    stage = Path(tempfile.mkdtemp(prefix="picocrypt-", dir=PATHS.work))
    try:
        staged = stage / safe_name(path.name)
        shutil.copy2(path, staged)
        progress(0.18, "Cifratura Picocrypt in corso")
        encrypted, _ = _run_picocrypt(
            staged,
            password,
            decrypt=False,
            paranoid=paranoid,
            recovery=recovery,
        )
        token = os.urandom(4).hex()
        if kind == "group":
            target_name = f"{safe_name(path.stem)}-{token}.vault.zip.pcv"
        elif kind == "dictionary":
            target_name = f"{safe_name(path.stem)}-{token}.dizionario.json.pcv"
        else:
            target_name = f"{path.stem}-{token}{path.suffix}.pcv"
        target = PATHS.vault / safe_name(target_name)
        shutil.move(encrypted, target)
        os.chmod(target, 0o600)
    finally:
        # This directory contains a plaintext copy. Remove it after every exit,
        # including incorrect passwords and interrupted subprocesses.
        shutil.rmtree(stage, ignore_errors=True)
    progress(0.96, "Volume salvato nella cassaforte")
    return target, {
        "engine": "Picocrypt CLI 1.49",
        "format": "pcv",
        "paranoid": paranoid,
        "reed_solomon": recovery,
        "kind": kind,
        "vault_name": target.name,
    }


def decrypt_group_from_vault(
    path: Path,
    password: str,
    output_dir: Path,
    progress: Progress,
) -> tuple[Path, dict[str, Any]]:
    """Decrypt one Picocrypt-protected ZIP and safely unpack its documents."""
    if not path.name.endswith(".vault.zip.pcv"):
        raise RuntimeError(
            "Per aprire un vault di gruppo serve un volume .vault.zip.pcv."
        )
    progress(0.08, "Preparazione vault locale")
    stage = Path(tempfile.mkdtemp(prefix="picocrypt-vault-", dir=PATHS.work))
    extracted: list[str] = []
    try:
        staged = stage / safe_name(path.name)
        shutil.copy2(path, staged)
        progress(0.18, "Decifratura vault locale in corso")
        decrypted, _ = _run_picocrypt(staged, password, decrypt=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        used: set[str] = set()
        with zipfile.ZipFile(decrypted) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000:
                    raise RuntimeError(
                        "Il vault contiene un collegamento non consentito."
                    )
                name = safe_name(Path(info.filename).name)
                if not name:
                    continue
                target_name = name
                if target_name in used or (output_dir / target_name).exists():
                    target_name = (
                        f"{Path(name).stem}-{os.urandom(3).hex()}{Path(name).suffix}"
                    )
                used.add(target_name)
                target = output_dir / target_name
                with archive.open(info) as source, target.open("xb") as destination:
                    shutil.copyfileobj(source, destination, length=8 * 1024 * 1024)
                os.chmod(target, 0o600)
                extracted.append(target.name)
        manifest = output_dir / "VAULT-CONTENTS.txt"
        manifest.write_text(
            "Documenti estratti dal vault locale\n\n" + "\n".join(extracted) + "\n",
            encoding="utf-8",
        )
        os.chmod(manifest, 0o600)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    progress(0.96, "Documenti del vault estratti")
    return manifest, {
        "engine": "Picocrypt CLI 1.49",
        "format": "vault.zip.pcv",
        "files": extracted,
    }


def decrypt_from_vault(
    path: Path,
    password: str,
    output_dir: Path,
    progress: Progress,
) -> tuple[Path, dict[str, Any]]:
    if path.suffix.lower() != ".pcv":
        raise RuntimeError("Per decifrare serve un volume Picocrypt .pcv.")
    progress(0.08, "Preparazione volume Picocrypt")
    stage = Path(tempfile.mkdtemp(prefix="picocrypt-", dir=PATHS.work))
    try:
        staged = stage / safe_name(path.name)
        shutil.copy2(path, staged)
        progress(0.18, "Decifratura Picocrypt in corso")
        decrypted, _ = _run_picocrypt(staged, password, decrypt=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / safe_name(decrypted.name)
        if target.exists():
            target = output_dir / f"{target.stem}-{os.urandom(3).hex()}{target.suffix}"
        shutil.move(decrypted, target)
    finally:
        # A successful decryption creates plaintext in this staging directory.
        # Remove it even if a later filesystem operation fails.
        shutil.rmtree(stage, ignore_errors=True)
    progress(0.96, "File decifrato")
    return target, {
        "engine": "Picocrypt CLI 1.49",
        "format": "pcv",
        "decrypted_name": target.name,
    }

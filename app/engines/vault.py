from __future__ import annotations

import os
import shutil
import tempfile
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
            "Picocrypt CLI non è installato. Esegui scripts/install-picocrypt.sh."
        )
    if len(password) < 10:
        raise RuntimeError(
            "Usa una password di almeno 10 caratteri; meglio una passphrase lunga."
        )
    try:
        import pexpect
    except ImportError as exc:
        raise RuntimeError("Manca il componente locale pexpect.") from exc

    arguments: list[str] = []
    if not decrypt and paranoid:
        arguments.append("-p")
    if not decrypt and recovery:
        arguments.append("-r")
    arguments.append(input_path.name)
    child = pexpect.spawn(
        str(PATHS.picocrypt),
        arguments,
        cwd=str(input_path.parent),
        encoding="utf-8",
        timeout=None,
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
        child.expect(pexpect.EOF)
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
) -> tuple[Path, dict[str, Any]]:
    progress(0.08, "Preparazione volume Picocrypt")
    stage = Path(tempfile.mkdtemp(prefix="picocrypt-", dir=PATHS.work))
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
    target_name = f"{path.stem}-{os.urandom(4).hex()}{path.suffix}.pcv"
    target = PATHS.vault / safe_name(target_name)
    shutil.move(encrypted, target)
    os.chmod(target, 0o600)
    shutil.rmtree(stage, ignore_errors=True)
    progress(0.96, "Volume salvato nella cassaforte")
    return target, {
        "engine": "Picocrypt CLI 1.49",
        "format": "pcv",
        "paranoid": paranoid,
        "reed_solomon": recovery,
        "vault_name": target.name,
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
    staged = stage / safe_name(path.name)
    shutil.copy2(path, staged)
    progress(0.18, "Decifratura Picocrypt in corso")
    decrypted, _ = _run_picocrypt(staged, password, decrypt=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / safe_name(decrypted.name)
    if target.exists():
        target = output_dir / f"{target.stem}-{os.urandom(3).hex()}{target.suffix}"
    shutil.move(decrypted, target)
    shutil.rmtree(stage, ignore_errors=True)
    progress(0.96, "File decifrato")
    return target, {
        "engine": "Picocrypt CLI 1.49",
        "format": "pcv",
        "decrypted_name": target.name,
    }

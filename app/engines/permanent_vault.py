from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import shutil
import struct
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..config import PATHS
from ..utils import safe_name

VAULT_VERSION = 1
HEADER_NAME = "vault.json"
INDEX_NAME = "index.enc"
OBJECTS_NAME = "objects"
MAGIC = b"PSV1"
CHUNK_SIZE = 4 * 1024 * 1024
SESSION_TTL_SECONDS = 30 * 60
KDF_N = 2**15
KDF_R = 8
KDF_P = 1


class PermanentVaultError(RuntimeError):
    pass


def _crypto() -> tuple[Any, Any]:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    except ImportError as exc:
        raise PermanentVaultError(
            "Il vault permanente richiede il pacchetto locale cryptography."
        ) from exc
    return AESGCM, Scrypt


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _validate_password(password: str) -> None:
    if not isinstance(password, str) or len(password) < 10:
        raise PermanentVaultError(
            "Usa una passphrase di almeno 10 caratteri per il vault permanente."
        )


def _atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    try:
        temporary.write_bytes(data)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        os.chmod(path, mode)
    finally:
        temporary.unlink(missing_ok=True)


def _is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _safe_vault_id(value: str) -> bool:
    return len(value) == 32 and all(char in "0123456789abcdef" for char in value)


@dataclass(frozen=True)
class VaultIdentity:
    vault_id: str
    created_at: str
    chunk_size: int


class PersistentVault:
    """Incremental encrypted document vault managed by Privacy Studio.

    The vault stores random object names and an AES-GCM encrypted index. Each
    object is chunk-encrypted, so adding or deleting one document does not
    require decrypting or rebuilding the other documents.
    """

    def __init__(self, root: Path):
        self.root = root
        self.objects = root / OBJECTS_NAME
        self.header_path = root / HEADER_NAME
        self.index_path = root / INDEX_NAME
        self._lock = threading.RLock()

    @property
    def exists(self) -> bool:
        return self.header_path.is_file() and self.index_path.is_file()

    def _header(self) -> dict[str, Any]:
        if not self.header_path.is_file():
            raise PermanentVaultError("Il vault permanente non è ancora creato.")
        try:
            value = json.loads(self.header_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PermanentVaultError("L’intestazione del vault non è valida.") from exc
        if (
            not isinstance(value, dict)
            or value.get("version") != VAULT_VERSION
            or not _safe_vault_id(str(value.get("vault_id", "")))
        ):
            raise PermanentVaultError("Formato del vault permanente non supportato.")
        return value

    @staticmethod
    def _derive_key(password: str, header: dict[str, Any]) -> bytes:
        _validate_password(password)
        AESGCM, Scrypt = _crypto()
        del AESGCM
        try:
            salt = base64.b64decode(str(header["salt"]), validate=True)
            n = int(header["kdf"]["n"])
            r = int(header["kdf"]["r"])
            p = int(header["kdf"]["p"])
        except (KeyError, TypeError, ValueError) as exc:
            raise PermanentVaultError("Parametri KDF del vault non validi.") from exc
        if (
            len(salt) < 16
            or n < 2**14
            or n > 2**20
            or r < 1
            or r > 32
            or p < 1
            or p > 8
        ):
            raise PermanentVaultError("Parametri KDF del vault non sicuri.")
        return Scrypt(salt=salt, length=32, n=n, r=r, p=p).derive(
            password.encode("utf-8")
        )

    def _aad(self, header: dict[str, Any], suffix: str) -> bytes:
        return f"privacy-studio-vault:{header['vault_id']}:{suffix}".encode()

    def _load_index(self, key: bytes, header: dict[str, Any]) -> list[dict[str, Any]]:
        AESGCM, _ = _crypto()
        try:
            encrypted = self.index_path.read_bytes()
            nonce, ciphertext = encrypted[:12], encrypted[12:]
            raw = AESGCM(key).decrypt(nonce, ciphertext, self._aad(header, "index"))
            value = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise PermanentVaultError(
                "Password errata o indice del vault non valido."
            ) from exc
        if not isinstance(value, dict) or not isinstance(value.get("files"), list):
            raise PermanentVaultError("Indice del vault non valido.")
        entries: list[dict[str, Any]] = []
        for entry in value["files"]:
            if not isinstance(entry, dict):
                raise PermanentVaultError("Indice del vault non valido.")
            entry_id = str(entry.get("id", ""))
            digest = str(entry.get("sha256", ""))
            if (
                not _safe_vault_id(entry_id)
                or not isinstance(entry.get("name"), str)
                or not isinstance(entry.get("size"), int)
                or entry["size"] < 0
                or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest)
            ):
                raise PermanentVaultError("Indice del vault non valido.")
            entries.append(entry)
        return entries

    def _save_index(
        self,
        key: bytes,
        header: dict[str, Any],
        entries: list[dict[str, Any]],
    ) -> None:
        AESGCM, _ = _crypto()
        nonce = secrets.token_bytes(12)
        payload = json.dumps(
            {"version": VAULT_VERSION, "updated_at": _now(), "files": entries},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        encrypted = nonce + AESGCM(key).encrypt(
            nonce, payload, self._aad(header, "index")
        )
        _atomic_write(self.index_path, encrypted)

    def create(self, password: str) -> dict[str, Any]:
        _validate_password(password)
        with self._lock:
            if self.exists or (self.root.is_dir() and any(self.root.iterdir())):
                raise PermanentVaultError(
                    "Esiste già un vault permanente in questa posizione."
                )
            self.root.mkdir(parents=True, exist_ok=True)
            self.objects.mkdir(parents=True, exist_ok=True)
            self.root.chmod(0o700)
            self.objects.chmod(0o700)
            vault_id = secrets.token_hex(16)
            header = {
                "version": VAULT_VERSION,
                "vault_id": vault_id,
                "created_at": _now(),
                "salt": base64.b64encode(secrets.token_bytes(16)).decode("ascii"),
                "kdf": {"name": "scrypt", "n": KDF_N, "r": KDF_R, "p": KDF_P},
                "chunk_size": CHUNK_SIZE,
            }
            key = self._derive_key(password, header)
            _atomic_write(
                self.header_path,
                json.dumps(header, indent=2).encode("utf-8"),
            )
            self._save_index(key, header, [])
            return self._metadata(header)

    def unlock(
        self, password: str
    ) -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
        with self._lock:
            header = self._header()
            key = self._derive_key(password, header)
            entries = self._load_index(key, header)
            return key, header, entries

    @staticmethod
    def _metadata(header: dict[str, Any]) -> dict[str, Any]:
        return {
            "vault_id": header["vault_id"],
            "created_at": header["created_at"],
            "chunk_size": header["chunk_size"],
            "kdf": "scrypt + AES-256-GCM",
        }

    def metadata(self, password: str) -> dict[str, Any]:
        _, header, _ = self.unlock(password)
        return self._metadata(header)

    def list_files(
        self, key: bytes, header: dict[str, Any], query: str = ""
    ) -> list[dict[str, Any]]:
        entries = self._load_index(key, header)
        needle = query.casefold().strip()
        return [
            {
                "id": entry["id"],
                "name": entry["name"],
                "size": entry["size"],
                "sha256": entry["sha256"],
                "created_at": entry["created_at"],
                "updated_at": entry["updated_at"],
            }
            for entry in entries
            if not needle or needle in str(entry.get("name", "")).casefold()
        ]

    def store_file(
        self,
        key: bytes,
        header: dict[str, Any],
        source: Path,
        original_name: str,
    ) -> dict[str, Any]:
        if not source.is_file():
            raise PermanentVaultError("Il documento da archiviare non esiste.")
        entry_id = secrets.token_hex(16)
        temporary = self.objects / f".{entry_id}.part"
        target = self.objects / f"{entry_id}.blob"
        digest = hashlib.sha256()
        size = 0
        AESGCM, _ = _crypto()
        try:
            with source.open("rb") as reader, temporary.open("wb") as writer:
                writer.write(MAGIC)
                while chunk := reader.read(CHUNK_SIZE):
                    digest.update(chunk)
                    size += len(chunk)
                    nonce = secrets.token_bytes(12)
                    encrypted = AESGCM(key).encrypt(
                        nonce,
                        chunk,
                        self._aad(header, f"file:{entry_id}:{size}"),
                    )
                    writer.write(struct.pack(">I", len(encrypted)))
                    writer.write(nonce)
                    writer.write(encrypted)
            os.chmod(temporary, 0o600)
            os.replace(temporary, target)
            os.chmod(target, 0o600)
            now = _now()
            entry = {
                "id": entry_id,
                "name": safe_name(original_name),
                "size": size,
                "sha256": digest.hexdigest(),
                "created_at": now,
                "updated_at": now,
            }
            with self._lock:
                entries = self._load_index(key, header)
                entries.append(entry)
                self._save_index(key, header, entries)
            return entry
        except Exception:
            target.unlink(missing_ok=True)
            raise
        finally:
            temporary.unlink(missing_ok=True)

    def _entry(
        self, key: bytes, header: dict[str, Any], entry_id: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if not _safe_vault_id(entry_id):
            raise PermanentVaultError("Documento del vault non valido.")
        entries = self._load_index(key, header)
        for entry in entries:
            if entry.get("id") == entry_id:
                return entries, entry
        raise PermanentVaultError("Documento non trovato nel vault permanente.")

    def restore_file(
        self,
        key: bytes,
        header: dict[str, Any],
        entry_id: str,
        target: Path,
    ) -> dict[str, Any]:
        _, entry = self._entry(key, header, entry_id)
        blob = self.objects / f"{entry_id}.blob"
        if not blob.is_file():
            raise PermanentVaultError("Il contenuto cifrato del documento non esiste.")
        AESGCM, _ = _crypto()
        target.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(target.parent, 0o700)
        digest = hashlib.sha256()
        size = 0
        try:
            with blob.open("rb") as reader, target.open("xb") as writer:
                if reader.read(len(MAGIC)) != MAGIC:
                    raise PermanentVaultError(
                        "Formato del documento cifrato non valido."
                    )
                while True:
                    raw_length = reader.read(4)
                    if not raw_length:
                        break
                    if len(raw_length) != 4:
                        raise PermanentVaultError("Blocco cifrato incompleto.")
                    length = struct.unpack(">I", raw_length)[0]
                    if length < 16 or length > CHUNK_SIZE + 16:
                        raise PermanentVaultError(
                            "Dimensione blocco cifrato non valida."
                        )
                    nonce = reader.read(12)
                    ciphertext = reader.read(length)
                    if len(nonce) != 12 or len(ciphertext) != length:
                        raise PermanentVaultError("Blocco cifrato incompleto.")
                    plaintext_size = length - 16
                    chunk = AESGCM(key).decrypt(
                        nonce,
                        ciphertext,
                        self._aad(
                            header,
                            f"file:{entry_id}:{size + plaintext_size}",
                        ),
                    )
                    if len(chunk) != plaintext_size:
                        raise PermanentVaultError("Blocco decifrato non valido.")
                    writer.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                if size != int(entry["size"]) or digest.hexdigest() != entry["sha256"]:
                    raise PermanentVaultError(
                        "Verifica integrità del documento fallita."
                    )
            os.chmod(target, 0o600)
            return {"name": entry["name"], "size": size, "sha256": digest.hexdigest()}
        except Exception:
            target.unlink(missing_ok=True)
            raise

    def delete_file(self, key: bytes, header: dict[str, Any], entry_id: str) -> None:
        with self._lock:
            entries, _ = self._entry(key, header, entry_id)
            remaining = [entry for entry in entries if entry.get("id") != entry_id]
            self._save_index(key, header, remaining)
            (self.objects / f"{entry_id}.blob").unlink(missing_ok=True)

    def backup(self, backup_root: Path, header: dict[str, Any]) -> dict[str, Any]:
        backup_root = backup_root.expanduser().resolve()
        source = self.root.resolve()
        if _is_inside(backup_root, source) or _is_inside(source, backup_root):
            raise PermanentVaultError(
                "La cartella di backup non può essere dentro o contenere "
                "il vault locale."
            )
        backup_root.mkdir(parents=True, exist_ok=True)
        backup_root.chmod(0o700)
        folder = backup_root / (
            f"privacy-studio-vault-{header['vault_id']}-{int(time.time())}"
        )
        temporary = backup_root / f".{folder.name}.{secrets.token_hex(6)}.tmp"
        try:
            shutil.copytree(source, temporary, copy_function=shutil.copy2)
            for directory in [temporary, *temporary.rglob("*")]:
                if directory.is_dir():
                    directory.chmod(0o700)
                else:
                    directory.chmod(0o600)
            os.replace(temporary, folder)
            return {"path": str(folder), "name": folder.name}
        finally:
            shutil.rmtree(temporary, ignore_errors=True)

    def restore_backup(self, backup: Path) -> dict[str, Any]:
        backup = backup.expanduser().resolve()
        if not backup.is_dir() or not (backup / HEADER_NAME).is_file():
            raise PermanentVaultError("Backup del vault non valido.")
        if self.exists or (self.root.exists() and any(self.root.iterdir())):
            raise PermanentVaultError(
                "Il vault locale contiene già dati: bloccalo e rimuovilo "
                "prima del ripristino."
            )
        self.root.mkdir(parents=True, exist_ok=True)
        self.root.chmod(0o700)
        temporary = self.root.with_name(
            f".{self.root.name}.restore-{secrets.token_hex(6)}"
        )
        try:
            shutil.copytree(backup, temporary, copy_function=shutil.copy2)
            for directory in [temporary, *temporary.rglob("*")]:
                if directory.is_dir():
                    directory.chmod(0o700)
                else:
                    directory.chmod(0o600)
            for child in temporary.iterdir():
                os.replace(child, self.root / child.name)
            return self._metadata(self._header())
        finally:
            shutil.rmtree(temporary, ignore_errors=True)

    def merge_backup(self, backup: Path, password: str) -> dict[str, Any]:
        source = PersistentVault(backup)
        backup_key, backup_header, backup_entries = source.unlock(password)
        local_key, local_header, local_entries = self.unlock(password)
        if local_header["vault_id"] != backup_header["vault_id"]:
            raise PermanentVaultError(
                "Il backup appartiene a un vault diverso da quello locale."
            )
        local_ids = {entry.get("id") for entry in local_entries}
        added: list[dict[str, Any]] = []
        for entry in backup_entries:
            entry_id = str(entry.get("id", ""))
            if entry_id in local_ids:
                continue
            if not _safe_vault_id(entry_id):
                raise PermanentVaultError("Il backup contiene un documento non valido.")
            source_blob = source.objects / f"{entry_id}.blob"
            target_blob = self.objects / f"{entry_id}.blob"
            if not source_blob.is_file():
                raise PermanentVaultError("Il backup contiene un documento incompleto.")
            temporary = self.objects / f".{entry_id}.merge"
            shutil.copy2(source_blob, temporary)
            os.chmod(temporary, 0o600)
            os.replace(temporary, target_blob)
            added.append(entry)
        if added:
            self._save_index(local_key, local_header, local_entries + added)
        del backup_key
        return {"metadata": self._metadata(local_header), "added": len(added)}


@dataclass
class _Session:
    key: bytes
    header: dict[str, Any]
    touched: float


class VaultSessions:
    def __init__(self, vault: PersistentVault):
        self.vault = vault
        self._values: dict[str, _Session] = {}
        self._lock = threading.Lock()

    def open(self, password: str) -> tuple[str, dict[str, Any]]:
        key, header, _ = self.vault.unlock(password)
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._values[token] = _Session(key, header, time.monotonic())
        return token, self.vault._metadata(header)

    def get(self, token: str | None) -> _Session:
        if not token:
            raise PermanentVaultError("Sblocca prima il vault permanente.")
        with self._lock:
            session = self._values.get(token)
            if session is None or (
                time.monotonic() - session.touched > SESSION_TTL_SECONDS
            ):
                self._values.pop(token, None)
                raise PermanentVaultError(
                    "La sessione del vault è scaduta: sbloccalo di nuovo."
                )
            session.touched = time.monotonic()
            return session

    def clear(self, token: str | None) -> None:
        if token:
            with self._lock:
                self._values.pop(token, None)

    def clear_all(self) -> None:
        with self._lock:
            self._values.clear()


PERMANENT_VAULT = PersistentVault(PATHS.permanent_vault)
VAULT_SESSIONS = VaultSessions(PERMANENT_VAULT)

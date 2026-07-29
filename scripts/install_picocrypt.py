#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import platform
import urllib.request
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
VERSION = "1.49"
BASE_URL = f"https://github.com/Picocrypt/CLI/releases/download/{VERSION}"
LICENSE_URL = f"https://raw.githubusercontent.com/Picocrypt/CLI/{VERSION}/LICENSE"
LICENSE_SHA256 = "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986"
ASSETS = {
    ("Linux", "x86_64"): (
        "picocrypt-linux-amd64",
        "9ecd432f96374944ae271b1a40cc21d844f6a6f7d6f115a3777338da3772a3e5",
    ),
    ("Linux", "aarch64"): (
        "picocrypt-linux-arm64",
        "bdbdee514a145d11940e6fa4fd1a783df2af02461f1dacc91d7654acdac31d1d",
    ),
    ("Darwin", "x86_64"): (
        "picocrypt-macos-amd64",
        "0c0984acb8d68fab207d41d802a43777b68bc01d4ab9db7b0486db35538b4440",
    ),
    ("Darwin", "arm64"): (
        "picocrypt-macos-arm64",
        "b22cf1d66a2c4291f7c028bf51ce7569688e4ca0eb2fb91b6a6f12616f67c979",
    ),
    ("Windows", "AMD64"): (
        "picocrypt-windows-amd64.exe",
        "f4849510fb7250582f5060c1b629a46477fad6794ba95607721109f75aff5665",
    ),
    ("Windows", "ARM64"): (
        "picocrypt-windows-arm64.exe",
        "913a10a3722bb9129dc694d7276693fa9d6272aec9e168aa5e2a34fb70401c3a",
    ),
}


def download_verified(url: str, target: Path, expected: str) -> None:
    temporary = target.with_suffix(target.suffix + ".download")
    digest = hashlib.sha256()
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Privacy-Studio-Installer/1.0"},
        )
        with (
            # URL is always one of the fixed HTTPS project release URLs above.
            urllib.request.urlopen(request, timeout=120) as response,  # nosec B310
            temporary.open("wb") as output,
        ):
            while block := response.read(1024 * 1024):
                digest.update(block)
                output.write(block)
        actual = digest.hexdigest()
        if actual != expected:
            raise RuntimeError(f"Checksum non valido per {target.name}: {actual}")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    key = (platform.system(), platform.machine())
    try:
        asset, expected = ASSETS[key]
    except KeyError:
        supported = ", ".join(f"{system}/{machine}" for system, machine in ASSETS)
        raise SystemExit(
            f"Picocrypt non è preparato per {key[0]}/{key[1]}. "
            f"Combinazioni note: {supported}."
        ) from None

    target_dir = APP_DIR / "bin"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / ("picocrypt.exe" if os.name == "nt" else "picocrypt")
    license_target = target_dir / "PICOCRYPT-LICENSE-GPL-3.0.txt"

    if (
        not target.is_file()
        or hashlib.sha256(target.read_bytes()).hexdigest() != expected
    ):
        print(f"Scarico Picocrypt CLI {VERSION} per {key[0]}/{key[1]}...")
        download_verified(f"{BASE_URL}/{asset}", target, expected)
    if (
        not license_target.is_file()
        or hashlib.sha256(license_target.read_bytes()).hexdigest() != LICENSE_SHA256
    ):
        download_verified(LICENSE_URL, license_target, LICENSE_SHA256)
    if os.name != "nt":
        target.chmod(0o755)
    license_target.chmod(0o644)
    print(f"Picocrypt pronto: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import os
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)

VERSION = "1.0.0"

IGNORED_NAMES = {
    "__pycache__",
    ".DS_Store",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "Thumbs.db",
}
IGNORED_SUFFIXES = {".pyc", ".pyo"}

TRACKED_PATHS = [
    "app", "licenses", "native", "packaging", "runtime_guard", "scripts",
    "static", "workers", "CHANGELOG.md", "CONTRIBUTING.md", "DISCLAIMER.md",
    "LICENSE", "NOTICE", "README.md", "SECURITY.md", "THIRD_PARTY_NOTICES.md",
    "install.cmd", "install.ps1", "install.sh", "pyproject.toml",
    "requirements-ai.txt", "requirements-core.txt", "requirements-dev.txt",
    "requirements-paddle.txt", "start.cmd", "start.ps1", "start.sh"
]


def should_exclude(path: Path) -> bool:
    return any(part in IGNORED_NAMES for part in path.parts) or (
        path.suffix.lower() in IGNORED_SUFFIXES
    )


def clean_tar_entry(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    return None if should_exclude(Path(info.name)) else info


def write_clean_tree(
    archive: zipfile.ZipFile, source: Path, archive_root: str
) -> None:
    for path in source.rglob("*"):
        relative = path.relative_to(ROOT)
        if path.is_file() and not should_exclude(relative):
            archive.write(path, f"{archive_root}/{relative.as_posix()}")

print("=== Building Local Release Bundles for AI Privacy Studio ===")

# 1. Build Linux AppImage payload
appdir = ROOT / "build" / "AppDir"
if appdir.exists():
    shutil.rmtree(appdir)

appdir_source = appdir / "usr" / "share" / "ai-privacy-studio"
appdir_source.mkdir(parents=True, exist_ok=True)

# Create source.tar
subprocess.run([
    "git", "archive", "--format=tar",
    f"--output={appdir_source / 'source.tar'}", "HEAD", "--"
] + TRACKED_PATHS, cwd=ROOT, check=True)

# Copy AppRun, desktop, icon
shutil.copy(ROOT / "packaging" / "linux" / "AppRun", appdir / "AppRun")
os.chmod(appdir / "AppRun", 0o755)
shutil.copy(ROOT / "static" / "icon.svg", appdir / "ai-privacy-studio.svg")
shutil.copy(ROOT / "LICENSE", appdir / "LICENSE")
shutil.copy(ROOT / "THIRD_PARTY_NOTICES.md", appdir / "THIRD_PARTY_NOTICES.md")
shutil.copy(
    ROOT / "packaging" / "INSTALLER_NOTICE.en-it.txt",
    appdir / "INSTALLER_NOTICE.en-it.txt",
)
shutil.copy(
    ROOT / "packaging" / "linux" / "ai-privacy-studio.desktop",
    appdir / "ai-privacy-studio.desktop",
)

print("AppDir payload assembled.")

# Create Linux Tarball
linux_tar = DIST / f"AI-Privacy-Studio-v{VERSION}-Linux-x86_64.tar.gz"
with tarfile.open(linux_tar, "w:gz") as tar:
    tar.add(
        appdir,
        arcname=f"AI-Privacy-Studio-v{VERSION}",
        filter=clean_tar_entry,
    )
print(f"Created: {linux_tar.name} ({linux_tar.stat().st_size / 1024 / 1024:.2f} MB)")

# Create Windows Zip
win_zip = DIST / f"AI-Privacy-Studio-v{VERSION}-Windows-x64.zip"
with zipfile.ZipFile(win_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    for rel_path in TRACKED_PATHS:
        full_p = ROOT / rel_path
        if full_p.is_file():
            zf.write(full_p, f"AI-Privacy-Studio/{rel_path}")
        elif full_p.is_dir():
            write_clean_tree(zf, full_p, "AI-Privacy-Studio")
print(f"Created: {win_zip.name} ({win_zip.stat().st_size / 1024 / 1024:.2f} MB)")

# Create macOS Tarball
mac_tar = DIST / f"AI-Privacy-Studio-v{VERSION}-macOS-Universal.tar.gz"
with tarfile.open(mac_tar, "w:gz") as tar:
    for rel_path in TRACKED_PATHS:
        full_p = ROOT / rel_path
        if full_p.exists():
            tar.add(
                full_p,
                arcname=f"AI-Privacy-Studio/{rel_path}",
                filter=clean_tar_entry,
            )
print(f"Created: {mac_tar.name} ({mac_tar.stat().st_size / 1024 / 1024:.2f} MB)")

print("=== Local Release Package Generation Complete ===")

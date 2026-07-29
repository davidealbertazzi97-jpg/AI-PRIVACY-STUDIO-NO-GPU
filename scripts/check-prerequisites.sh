#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  printf 'Privacy Studio supporta attualmente Linux.\n' >&2
  exit 1
fi

case "$(uname -m)" in
  x86_64 | amd64) ;;
  *)
    printf 'Il programma di installazione supporta attualmente Linux x86_64.\n' >&2
    exit 1
    ;;
esac

required=(
  bash
  cc
  curl
  ffmpeg
  ffprobe
  ollama
  python3
  sha256sum
  systemctl
  uv
)
missing=()
for command in "${required[@]}"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    missing+=("$command")
  fi
done

browser_found=false
for browser in chromium chromium-browser google-chrome google-chrome-stable; do
  if command -v "$browser" >/dev/null 2>&1; then
    browser_found=true
    break
  fi
done
if [[ "$browser_found" == false ]]; then
  missing+=("chromium-or-google-chrome")
fi

if ((${#missing[@]})); then
  printf 'Dipendenze di sistema mancanti:\n' >&2
  printf '  - %s\n' "${missing[@]}" >&2
  exit 1
fi

python3 - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Serve Python 3.10 o successivo.")
print(f"Python {sys.version_info.major}.{sys.version_info.minor}: pronto")
PY

printf 'Prerequisiti di sistema: pronti.\n'

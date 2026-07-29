#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$(command -v "${PYTHON_BIN:-python3}")"
uv_bin="$(command -v uv || true)"

if [[ -n "$uv_bin" ]]; then
  if [[ ! -x "$app_dir/.venv/bin/python" ]]; then
    "$uv_bin" venv --python "$python_bin" "$app_dir/.venv"
  fi
  "$uv_bin" pip install --python "$app_dir/.venv/bin/python" \
    --requirement "$app_dir/requirements-core.txt"
else
  if [[ ! -x "$app_dir/.venv/bin/python" ]]; then
    "$python_bin" -m venv "$app_dir/.venv"
  fi
  "$app_dir/.venv/bin/python" -m pip install --upgrade pip
  "$app_dir/.venv/bin/python" -m pip install \
    --requirement "$app_dir/requirements-core.txt"
fi

"$app_dir/.venv/bin/python" -c \
  "import fastapi, httpx, markitdown, multipart, pexpect, pypdfium2, uvicorn; print('core pronto')"

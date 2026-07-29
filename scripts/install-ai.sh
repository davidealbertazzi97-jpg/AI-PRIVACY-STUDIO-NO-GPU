#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$(command -v "${PYTHON_BIN:-python3}")"
uv_bin="$(command -v uv || true)"

if [[ -z "$uv_bin" ]]; then
  printf 'Privacy Studio richiede uv per installare il motore AI CPU in un ambiente isolato.\n' >&2
  exit 1
fi

if [[ ! -x "$app_dir/.venv-ai/bin/python" ]]; then
  "$uv_bin" venv --python "$python_bin" "$app_dir/.venv-ai"
fi
"$uv_bin" pip install --python "$app_dir/.venv-ai/bin/python" \
  "torch==2.13.0+cpu" \
  --index-url https://download.pytorch.org/whl/cpu
"$uv_bin" pip install --python "$app_dir/.venv-ai/bin/python" \
  --requirement "$app_dir/requirements-ai.txt"

"$app_dir/.venv-ai/bin/python" -c \
  "from transformers import AutoModelForTDT, AutoProcessor; import librosa, opf, torch; print('AI pronto', torch.__version__)"

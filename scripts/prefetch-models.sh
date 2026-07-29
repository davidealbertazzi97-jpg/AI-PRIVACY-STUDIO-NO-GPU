#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ai_python="$app_dir/.venv-ai/bin/python"

if [[ ! -x "$ai_python" ]]; then
  printf 'Installa prima il motore AI con scripts/install-ai.sh.\n' >&2
  exit 1
fi

printf 'Scarico NVIDIA Parakeet v3 nel cache locale...\n'
exec "$ai_python" "$app_dir/scripts/prefetch_models.py"

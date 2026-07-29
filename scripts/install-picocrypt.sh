#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$app_dir/.venv/bin/python"
if [[ ! -x "$python_bin" ]]; then
  printf 'Installa prima il core con ./install.sh --core-only.\n' >&2
  exit 1
fi
exec "$python_bin" "$app_dir/scripts/install_picocrypt.py"

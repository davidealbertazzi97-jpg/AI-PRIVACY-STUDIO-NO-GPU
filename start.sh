#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="$app_dir/.venv/bin/python"
if [[ ! -x "$python_bin" ]]; then
  printf 'Privacy Studio non è installato. Esegui prima ./install.sh.\n' >&2
  exit 1
fi
exec "$python_bin" "$app_dir/scripts/start.py" "$@"

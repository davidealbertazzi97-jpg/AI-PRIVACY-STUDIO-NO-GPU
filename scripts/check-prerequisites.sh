#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$(command -v python3 || true)"
if [[ -z "$python_bin" ]]; then
  printf 'Python non è presente: usa ./install.sh per il bootstrap automatico.\n' >&2
  exit 1
fi
exec "$python_bin" "$app_dir/scripts/bootstrap.py" --dry-run "$@"

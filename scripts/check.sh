#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$app_dir"

uvx --from "ruff==0.16.0" ruff check .
uvx --from "ruff==0.16.0" ruff format --check .
uvx --from "bandit==1.9.4" bandit -q -c pyproject.toml \
  -r app runtime_guard scripts workers

while IFS= read -r -d '' script; do
  bash -n "$script"
done < <(find scripts -type f -name '*.sh' -print0)
bash -n install.sh start.sh

if command -v node >/dev/null 2>&1; then
  node --check static/app.js
fi

python3 -m compileall -q app runtime_guard scripts tests workers
printf 'Controlli statici completati.\n'

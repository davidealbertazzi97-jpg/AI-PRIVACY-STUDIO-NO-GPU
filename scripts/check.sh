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
python3 -m unittest tests.test_security
python3 - <<'PY'
import re
from pathlib import Path

html = Path("static/index.html").read_text(encoding="utf-8")
javascript = Path("static/app.js").read_text(encoding="utf-8")
assert 'data-language="it"' in html
assert 'data-language="en"' in html
translation_keys = set(
    re.findall(
        r'data-i18n(?:-html|-aria|-placeholder)?="([^"]+)"',
        html,
    )
)
missing = sorted(
    key for key in translation_keys if javascript.count(f'"{key}":') < 2
)
assert not missing, f"Traduzioni IT/EN mancanti: {missing}"
PY
python3 - <<'PY'
from scripts.start import guarded_environment

environment = guarded_environment("x" * 48, 54321, 54322)
assert environment["OLLAMA_HOST"] == "127.0.0.1:54322"
assert environment["PRIVACY_STUDIO_OLLAMA_URL"] == "http://127.0.0.1:54322"
assert environment["OLLAMA_NO_CLOUD"] == "1"
assert environment["HF_HUB_OFFLINE"] == "1"
PY
printf 'Controlli statici completati.\n'

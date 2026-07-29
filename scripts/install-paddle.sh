#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$(command -v "${PYTHON_BIN:-python3}")"
uv_bin="$(command -v uv || true)"

if [[ -n "$uv_bin" ]]; then
  if [[ ! -x "$app_dir/.venv-paddle/bin/python" ]]; then
    "$uv_bin" venv --python "$python_bin" "$app_dir/.venv-paddle"
  fi
  "$uv_bin" pip install --python "$app_dir/.venv-paddle/bin/python" \
    --requirement "$app_dir/requirements-paddle.txt"
else
  if [[ ! -x "$app_dir/.venv-paddle/bin/python" ]]; then
    "$python_bin" -m venv "$app_dir/.venv-paddle"
  fi
  "$app_dir/.venv-paddle/bin/python" -m pip install --upgrade pip
  "$app_dir/.venv-paddle/bin/python" -m pip install \
    --requirement "$app_dir/requirements-paddle.txt"
fi

"$app_dir/.venv-paddle/bin/python" -c \
  "import paddle, paddleocr; print('Paddle pronto', paddle.__version__)"

printf 'Scarico e verifico i modelli PaddleOCR e PP-StructureV3...\n'
"$app_dir/.venv-paddle/bin/python" - <<'PY'
import os

os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

from paddleocr import PaddleOCR, PPStructureV3

PaddleOCR(
    lang="it",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    device="cpu",
    enable_mkldnn=False,
)
PPStructureV3(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    use_formula_recognition=False,
    use_chart_recognition=False,
    device="cpu",
    enable_mkldnn=False,
)
print("Modelli PaddleOCR pronti.")
PY

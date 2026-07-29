#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ai_python="$app_dir/.venv-ai/bin/python"

if [[ ! -x "$ai_python" ]]; then
  printf 'Installa prima il motore AI con scripts/install-ai.sh.\n' >&2
  exit 1
fi

printf 'Scarico NVIDIA Parakeet v3 nel cache locale...\n'
"$ai_python" - <<'PY'
from huggingface_hub import snapshot_download
from transformers import AutoProcessor

model_id = "nvidia/parakeet-tdt-0.6b-v3"
revision = "7c35754d166cca382ad1e53e68b01e7c575f3a1d"

snapshot_download(
    repo_id=model_id,
    revision=revision,
    allow_patterns=[
        "config.json",
        "generation_config.json",
        "model.safetensors",
        "processor_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
    ],
)
AutoProcessor.from_pretrained(
    model_id,
    revision=revision,
    local_files_only=True,
)
print("Parakeet v3 pronto.")
PY

printf 'Scarico e verifico OpenAI Privacy Filter nel cache locale...\n'
"$ai_python" - <<'PY'
from opf import OPF

detector = OPF(device="cpu", output_mode="typed", decode_mode="viterbi")
result = detector.redact(
    "Scrivi a mario.rossi@example.test oppure chiama il numero 333 1234567."
)
if not result.to_dict().get("detected_spans"):
    raise SystemExit("Privacy Filter non ha prodotto rilevamenti nel test locale.")
print("OpenAI Privacy Filter pronto.")
PY

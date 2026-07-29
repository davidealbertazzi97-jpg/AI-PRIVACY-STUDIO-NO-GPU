#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null 2>&1; then
  printf 'Ollama non è installato.\n' >&2
  exit 1
fi

ollama pull glm-ocr:q8_0
ollama show glm-ocr:q8_0 >/dev/null
printf 'GLM-OCR q8_0 pronto in Ollama.\n'

#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import snapshot_download
from opf import OPF
from transformers import AutoProcessor

APP_DIR = Path(__file__).resolve().parent.parent
HF_HOME = APP_DIR / "models" / "huggingface"
PARAKEET_MODEL_ID = "nvidia/parakeet-tdt-0.6b-v3"
PARAKEET_REVISION = "7c35754d166cca382ad1e53e68b01e7c575f3a1d"
OPF_MODEL_ID = "openai/privacy-filter"
OPF_REVISION = "7ffa9a043d54d1be65afb281eddf0ffbe629385b"


def main() -> int:
    os.environ["HF_HOME"] = str(HF_HOME)
    print("Scarico NVIDIA Parakeet v3 nella cache locale...")
    snapshot_download(
        repo_id=PARAKEET_MODEL_ID,
        revision=PARAKEET_REVISION,
        cache_dir=HF_HOME / "hub",
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
        PARAKEET_MODEL_ID,
        revision=PARAKEET_REVISION,
        cache_dir=HF_HOME / "hub",
        local_files_only=True,
    )
    print("Scarico e verifico OpenAI Privacy Filter...")
    opf_snapshot = Path(
        snapshot_download(
            repo_id=OPF_MODEL_ID,
            revision=OPF_REVISION,
            cache_dir=HF_HOME / "hub",
            allow_patterns=["original/*"],
        )
    )
    checkpoint = opf_snapshot / "original"
    if not (checkpoint / "model.safetensors").is_file():
        raise RuntimeError("Checkpoint OpenAI Privacy Filter incompleto.")
    os.environ["OPF_CHECKPOINT"] = str(checkpoint)
    detector = OPF(device="cpu", output_mode="typed", decode_mode="viterbi")
    result = detector.redact(
        "Scrivi a mario.rossi@example.test oppure chiama il 333 1234567."
    )
    if not result.to_dict().get("detected_spans"):
        raise RuntimeError("Privacy Filter non ha rilevato i dati sintetici.")
    print("Modelli AI pronti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

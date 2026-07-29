#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, path)


def progress(path: Path, value: float, stage: str) -> None:
    write_json(path, {"progress": max(0.0, min(1.0, value)), "stage": stage})


LABEL_NAMES = dict(
    [
        ("private_person", "PERSONA"),
        ("private_address", "INDIRIZZO"),
        ("private_email", "EMAIL"),
        ("private_phone", "TELEFONO"),
        ("private_url", "URL_PRIVATO"),
        ("private_date", "DATA"),
        ("account_number", "CONTO"),
        ("secret", "SEGRETO"),
        ("codice_fiscale", "CODICE_FISCALE"),
        ("iban", "IBAN"),
        ("partita_iva", "PARTITA_IVA"),
        ("ip_address", "INDIRIZZO_IP"),
    ]
)


PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "private_email",
        re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])", re.I),
    ),
    (
        "iban",
        re.compile(r"\bIT\d{2}[A-Z]\d{10}[A-Z0-9]{12}\b", re.I),
    ),
    (
        "codice_fiscale",
        re.compile(r"\b[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]\b", re.I),
    ),
    (
        "partita_iva",
        re.compile(r"(?<!\d)(?:IT[\s-]?)?\d{11}(?!\d)", re.I),
    ),
    (
        "ip_address",
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
        ),
    ),
    (
        "private_phone",
        re.compile(
            r"(?<!\w)(?:\+?39[\s./-]?)?(?:0\d{1,3}|3\d{2})"
            r"(?:[\s./-]?\d){6,9}(?!\w)"
        ),
    ),
    (
        "secret",
        re.compile(
            r"(?i)\b(?:sk-[a-z0-9_-]{16,}|gh[pousr]_[a-z0-9]{20,}|"
            r"api[_-]?key\s*[:=]\s*[\"']?[a-z0-9_./+=-]{16,})"
        ),
    ),
]
DATE_PATTERN = re.compile(
    r"\b(?:0?[1-9]|[12]\d|3[01])[/.-](?:0?[1-9]|1[0-2])"
    r"[/.-](?:19|20)\d{2}\b"
)

PARAKEET_MODEL_ID = "nvidia/parakeet-tdt-0.6b-v3"
PARAKEET_REVISION = "7c35754d166cca382ad1e53e68b01e7c575f3a1d"


def regex_spans(text: str, include_dates: bool) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    patterns = list(PATTERNS)
    if include_dates:
        patterns.append(("private_date", DATE_PATTERN))
    for label, pattern in patterns:
        for match in pattern.finditer(text):
            found.append(
                {
                    "label": label,
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                    "source": "regola italiana",
                }
            )
    return found


def chunk_ranges(text: str, max_chars: int = 48_000, overlap: int = 512):
    primary_start = 0
    length = len(text)
    while primary_start < length:
        primary_end = min(length, primary_start + max_chars)
        if primary_end < length:
            candidates = [
                text.rfind("\n\n", primary_start + max_chars // 2, primary_end),
                text.rfind("\n", primary_start + max_chars // 2, primary_end),
                text.rfind(" ", primary_start + max_chars // 2, primary_end),
            ]
            primary_end = max(
                [point for point in candidates if point > 0],
                default=primary_end,
            )
        context_start = max(0, primary_start - overlap)
        context_end = min(length, primary_end + overlap)
        yield primary_start, primary_end, context_start, context_end
        primary_start = primary_end


def opf_spans(
    text: str, progress_path: Path
) -> tuple[list[dict[str, Any]], str | None]:
    from opf import OPF

    ranges = list(chunk_ranges(text))
    progress(progress_path, 0.02, "Caricamento OpenAI Privacy Filter (CPU)")
    detector = OPF(device="cpu", output_mode="typed", decode_mode="viterbi")
    found: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, (primary_start, primary_end, start, end) in enumerate(ranges):
        progress(
            progress_path,
            0.05 + index / max(1, len(ranges)) * 0.86,
            f"Privacy Filter: blocco {index + 1}/{len(ranges)}",
        )
        result = detector.redact(text[start:end])
        payload = result.to_dict()
        if payload.get("warning"):
            warnings.append(str(payload["warning"]))
        for span in payload.get("detected_spans", []):
            global_start = start + int(span["start"])
            global_end = start + int(span["end"])
            if global_end <= primary_start or global_start >= primary_end:
                continue
            found.append(
                {
                    "label": str(span["label"]),
                    "start": global_start,
                    "end": global_end,
                    "text": text[global_start:global_end],
                    "source": "OpenAI Privacy Filter",
                }
            )
    return found, ("; ".join(sorted(set(warnings))) or None)


def remove_overlaps(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[int, int, str], dict[str, Any]] = {}
    for span in spans:
        start = max(0, int(span["start"]))
        end = max(start, int(span["end"]))
        if not span.get("text") or end <= start:
            continue
        key = (start, end, str(span["label"]))
        current = unique.get(key)
        if current is None or span["source"] == "regola italiana":
            unique[key] = {**span, "start": start, "end": end}

    ordered = sorted(
        unique.values(),
        key=lambda item: (
            item["start"],
            -(item["end"] - item["start"]),
            0 if item["source"] == "regola italiana" else 1,
        ),
    )
    selected: list[dict[str, Any]] = []
    for span in ordered:
        if selected and span["start"] < selected[-1]["end"]:
            previous = selected[-1]
            if span["end"] - span["start"] > previous["end"] - previous["start"]:
                selected[-1] = span
            continue
        selected.append(span)
    return selected


def apply_redactions(
    text: str, spans: list[dict[str, Any]]
) -> tuple[str, list[dict[str, Any]], Counter[str]]:
    counters: defaultdict[str, int] = defaultdict(int)
    identities: dict[tuple[str, str], str] = {}
    pieces: list[str] = []
    cursor = 0
    public_spans: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for span in spans:
        label = str(span["label"])
        value = str(span["text"])
        identity = (label, re.sub(r"\s+", " ", value.casefold()).strip())
        if identity not in identities:
            counters[label] += 1
            base = LABEL_NAMES.get(label, label.upper())
            identities[identity] = f"[{base}_{counters[label]:03d}]"
        placeholder = identities[identity]
        pieces.append(text[cursor : span["start"]])
        pieces.append(placeholder)
        cursor = span["end"]
        counts[label] += 1
        span["placeholder"] = placeholder
        public_spans.append(
            {
                "label": label,
                "start": span["start"],
                "end": span["end"],
                "placeholder": placeholder,
                "source": span["source"],
            }
        )
    pieces.append(text[cursor:])
    return "".join(pieces), public_spans, counts


def anonymize(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)
    progress_path = Path(args.progress)
    text = input_path.read_text(encoding="utf-8")
    deterministic = regex_spans(text, bool(args.include_dates))
    detected, warning = opf_spans(text, progress_path)
    selected = remove_overlaps(deterministic + detected)
    redacted, public_spans, counts = apply_redactions(text, selected)
    progress(progress_path, 0.96, "Creazione del rapporto privacy")
    payload = {
        "engine": "OpenAI Privacy Filter + regole italiane locali",
        "model": "openai/privacy-filter",
        "characters": len(text),
        "detections": len(selected),
        "counts": dict(sorted(counts.items())),
        "spans": public_spans,
        "warning": warning,
        "review_required": True,
        "redacted_text": redacted,
        "_private_spans": selected,
    }
    write_json(output_path, payload)
    progress(progress_path, 1.0, "Completato")


def transcribe(args: argparse.Namespace) -> None:
    import numpy as np
    import soundfile as sf
    import torch
    from transformers import AutoModelForTDT, AutoProcessor

    input_dir = Path(args.input_dir)
    output_path = Path(args.output)
    progress_path = Path(args.progress)
    files = sorted(input_dir.glob("blocco-*.wav"))
    if not files:
        raise RuntimeError("Nessun blocco audio trovato.")
    torch.set_num_threads(max(1, min(6, os.cpu_count() or 4)))
    progress(progress_path, 0.02, "Caricamento NVIDIA Parakeet TDT 0.6B v3")
    processor = AutoProcessor.from_pretrained(
        PARAKEET_MODEL_ID,
        revision=PARAKEET_REVISION,
        local_files_only=True,
    )
    model = AutoModelForTDT.from_pretrained(
        PARAKEET_MODEL_ID,
        revision=PARAKEET_REVISION,
        dtype=torch.float32,
        low_cpu_mem_usage=True,
        local_files_only=True,
    )
    model.to("cpu")
    model.eval()

    segments: list[dict[str, Any]] = []
    texts: list[str] = []
    offset = 0.0
    for index, path in enumerate(files):
        progress(
            progress_path,
            0.05 + index / len(files) * 0.9,
            f"Parakeet v3: blocco {index + 1}/{len(files)}",
        )
        audio, sampling_rate = sf.read(path, dtype="float32", always_2d=False)
        if getattr(audio, "ndim", 1) > 1:
            audio = np.mean(audio, axis=1)
        target_rate = int(processor.feature_extractor.sampling_rate)
        if sampling_rate != target_rate:
            raise RuntimeError(f"Audio a {sampling_rate} Hz; attesi {target_rate} Hz.")
        inputs = processor(
            audio,
            sampling_rate=sampling_rate,
            return_tensors="pt",
        )
        with torch.inference_mode():
            generated = model.generate(**inputs, return_dict_in_generate=True)
        decoded = processor.decode(
            generated.sequences,
            durations=getattr(generated, "durations", None),
            skip_special_tokens=True,
        )
        decoded_text = decoded[0] if isinstance(decoded, tuple) else decoded
        if isinstance(decoded_text, list):
            decoded_text = decoded_text[0] if decoded_text else ""
        decoded_text = str(decoded_text).strip()
        duration = len(audio) / sampling_rate
        if decoded_text:
            texts.append(decoded_text)
            segments.append(
                {
                    "start": round(offset, 3),
                    "end": round(offset + duration, 3),
                    "text": decoded_text,
                }
            )
        offset += duration
    write_json(
        output_path,
        {
            "engine": "NVIDIA Parakeet TDT 0.6B v3",
            "model": PARAKEET_MODEL_ID,
            "revision": PARAKEET_REVISION,
            "text": "\n\n".join(texts),
            "segments": segments,
        },
    )
    progress(progress_path, 1.0, "Completato")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="command", required=True)
    anonymize_command = commands.add_parser("anonymize")
    anonymize_command.add_argument("--input", required=True)
    anonymize_command.add_argument("--output", required=True)
    anonymize_command.add_argument("--progress", required=True)
    anonymize_command.add_argument("--include-dates", action="store_true")
    transcribe_command = commands.add_parser("transcribe")
    transcribe_command.add_argument("--input-dir", required=True)
    transcribe_command.add_argument("--output", required=True)
    transcribe_command.add_argument("--progress", required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "anonymize":
            anonymize(args)
        elif args.command == "transcribe":
            transcribe(args)
        return 0
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

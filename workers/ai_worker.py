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
        ("fullname", "PERSONA"),
        ("persona", "PERSONA"),
        ("nome", "NOME"),
        ("cognome", "COGNOME"),
        ("indirizzo", "INDIRIZZO"),
        ("email", "EMAIL"),
        ("telefono", "TELEFONO"),
        ("data", "DATA"),
        ("documento", "DOCUMENTO"),
        ("catasto", "CATASTO"),
        ("provincia", "PROVINCIA"),
        ("targa", "TARGA"),
        ("citta", "CITTA"),
        ("luogo", "LUOGO"),
        ("organizzazione", "ORGANIZZAZIONE"),
        ("age", "ETA"),
        ("gender", "GENERE"),
        ("time", "ORA"),
        ("street", "VIA"),
        ("building_number", "NUMERO_CIVICO"),
        ("zipcode", "CAP"),
        ("credit_card", "CARTA"),
        ("amount", "IMPORTO"),
        ("manual_text", "TESTO"),
    ]
)

RIZZO_LABEL_NAMES = {
    "FULLNAME": "persona",
    "PER": "persona",
    "FIRSTNAME": "nome",
    "LASTNAME": "cognome",
    "ADDRESS": "indirizzo",
    "EMAIL": "email",
    "PHONE": "telefono",
    "TELEPHONENUM": "telefono",
    "PHONENUMBER": "telefono",
    "DATE": "data",
    "CF": "codice_fiscale",
    "PARTITA_IVA": "partita_iva",
    "PIVA": "partita_iva",
    "IBAN": "iban",
    "ID_DOC": "documento",
    "DOCID": "documento",
    "CATASTO": "catasto",
    "PROVINCE": "provincia",
    "TARGA": "targa",
    "IP": "ip_address",
    "CITY": "citta",
    "LOCATION": "luogo",
    "LOC": "luogo",
    "ORGANIZATION": "organizzazione",
    "ORG": "organizzazione",
    "AGE": "age",
    "GENDER": "gender",
    "TIME": "time",
    "STREET": "street",
    "BUILDINGNUM": "building_number",
    "ZIPCODE": "zipcode",
    "CREDITCARDNUMBER": "credit_card",
    "CREDITCARD": "credit_card",
    "AMOUNT": "amount",
}


PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "private_email",
        re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])", re.I),
    ),
    (
        "iban",
        re.compile(r"\bIT[\s-]?\d{2}[\s-]?[A-Z](?:[\s-]?[A-Z0-9]){22}\b", re.I),
    ),
    (
        "codice_fiscale",
        re.compile(
            r"\b[A-Z]{6}[0-9LMNPQRSTUV]{2}[A-EHLMPRST]"
            r"[0-9LMNPQRSTUV]{2}[A-Z][0-9LMNPQRSTUV]{3}[A-Z]\b",
            re.I,
        ),
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
    (
        "credit_card",
        re.compile(r"(?<!\d)(?:\d[ .-]?){12,18}\d(?!\d)"),
    ),
]
DATE_PATTERN = re.compile(
    r"\b(?:0?[1-9]|[12]\d|3[01])[/.-](?:0?[1-9]|1[0-2])"
    r"[/.-](?:19|20)\d{2}\b"
)

PARAKEET_MODEL_ID = "nvidia/parakeet-tdt-0.6b-v3"
PARAKEET_REVISION = "7c35754d166cca382ad1e53e68b01e7c575f3a1d"


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def valid_iban(value: str) -> bool:
    compact = re.sub(r"[\s-]", "", value).upper()
    if not compact.startswith("IT") or len(compact) != 27:
        return False
    rearranged = compact[4:] + compact[:4]
    numeric = "".join(
        str(ord(char) - ord("A") + 10) if char.isalpha() else char
        for char in rearranged
    )
    remainder = 0
    for digit in numeric:
        remainder = (remainder * 10 + int(digit)) % 97
    return remainder == 1


def valid_luhn(value: str) -> bool:
    digits = _digits(value)
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        number = int(digit)
        if index % 2 == parity:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return total % 10 == 0


def valid_partita_iva(value: str) -> bool:
    digits = _digits(value)
    if len(digits) != 11 or not digits.isdigit():
        return False
    total = 0
    for index, digit in enumerate(digits[:10]):
        number = int(digit)
        if index % 2:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return (10 - total % 10) % 10 == int(digits[-1])


CF_ODD = {
    **dict(
        zip(
            "0123456789",
            [1, 0, 5, 7, 9, 13, 15, 17, 19, 21],
            strict=True,
        )
    ),
    **dict(
        zip(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            [
                1,
                0,
                5,
                7,
                9,
                13,
                15,
                17,
                19,
                21,
                2,
                4,
                18,
                20,
                11,
                3,
                6,
                8,
                12,
                14,
                16,
                10,
                22,
                25,
                24,
                23,
            ],
            strict=True,
        )
    ),
}
CF_EVEN = {
    **dict(zip("0123456789", range(10), strict=True)),
    **dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", range(26), strict=True)),
}


def valid_codice_fiscale(value: str) -> bool:
    compact = re.sub(r"\s", "", value).upper()
    if len(compact) != 16 or not re.fullmatch(r"[A-Z0-9]{16}", compact):
        return False
    total = sum(
        (CF_ODD if index % 2 == 0 else CF_EVEN)[char]
        for index, char in enumerate(compact[:15])
    )
    return chr(ord("A") + total % 26) == compact[-1]


def checksum_valid(label: str, value: str) -> bool:
    if label == "iban":
        return valid_iban(value)
    if label == "codice_fiscale":
        return valid_codice_fiscale(value)
    if label == "partita_iva":
        return valid_partita_iva(value)
    if label == "credit_card":
        return valid_luhn(value)
    return True


def regex_spans(text: str, include_dates: bool) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    patterns = list(PATTERNS)
    if include_dates:
        patterns.append(("private_date", DATE_PATTERN))
    for label, pattern in patterns:
        for match in pattern.finditer(text):
            value = match.group(0)
            if label in {
                "iban",
                "codice_fiscale",
                "partita_iva",
                "credit_card",
            } and not checksum_valid(label, value):
                continue
            found.append(
                {
                    "label": label,
                    "start": match.start(),
                    "end": match.end(),
                    "text": value,
                    "source": (
                        "regola italiana + checksum"
                        if label
                        in {"iban", "codice_fiscale", "partita_iva", "credit_card"}
                        else "regola italiana"
                    ),
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


def rizzo_spans(
    text: str, progress_path: Path
) -> tuple[list[dict[str, Any]], str | None]:
    from transformers import pipeline

    ranges = list(chunk_ranges(text, max_chars=3000, overlap=256))
    progress(progress_path, 0.02, "Caricamento Rizzo PII 0.3B (CPU)")
    nlp = pipeline(
        "token-classification",
        model="rizzoaiacademy/rizzo-pii-0.3B",
        aggregation_strategy="simple",
        device="cpu",
    )
    found: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, (primary_start, primary_end, start, end) in enumerate(ranges):
        progress(
            progress_path,
            0.05 + index / max(1, len(ranges)) * 0.86,
            f"Rizzo PII 0.3B: blocco {index + 1}/{len(ranges)}",
        )
        chunk_text = text[start:end]
        if not chunk_text.strip():
            continue
        try:
            entities = nlp(chunk_text)
            for ent in entities:
                global_start = start + int(ent["start"])
                global_end = start + int(ent["end"])
                if global_end <= primary_start or global_start >= primary_end:
                    continue
                raw_label = str(ent["entity_group"]).upper()
                norm_label = RIZZO_LABEL_NAMES.get(raw_label, raw_label.lower())
                found.append(
                    {
                        "label": norm_label,
                        "start": global_start,
                        "end": global_end,
                        "text": text[global_start:global_end],
                        "source": "Rizzo PII 0.3B (Italiano)",
                    }
                )
        except Exception as exc:
            warnings.append(str(exc))
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


def filter_selected_spans(
    spans: list[dict[str, Any]], selection: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    """Keep only the exact detections confirmed in the local preview.

    The selection contains positions and labels, never the private values.  A
    missing/empty list is intentional: the user may choose not to anonymize
    any detected element.
    """
    if selection is None:
        return spans
    allowed: dict[tuple[int, int, str], str] = {}
    for item in selection:
        if not isinstance(item, dict):
            continue
        try:
            key = (int(item["start"]), int(item["end"]), str(item["label"]))
        except (KeyError, TypeError, ValueError):
            continue
        if key[0] >= 0 and key[1] > key[0] and key[2]:
            replacement = item.get("replacement", "")
            if isinstance(replacement, str):
                replacement = replacement.strip()[:180]
                if any(ord(char) < 32 and char not in "\t" for char in replacement):
                    replacement = ""
            else:
                replacement = ""
            allowed[key] = replacement
    selected: list[dict[str, Any]] = []
    for span in spans:
        key = (int(span["start"]), int(span["end"]), str(span["label"]))
        if key not in allowed:
            continue
        copy = dict(span)
        if allowed[key]:
            copy["replacement"] = allowed[key]
        selected.append(copy)
    return selected


def manual_spans_from_selection(
    text: str, selection: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Build local spans for words or phrases added by the user in the preview."""
    manual: list[dict[str, Any]] = []
    for item in selection:
        if not isinstance(item, dict) or str(item.get("label")) != "manual_text":
            continue
        try:
            start = int(item["start"])
            end = int(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if start < 0 or end <= start or end > len(text):
            continue
        value = text[start:end]
        if not value.strip():
            continue
        manual.append(
            {
                "label": "manual_text",
                "start": start,
                "end": end,
                "text": value,
                "source": "selezione manuale nella preview",
            }
        )
        replacement = item.get("replacement", "")
        if isinstance(replacement, str):
            replacement = replacement.strip()[:180]
            if replacement and not any(
                ord(char) < 32 and char not in "\t" for char in replacement
            ):
                manual[-1]["replacement"] = replacement
    return manual


def select_requested_spans(
    text: str,
    detected: list[dict[str, Any]],
    selection: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Apply the preview selection and merge manually added local spans."""
    if selection is None:
        return detected
    selected = filter_selected_spans(detected, selection)
    return remove_overlaps(selected + manual_spans_from_selection(text, selection))


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
        replacement = str(span.get("replacement") or placeholder).strip() or placeholder
        pieces.append(text[cursor : span["start"]])
        pieces.append(replacement)
        cursor = span["end"]
        counts[label] += 1
        span["placeholder"] = placeholder
        public_spans.append(
            {
                "label": label,
                "start": span["start"],
                "end": span["end"],
                "placeholder": placeholder,
                "replacement": replacement,
                "source": span["source"],
            }
        )
    pieces.append(text[cursor:])
    return "".join(pieces), public_spans, counts


def residual_warnings(
    redacted: str, spans: list[dict[str, Any]]
) -> tuple[list[str], list[str]]:
    residual_labels: list[str] = []
    short_labels: list[str] = []
    lowered = redacted.casefold()
    for span in spans:
        value = str(span.get("text") or "")
        label = str(span.get("label") or "PII")
        if len(re.sub(r"\W", "", value, flags=re.UNICODE)) < 2:
            short_labels.append(label)
            continue
        if value.casefold() in lowered:
            residual_labels.append(label)
    return sorted(set(residual_labels)), sorted(set(short_labels))


def anonymize(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)
    progress_path = Path(args.progress)
    text = input_path.read_text(encoding="utf-8")
    engine_choice = getattr(args, "engine", "privacy_filter")
    if engine_choice == "privacy_filter_rizzo":
        engine_title = "Rizzo PII 0.3B (Simone Rizzo) + regole italiane locali"
        model_name = "rizzoaiacademy/rizzo-pii-0.3B"
    else:
        engine_title = "OpenAI Privacy Filter + regole italiane locali"
        model_name = "openai/privacy-filter"

    cached_spans_file = getattr(args, "detected_spans_file", None)
    if cached_spans_file:
        cached_payload = json.loads(Path(cached_spans_file).read_text(encoding="utf-8"))
        if not isinstance(cached_payload, list):
            raise ValueError("Le rilevazioni cache devono essere una lista.")
        detected = cached_payload
        warning = None
        progress(progress_path, 0.88, "Riutilizzo rilevazioni della preview")
    else:
        deterministic = regex_spans(text, bool(args.include_dates))
        if engine_choice == "privacy_filter_rizzo":
            detected, warning = rizzo_spans(text, progress_path)
        else:
            detected, warning = opf_spans(text, progress_path)

        detected = deterministic + detected

    selected = remove_overlaps(detected)
    selection = None
    selected_spans_file = getattr(args, "selected_spans_file", None)
    if selected_spans_file:
        selection_payload = json.loads(
            Path(selected_spans_file).read_text(encoding="utf-8")
        )
        if not isinstance(selection_payload, list):
            raise ValueError("La selezione della preview deve essere una lista.")
        selection = selection_payload
        selected = select_requested_spans(text, selected, selection)
    redacted, public_spans, counts = apply_redactions(text, selected)
    residual_labels, short_labels = residual_warnings(redacted, selected)
    progress(progress_path, 0.96, "Creazione del rapporto privacy")

    ui_spans = [
        {
            "id": index,
            "label": s["label"],
            "start": s["start"],
            "end": s["end"],
            "original": s["text"],
            "placeholder": s.get("placeholder", f"[{s['label'].upper()}]"),
            "replacement": s.get("replacement", s.get("placeholder", "")),
            "source": s["source"],
        }
        for index, s in enumerate(selected)
    ]

    payload = {
        "engine": engine_title,
        "model": model_name,
        "characters": len(text),
        "detections": len(selected),
        "counts": dict(sorted(counts.items())),
        "spans": ui_spans,
        "warning": warning,
        "residual_labels": residual_labels,
        "short_value_labels": short_labels,
        "residual_warning": bool(residual_labels or short_labels),
        "review_required": True,
        "redacted_text": redacted,
        "original_text": text,
        "_private_spans": selected,
        "selection_applied": selection is not None,
        "preview_only": bool(getattr(args, "preview_only", False)),
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
    anonymize_command.add_argument(
        "--engine",
        default="privacy_filter",
        choices=["privacy_filter", "privacy_filter_rizzo"],
    )
    anonymize_command.add_argument("--input", required=True)
    anonymize_command.add_argument("--output", required=True)
    anonymize_command.add_argument("--progress", required=True)
    anonymize_command.add_argument("--include-dates", action="store_true")
    anonymize_command.add_argument("--selected-spans-file")
    anonymize_command.add_argument("--detected-spans-file")
    anonymize_command.add_argument("--preview-only", action="store_true")
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

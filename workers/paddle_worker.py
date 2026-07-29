#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# oneDNN in PaddlePaddle 3.3 can reject PP-OCRv6 graph attributes on some
# CPU-only builds. The plain CPU executor is slower but portable and stable.
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, path)


def progress(path: Path, value: float, stage: str) -> None:
    write_json(path, {"progress": value, "stage": stage})


def as_dict(result: Any) -> dict[str, Any]:
    value = getattr(result, "json", result)
    if callable(value):
        value = value()
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {"text": value}
    return value if isinstance(value, dict) else {}


def find_texts(value: Any) -> list[str]:
    texts: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"rec_texts", "texts"} and isinstance(nested, list):
                texts.extend(str(item) for item in nested if str(item).strip())
            elif key in {"text", "block_content"} and isinstance(nested, str):
                if nested.strip():
                    texts.append(nested.strip())
            else:
                texts.extend(find_texts(nested))
    elif isinstance(value, list):
        for nested in value:
            texts.extend(find_texts(nested))
    return texts


def run_ocr(input_path: Path, progress_path: Path) -> tuple[str, int]:
    from paddleocr import PaddleOCR

    progress(progress_path, 0.04, "Caricamento modelli PaddleOCR")
    try:
        pipeline = PaddleOCR(
            lang="it",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            device="cpu",
            enable_mkldnn=False,
            cpu_threads=max(1, min(6, os.cpu_count() or 4)),
        )
    except TypeError:
        pipeline = PaddleOCR(lang="it", use_angle_cls=False)

    output = pipeline.predict(input=str(input_path))
    parts: list[str] = []
    pages = 0
    for pages, result in enumerate(output, start=1):
        progress(
            progress_path,
            min(0.94, 0.08 + pages * 0.02),
            f"PaddleOCR: pagina {pages}",
        )
        content = find_texts(as_dict(result))
        parts.append(f"<!-- pagina {pages} -->\n\n" + "\n".join(dict.fromkeys(content)))
    return "\n\n---\n\n".join(parts), pages


def run_structure(input_path: Path, progress_path: Path) -> tuple[str, int]:
    from paddleocr import PPStructureV3

    progress(progress_path, 0.03, "Caricamento PP-StructureV3")
    pipeline = PPStructureV3(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        use_formula_recognition=False,
        use_chart_recognition=False,
        device="cpu",
        enable_mkldnn=False,
        cpu_threads=max(1, min(6, os.cpu_count() or 4)),
    )
    output = pipeline.predict(input=str(input_path))
    markdown_pages: list[dict[str, Any]] = []
    fallback: list[str] = []
    pages = 0
    for pages, result in enumerate(output, start=1):
        progress(
            progress_path,
            min(0.94, 0.07 + pages * 0.02),
            f"PP-StructureV3: pagina {pages}",
        )
        markdown = getattr(result, "markdown", None)
        if isinstance(markdown, dict):
            markdown_pages.append(markdown)
        else:
            fallback.extend(find_texts(as_dict(result)))
    if markdown_pages and hasattr(pipeline, "concatenate_markdown_pages"):
        text = pipeline.concatenate_markdown_pages(markdown_pages)
    elif markdown_pages:
        text = "\n\n---\n\n".join(
            str(page.get("markdown_texts", "")) for page in markdown_pages
        )
    else:
        text = "\n".join(fallback)
    return str(text), pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--progress", required=True)
    parser.add_argument("--mode", choices=("ocr", "structure"), default="ocr")
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    progress_path = Path(args.progress)
    try:
        if args.mode == "structure":
            text, pages = run_structure(input_path, progress_path)
            engine = "PaddleOCR PP-StructureV3"
        else:
            text, pages = run_ocr(input_path, progress_path)
            engine = "PaddleOCR"
        write_json(
            output_path,
            {
                "text": text,
                "engine": engine,
                "pages": pages,
                "characters": len(text),
            },
        )
        progress(progress_path, 1.0, "Completato")
        return 0
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

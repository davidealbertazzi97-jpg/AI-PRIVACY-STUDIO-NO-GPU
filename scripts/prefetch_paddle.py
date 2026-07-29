#!/usr/bin/env python3
from __future__ import annotations

import os

os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

from paddleocr import PaddleOCR, PPStructureV3


def main() -> int:
    print("Scarico e verifico i modelli PaddleOCR e PP-StructureV3...")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import httpx
from smoke_local import create_fixtures, require_text, submit_job, test_server


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="privacy-studio-structure-") as temp:
        root = Path(temp)
        fixtures = create_fixtures(root)
        with (
            test_server(root) as (base_url, token, _),
            httpx.Client(
                headers={"X-Privacy-Studio-Token": token},
                timeout=60,
            ) as client,
        ):
            job = submit_job(
                client,
                base_url,
                fixtures["image"],
                "ocr",
                "paddle_structure",
                timeout_seconds=1800,
            )
            text = require_text(
                Path(job["output_path"]),
                ("PRIVACY STUDIO", "Documento OCR"),
            )
            print(
                json.dumps(
                    {
                        "engine": job["result"].get("engine"),
                        "pages": job["result"].get("pages"),
                        "characters": len(text),
                        "status": job["status"],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

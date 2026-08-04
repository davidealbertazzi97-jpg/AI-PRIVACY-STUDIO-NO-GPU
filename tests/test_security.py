from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

_TEST_ROOT = tempfile.TemporaryDirectory(prefix="privacy-studio-unit-")
os.environ["PRIVACY_STUDIO_DATA"] = str(Path(_TEST_ROOT.name) / "data")
os.environ["PRIVACY_STUDIO_STATE"] = str(Path(_TEST_ROOT.name) / "state")
os.environ["PRIVACY_STUDIO_OUTPUTS"] = str(Path(_TEST_ROOT.name) / "outputs")

vault = importlib.import_module("app.engines.vault")
guarded_environment = importlib.import_module("scripts.start").guarded_environment
apply_redactions = importlib.import_module("workers.ai_worker").apply_redactions
rizzo_spans = importlib.import_module("workers.ai_worker").rizzo_spans


class PrivacyCleanupTests(unittest.TestCase):
    def test_encrypt_failure_removes_plaintext_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            destination = root / "vault"
            work.mkdir()
            destination.mkdir()
            source = root / "private.txt"
            source.write_text("private test data", encoding="utf-8")
            paths = SimpleNamespace(work=work, vault=destination)

            with (
                patch.object(vault, "PATHS", paths),
                patch.object(
                    vault,
                    "_run_picocrypt",
                    side_effect=RuntimeError("synthetic failure"),
                ),
                self.assertRaisesRegex(RuntimeError, "synthetic failure"),
            ):
                vault.encrypt_to_vault(
                    source,
                    "a-long-test-passphrase",
                    lambda *_: None,
                )

            self.assertEqual(list(work.iterdir()), [])

    def test_decrypt_failure_removes_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            destination = root / "vault"
            output = root / "output"
            work.mkdir()
            destination.mkdir()
            source = destination / "private.txt.pcv"
            source.write_bytes(b"synthetic encrypted fixture")
            paths = SimpleNamespace(work=work, vault=destination)

            with (
                patch.object(vault, "PATHS", paths),
                patch.object(
                    vault,
                    "_run_picocrypt",
                    side_effect=RuntimeError("synthetic failure"),
                ),
                self.assertRaisesRegex(RuntimeError, "synthetic failure"),
            ):
                vault.decrypt_from_vault(
                    source,
                    "a-long-test-passphrase",
                    output,
                    lambda *_: None,
                )

            self.assertEqual(list(work.iterdir()), [])


class DataMinimizationTests(unittest.TestCase):
    def test_rizzo_loader_uses_the_verified_offline_snapshot(self) -> None:
        calls: dict[str, object] = {}

        class FakeTokenizer:
            @staticmethod
            def from_pretrained(model_id: str, **kwargs: object) -> object:
                calls["tokenizer"] = (model_id, kwargs)
                return object()

        class FakeModel:
            @staticmethod
            def from_pretrained(model_id: str, **kwargs: object) -> object:
                calls["model"] = (model_id, kwargs)
                return object()

        def fake_pipeline(task: str, **kwargs: object) -> object:
            calls["pipeline"] = (task, kwargs)
            return lambda _text: [{"start": 0, "end": 5, "entity_group": "FULLNAME"}]

        fake_transformers = SimpleNamespace(
            AutoModelForTokenClassification=FakeModel,
            AutoTokenizer=FakeTokenizer,
            pipeline=fake_pipeline,
        )
        with tempfile.TemporaryDirectory() as temporary:
            progress_path = Path(temporary) / "progress.json"
            with patch.dict(sys.modules, {"transformers": fake_transformers}):
                spans, warning = rizzo_spans("Mario", progress_path)

        self.assertIsNone(warning)
        self.assertEqual(spans[0]["label"], "persona")
        for key in ("tokenizer", "model"):
            _, kwargs = calls[key]
            self.assertTrue(kwargs["local_files_only"])
            self.assertEqual(len(str(kwargs["revision"])), 40)
        _, pipeline_kwargs = calls["pipeline"]
        self.assertNotIn("local_files_only", pipeline_kwargs)

    def test_public_redaction_report_has_no_value_preview(self) -> None:
        original = "Contact alice@example.test now."
        start = original.index("alice")
        spans = [
            {
                "label": "private_email",
                "start": start,
                "end": start + len("alice@example.test"),
                "text": "alice@example.test",
                "source": "synthetic test",
            }
        ]

        redacted, public_spans, _ = apply_redactions(original, spans)
        report = json.dumps(public_spans)

        self.assertIn("[EMAIL_001]", redacted)
        self.assertNotIn("alice", report)
        self.assertNotIn("preview", public_spans[0])

    def test_runtime_environment_drops_inherited_injection_paths(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "PYTHONPATH": "/tmp/untrusted-python",
                "LD_PRELOAD": "/tmp/untrusted-library.so",
            },
        ):
            environment = guarded_environment("x" * 48, 54321, 54322)

        self.assertNotIn("untrusted-python", environment["PYTHONPATH"])
        self.assertNotIn("untrusted-library", environment.get("LD_PRELOAD", ""))


if __name__ == "__main__":
    unittest.main()

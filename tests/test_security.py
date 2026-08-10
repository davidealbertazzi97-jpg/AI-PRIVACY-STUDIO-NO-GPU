from __future__ import annotations

import importlib
import json
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

_TEST_ROOT = tempfile.TemporaryDirectory(prefix="privacy-studio-unit-")
os.environ["PRIVACY_STUDIO_DATA"] = str(Path(_TEST_ROOT.name) / "data")
os.environ["PRIVACY_STUDIO_STATE"] = str(Path(_TEST_ROOT.name) / "state")
os.environ["PRIVACY_STUDIO_OUTPUTS"] = str(Path(_TEST_ROOT.name) / "outputs")

vault = importlib.import_module("app.engines.vault")
permanent_vault = importlib.import_module("app.engines.permanent_vault")
guarded_environment = importlib.import_module("scripts.start").guarded_environment
public_privacy_report = importlib.import_module("app.utils").public_privacy_report
apply_redactions = importlib.import_module("workers.ai_worker").apply_redactions
worker = importlib.import_module("workers.ai_worker")
filter_selected_spans = worker.filter_selected_spans
select_requested_spans = worker.select_requested_spans
regex_spans = worker.regex_spans
residual_warnings = worker.residual_warnings
valid_codice_fiscale = worker.valid_codice_fiscale
valid_iban = worker.valid_iban
anonymize_worker = worker.anonymize


class PrivacyCleanupTests(unittest.TestCase):
    def test_permanent_vault_is_incremental_and_restorable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            local_root = root / "permanent-vault"
            backup_root = root / "cloud-sync-folder"
            source = root / "contratto.txt"
            source.write_text("contenuto strettamente riservato", encoding="utf-8")
            store = permanent_vault.PersistentVault(local_root)
            metadata = store.create("una-passphrase-lunga-e-sicura")
            key, header, _ = store.unlock("una-passphrase-lunga-e-sicura")
            entry = store.store_file(key, header, source, source.name)
            blob = local_root / "objects" / f"{entry['id']}.blob"

            self.assertEqual(metadata["kdf"], "scrypt + AES-256-GCM")
            self.assertNotIn(source.read_bytes(), blob.read_bytes())
            self.assertNotIn(
                b"una-passphrase-lunga-e-sicura",
                (local_root / "index.enc").read_bytes(),
            )
            self.assertEqual(store.list_files(key, header)[0]["name"], source.name)

            restored = root / "restored.txt"
            store.restore_file(key, header, entry["id"], restored)
            self.assertEqual(restored.read_text(encoding="utf-8"), source.read_text())

            backup = store.backup(backup_root, header)
            store.delete_file(key, header, entry["id"])
            merged = store.merge_backup(
                Path(backup["path"]), "una-passphrase-lunga-e-sicura"
            )
            self.assertEqual(merged["added"], 1)
            recovered_root = root / "recovered-vault"
            recovered = permanent_vault.PersistentVault(recovered_root)
            recovered.restore_backup(Path(backup["path"]))
            recovered_key, recovered_header, _ = recovered.unlock(
                "una-passphrase-lunga-e-sicura"
            )
            recovered_file = root / "recovered.txt"
            recovered.restore_file(
                recovered_key,
                recovered_header,
                entry["id"],
                recovered_file,
            )
            self.assertEqual(
                recovered_file.read_text(encoding="utf-8"),
                "contenuto strettamente riservato",
            )

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

    def test_group_vault_encrypts_once_and_extracts_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            vault_dir = root / "vault"
            work.mkdir()
            vault_dir.mkdir()
            archive = root / "progetto.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("contratto.txt", "documento riservato")
                bundle.writestr("note.md", "secondo documento")
            paths = SimpleNamespace(work=work, vault=vault_dir)

            def fake_picocrypt(input_path, password, *, decrypt, **_kwargs):
                output = (
                    input_path.with_suffix("")
                    if decrypt
                    else input_path.with_name(input_path.name + ".pcv")
                )
                shutil.copy2(input_path, output)
                return output, ""

            with (
                patch.object(vault, "PATHS", paths),
                patch.object(vault, "_run_picocrypt", side_effect=fake_picocrypt),
            ):
                encrypted, result = vault.encrypt_to_vault(
                    archive,
                    "a-long-test-passphrase",
                    lambda *_: None,
                    kind="group",
                )
                output_dir = root / "extracted"
                manifest, extracted = vault.decrypt_group_from_vault(
                    encrypted,
                    "a-long-test-passphrase",
                    output_dir,
                    lambda *_: None,
                )

            self.assertTrue(encrypted.name.endswith(".vault.zip.pcv"))
            self.assertEqual(result["kind"], "group")
            self.assertTrue(manifest.is_file())
            self.assertEqual(sorted(extracted["files"]), ["contratto.txt", "note.md"])
            self.assertEqual(
                (output_dir / "contratto.txt").read_text(), "documento riservato"
            )


class DataMinimizationTests(unittest.TestCase):
    def test_preview_selection_can_leave_one_detection_clear(self) -> None:
        spans = [
            {
                "label": "private_email",
                "start": 9,
                "end": 27,
                "text": "alice@example.test",
                "source": "synthetic test",
            },
            {
                "label": "private_phone",
                "start": 34,
                "end": 46,
                "text": "+39 333 123456",
                "source": "synthetic test",
            },
        ]
        selected = filter_selected_spans(
            spans,
            [{"label": "private_email", "start": 9, "end": 27}],
        )
        redacted, _, _ = apply_redactions(
            "Contatta alice@example.test o +39 333 123456.", selected
        )

        self.assertIn("[EMAIL_001]", redacted)
        self.assertIn("+39 333 123456", redacted)

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

    def test_public_privacy_report_removes_private_fragments(self) -> None:
        report = public_privacy_report(
            {
                "original_text": "Contact alice@example.test.",
                "_private_spans": [{"text": "alice@example.test"}],
                "spans": [
                    {
                        "label": "private_email",
                        "start": 8,
                        "end": 26,
                        "original": "alice@example.test",
                        "placeholder": "[EMAIL_001]",
                        "replacement": "[CONTATTO]",
                    }
                ],
            }
        )

        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("alice@example.test", serialized)
        self.assertNotIn("original_text", report)
        self.assertNotIn("_private_spans", report)
        self.assertEqual(
            report["spans"],
            [
                {
                    "label": "private_email",
                    "start": 8,
                    "end": 26,
                    "placeholder": "[EMAIL_001]",
                }
            ],
        )

    def test_preview_can_add_a_manual_phrase(self) -> None:
        original = "Progetto Aurora: non condividere il codice interno."
        start = original.index("codice interno")
        selected = select_requested_spans(
            original,
            [],
            [
                {
                    "label": "manual_text",
                    "start": start,
                    "end": start + len("codice interno"),
                }
            ],
        )
        redacted, _, _ = apply_redactions(original, selected)

        self.assertIn("[TESTO_001]", redacted)
        self.assertNotIn("codice interno", redacted)

    def test_preview_replacement_can_be_customized(self) -> None:
        original = "Contatta alice@example.test."
        start = original.index("alice")
        selected = select_requested_spans(
            original,
            [
                {
                    "label": "private_email",
                    "start": start,
                    "end": start + len("alice@example.test"),
                    "text": "alice@example.test",
                    "source": "synthetic test",
                }
            ],
            [
                {
                    "label": "private_email",
                    "start": start,
                    "end": start + len("alice@example.test"),
                    "replacement": "[CONTATTO_PRIVATO]",
                }
            ],
        )
        redacted, _, _ = apply_redactions(original, selected)

        self.assertIn("[CONTATTO_PRIVATO]", redacted)
        self.assertNotIn("alice@example.test", redacted)

    def test_checksum_rules_reject_invalid_structured_identifiers(self) -> None:
        self.assertTrue(valid_iban("IT60X0542811101000000123456"))
        self.assertFalse(valid_iban("IT60X0542811101000000123457"))
        self.assertTrue(valid_codice_fiscale("RSSMRA85M01H501Q"))
        self.assertNotEqual(
            [span["text"] for span in regex_spans("IT60X0542811101000000123457", True)],
            ["IT60X0542811101000000123457"],
        )

    def test_residual_warning_does_not_expose_original_value(self) -> None:
        labels, short = residual_warnings(
            "Il valore resta chiaro.",
            [
                {
                    "label": "manual_text",
                    "text": "valore",
                    "replacement": "valore",
                }
            ],
        )

        self.assertEqual(labels, ["manual_text"])
        self.assertEqual(short, [])

    def test_cached_preview_spans_skip_model_inference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.md"
            output = root / "output.json"
            progress = root / "progress.json"
            cache = root / "detected.json"
            selection = root / "selection.json"
            original = "Contatta alice@example.test."
            start = original.index("alice")
            source.write_text(original, encoding="utf-8")
            cache.write_text(
                json.dumps(
                    [
                        {
                            "label": "private_email",
                            "start": start,
                            "end": start + len("alice@example.test"),
                            "text": "alice@example.test",
                            "source": "preview cache",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            selection.write_text(
                json.dumps(
                    [
                        {
                            "label": "private_email",
                            "start": start,
                            "end": start + len("alice@example.test"),
                            "replacement": "[CONTATTO]",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            anonymize_worker(
                SimpleNamespace(
                    input=source,
                    output=output,
                    progress=progress,
                    engine="privacy_filter",
                    include_dates=False,
                    selected_spans_file=selection,
                    detected_spans_file=cache,
                    preview_only=False,
                )
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["redacted_text"], "Contatta [CONTATTO].")
        self.assertEqual(payload["detections"], 1)

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
        self.assertEqual(
            Path(environment["TIKTOKEN_CACHE_DIR"]).parts[-2:],
            ("models", "tiktoken"),
        )


if __name__ == "__main__":
    unittest.main()

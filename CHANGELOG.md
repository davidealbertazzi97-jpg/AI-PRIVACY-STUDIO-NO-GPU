# Changelog

All notable changes to AI Privacy Studio will be documented here.

## 1.1.0 - 2026-08-10

- Added a local two-step anonymization flow for OpenAI Privacy Filter and Rizzo PII.
- Added side-by-side preview of detected text and the proposed redacted output.
- Added per-detection selection, select-all, and deselect-all controls before output creation.
- Added a live preview progress bar and manual word/phrase selections, with every matching occurrence independently deselectable.
- Added persistent category filters, per-occurrence and document-wide custom replacements, plus residual-value warnings.
- Added checksum-aware Italian rules for IBAN, tax codes, VAT IDs, and payment cards.
- Added original/redacted PDF preview panes and secure rasterized redacted-PDF output without the original searchable layer; incomplete PDF redactions are withheld when OCR spans cannot be located.
- Added an optional reversible dictionary encrypted in its own Picocrypt volume; dictionary passwords are never written to the database.
- Added download/delete controls for vault volumes and one-password group vaults that encrypt multiple documents in a single archive.
- Added a temporary permission-restricted preview cache so confirmation can reuse extraction and detections without a second model inference.
- Added a permanent incremental vault managed by the app with Scrypt + AES-256-GCM, encrypted index, per-document storage, unlock/search/download/delete, and in-memory sessions.
- Added encrypted backup and restore through a user-selected local sync folder; direct cloud networking remains disabled by design.
- Added an optional editable-PDF profile using PyMuPDF; the default installer keeps the secure raster fallback until its AGPL/commercial licensing is explicitly accepted.
- Added offline prefetching for the OpenAI Privacy Filter `o200k_base` tokenizer.
- Kept preview sources in the private inbox only until the user confirms or cancels the review.
- Separated single-document `.pcv` encryption from persistent and portable vault management in the interface, with dedicated controls and usage guidance.

## 1.0.0 - 2026-07-29

- Local document conversion with Microsoft MarkItDown.
- Assisted redaction with OpenAI Privacy Filter and Italian deterministic rules.
- Local transcription with NVIDIA Parakeet TDT 0.6B v3.
- OCR with PaddleOCR, PP-StructureV3, and GLM-OCR through Ollama.
- Picocrypt-compatible local vault.
- Loopback-only API, per-installation token, and outbound network guard.
- Responsive local interface with vendored Inter and Lucide assets.
- Verified bootstrap for Linux x86-64, macOS arm64, and Windows x86-64.
- Managed Python, FFmpeg, Picocrypt, Ollama, and model downloads.
- Cross-platform launcher and Python outbound-network guard.
- Dedicated loopback-only Ollama process with cloud features disabled.
- GPL-3.0-only licensing with a detailed third-party inventory.
- Bilingual, user-oriented README with release installer instructions.
- Online `.exe`, `.AppImage`, and `.dmg` release packages.
- Cleanup of Picocrypt plaintext staging on every error path.
- Redaction reports no longer include partial previews of detected private data.

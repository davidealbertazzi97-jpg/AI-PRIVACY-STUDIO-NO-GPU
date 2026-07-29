# Changelog

All notable changes to AI Privacy Studio will be documented here.

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

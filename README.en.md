<p align="center">
  <img src="static/icon.svg" width="88" height="88" alt="Privacy Studio">
</p>

<h1 align="center">Privacy Studio Locale</h1>

<p align="center">
  Documents, OCR, transcription, assisted redaction, and encryption.<br>
  Everything stays on your computer.
</p>

<p align="center">
  <a href="README.md">Italiano</a> · <strong>English</strong>
</p>

## What it is

Privacy Studio Locale is an open-source desktop application for processing
sensitive documents without sending them to cloud services. It provides a local
web interface, a persistent job queue, and specialized on-device engines.

- assisted redaction with OpenAI Privacy Filter and Italian deterministic rules;
- audio and video transcription with NVIDIA Parakeet TDT 0.6B v3;
- OCR with PaddleOCR, PP-StructureV3, or GLM-OCR through Ollama;
- PDF and Office document conversion with Microsoft MarkItDown;
- encryption and decryption of Picocrypt-compatible `.pcv` volumes;
- a responsive interface with locally served open-source fonts and icons.

This is an independent project. It is not affiliated with, sponsored by, or
endorsed by the organizations that develop the integrated engines.

## Privacy and security

The server binds exclusively to `127.0.0.1` and requires a random token created
during installation. Original files are never overwritten, and temporary
copies are removed after every job.

The service and dedicated browser load a small native guard that denies
non-loopback IPv4 and IPv6 connections. Chromium also runs with a separate
profile, a closed proxy, and external name resolution disabled.

Network access is required during installation to download packages and model
weights. Once installed, the engines work with local files and local caches.
The guard is a defense-in-depth measure, not a replacement for an operating
system firewall or sandbox.

> [!WARNING]
> OpenAI Privacy Filter reduces the risk of exposing personal information, but
> it does not guarantee complete anonymization or legal compliance. Always
> review results before sharing them.

## Requirements

The automated installer is currently supported and tested on:

- Linux x86_64 with a systemd user session;
- Python 3.10 or newer; Python 3.12 is recommended;
- [`uv`](https://docs.astral.sh/uv/), a C compiler, `curl`, and `sha256sum`;
- FFmpeg and ffprobe;
- [Ollama](https://ollama.com/) for GLM-OCR;
- Chromium, Chromium Browser, or Google Chrome.

The models require several gigabytes of disk space. Execution is configured for
CPU; GLM-OCR is accurate but can be very slow without hardware acceleration.

## Installation

Clone or download the repository, then run:

```bash
cd PrivacyStudio
./scripts/install.sh
```

The installer:

1. checks prerequisites without installing system packages;
2. creates three isolated Python environments;
3. downloads and verifies Picocrypt CLI and its GPL license;
4. compiles the network guard from its C source;
5. downloads and prepares every model;
6. installs a desktop launcher and user-level systemd service.

Every `scripts/install-*.sh` script can be rerun independently. Picocrypt
downloads are pinned by SHA-256 checksums, and OpenAI Privacy Filter is pinned
to a specific Git commit.

## Starting the application

Open **Privacy Studio Locale** from your application menu. Alternatively:

```bash
./scripts/open.sh
```

The service is not exposed to the LAN and is not automatically enabled at
system startup. The launcher starts it when needed.

## Local data

| Content | Default path |
| --- | --- |
| Queue, database, and temporary files | `~/.local/share/privacy-studio` |
| Picocrypt vault | `~/.local/share/privacy-studio/vault` |
| Results | `~/Documenti/Privacy Studio - Risultati` |
| Token and port | `~/.config/privacy-studio/environment` |
| Isolated Chromium profile | `~/.local/state/privacy-studio/chrome-profile` |

Data directories use `0700` permissions; tokens, databases, and volumes use
private file permissions. Picocrypt passphrases remain in memory only while a
job runs and are never stored.

## Development and tests

Static checks:

```bash
./scripts/check.sh
```

Lightweight isolated smoke test:

```bash
.venv/bin/python tests/smoke_local.py --core-only
```

Local conversion, Privacy Filter, and Picocrypt test:

```bash
.venv/bin/python tests/smoke_local.py --skip-heavy
```

Full test except for the slow GLM-OCR engine:

```bash
.venv/bin/python tests/smoke_local.py --skip-glm
```

Every test creates synthetic documents in temporary directories only. Pull
requests run Ruff, Python compilation, shell and JavaScript validation, and the
Bandit security scanner and core smoke test.

## Repository layout

```text
app/         API, persistent queue, and orchestration
workers/     isolated AI and PaddleOCR processes
static/      local interface and vendored assets
native/      network guard source
scripts/     installation, launch, and quality checks
packaging/   portable desktop and systemd templates
tests/       smoke tests with synthetic fixtures
```

## Licensing

Original Privacy Studio Locale code is released under the
[BSD Zero Clause (0BSD) License](LICENSE), an extremely permissive open-source
license that places no conditions on reuse of the original code.

Dependencies retain their respective licenses. In particular, Picocrypt CLI is
a separate GPL-3.0-only command-line program, and its binary is not committed to
this repository. Inter is OFL-1.1, Lucide is ISC, and the NVIDIA Parakeet model
is CC-BY-4.0. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for the
complete inventory and attribution.

This compatibility review is a prudent technical assessment, not legal advice.
Consider obtaining professional review before distributing a commercial binary
bundle.

## Contributing and security

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting changes. Do not
disclose vulnerabilities in public issues; follow [`SECURITY.md`](SECURITY.md).

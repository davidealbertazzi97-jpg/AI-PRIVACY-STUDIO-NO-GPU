<p align="center">
  <img src="static/icon.svg" width="88" height="88" alt="Privacy Studio">
</p>

<h1 align="center">AI Privacy Studio (No GPU)</h1>

<p align="center">
  <strong>Local privacy for teachers and professionals, with no GPU.</strong><br>
  Confidential documents stay on your computer and are never sent to external
  servers.
</p>

<p align="center">
  <a href="README.md">Italiano</a> · <strong>English</strong>
</p>

## What it does

**Privacy Studio Locale was born in my homelab from a personal need:** handling
confidential documents with local AI tools on an ordinary computer, without
depending on the cloud or an expensive GPU.

It is designed especially for **teachers and professionals** who work with
sensitive material and need to retain control over it. It runs entirely on CPU
and targets low- to mid-range consumer hardware: the goal is a product that is
genuinely accessible to everyone.

The application processes sensitive documents without entrusting their
contents to cloud services:

- selectable Italian or English interface, with a remembered preference;
- assisted redaction with OpenAI Privacy Filter and Italian rules;
- audio/video transcription with NVIDIA Parakeet TDT 0.6B v3;
- OCR with PaddleOCR, PP-StructureV3, or GLM-OCR through Ollama;
- PDF and Office conversion with Microsoft MarkItDown;
- encryption and decryption of Picocrypt `.pcv` volumes;
- a persistent queue and responsive UI with locally served assets.

This is an independent project and is not affiliated with the organizations
that build the integrated engines.

## Automatic installation

The full profile is prepared for:

| Operating system | Architecture |
| --- | --- |
| Linux | x86-64 |
| macOS | Apple Silicon (arm64) |
| Windows 10/11 | x86-64 |

On Linux or macOS:

```bash
cd PrivacyStudio
chmod +x install.sh start.sh
./install.sh
```

On Windows, from PowerShell:

```powershell
cd PrivacyStudio
.\install.ps1
```

From Command Prompt, use `install.cmd`; the wrapper applies a PowerShell policy
exception only to its own process and does not change system settings.

You do not need to install Python, `uv`, FFmpeg, Picocrypt, Ollama, or the
models manually. The installer downloads `uv` and verifies its checksum,
installs a managed Python 3.12, creates three isolated environments, and
prepares every engine. Direct Picocrypt and Ollama downloads are version-pinned
and SHA-256 verified. Parakeet and Privacy Filter are pinned to exact commits;
the GLM-OCR manifest is checked by digest, while PaddleOCR comes from the
pinned Python release and is validated through synthetic inference.

The full installation needs network access, time, and several gigabytes of
disk space. To omit Ollama and GLM-OCR, which add roughly 3 GB by themselves:

```bash
./install.sh --without-glm
```

Use the same flag with `.\install.ps1` in PowerShell. For the lightweight core
only, use `--core-only --skip-desktop`.

The full engine profile and smoke tests have been verified on Linux x86-64.
CI also verifies the core on macOS and Windows; the listed combinations follow
official PyTorch, PaddlePaddle, and other component wheels. NVIDIA lists Linux
as the preferred OS for Parakeet, so transcription on the two non-Linux
systems is best-effort until it is covered by complete hardware tests.

## Starting

On Linux/macOS:

```bash
./start.sh
```

On Windows:

```powershell
.\start.ps1
```

`start.cmd` is also available from Command Prompt.

The launcher creates a private key, starts any local services, waits for the
health check, and opens the browser. `Ctrl+C` stops processes started by that
session. On Linux, the installer can also add **Privacy Studio Locale** to the
application menu.

## Privacy and security limits

The server binds only to `127.0.0.1`, and every API requires a random token.
Python processes receive a cross-platform guard that rejects non-loopback
connections; Linux adds a second native guard when a C compiler is available.
The launcher starts a private Ollama instance on a dedicated loopback port with
cloud features disabled; it does not reuse an existing system Ollama server.
There is no telemetry, CDN, or remote inference.

Network access is allowed during installation to obtain software and models.
At runtime, engines use local files and caches. The default browser remains an
external program and may generate its own background traffic; the server does
not expose content on external network interfaces.

Original files are never overwritten. Working copies are removed when a job
finishes, and Picocrypt passphrases remain in RAM only for the duration of an
operation.

> [!WARNING]
> Automated redaction reduces risk, but it cannot guarantee that every piece
> of personal data is detected and is not a legal compliance assessment.
> Always review output before sharing it.

## Local data

| OS | Data and vault | Token and logs | Results |
| --- | --- | --- | --- |
| Linux | `~/.local/share/privacy-studio` | `~/.config/privacy-studio` | `~/Documents/Privacy Studio - Results` |
| macOS | `~/Library/Application Support/Privacy Studio` | same directory | `~/Documents/Privacy Studio - Results` |
| Windows | `%LOCALAPPDATA%\Privacy Studio` | same directory | `%USERPROFILE%\Documents\Privacy Studio - Results` |

On an Italian Linux system that has `~/Documenti` but no `~/Documents`, the
launcher automatically uses the localized folder. Downloaded artifacts
(`.venv*`, `bin`, and `models`) are excluded from Git.

## Installation through an AI coding agent

Anyone using a coding agent can copy the prepared prompt:

- [English prompt](docs/CODING_AGENT_PROMPT.en.md);
- [prompt in italiano](docs/CODING_AGENT_PROMPT.it.md).

It instructs the agent to detect the OS and architecture, use the official
installer, avoid administrator privileges, run local checks, and never upload
documents or secrets.

## Development and testing

```bash
./scripts/check.sh
.venv/bin/python tests/smoke_local.py --core-only
.venv/bin/python tests/smoke_local.py --skip-heavy
.venv/bin/python tests/smoke_local.py --skip-glm
```

Tests use synthetic documents in temporary directories only. The first command
runs static checks; the others exercise the core, light engines, and the full
profile except GLM-OCR, respectively.

## Repository layout

```text
app/             API, queue, and orchestration
workers/         isolated AI and PaddleOCR processes
static/          interface and local assets
runtime_guard/   cross-platform Python network guard
native/          additional Linux network guard
scripts/         bootstrap, launcher, and checks
packaging/       Linux desktop integration
tests/           smoke tests with synthetic fixtures
```

## License

Original code is released under the
[Apache License 2.0](LICENSE). It is a permissive open-source license that
allows use, modification, and redistribution, includes an express patent
grant, and provides warranty disclaimers and limitations of liability. It
requires preservation of the license and notices and identification of changed
files.

It was chosen over 0BSD for its express patent protection while remaining
highly permissive. Dependencies retain their licenses: Picocrypt CLI is a
separate GPL-3.0-only program downloaded by the user through the installer;
the FFmpeg binary in the inspected wheel is also a separate GPL process;
Parakeet is CC-BY-4.0; Inter is OFL-1.1, and Lucide is ISC. See the
[third-party notices](THIRD_PARTY_NOTICES.md).

This is a prudent technical assessment, not legal advice. The source
repository does not include downloaded Python environments, model weights, or
binaries. Anyone distributing a preassembled binary package must regenerate
the inventory and meet the obligations of every included artifact.

## Disclaimer

This is a personal and experimental project, created in part through
AI-assisted "vibe coding" and made available free of charge. It is provided
"as is", without warranties; use is at the user's own risk, and the author and
contributors assume no liability to the maximum extent permitted by law.

Redaction, OCR, and transcription can be wrong: every output must be reviewed
manually before it is used or shared. Read the
[complete disclaimer in English](DISCLAIMER.en.md) or
[in Italian](DISCLAIMER.md).

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before contributing. Follow
[SECURITY.md](SECURITY.md) for vulnerabilities instead of opening public
issues.

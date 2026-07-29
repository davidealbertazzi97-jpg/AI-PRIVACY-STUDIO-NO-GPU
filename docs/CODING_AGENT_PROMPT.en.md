# Coding-agent prompt — English

**English** · [Italiano](CODING_AGENT_PROMPT.it.md)

Replace `<REPOSITORY_URL>` with the public repository URL, then copy only the
following block into your coding agent.

```text
Install and make Privacy Studio Locale operational from:
<REPOSITORY_URL>

Goal: when finished, the application must be installed, verified, and ready
to start on the local computer, using only installers provided by the
repository.

Mandatory rules:
1. Work only inside the directory selected for Privacy Studio. Do not modify
   or delete unrelated files and do not use destructive commands.
2. Do not use sudo, administrator privileges, or system package managers. If
   an administrative action is required, stop and explain it.
3. Do not read, copy, upload, or use personal documents, tokens, passphrases,
   or other credentials. Tests must use only synthetic fixtures included in
   the project.
4. Network access is authorized only to clone/download the repository and for
   downloads performed by the installer. Do not add cloud services,
   telemetry, CDNs, or remote inference.
5. Do not disable the 127.0.0.1 binding, local token, runtime_guard,
   checksums, or version pins. Do not open firewall ports.
6. Do not commit, push, or modify the repository unless a fix is strictly
   required to complete installation; in that case, show me the problem and
   proposed change first.

Procedure:
1. Detect the operating system and architecture without changing computer
   state. Supported full profiles are Linux x86-64, macOS Apple Silicon
   arm64, and Windows x86-64. If the combination differs, do not force the
   installation; report the incompatibility.
2. If you are not already inside a valid project copy, clone
   <REPOSITORY_URL> into a new PrivacyStudio directory. If Git is unavailable
   but you can download a source archive from the same origin, download and
   extract it into a new directory.
3. Read README.en.md, THIRD_PARTY_NOTICES.md, and SECURITY.md. Check that
   install.sh/install.ps1, scripts/bootstrap.py, and requirement files exist.
4. Show free disk space and the installation plan by running:
   - Linux/macOS: python3 scripts/bootstrap.py --dry-run if python3 is already
     available; otherwise continue with install.sh, which installs Python.
   - Windows: py scripts\bootstrap.py --dry-run if the py launcher is already
     available; otherwise continue with install.ps1.
   The full profile uses several gigabytes. If space is clearly insufficient,
   stop without making a partial installation.
5. Run the official full installer:
   - Linux/macOS: chmod +x install.sh start.sh && ./install.sh
   - Windows PowerShell: .\install.ps1
   Do not replace these commands with manual installations. The installer
   must prepare uv, Python 3.12, isolated environments, FFmpeg, Picocrypt,
   OpenAI Privacy Filter, Parakeet, PaddleOCR, Ollama, and GLM-OCR. If the user
   explicitly asked to save space, use --without-glm.
6. If a download or checksum fails, do not bypass verification and do not use
   a random mirror. Report the URL, component, and error message without
   exposing tokens or sensitive paths.
7. When installation finishes, run available checks:
   - import the core with the Python interpreter in .venv;
   - run tests/smoke_local.py --core-only;
   - if the full installation succeeded, run
     tests/smoke_local.py --skip-glm;
   - on Linux, also run scripts/check.sh if development tools are present.
8. Start the application without opening the browser only long enough to
   verify /health on 127.0.0.1, then stop the process cleanly. Use
   scripts/start.py --no-browser with the .venv Python interpreter. Do not
   print the local token in logs or your report.
9. Provide a final report listing: detected platform, installed components,
   passed/failed checks, exact start command (./start.sh or .\start.ps1),
   results directory, and any limitation. Do not claim success for anything
   you did not verify.

Proceed autonomously while staying within these rules. Ask for confirmation
only if privileges, a choice that changes the requested profile, or a
potentially destructive operation is required.
```

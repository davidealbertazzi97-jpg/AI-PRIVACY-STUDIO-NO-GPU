# Contributing

Thanks for helping improve Privacy Studio Locale.

## Development

1. Use Python 3.12 and `uv`; Node.js and a C compiler are needed only for all
   optional checks on Linux.
2. Run `./install.sh --core-only --skip-desktop` on Linux/macOS or
   `.\install.ps1 --core-only --skip-desktop` on Windows.
3. Run `./scripts/install-netguard.sh` before Linux integration tests when a C
   compiler is available.
4. Run `./scripts/check.sh` before opening a pull request.
5. Run `.venv/bin/python tests/smoke_local.py --core-only` for the core smoke
   test. Full engine tests require the locally downloaded models.

Tests must use synthetic fixtures. Never commit real personal documents,
tokens, passphrases, model weights, generated volumes, or application state.

## Changes

- Keep the service bound to loopback.
- Preserve the runtime network guard and explicit local-only behavior.
- Do not add telemetry, CDN assets, or remote inference.
- Document new runtime dependencies and their licenses in
  `THIRD_PARTY_NOTICES.md`.
- Keep third-party code and binaries under their original licenses.

By submitting a contribution, you agree that it may be distributed under the
repository's GNU GPL version 3 only.

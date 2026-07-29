# Contributing

Thanks for helping improve Privacy Studio Locale.

## Development

1. Use Linux with Python 3.10 or newer, `uv`, Node.js, and a C compiler.
2. Run `./scripts/install-core.sh` for the lightweight backend environment.
3. Run `./scripts/install-netguard.sh` before integration tests.
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
repository's 0BSD License.

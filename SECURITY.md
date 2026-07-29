# Security policy

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability involving
authentication, file access, secret handling, network isolation, or encrypted
volumes.

Use GitHub's **Private vulnerability reporting** feature for the repository.
Include the affected version, reproduction steps, impact, and any suggested
mitigation. Avoid attaching real personal documents, passwords, access tokens,
or decrypted data.

## Scope

The application is designed for a single user on a supported local Linux,
macOS, or Windows workstation. It binds to loopback and requires a
per-installation token, but it is not designed to be exposed to a LAN or the
public internet.

OpenAI Privacy Filter assists with data minimization. It does not guarantee
anonymization, regulatory compliance, or removal of every sensitive datum.

Picocrypt volumes cannot be recovered without the correct passphrase.
The upstream Picocrypt CLI repository is archived and no longer receives
maintenance updates. The installer pins and verifies version 1.49, but users
with high-assurance requirements should evaluate this maintenance status
before relying on it for new sensitive archives.

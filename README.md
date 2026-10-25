# GarlicSMTP

**Development version:** `0.1.1a0`
**Release target:** `v0.1.1-alpha`
**Latest development commit reviewed for this documentation:** `8faf1c6`
**Status:** experimental Alpha; this documentation does not certify a clean installation or independent security audit.

GarlicSMTP is a privacy-oriented SMTP messaging application that communicates through Tor Onion Services. It includes a Linux desktop interface built with Tkinter, SMTP/IMAP components, and command-line mailbox operations.

> **Security warning:** GarlicSMTP has not undergone an independent professional security audit. Tor, encryption, and passing tests do not guarantee anonymity, confidentiality, integrity, or safety on a compromised device. Review [SECURITY.md](SECURITY.md) before use with sensitive data.

## Features

- Bidirectional SMTP messaging between Tor Onion Service peers; developer-to-Ubuntu-Virtual Machine and REAL Machine messaging has been exercised in earlier integration testing.
- Bidirectional SMTP messaging between Tor Onion Service peers; developer-to-KALI REAL Machine messaging has been exercised in earlier integration testing.
- Bidirectional SMTP messaging between Tor Onion Service peers; Ubuntu REAL Machine and KALI Real Machine messaging has been exercised in earlier integration testing.
- Message encryption using X25519 key discovery and pinning, HKDF, and ChaCha20-Poly1305, with Ed25519 signatures and verification.
- Received and Sent mailboxes and a persistent delivery queue using SQLCipher with a password-unlocked 32-byte data-encryption key (DEK).
- Encrypted local attachment content and metadata in authenticated GSAT v1 files.
- Application authentication and offline password recovery using recovery material; no default GUI password.
- Tkinter desktop interface for composing, receiving, and reading messages, including delivery retry support.
- Configurable Onion Service presence page, including optional custom HTML path validation in GUI preferences. Enabling a custom page requires a nonempty path to a file; changes take effect after restarting the relevant service/application.

These describe implemented functionality, not a security certification or a guarantee that every deployment configuration works.

## Verification status

The latest reported development run for the `0.1.1a0` preparation was **1,974 tests passed** (`python -m pytest -q`, 135.21 seconds), with `git diff --check` passing. These results were supplied from the WSL development environment; they do not establish a clean installation, reproducible release build, or independent audit.

Earlier developer ↔ Ubuntu VM integration tests included bidirectional messages and attachments. Earlier read-only checks of selected Received, Sent, and Queue databases found no plaintext SQLite headers, and selected attachment files exhibited the GSAT v1 format. These were limited checks, not proof that every file, backup, temporary artifact, or key is encrypted.

The inspected development environment used `sqlcipher3==0.6.3` and reported SQLCipher `4.12.0 community` / SQLite `3.51.1`. This is an observation of the development environment, not a specification for all future release artifacts.

## Supported environment and installation

The declared installer profile in `install/manifest.toml` targets **Ubuntu 24.04**. An Ubuntu 22.04 VM has also been used for GUI/integration checks, but that does not expand the declared supported installer profile. WSL is a development environment; no native Windows desktop release is claimed. Other operating systems and configurations are not validated here.

For a new checkout:

```bash
git clone https://github.com/giulsign/GarlicSMTP.git
cd GarlicSMTP
./install.sh
```

**Do not run `sudo ./install.sh`.** The installer may request elevated privileges for specific system prerequisites. A fresh clean-install test of the exact future `v0.1.1-alpha` release has not yet been documented as complete. Before installation, review `docs/quicklaunch.md` and `docs/installation-architecture.md` and confirm that they match the intended release. Never delete application data, recovery material, or Onion identity keys as a generic troubleshooting step.

For an already configured WSL development environment:

```bash
cd /mnt/c/garlicsmtp
source .venv/bin/activate
python -m garlicsmtp.gui
```

This development path is not a general installation recipe. The historical CLI `start` bootstrap limitation (failure without an unlocked DEK) must be rechecked against the current code before publication; do not assume it has been fixed or that it bypasses database encryption.

## Runtime dependencies

The declared Python runtime dependencies in `pyproject.toml` and `requirements.txt` are:

| Package | Requirement |
|---|---|
| dnspython | `>=2.8,<3` |
| cryptography | `>=46,<47` |
| sqlcipher3 | `==0.6.3` |

The Ubuntu installer profile also requires Tor, `python3-venv`, and `python3-tk` as system prerequisites. The GUI uses **Tkinter**, not PySide6. PySide6 remains installed in one historical development virtual environment but is **not used by the current project** and is not a declared runtime dependency. Transitive dependencies and native libraries may also be present; see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Release and versioning

The Python package currently declares `0.1.1a0`, intended for a future `v0.1.1-alpha` release. The `v0.1.1-alpha` tag, final source commit, distributable artifacts, and GitHub release have **not yet been confirmed**. Commit `8faf1c6` identifies a reviewed development state, not a frozen or audited release.

The earlier `v0.1.0-alpha.1` / `9bfc2f7` baseline is historical. Update this section only after the release has actually been tagged and published. Do not infer that a release exists from the version number alone.

## Security and vulnerability reports

See [SECURITY.md](SECURITY.md) for the security policy, known limits, and coordinated disclosure guidance. Send suspected vulnerabilities privately to **giulisign@gmail.com**. Do not attach passwords, DEKs, recovery keys, Onion Service private keys, Tor authentication cookies, mailbox contents, or live databases to reports.

## Licensing

GarlicSMTP is **source-available, not OSI-approved open source**. Original project code is made available under the **PolyForm Noncommercial License 1.0.0**. Uses outside that license's permissions, including certain commercial uses, require a separate written license. Third-party software retains its own licenses; see `LICENSE`, `NOTICE`, `COMMERCIAL-LICENSE.md`, `THIRD_PARTY_LICENSES.md`, `CONTRIBUTING.md`, and `CLA.md`.

Copyright © 2026 Giuliano Signorelli — GarlicSMTP Project.
Commercial licensing inquiries: **giulisign@gmail.com**.

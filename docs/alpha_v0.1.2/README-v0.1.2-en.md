# GarlicSMTP

**Release target:** `v0.1.2-alpha` (in preparation; not yet confirmed published)
**Current package metadata:** `0.1.2a0` in `pyproject.toml` and `garlicsmtp/__init__.py` (aligned and verified; release artifacts not yet validated)
**Status:** Experimental Alpha; no independent professional security audit or security warranty.

GarlicSMTP is a privacy-oriented SMTP messaging application that communicates through Tor Onion Services. It includes a Linux desktop interface built with Tkinter, SMTP/IMAP components, and command-line mailbox operations.

> **Security warning:** GarlicSMTP has not undergone an independent professional security audit. Tor, encryption, and passing tests do not guarantee anonymity, confidentiality, integrity, or safety on a compromised device. Review [SECURITY.md](SECURITY.md) before using sensitive data.

## Features

- Bidirectional SMTP messaging between Tor Onion Service peers; earlier integration testing exercised communication between a development machine and an Ubuntu virtual machine.
- Message encryption using X25519 key discovery and pinning, HKDF, and ChaCha20-Poly1305, with Ed25519 signatures and verification.
- Received and Sent mailboxes and a persistent delivery queue using SQLCipher with a password-unlocked 32-byte data-encryption key (DEK).
- Encrypted local attachment content and metadata stored in authenticated GSAT v1 files.
- Application authentication and offline password recovery using recovery material; no default GUI password.
- Tkinter desktop interface for composing, receiving, and reading messages, including delivery retry support.
- Configurable Onion Service presence page, including optional custom HTML file-path validation in GUI preferences. A custom page requires a nonempty path to a file; changes take effect after the relevant service or application is restarted.

These are descriptions of implemented functionality, not certification of security or universal deployment compatibility.

## Verification status

The latest reported full development test run for the v0.1.2-alpha preparation passed **1,993 tests** (`python -m pytest -q`). The internal review covered SMTP and IMAP listener restrictions, SMTP message-size enforcement, socket and thread cleanup, queue retry behavior, authentication state, logging privacy, and related regression tests. These results do **not** constitute an independent security audit, a reproducible-build verification, or proof of a clean installation from the final release artifacts.

Earlier developer-to-Ubuntu-VM integration tests exercised bidirectional messaging and attachments. Earlier read-only checks of selected Received, Sent, and Queue databases found no plaintext SQLite headers, and selected attachment files exhibited the GSAT v1 format. These observations do not prove that every local file, temporary artifact, backup, key, or deployment configuration is protected.

The inspected Python development environment included `sqlcipher3==0.6.3`, with SQLCipher `4.12.0 community` and SQLite `3.51.1` reported at runtime. Those observations are environment-specific, not guarantees about future distribution artifacts.

## Supported environment and installation

The installation manifest (`install/manifest.toml`) declares the following Linux profiles:

| Distribution | Declared version |
|---|---|
| Ubuntu | 24.04 |
| Kali Linux | 2026.1 |
| Debian | 13 |

These are **declared installer profiles**, not a claim that every configuration has undergone identical end-to-end release testing. Earlier Ubuntu 22.04 VM testing does not make it a declared profile. WSL is used for development; no native Windows desktop release is claimed.

For a new checkout:

```bash
git clone https://github.com/giulsign/GarlicSMTP.git
cd GarlicSMTP
./install.sh
```

**Do not run `sudo ./install.sh`.** The installer may request elevated privileges for specific system prerequisites. Review the installer and [docs/quicklaunch.md](docs/quicklaunch.md) and [docs/installation-architecture.md](docs/installation-architecture.md) before installation. A clean installation of the exact final v0.1.2-alpha release artifacts has not yet been established by the verification reported here. Never delete application data, recovery material, or Onion Service identity keys as a generic troubleshooting step.

For an already configured WSL development environment:

```bash
cd /mnt/c/garlicsmtp
source .venv/bin/activate
python -m garlicsmtp.gui
```

This is a development workflow, not a general installation recipe. The historically documented CLI `start` behavior when no DEK is available remains a release-verification item; do not assume that it has been resolved or that database encryption can be bypassed.

## SMTP limits

The current audited implementation enforces a **64 KiB maximum SMTP line length** and a **2 MiB (2,097,152-byte) maximum SMTP message size**. The attachment-size limit remains **1 MiB (1,048,576 bytes)**. These are separate limits; a message containing attachments must still satisfy the total message-size limit.

## Runtime dependencies

The declared Python runtime dependencies in `pyproject.toml` and `requirements.txt` are:

| Package | Requirement |
|---|---|
| dnspython | `>=2.8,<3` |
| cryptography | `>=46,<47` |
| sqlcipher3 | `==0.6.3` |

The Linux installer profiles require Tor, `python3-venv`, and `python3-tk` as system prerequisites. The desktop GUI uses **Tkinter**, not PySide6. A package installed in a developer's virtual environment is not necessarily a distributed dependency. Transitive Python packages and native libraries have their own license obligations; see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Release and versioning

**`v0.1.2-alpha` is the intended next release, not a claim that its Git tag, final commit, distribution archives, or GitHub release already exist.** At the time of this documentation review, `pyproject.toml` still declares `0.1.1a0`, the installed editable package reports `0.1.0a0`, and existing `dist/` archives are named for `0.1.0a0`. These are development-state discrepancies to resolve during release consolidation, not valid v0.1.2-alpha artifacts.

Before publishing, align package metadata, build and inspect new artifacts, verify license notices and security-relevant documentation, rerun appropriate tests, and confirm the actual release commit and tag. Historical release tags and commits must not be represented as the new release baseline.

## Security and vulnerability reports

See [SECURITY.md](SECURITY.md) for the security policy, known limits, and coordinated-disclosure guidance. Report suspected vulnerabilities privately to **giulisign@gmail.com**. Do not attach passwords, DEKs, recovery secrets, Onion Service private keys, Tor authentication cookies, mailbox contents, or live databases to reports.

## Contributing

Contributions and independent review are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the actual [CLA.md](CLA.md) before submitting a code contribution. Security-sensitive findings should follow the private reporting process in [SECURITY.md](SECURITY.md).

## Licensing

GarlicSMTP is **source-available, not OSI-approved open source**. Original project code is available under the **PolyForm Noncommercial License 1.0.0**. Uses outside the permissions of that license, including certain commercial uses, require a separate written license. Third-party components retain their own licenses. See [LICENSE](LICENSE), [NOTICE](NOTICE), [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md), [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [CLA.md](CLA.md).

Copyright © 2026 Giuliano Signorelli — GarlicSMTP Project.
Commercial licensing inquiries: **giulisign@gmail.com**.

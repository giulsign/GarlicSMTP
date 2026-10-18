# GarlicSMTP

**Current release baseline: `v0.1.0-alpha.1`**
**Validated source commit: `9bfc2f7`**
**Status: public Alpha candidate — Git tag and GitHub release publication not yet confirmed.**

GarlicSMTP is a privacy-oriented SMTP messaging application for communicating through Tor Onion Services. Its Linux desktop GUI is implemented with Tkinter; the Python application also provides SMTP/IMAP components and command-line mailbox operations.

> **Security notice:** This is experimental Alpha software. It has not undergone an independent professional security audit. Tor and cryptography do not guarantee anonymity or security against a compromised endpoint.

## Features in the validated baseline

- Bidirectional SMTP messaging between Tor Onion Service peers, with real developer ↔ Ubuntu VM validation.
- End-to-end message encryption using X25519 key discovery/pinning, HKDF and ChaCha20-Poly1305, with Ed25519 signing and verification.
- Received and Sent mailboxes and a persistent delivery queue, stored using SQLCipher and a password-unlocked 32-byte data encryption key (DEK).
- Encrypted local attachment content and metadata in authenticated GSAT v1 files.
- Application authentication and offline password recovery using recovery material; no default GUI password.
- Tkinter desktop interface for composing, receiving and viewing messages, plus delivery retry support.

**Validation:** The development test suite reported **1844 passed**. Real self-send and bidirectional developer/Ubuntu VM sends succeeded, including attachments. Read-only checks found no plaintext SQLite headers in Received, Sent or Queue on either system, and checked the encrypted attachment format. These checks are not a complete security audit.

## Supported environment and getting started

The historically validated target is **Ubuntu 24.04 Desktop**. Windows/WSL is used for development, not as a native Windows desktop release. Other platforms are not validated.

```bash
git clone https://github.com/giulsign/GarlicSMTP.git
cd GarlicSMTP
./install.sh
```

Do **not** run `sudo ./install.sh`. This installer workflow was validated historically; a fresh clean-install of the exact `v0.1.0-alpha.1` package and its updated SQLCipher dependencies has **not** been revalidated as part of the latest checks. Review `docs/quicklaunch.md` and `docs/installation-architecture.md` before installation. Do not delete application data or Onion identity keys to repair an installation.

For development from an already configured WSL virtual environment:

```bash
cd /mnt/c/garlicsmtp
source .venv/bin/activate
python -m garlicsmtp.gui
```

The CLI runtime `start` path has a known functional limitation: the bootstrap is invoked without a DEK and fails closed. This is **not** a confirmed plaintext database bypass. The authenticated mailbox CLI is a separate path.

## Release and versioning

`v0.1.0-alpha.1` names the intended frozen baseline at commit `9bfc2f7`. Publishing a matching Git tag, release artifacts and GitHub release requires a separate explicit release action; this README does not attest that they already exist. Later features must be developed separately from this frozen baseline.

## Licensing

GarlicSMTP is **source-available**, not OSI-approved open source. Original project code is licensed under the **PolyForm Noncommercial License 1.0.0**; commercial use outside its permissions requires a separate written license. See `LICENSE`, `NOTICE`, `COMMERCIAL-LICENSE.md`, `THIRD_PARTY_LICENSES.md`, `CONTRIBUTING.md` and `CLA.md`.

Copyright © 2026 Giuliano Signorelli — GarlicSMTP Project.
Commercial licensing: giulisign@gmail.com

## Security

See [`SECURITY.md`](SECURITY.md) for responsible disclosure and limitations. Never upload passwords, DEKs, recovery keys, Onion Service private keys, authentication cookies or live application databases in bug reports.

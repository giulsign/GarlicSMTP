# GarlicSMTP

**Version:** `0.1.2a0` · **Git tag:** [`v0.1.2-alpha`](https://github.com/giulsign/GarlicSMTP/tree/v0.1.2-alpha) · **Maturity:** Experimental Alpha

GarlicSMTP is a privacy-oriented messaging application for communication between Tor Onion Service peers. It combines SMTP and IMAP components, a Tkinter desktop interface, local mailbox storage, and a persistent outgoing delivery queue.

The `v0.1.2-alpha` tag is present on GitHub, as confirmed by the project maintainer. **A Git tag is not the same as a GitHub Release with downloadable, validated distribution artifacts.** This README does not claim that such artifacts have been published or qualified.

> **Security notice:** GarlicSMTP has not undergone an independent professional security audit or certification. Tor connectivity, encryption and successful experimental tests do not guarantee anonymity, complete network isolation, security on a compromised device, or production readiness. Read [SECURITY.md](SECURITY.md) before handling sensitive information.

## Features

- Bidirectional SMTP messaging between GarlicSMTP Onion Service peers.
- Message encryption using X25519-based peer-key discovery/pinning, HKDF and ChaCha20-Poly1305, with Ed25519 signing and signature verification in the documented messaging paths.
- Separate **Received** and **Sent** mailboxes and a persistent outgoing queue with retry scheduling.
- SQLCipher-backed Received, Sent and Queue databases, unlocked with a 32-byte data-encryption key (DEK) in the documented application paths.
- Authenticated, encrypted attachment storage using the GSAT v1 format. Exported attachments are readable at their destination.
- GUI account authentication and offline recovery-key support. Recovery material protects access to the existing DEK; it is not a backup of the application data or Onion identity.
- Tkinter desktop interface for composing and viewing messages, monitoring Tor/services and requesting retries of pending deliveries.
- Optional Onion HTTP presence page with configurable custom HTML through GUI preferences.

**Sent is not a delivery receipt.** It records messages accepted for sending by the application; remote delivery is a separate event. **Retry pending** makes pending messages eligible for another attempt by the queue worker; it does not itself prove successful transmission.

## Verification and evidence

The latest reported full development regression for this release preparation passed **1,993 tests**. This result describes a development test run; it is not proof that the exact tagged distribution artifacts underwent a reproducible build, fresh installation or independent security assessment.

The project's [integrated audit and operational verification report](docs/GarlicSMTP_Integrated_Audit_2026-11-05_T8.md) records additional experimental checks on WSL2 Ubuntu and an Ubuntu 24.04 VirtualBox VM:

- **T0–T4:** successful Onion-to-Onion SMTP communication in both directions in the tested configurations, including tests with conventional DNS traffic on TCP/UDP port 53 blocked and isolated Tor bootstrap scenarios.
- **T8:** successful bidirectional Onion SMTP delivery while temporary `nftables` OUTPUT rules on both hosts blocked observed direct outbound connections from non-Tor processes, allowing Tor-mediated connectivity. SOCKS5 handshakes and Tor-mediated CONNECT operations were observed. The temporary filtering rules were removed after the experiment.

**Scope of these results:** they support operational feasibility in the configurations tested. They do **not** establish universal absence of DNS or traffic leaks, complete isolation of every network path, automatic recovery from all Tor failures, anonymity guarantees, or security certification. Tor itself uses underlying IP connectivity to reach its relays.

The audit includes dated historical findings and subsequent follow-up notes. Their original revision boundaries must be preserved: an issue identified in an earlier source snapshot must not automatically be described as present or resolved in the tagged version without issue-specific evidence.

## Linux installation

The documented installer manifest declares these profiles:

| Distribution | Version |
| --- | --- |
| Ubuntu | 24.04 |
| Kali Linux | 2026.1 |
| Debian | 13 |

These are declared installation profiles, not a guarantee of equivalent qualification of every release artifact and system configuration. WSL Ubuntu is a documented development environment, **not** a native Windows release target. Native Windows, macOS and other Linux distributions are not claimed as validated targets.

To obtain the confirmed tag rather than an unspecified moving default branch:

```bash
git clone --branch v0.1.2-alpha --single-branch https://github.com/giulsign/GarlicSMTP.git
cd GarlicSMTP
./install.sh
```

Run the installer as an ordinary user: **do not use `sudo ./install.sh`**, `sudo pip` or a global Python package installation. The installer may request authorization for system prerequisites. Tor is a system prerequisite. Read the [Quicklaunch guide](docs/quicklaunch.md) and [Installation Architecture](docs/installation-architecture.md) before installation or any operation involving existing data.

After installation, the documented desktop launcher or the following executable may be used:

```bash
~/.local/share/garlicsmtp/venv/bin/garlicsmtp-gui
```

The first-run setup uses personal credentials and recovery material. Store the offline recovery key securely **off the device**. If Tor-cookie group membership was changed, a full graphical logout and login may be necessary.

### Development startup

For an existing WSL checkout with its virtual environment already configured:

```bash
cd /mnt/c/garlicsmtp
source .venv/bin/activate
python -m garlicsmtp.gui
```

The development entry point and installed launcher have different configuration/path contexts and must not be treated as interchangeable installation methods.

## Message and attachment limits

The documented SMTP input limits are:

| Limit | Value |
| --- | --- |
| SMTP input line | 64 KiB |
| Total SMTP message | 2 MiB (2,097,152 bytes) |
| Application attachment | 1 MiB (1,048,576 bytes) |

The message and attachment limits are separate. Remote peers may apply additional restrictions.

## Runtime and data protection

GarlicSMTP requires **Python 3.12 or newer** and uses Tkinter for its desktop GUI, not PySide6. The documented Python runtime requirements are `dnspython>=2.8,<3`, `cryptography>=46,<47` and `sqlcipher3==0.6.3`; the installer also manages relevant Linux system prerequisites, including Tor and Tkinter.

The documented persistent installation root is `~/.local/share/garlicsmtp/`, with configuration, credentials, encrypted databases, attachments and identities managed by their respective components. The source of truth for application paths is the implementation's `ApplicationPaths.for_user()`.

Encryption at rest in the documented application stores does **not** imply comprehensive protection of exports, backups, temporary files, logs, private keys, historical plaintext material or a compromised operating system. No universally validated backup/restore or legacy plaintext migration procedure is claimed here. **Never delete databases, recovery material or Onion Service identities as a generic troubleshooting step.** Uninstallation can irreversibly remove application state and identities.

## Documentation

- [Quicklaunch](docs/quicklaunch.md) — installation and first start.
- [Installation Architecture](docs/installation-architecture.md) — installation design, persistence and operational boundaries.
- [Handbook](docs/GarlicSMTP-Handbook.txt) — application use, credentials, Tor and limitations.
- [Integrated audit and T8 report](docs/GarlicSMTP_Integrated_Audit_2026-11-05_T8.md) — historical static findings and experimental evidence.
- [Changelog](CHANGELOG.md) — release history and dated development checkpoints.
- [Security policy](SECURITY.md) — vulnerability reporting and security limitations.

Historical material under `docs/alpha_v0.1.0/`, `docs/alpha_v0.1.1/` and `docs/alpha_v0.1.2/` documents earlier snapshots and should not be confused with current canonical guidance.

## Security reports and contributions

Please report suspected vulnerabilities privately using the contact and process in [SECURITY.md](SECURITY.md). Do not include passwords, DEKs, recovery secrets, Onion Service private keys, Tor cookies, mailbox contents or live databases in a report.

Contributions and independent review are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CLA.md](CLA.md) before submitting code contributions.

## Licensing

GarlicSMTP is **source-available, not OSI-approved open source**. Original project code is licensed under the **PolyForm Noncommercial License 1.0.0**; commercial permissions outside its terms require a separate written agreement. Third-party components retain their respective licenses.

See [LICENSE](LICENSE), [NOTICE](NOTICE), [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md) and [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

Copyright © 2026 Giuliano Signorelli — GarlicSMTP Project.

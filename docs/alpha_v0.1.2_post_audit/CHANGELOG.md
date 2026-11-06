# Changelog

This changelog records dated development milestones, documented changes, and experimental verification. Historical statements describe what was known at the time; they are not assertions about the present status of earlier tags or releases. Developer-reported checks and operator-executed experiments are not independent security certification.

## v0.1.2-alpha (`0.1.2a0`) — Tagged Alpha baseline, 5 November 2026

**Version and source status:** `pyproject.toml` and `garlicsmtp/__init__.py` declare `0.1.2a0`. The project maintainer confirms that source consolidation is complete and the `v0.1.2-alpha` Git tag exists on GitHub. These are maintainer confirmations, not an independent inspection of the tagged tree. A Git tag does **not** by itself establish that a GitHub Release, validated wheel, or source-distribution artifact has been published.

### Security and reliability changes recorded during release preparation

- Enforced an SMTP input-line limit of **64 KiB** and total SMTP message DATA limit of **2 MiB (2,097,152 bytes)**; the separate attachment limit remains **1 MiB (1,048,576 bytes)**.
- Restricted configurable SMTP and IMAP listeners to loopback addresses, including the `127.0.0.x` range.
- Improved socket, connection, and thread lifecycle cleanup in TCP, SOCKS5, text transport, SMTP transport, and SMTP/IMAP startup/shutdown paths. These changes do not establish that every historical lifecycle concern has been closed.
- Improved queue handling of unexpected delivery exceptions with retry/backoff behavior.
- Moved installer IMAP-password validation ahead of avoidable installation side effects.
- Strengthened test assertions and addressed duplicate/shadowed pytest definitions identified in the October static review.

### Development checks and documentation

- **1,993 tests passed** in the reported full `python -m pytest -q` development regression following the recorded changes. This is a development result, not a verified run against a packaged or tagged distribution.
- Reviewed logging privacy, SQLCipher queue transaction recovery, IMAP authentication/session state, and incomplete SMTP DATA handling on EOF. The review recorded no additional change required for those specific inspected paths; it was not an exhaustive security assessment.
- Reviewed installed third-party Python dependency metadata and license material. The development environment reported `dnspython 2.8.0`, `cryptography 46.0.7`, `sqlcipher3 0.6.3`, `cffi 2.1.1`, and `pycparser 3.0`. These observations are not a verified inventory of the eventual distribution or every native component.
- The installation manifest was documented as declaring **Ubuntu 24.04**, **Kali 2026.1**, and **Debian 13** profiles. This is not evidence of a fresh clean installation from the exact tagged artifacts on all three platforms.
- Updated the documentation and audit record for the `v0.1.2-alpha` baseline, while retaining the revision boundaries of earlier findings.

### Experimental Tor/SMTP verification — 5 November 2026

The [integrated audit and operational report](docs/GarlicSMTP_Integrated_Audit_2026-11-05_T8.md) records operator-executed experiments on WSL2 Ubuntu and an Ubuntu 24.04 VirtualBox VM:

- **T0–T4:** bidirectional Onion-to-Onion SMTP messaging succeeded in the tested scenarios, including conventional DNS TCP/UDP port 53 filtering and isolated Tor bootstrap checks.
- **T8:** bidirectional Onion-to-Onion SMTP messaging succeeded while temporary `nftables` OUTPUT filtering was active on both hosts. Direct outbound connection failures were observed, as were successful local Tor SOCKS5 handshakes and SOCKS CONNECT operations. The temporary filtering table was removed on both hosts after testing.

**Evidence boundary:** these tests support operational feasibility in the two tested environments. They do not demonstrate universal absence of DNS or network leaks, complete isolation of all network paths, guaranteed anonymity, resilience to every Tor outage, or a professional security certification. The exact tested source commit and reproducible artifact hashes were not recorded as part of the experiment.

### Validation and publication boundaries

The following activities are **not established by the available documentary record** and must not be described as completed merely because the Git tag exists:

- Publication and validation of a GitHub Release with fresh `0.1.2a0` wheel/source-distribution artifacts, bundled notices, and native-component inventory.
- Clean-install qualification and any supported upgrade/migration procedure against the exact tagged artifacts on every declared Linux profile.
- A comprehensive backup/restore or legacy plaintext-data migration procedure.
- An independent professional security or cryptographic audit.
- Issue-specific closure of all historical static-audit findings. In particular, the October audit's **A-14** SQLite IMAP UID monotonicity finding and **D-09** Ubuntu manifest finding concern earlier reviewed revisions; the later documentation does not establish release-specific closure of both. Their historical status must not be mistaken for proof that the same defects exist in the current tag.

## v0.1.1-alpha (`0.1.1a0`) — Development checkpoint, 25 October 2026

**Historical status:** At this checkpoint, release publication and distribution artifacts had not been independently confirmed. The subsequent 27 October static review observed a **local** `v0.1.1-alpha` tag at commit `f8ad5eeb72c626302ec373f8943ed0d21f06b441`; that observation did not independently verify GitHub publication. Development commit `8faf1c6` was another reviewed reference point, not itself a release tag.

### Changed and fixed

- Added configurable optional custom HTML for an Onion HTTP presence page, with GUI preferences and configuration support.
- Validated the custom HTML path when the page is enabled: it must be nonempty and refer to a file, not a directory. Relevant settings take effect after restart.
- Updated English-language GUI preferences for the optional Onion page.
- Updated package/application version declarations to `0.1.1a0` **at that historical checkpoint**; these were subsequently superseded by `0.1.2a0`.

### Historical validation

- **1,974 tests passed** in the WSL development environment (`python -m pytest -q`, reported duration 135.21 seconds); `git diff --check` passed.
- The Ubuntu 22.04 VM GUI was checked during development. Ubuntu 22.04 was not thereby added to the declared Ubuntu 24.04 installation profile.
- The installed `sqlcipher3==0.6.3` module reported SQLCipher `4.12.0 community` and SQLite `3.51.1`; this was an environment observation, not a full binary/security audit.

At the time of this checkpoint, fresh release packaging, clean-install/upgrade validation, complete third-party component inventory, and the historical CLI `start`/DEK behavior still required release-specific verification. These are historical observations, not a current GitHub status report.

## v0.1.0-alpha.1 — First Alpha baseline (19 October 2026)

**Historical baseline source commit:** `9bfc2f7`. At the time this entry was recorded, creation/publication of the corresponding tag and GitHub Release had not been confirmed. No current publication claim is inferred from that historical note.

### Added and consolidated

- Tkinter desktop GUI with account setup, authentication, composition, and separate Received and Sent views.
- Bidirectional Tor Onion SMTP messaging, Ed25519 signature verification, X25519-based peer-key trust/pinning, and encrypted messaging paths.
- SQLCipher protection for Received, Sent, and Queue databases using a password-unlocked data-encryption key (DEK).
- GSAT v1 authenticated encrypted attachment storage, including metadata.
- Offline application password recovery and DEK rewrapping/key-rotation flows.
- GUI background sending and improved pipeline diagnostics.

### Historical validation and limitations

- **1,844 development tests passed** in the then-reported complete suite.
- Developer and Ubuntu VM self-send and bidirectional messaging were reported successful, including attachments.
- Selected read-only checks found no plaintext SQLite header in the three application databases and observed GSAT v1 attachment format.
- The CLI `start` path without a DEK failed closed at that baseline; this was a functional limitation, not evidence of plaintext access. Its later status is not established here.
- No independent professional security audit, verified legacy-data migration, or fresh release-artifact installation qualification was claimed.

## v0.0.1-alpha — Historical development baseline

- Initial project structure and Python package definition.
- Early development milestone, distinct from `v0.1.0-alpha.1`.

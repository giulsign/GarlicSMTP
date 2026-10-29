# Changelog

This changelog distinguishes historical validation from work preparing the next Alpha release. Entries describe documented changes and checks, not an independent security audit.

## v0.1.2-alpha (`0.1.2a0` target) — Release preparation, 29 October 2026

**Status:** Candidate under preparation, not a confirmed published release. The Git tag, final source commit, release artifacts, and GitHub release have not yet been verified or published as part of this preparation. The project and application version declarations have since been aligned to `0.1.2a0`, and the full suite passed 1,993 tests. Previously inspected installed metadata and `dist/` artifacts reflected `0.1.0a0`; fresh release artifacts remain to be built and verified. This entry does not claim that `0.1.2a0` is already installed or tagged.

### Security and reliability changes

- Strengthened SMTP input bounds: maximum accepted SMTP line size **64 KiB** and maximum message DATA size **2 MiB (2,097,152 bytes)**. The attachment size limit remains **1 MiB (1,048,576 bytes)**.
- Restricted configurable SMTP and IMAP listener hosts to loopback addresses, while permitting addresses in the `127.0.0.x` range.
- Improved socket, connection, and thread lifecycle cleanup in TCP, SOCKS5, text transport, SMTP transport, and SMTP/IMAP service startup and shutdown paths.
- Improved delivery-queue handling of unexpected exceptions so failed attempts follow retry/backoff behavior rather than immediately repeating in a tight loop.
- Ensured installer IMAP-password validation takes place before installation side effects.
- Strengthened test assertions and removed duplicate/shadowed tests found during the internal review.

### Review and validation

- **1,993 tests passed** in the reported full `python -m pytest -q` development-suite run after the reviewed changes. This is a developer-reported test result, not an independent security audit or clean-install certification.
- Reviewed logging privacy, SQLCipher queue transaction recovery, IMAP authentication/session state, and incomplete SMTP DATA handling on EOF; no additional production change was required for those specific checks.
- Reviewed third-party Python dependency metadata and installed license files. Observed `dnspython 2.8.0` (ISC), `cryptography 46.0.7` (Apache-2.0 OR BSD-3-Clause), `sqlcipher3 0.6.3` (installed license file), `cffi 2.1.1` (MIT-0), and `pycparser 3.0` (BSD-3-Clause). Native extension linkage was inspected with `ldd`; this does not establish a complete inventory of statically included components.
- Confirmed that `install/manifest.toml` declares installer profiles for **Ubuntu 24.04**, **Kali 2026.1**, and **Debian 13**. Declared profiles are not, by themselves, a claim of validated installation from final release artifacts.
- Updated release-candidate documentation for the current audit and release-preparation state.

### Checks remaining before publication

- Align package and application version declarations with the intended `0.1.2a0` release and verify the final Git state.
- Build and inspect fresh wheel/source-distribution artifacts, including included files, native components, third-party licenses, and required notices; historical `0.1.0a0` files in `dist/` do not validate this candidate.
- Validate clean installation and any supported upgrade/migration path on the intended target environments, and record actual results.
- Recheck the historical CLI `start` behavior when the DEK is unavailable; do not assume that the earlier limitation has been fixed.
- Verify the final release commit, tag, and public publication only after those actions actually occur.
- Obtain independent security review where possible; no independent professional security audit is claimed.

## v0.1.1-alpha (`0.1.1a0`) — 25 October 2026

**Status:** Release preparation; the `v0.1.1-alpha` Git tag, final release commit, distribution artifacts and GitHub publication have not been confirmed. Development commit `8faf1c6` is a reviewed reference point, **not** a release tag.

### Changed and fixed

- Added support for configuring an optional custom HTML presence page for an Onion Service, including related GUI preferences and configuration settings.
- Improved GUI preference validation: when a custom Onion page is enabled, the HTML path must be nonempty and refer to a file rather than a directory. The selected settings take effect after the relevant restart.
- Updated English-language GUI preference text associated with the custom Onion page.
- Updated package version declarations to `0.1.1a0` in `pyproject.toml`, `garlicsmtp/__init__.py`, and the corresponding installation-manifest tests as part of release preparation.

### Validation reported during preparation

- **1,974 tests passed** with `python -m pytest -q` in the WSL development environment (135.21 seconds); `git diff --check` passed.
- The Ubuntu 22.04 VM GUI was checked during development. The declared installer profile remains Ubuntu 24.04; this does not certify installation on either version from final release artifacts.
- The installed `sqlcipher3==0.6.3` module reported SQLCipher `4.12.0 community` and SQLite `3.51.1`. This is an environment observation, not a full binary or security audit.

### Release checks still open

- Create and verify the final Git tag, release commit, release artifacts and GitHub publication.
- Revalidate a clean installation and any upgrade or migration path intended to be supported; no such certification is claimed here.
- Review actual packaged third-party components, notices, licenses and native libraries.
- Confirm the current status of the historical CLI `start` bootstrap limitation by inspecting code and tests.
- No independent professional security audit has been performed.

## v0.1.0-alpha.1 — First official Alpha baseline (release preparation, 19 October 2026)

Baseline source commit: `9bfc2f7`. At the time this historical entry was written, creation of the Git tag and publication of the GitHub release had not been confirmed. That statement records the status **at that time**, not a fresh check of GitHub today.

### Added and consolidated

- Tkinter desktop GUI with authentication, account setup, message composition, Received and Sent views.
- Bidirectional Tor Onion SMTP messaging with end-to-end encryption, Ed25519 authenticity verification and X25519 trust/pinning.
- SQLCipher encryption at rest for Received, Sent and Queue databases, using a password-unlocked DEK.
- Authenticated GSAT v1 encrypted attachment storage, including metadata.
- Offline application password recovery and DEK rewrapping/key-rotation flows.
- GUI background send handling and improved pipeline diagnostics.

### Validation recorded for that baseline

- **1,844 developer tests passed** in the then-confirmed full suite.
- Developer and Ubuntu VM: self-send and bidirectional delivery validated, including attachments.
- Both systems: checked Received, Sent and Queue databases lacked plaintext SQLite headers; selected attachment GSAT v1 format checked read-only.

### Known limitations recorded for that baseline

- No independent professional security audit; Alpha use only.
- CLI `start` bootstrap without a DEK failed closed; this was a functional limitation, not evidence of plaintext access. Current status requires rechecking.
- Installer/dependencies and clean-install packaging for that exact baseline had not been freshly revalidated in the recorded milestone.
- No existing-data migration or upgrade-path certification was claimed.

## v0.0.1-alpha — Historical development baseline

- Initial project structure and Python package definition.
- Early development milestone (historical tag, distinct from `v0.1.0-alpha.1`).

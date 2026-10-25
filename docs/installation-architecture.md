# GarlicSMTP — Installation Architecture — 0.1.1a0

**Document status:** release-candidate architecture; 25 October 2026. **Release target:** `v0.1.1-alpha`.

## 1. Scope, source hierarchy and release state

This is the **current architecture and release-readiness specification**, not evidence that an installer was executed during this documentation update. Sources: the four supplied architecture documents (historical baseline dated 6 September; updates 8, 13, 18 and 19 October 2026), and the subsequent development checkpoints provided for the `0.1.1a0` candidate. Where historical statements conflict, the newer dated implementation evidence takes precedence **only for implementation status**, not for the original requirements.

- **Candidate:** Python package version `0.1.1a0`; proposed Git tag `v0.1.1-alpha` (not confirmed as created or released).
- **Development baseline:** commit `8faf1c6` reported pushed on `main`; complete development suite **1,974 passed**. This is not a newly executed test run for this document.
- **Historical checkpoint:** commit `9bfc2f7`, 1,844 passed and developer ↔ Ubuntu VM SMTP/attachment exchange. Those checks are not a fresh installer qualification for `0.1.1a0`.
- **Target platform:** Ubuntu 24.04 Desktop / GNOME for the installation manifest; Ubuntu 22.04 GUI VM observations are not a substitute for Ubuntu 24.04 clean-install validation. Windows WSL is a development environment, not a native Windows release target.

## 2. Installation ownership and flow

The installer is infrastructure; it must not reproduce application responsibilities or change tested runtime behavior without a documented requirement and tests. `install/manifest.toml`, `pyproject.toml`, generated installer components and `ApplicationPaths.for_user()` must be reconciled before a release.

```text
CHECK → SYSTEM PREREQUISITES → PYTHON → ISOLATED VENV
      → INSTALL DEPENDENCIES → VERIFY ENVIRONMENT
      → FIRST-RUN SETUP → VERIFY GARLICSMTP → COMPLETE
```

Run `./install.sh` from the repository root as a **normal user**. Never use `sudo ./install.sh`, `sudo pip`, global `pip install`, `pip --user`, or `--break-system-packages`. System package installation may request authorization; the runtime and its persistent state must remain owned by the ordinary user. Detect before modifying; preserve an existing compatible installation. No `curl | sh` or implicit remote execution.

Production entry point: `~/.local/share/garlicsmtp/venv/bin/garlicsmtp-gui` (or installed desktop launcher). Development entry point from the existing checkout and active `.venv`: `python -m garlicsmtp.gui`. These use different path/configuration contexts and must not be conflated. Current GUI is **Tkinter**, not PySide6/Qt. A complete graphical logout/login may be necessary after adding the user to `debian-tor`.

## 3. Versioned runtime and dependency boundary

Python **>=3.12** and a dedicated virtual environment. The reported `pyproject.toml` runtime requirements are `dnspython>=2.8,<3`, `cryptography>=46,<47`, and `sqlcipher3==0.6.3`; setuptools >=77 is a build dependency. PySide6 in a developer virtual environment is **not** a GarlicSMTP runtime dependency. Confirm actual install/build behavior on the target VM rather than treating dependency metadata alone as packaging evidence.

Tor is a system prerequisite. Tor Control is local (`127.0.0.1:9051` in the documented configuration), with **SAFECOOKIE** using the cookie advertised by the active Tor instance. GarlicSMTP manages its Onion Service lifecycle; it must preserve the real Onion identity and derive the canonical mail identity from that hostname. `test.onion` is not a deployed identity. GUI, IMAP authentication and Onion identities are separate concepts.

## 4. Persistent layout and ownership

`ApplicationPaths.for_user()` is authoritative. The documented installation root is `~/.local/share/garlicsmtp/`:

| Path | Purpose / boundary |
|---|---|
| `venv/` | Isolated installed Python environment |
| `config/settings.toml` | Runtime configuration; preserve existing user settings |
| `state/account-credentials.json` | GUI account credentials, recovery and wrapped-key state as implemented; restrictive permissions |
| `data/mailboxes.db` | Received message store, SQLCipher |
| `data/sent.db` | Sent message store, SQLCipher |
| `state/queue.db` | Delivery queue, SQLCipher |
| `data/attachments/` | Encrypted attachment store (GSAT v1) |

The table is **not an exhaustive file manifest**. Identity files, private keys, trust pins and Tor state are managed by their responsible components; inspect the actual paths and installer source before changing them. Existing state must never be silently overwritten or regenerated. Software installation, upgrade, repair, password recovery, migration and uninstall are separate operations.

## 5. Cryptographic unlock and at-rest storage

The implemented design uses an independent **32-byte DEK**, password-based wrapping and offline recovery-key wrapping. The GUI must unlock before constructing encrypted stores and starting receive services; failed unlock is fail-closed. Offline recovery changes the application password without regenerating the DEK. Preserve the recovery key outside the device; it is not a routine alternate login.

The documented `connect_encrypted_sqlite(path, *, dek)` validates the 32-byte DEK, checks SQLCipher availability via `PRAGMA cipher_version`, sets the key and verifies the database by querying `sqlite_master`. `SQLiteMessageStoreBackend` and `SQLiteQueueBackend` use this boundary; Received, Sent and Queue require the DEK. The DEK-less CLI `start` path is reported to fail closed. This does **not** establish complete coverage of every future entry point.

GSAT v1 attachment storage uses a `GSAT` versioned header, a 12-byte nonce, HKDF-SHA256-derived subkey and ChaCha20-Poly1305 authenticated encryption of content and JSON metadata, with contextual AAD. Legacy plaintext attachment files are rejected by the encrypted read path. Explicit exports are plaintext at their destination. SQLCipher database headers and GSAT markers observed on developer/VM machines are useful checks, **not an independent cryptographic audit**.

The encryption boundary does not establish universal protection for backups, temporary files, SQLite WAL/SHM/journals, exported attachments, private keys or pre-existing plaintext archives. Do not claim full S1–S7 compliance without dedicated evidence.

## 6. Optional Onion HTML page

The candidate adds a configurable Onion HTTP presence page, with GUI preferences validation. The HTTP page is a distinct service from Onion SMTP/IMAP; changing its configuration must not regenerate or replace mail/Onion identities. Validate configuration through the GUI and apply changes by restarting the relevant services as required by the implementation. Treat custom HTML as untrusted content and avoid publishing private information. Verify the current service module, preferences code, and tests before modifying implementation or declaring specific binding/path details.

## 7. Verification, release gates and safe operations

| Gate | Current evidence | Remaining work |
|---|---|---|
| Development tests | 1,974 passed for `0.1.1a0` | Repeat on the exact release candidate after changes |
| Transport and attachments | Historical developer ↔ VM tests | Repeat if the candidate changes relevant behavior |
| SQLCipher / GSAT | Historical read-only headers and attachment checks | Full target-platform, recovery and crash/backup coverage |
| Installer and dependencies | Earlier Ubuntu 24.04 installation validation | **Fresh clean install and upgrade of `0.1.1a0` not established** |
| Migration | No validated plaintext-to-encrypted migration | Explicit safe migration plan, backups and rollback testing |
| Release | Version metadata reported as `0.1.1a0` | Verify manifest, tag, artifacts and publish only by explicit decision |

Never test migration or destructive repair on real user databases or Onion identities. Never run `git add .`, reset/clean a working tree or create tags/commits implicitly. Inspect real source and tests before any implementation change; use focused regression, full suite and VM tests as applicable. The documented uninstaller (`python3 -m install.uninstaller` from checkout root) requires `DELETE` and **irreversibly removes application data and Onion identities** while preserving the source checkout; it is not a password reset.

## 8. Architectural requirements and continuity

**P1–P46** are the original September installation principles; **S1–S7** were added later and do not renumber or override the P principles. The index below preserves all original identifiers and names. For the full original normative paragraphs and historical checkpoints, retain the supplied September–October architecture source documents as the immutable historical record; this edition is the consolidated current specification, **not a verbatim replacement for that archive**.

### P1–P46 — original principle identifiers and names

- **P1 — Mandatory isolated virtual environment**
- **P2 — GarlicSMTP never runs as root**
- **P3 — Detect before modifying**
- **P4 — Bootstrap is idempotent**
- **P5 — Installation is phased and verifiable**
- **P6 — Deterministic versions and dependencies**
- **P7 — No implicit remote script execution**
- **P8 — Installation manifest as a source of release truth**
- **P9 — Detect project/installer divergence**
- **P10 — Installer is generated**
- **P11 — Contemporaneous versioned documentation**
- **P12 — Upgrade is not reinstall**
- **P13 — Software and persistent state are separated**
- **P14 — Persistent state belongs to the runtime user**
- **P15 — Restrictive secret permissions**
- **P16 — ApplicationPaths.for_user() is authoritative for V1**
- **P17 — No persistent writes outside declared layout**
- **P18 — Persistent layout changes are migrations**
- **P19 — First-run is determined from real state**
- **P20 — No default or shared secrets**
- **P21 — Cryptographic secrets are generated by their responsible components**
- **P22 — Creation is not regeneration**
- **P23 — Generated configuration is minimal**
- **P24 — Existing configuration is not silently overwritten**
- **P25 — First-run is resumable**
- **P26 — Persistent local IMAP credentials**
- **P27 — Passwords use a dedicated password-hashing scheme**
- **P28 — Credential state is separate from settings.toml**
- **P29 — Credentials are created once**
- **P30 — Password reset is not reinstall**
- **P31 — Authentication remains separate from IMAP protocol logic**
- **P32 — Onion Service is the network-identity authority**
- **P33 — Canonical V1 mail address derives from the real Onion hostname**
- **P34 — test.onion is not an installed identity**
- **P35 — Onion identity is persistent**
- **P36 — GUI sender remains backend-derived**
- **P37 — IMAP authentication identity and Onion identity are distinct**
- **P38 — First-run verifies the real Onion identity**
- **P39 — Tor is a system prerequisite**
- **P40 — GarlicSMTP owns the Onion Service lifecycle**
- **P41 — Tor Control remains local**
- **P42 — SAFECOOKIE is mandatory**
- **P43 — Tor's advertised cookie is authoritative**
- **P44 — SAFECOOKIE access without root runtime**
- **P45 — Detect Tor state before modifying it**
- **P46 — First-run performs end-to-end Tor verification**

### S1–S7 — subsequent requirements

- **S1 — Complete at-rest coverage:** Protect database contents, metadata, SQLite sidecars, temporary files and backups, including crash scenarios.
- **S2 — Key hierarchy:** An independent 32-byte DEK is wrapped by password and recovery-derived keys; secrets must not be stored in plaintext.
- **S3 — Offline recovery:** Recovery key is generated, confirmed and stored offline; password reset preserves the DEK, key rotation invalidates the old recovery key.
- **S4 — Continuity and migration:** Preserve mail, attachments, signing and encryption keys, trust pins and Onion identity during migrations; no developer bypass.
- **S5 — Unlock and lifecycle:** Unlock before receiving; close receiving services on GUI shutdown; CLI and bootstrap must not bypass the DEK.
- **S6 — End-to-end security verification:** Validate real receive, close, encrypted database copy, restart, offline recovery and preserved identities.
- **S7 — Packaging:** Validate SQLCipher dependency/build/installation on Ubuntu 24.04, including clean install and upgrade.

## 9. Document control

Historical source documents are retained unchanged. Before promoting this candidate, reconcile this specification with the actual repository source, installation manifest and release artifacts. No fresh repository inspection or VM execution was performed for this document.

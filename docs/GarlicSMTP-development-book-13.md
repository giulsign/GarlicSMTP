# GARLICSMTP — DEVELOPMENT BOOK 13
## Definitive pre-Git-consolidation handoff for `v0.1.2-alpha`

**Edition:** 13 · 29 October 2026
**Scope:** Complete the documentation/review handoff and begin the **Git consolidation and release preparation** in the next chat.
**Working release target:** `v0.1.2-alpha` (proposed Python package version `0.1.2a0`).
**Status:** Documentation review completed; Git consolidation, exact release commit, tag, artifacts and publication **not yet performed or verified**.
**Language:** English-only project documentation.
**Authority:** The actual checkout, source, tests, manifests and Git state supersede this book. Do not treat this handoff as evidence of a clean Git tree or a published release.

> **Primary instruction for the next chat:** Do **not** reopen the already approved documentation review. Start with a read-only Git inventory and prepare a precise, user-approved consolidation plan. The user executes repository commands and approves each consequential Git operation. Do not commit, tag, push, publish, delete, reset or clean without explicit authorization.

## 1. What has been completed in the current work session

The original AI-assisted static audit dated **27 October 2026** was a read-only assessment, not a penetration test or security certification. The subsequent development work and the documentation review are recorded in the approved **29 October post-audit follow-up**. That addendum preserves the original audit's historical findings rather than rewriting them.

The **complete development pytest suite subsequently reported 1,993 passing tests**. This supersedes the previous `1,974 passed` development checkpoint for recency, not as proof that a release wheel, source distribution, clean install or tagged revision has been tested. Earlier checkpoints (`1,797`, `1,830`, `1,844`, `1,974`) remain valid only as dated history.

The following follow-up activities were reported and reviewed:

| ID | Recorded follow-up | Evidence boundary |
|---|---|---|
| B-01 | Duplicate/shadowed pytest test definitions addressed | Later full suite reported passing; do not infer exhaustive coverage |
| B-03 | Weak test assertions strengthened | Focused test-quality improvement |
| D-05 | IMAP installer password validation moved ahead of avoidable side effects | Does not prove a fresh release installation |
| A-08a | Socket/thread/resource ownership cleanup across TCPServer, SOCKS5 client/connection, text connection, SMTP transport and IMAP/SMTP startup/shutdown | Does not close every wider A-02, A-03/C-07 or A-08 concern |
| S-01 | Logging privacy inspected; no defect identified in the examined path | Not a universal logging privacy certification |
| S-02 | Queue unexpected exceptions handled with retry/backoff | Within examined queue path |
| S-03 | SQLCipher queue duplicate-insert transaction recovery checked | Within tested transaction path |
| S-04 | IMAP authentication/session state checked | Within inspected/tested paths |
| S-05 / S-06 | SMTP/IMAP listeners reject non-loopback binds and accept `127.0.0.x` loopback | No claim of network-wide hardening |
| S-07 | SMTP incomplete-DATA EOF inspected; no defect identified | No blanket SMTP parser certification |
| S-08 | SMTP input bounds established | 64 KiB line; 2 MiB / 2,097,152-byte message; 1 MiB / 1,048,576-byte attachment |

**Still open / not demonstrated closed:** A-14 (SQLite IMAP UID monotonicity, `MAX(uid)+1` after highest-UID deletion); the broader lifecycle issues A-02, A-03/C-07, A-08 and trust-store persistence A-11 should not be declared closed without current evidence. Tor automatic recovery/republication after control loss, complete backup/restore, legacy plaintext migration, exhaustive at-rest coverage and independent security review are not established. Treat any other historical audit observation as requiring source-specific re-evaluation before claiming closure.

## 2. Release baseline and environments

- Canonical remote: `https://github.com/giulsign/GarlicSMTP.git`.
- Development checkout historically used by the user: `/mnt/c/garlicsmtp` in WSL Ubuntu; the user executes shell commands manually.
- `pyproject.toml` was last inspected declaring **`0.1.1a0`**, Python `>=3.12`, `LicenseRef-PolyForm-Noncommercial-1.0.0`, and `LICENSE`, `NOTICE`, `THIRD_PARTY_LICENSES.md` as license files. **The desired `0.1.2a0` has not yet been verified in source metadata.** Inspect `garlicsmtp/__init__.py` and all relevant version declarations before editing.
- Declared Python runtime dependencies: `dnspython>=2.8,<3`, `cryptography>=46,<47`, `sqlcipher3==0.6.3`; build backend requires `setuptools>=77`.
- Observed installed development versions: dnspython 2.8.0, cryptography 46.0.7, sqlcipher3 0.6.3; these are environment observations, not a lockfile or verified release artifact.
- Historical installed `GarlicSMTP==0.1.0a0` and existing `dist/` artifacts for `0.1.0a0` are **stale**; do not mistake them for the proposed release. Do not remove them without approval.
- The later `install/manifest.toml` declares **Ubuntu 24.04, Kali 2026.1, Debian 13** profiles with `apt-get`, Tor, `python3-venv`, `python3-tk`, and Tor Control `127.0.0.1:9051` with SAFECOOKIE. Debian 13 installation was separately reported verified. Do not claim a fresh candidate installation on all three platforms.
- GUI is **Tkinter**, not PySide6. Installed PySide6 in a development environment is not evidence of a runtime dependency.
- Production launcher: `~/.local/share/garlicsmtp/venv/bin/garlicsmtp-gui`; development entry: `python -m garlicsmtp.gui`. Installer is invoked as normal user via `./install.sh`, never `sudo ./install.sh`.
- Persistent paths include `config/settings.toml`, `state/account-credentials.json`, `data/mailboxes.db`, `data/sent.db`, `state/queue.db`, `data/attachments/` under `~/.local/share/garlicsmtp/`, subject to `ApplicationPaths.for_user()` as the source of truth.
- The documented uninstaller is `python3 -m install.uninstaller` with explicit `DELETE` confirmation; it is **destructive to application data and Onion identity**. Do not run it during consolidation.

## 3. Architecture and non-negotiable invariants

GarlicSMTP is a Python SMTP/IMAP messaging application with Tor Onion Services, persistent queue and retries, X25519/ChaCha20-Poly1305 E2EE and Ed25519 signatures. Onion, signing and encryption identities are separate. Encrypt remote E2EE content before enqueueing; maintain peer-key TOFU/pinning. **Sent** is local application acceptance, not remote delivery; **Retry pending** advances eligibility, not proof of delivery.

Received, Sent and Queue use SQLCipher with a mandatory **32-byte DEK** in documented standard paths. The password and offline recovery key independently protect the **same DEK**; reset/recovery must preserve stored messages and identities. Attachments in the application store use GSAT v1 encrypted blobs. An exported attachment is readable at its export destination. Do not assert universal protection for private keys, logs, backups, temporary files, caches, exported files or all legacy data. GUI login/setup and successful DEK unlock must precede receiving; failures must remain fail-closed.

The optional custom Onion HTML presence page is configured in GUI preferences, requires a valid existing HTML file when enabled, and requires relevant service restart; it must not expose secrets. Tor-ready does not prove remote `.onion` reachability. No independent cryptographic audit or production-readiness certification has occurred.

## 4. Documentation status — approved and frozen for the Git phase

The user explicitly approved the following reviewed items, in sequence:

| Item | Status / important note |
|---|---|
| `project-tree.txt` | Approved; do not regenerate/review merely to reopen documentation |
| `THIRD_PARTY_LICENSES.md` | Approved |
| `CONTRIBUTING.md` | Approved |
| `SECURITY.md` | Approved |
| `README.md` | Approved |
| `CHANGELOG.md` | Approved |
| `CLA.md` | Approved |
| `installation-architecture-en.md` | Approved English revision |
| `quicklaunch-en.md` | Approved English revision |
| `COMMERCIAL-LICENSE.md` | Approved |
| `NOTICE` | Approved; repository filename is `NOTICE`, not a `.md` variant |
| `LICENSE` | Reviewed without modifying PolyForm 1.0.0 legal terms or project `Required Notice` lines; **no separate explicit approval was recorded before the user moved to the audit update**. Do not claim an approval that did not occur. The license content itself must remain unchanged; ask only if approval is necessary for the Git inclusion decision. Repository filename is `LICENSE`. |
| Static audit report + 29 Oct follow-up | Explicitly approved |
| GarlicSMTP Handbook v0.1.2 | Explicitly approved |
| This Development Book 13 | Prepared as the final handoff; no approval assumed until user confirms |

The deliverables were prepared as **out-of-repository files**, often named with `-v0.1.2-en` suffixes. They have **not** thereby been copied into the repository or committed. During consolidation, map each approved artifact to its intended canonical repository path and filename, review content and diffs, and preserve historical documents when appropriate. Avoid accidentally publishing alternative translations, temporary copies, backup files, secrets or obsolete release artifacts. Do not infer the existence of a path solely from a documentation filename; verify it.

The source-available project license is **PolyForm Noncommercial License 1.0.0**, not an OSI-approved open-source license. Separate commercial permissions require a written agreement. Third-party licenses remain independently applicable.

## 5. Immediate next phase: Git consolidation, then publication

**The very next action in the new chat is a read-only Git inventory, not another documentation revision, new feature or code patch.** Request the following exact commands from the user, executed in their existing checkout:

```bash
cd /mnt/c/garlicsmtp
pwd
git status --short
git branch --show-current
git log -1 --format='%h %H %s'
git remote -v
git tag --list 'v0.1.2*'
git diff --check
git diff --stat
git ls-files 'README*' 'CHANGELOG*' 'LICENSE' 'NOTICE' 'THIRD_PARTY_LICENSES*' 'CONTRIBUTING*' 'SECURITY*' 'CLA*' '*quicklaunch*' '*installation-architecture*' '*Handbook*' '*development-book*' 'docs/**'
rg -n '0\.1\.[012]|__version__|version\s*=' pyproject.toml garlicsmtp/__init__.py install 2>/dev/null
```

**After inspecting the output**, inventory modified, deleted and untracked files and identify which changes belong to the proposed release versus unrelated work. Ask for focused diffs/contents when needed. Do not assume the checkout is clean, that all approved docs exist in the repo, or that the package version has already been bumped.

Proposed **approval-gated** consolidation sequence (not an authorization to execute):

1. Agree on the exact canonical destination for each approved English document and audit/handbook/development-book artifact; keep `LICENSE` and `NOTICE` under their correct names. Compare existing tracked files with approved copies and explicitly handle historical material and unrelated changes.
2. Verify source and package version consistency (`0.1.2a0` target), release naming (`v0.1.2-alpha` target), manifest profile structure, release notes and licensing metadata. Any necessary source/metadata change must be shown and separately approved before the user applies it.
3. Review `git diff --check`, the complete **scoped** diff and staging plan. **Never use `git add .` or blanket staging.** The user explicitly authorizes the file list and commit message before staging/committing.
4. Run focused checks if the actual changes require them, then the full pytest suite at the agreed release gate; the historical **1,993 passed** is not automatically a test result for the final release commit. Inspect packaging outputs rather than relying on stale `dist/` files.
5. Only after user approval, commit the exact selected changes; verify commit SHA, working-tree status, and remote relationship. Discuss and explicitly approve push, tag creation, and GitHub Release publication **as separate steps**. Never claim a tag, artifact or GitHub release exists before verification.
6. After publication, record the actual SHA, tag, artifact filenames/hashes, test results, installation evidence and release URL in a short final addendum to this Book 13. **This is the only expected substantive post-handoff update**, apart from factual corrections discovered during Git consolidation.

The user's previously agreed broader roadmap after publication is **promotion, collaboration invitations and seeking independent security reviewers**, followed by choosing suitable forums/platforms. Do not start those phases before Git/release consolidation is complete and approved.

## 6. Safety, workflow and historical boundaries

- The user runs all repository commands and approves each consequential action. The assistant advises in Italian; **project documentation is English-only**.
- Before any source/test change, inspect actual source and tests; use one reproducible micro-goal and minimal TDD. Do not generate speculative patches.
- Preserve all unrelated working-tree changes, historical documentation, backups, private messages, SQLCipher databases, DEK, recovery material and Onion/Ed25519/X25519 private identities.
- No destructive `git reset --hard`, `git clean`, forced checkout, blanket `git add .`, `sudo ./install.sh`, real uninstallation, database deletion, identity regeneration or release publication without explicit approval.
- Historical `v0.1.0-alpha.1` publication and `v0.1.1-alpha` audit/tag references belong to older milestones; do not conflate them with `v0.1.2-alpha`.
- The static audit's A-14 remains an unresolved finding on available follow-up evidence. Do not silently relabel it fixed or certify release readiness. If it affects the planned release decision, present the risk explicitly and let the user decide whether to pause publication for a targeted remediation.
- Keep historical audit claims intact. The approved audit addendum is subsequent author-reported/project evidence, not an independent security assessment.

## 7. Complete opening declaration for the new chat

Copy the following into the first message of the next chat, **attach this Book 13**, and supply the actual Git outputs when requested:

```text
START — GARLICSMTP v0.1.2-alpha GIT CONSOLIDATION SESSION

We are continuing GarlicSMTP (https://github.com/giulsign/GarlicSMTP.git).
The attached Development Book 13 (29 October 2026) is the definitive pre-Git handoff. Read its Sections 1–7 before proposing any action. The previous chat's documentation review is COMPLETE; do not restart it.

TARGET AND VERIFIED BOUNDARIES
- Proposed release: v0.1.2-alpha; proposed Python package version: 0.1.2a0.
- Last observed pyproject.toml version: 0.1.1a0; Git consolidation/version alignment still pending.
- Latest complete developer suite reported: 1,993 passed; not a final tagged-artifact test.
- The 27 October AI-assisted static audit and 29 October post-audit follow-up were approved; no independent security audit.
- A-14 SQLite IMAP UID monotonicity has no verified resolution in the handoff. Other audit findings must not be assumed closed.
- Later installer manifest declares Ubuntu 24.04, Kali 2026.1 and Debian 13; Debian 13 installation reported verified. No blanket fresh-install certification for all three.
- Reviewed English release documents, updated audit and Handbook are approved. LICENSE was preserved unchanged but its individual approval was not explicitly recorded. This Book 13 is the handoff.
- No v0.1.2-alpha commit, tag, release artifacts or GitHub publication has been established.

STRICT WORKFLOW
1. We are starting GIT CONSOLIDATION NOW, not another document review or feature sprint.
2. I execute all commands in my WSL checkout /mnt/c/garlicsmtp and paste their output. You do not modify my repository.
3. FIRST request a read-only inventory: git status, branch, HEAD, remote, tags, diff/check and tracked documentation/version files.
4. Identify release-related versus unrelated changes. Map approved English artifacts to canonical paths and review the precise proposed diff.
5. No git add ., reset, clean, force operations, commit, tag, push, publication, destructive installer/uninstaller commands, or changes to real data without my explicit authorization.
6. Agree on metadata version bump, exact staged files, commit and full test gate. Obtain separate approval for tag/push/release.
7. After actual Git/release results are verified, add only a factual final consolidation appendix to Book 13. Then proceed to promotion and independent-audit outreach in the agreed order.

FIRST RESPONSE: In Italian, briefly acknowledge the handoff and ask me to run the read-only Git inventory commands from Book 13 Section 5. Do not assume any missing SHA, release artifact, test result or approval.

END — GARLICSMTP v0.1.2-alpha GIT CONSOLIDATION SESSION
```

## 8. Archival continuity: Development Book 12, English current-state sections

The following is the **pre-29-October** English narrative from Book 12, retained to preserve its architecture, development method, earlier handoff and dated assumptions. It is superseded by Sections 1–7 above for current release status. Book 12 itself contains older historical appendices, including Italian archival material; these are not reproduced in this English-only edition. Consult the original Book 12 if that deep history becomes necessary. Do not treat Book 12's old `v0.1.1-alpha` release plan or `1,974 passed` as current instructions.

---

# GARLICSMTP — DEVELOPMENT BOOK 12
## Development history, architecture, working protocol and reproducible handoff

**Edition:** 12 · 25 October 2026
**Working target:** `v0.1.1-alpha` candidate · Python distribution `0.1.1a0`
**Latest reported development checkpoint:** `8faf1c6` on `main`, pushed to `origin/main`
**Last reported complete development suite:** `1,974 passed` (`python -m pytest -q`, approximately 135.21 s)
**Status:** continuity and third-party onboarding document; **not** a release announcement, fresh code audit or security certification.

> **Authority and evidence hierarchy.** The checkout actually selected, its source code, dependency manifest, tests and reproducible runtime observations take priority over this book. Historical test results are dated evidence, not newly executed tests. Before modifying code, inspect the existing implementation and the relevant tests. Any discrepancies must be recorded, not silently reconciled.

## 0. How to use this book

Read Sections 1–4 to understand scope and verified status; Sections 5–9 before changing any code; Sections 10–13 to resume or fork development. **Section 14 is the complete opening declaration to paste into a new chat, together with this document and relevant source files.** Appendix A contains the original complete Book 11 in English, itself retaining earlier historical material. The appendix is archival: newer dated evidence supersedes older status claims without changing their historical meaning.

**Evidence labels:** `IMPLEMENTED` = reported in inspected source or historical documentation; `TESTED` = accompanied by a named test checkpoint; `MANUALLY VERIFIED` = user-reported runtime exercise; `DECIDED` = required behavior not necessarily verified in all paths; `OPEN` = unclosed question; `NOT VERIFIED` = do not infer support. These labels are not interchangeable.

## 1. Mission, boundaries and product identity

GarlicSMTP is a Python-based privacy-oriented messaging application with SMTP and IMAP components, persistent mailbox and delivery queue, Tor Onion transport and its own Onion Service identity. It is not merely a GUI for public mail providers. The current GUI is **Tkinter**, not PySide6. The software is source-available under **PolyForm Noncommercial License 1.0.0**, not an OSI-approved open-source license. Separate commercial licensing is possible; the repository's authoritative `LICENSE` governs. Copyright © 2026 Giuliano Signorelli. Licensing contact: `giulisign@gmail.com`. Third-party licenses remain separately applicable.

The design distinguishes: (a) Tor transport and Onion reachability; (b) end-to-end content encryption and sender signatures; (c) encrypted local application stores; and (d) operating-system, endpoint and human operational security. None alone guarantees anonymity, trust, availability, complete disk encryption or delivery.

## 2. Provenance and chronological checkpoints

| Checkpoint | Evidence and meaning |
|---|---|
| 08 Oct · Book 8 | Narrative architectural and method baseline; its then-open at-rest work is historical. |
| 13 Oct · Book 9 | SQLCipher/DEK/recovery implementation progress; `1,797 passed` reported. |
| 18 Oct · Book 10 history | `1,830 passed`; development recovery exercise reported. |
| 19 Oct · Book 10 | `1,844 passed`; application baseline `9bfc2f7`; real developer ↔ Ubuntu VM message/attachment exchange; encrypted-store observations. |
| 19 Oct · Book 11 closure | Public `v0.1.0-alpha.1` pre-release reported, release commit `212b9dd`, package `0.1.0a1`. Earlier Book 11 paragraphs saying publication was pending are superseded by its closure update. |
| Later `v0.1.1-alpha` work | Reported `main` checkpoint `8faf1c6`, package `0.1.1a0`, optional configurable Onion HTML presence page, and full suite `1,974 passed`. **Candidate only**; no new tag or GitHub release confirmed. |

Do not add checkpoint test totals together: they are distinct runs, and focused test groups may overlap. The Book 11 release and the Book 12 candidate are separate milestones. No independent security audit, certified clean installation, upgrade path or data migration is established for `v0.1.1-alpha`.

## 3. Repository, environments and branch hygiene

**Canonical remote:** `https://github.com/giulsign/GarlicSMTP.git`; historical working directory: `/mnt/c/garlicsmtp` inside Ubuntu on WSL, branch `main`. The user may have a different checkout: never assume paths or HEAD without checking. Ubuntu 24.04 is the documented installer target and historical VM validation environment; Ubuntu 22.04 GUI VM testing is also reported for subsequent work. Neither means native Windows/macOS or every Linux distribution is supported. Python requirement was historically `>=3.12`; inspect the current `pyproject.toml` before relying on it.

Reported `0.1.1a0` dependency constraints: `dnspython>=2.8,<3`, `cryptography>=46,<47`, `sqlcipher3==0.6.3`, build `setuptools>=77`. Inspect exact lock/build resolution in the selected checkout. `sqlcipher3` has its own third-party licensing; it is not automatically relicensed by GarlicSMTP's PolyForm license.

**Read-only starting checks** (run from the correct checkout, not from a live production data directory):

```bash
pwd
git status --short
git branch --show-current
git log -1 --oneline
git remote -v
git diff --check
python --version
python -m pytest -q
```

The full test command is a proposed new verification, not a claim it has just been run. Capture exit status, exact count and duration. Never use `git add .`, `git reset --hard`, `git clean`, destructive checkout or automated cleanup. Historical working trees contained unrelated edits, deleted docs, untracked documents and backups; preserve them. Do not stage or commit without explicit approval. Never manipulate real databases, keys, recovery credentials, Onion identities or VM snapshots merely to test a hypothesis.

**For an independent development branch:** first record the upstream URL, current HEAD, `git status`, package metadata and baseline test result; work from an explicitly chosen immutable commit or tag in a separate clone/worktree **only after ensuring that local changes and private data will not be affected**. Choose a new branch name, record its base SHA and document divergences. Do not copy private state or secrets into the fork. The right to use or distribute a fork is subject to `LICENSE`, third-party notices and any separate authorization; a public GitHub repository does not by itself confer unrestricted commercial rights.

## 4. Architectural map and responsibilities

```text
Tkinter GUI / supported CLI entrypoints
    → authentication / setup / password or recovery unlock
    → 32-byte DEK available for protected stores
    → ApplicationViewModel / ApplicationController
    → ApplicationBuilder (composition root)
       ├─ SMTP server → message pipeline → local Received store / remote delivery
       ├─ IMAP server → mailbox access according to configured auth
       ├─ MailComposerService → signature / routing / E2EE preparation
       ├─ QueueWorker → TransportManager → OnionTransport → Tor SOCKS5
       ├─ SQLCipher Received, Sent and Queue backends
       └─ GSAT v1 encrypted AttachmentStore
```

This is a conceptual map, not a guaranteed exact call graph. Check constructors, call sites and tests in the current checkout. Historical paths to inspect **only when relevant**: `garlicsmtp/application/builder.py`, `garlicsmtp/gui/application.py`, `garlicsmtp/gui/tk_main_window.py`, `garlicsmtp/gui/tk_compose_section.py`, `garlicsmtp/core/pipeline/`, `garlicsmtp/security/auth/account_credentials.py`, `garlicsmtp/security/encrypted_sqlite.py`, `garlicsmtp/storage/sqlite/backend.py`, `garlicsmtp/queue/sqlite.py`, `garlicsmtp/storage/attachment_store.py`, `garlicsmtp/cli/mailbox.py`, Tor/Onion transport modules and corresponding `tests/`. Names and paths are historical pointers, not substitutes for listing the tree.

**Outbound path:** compose → Ed25519 signature → determine local/remote destination → remote capability/key discovery and X25519 TOFU pin verification → HKDF/ChaCha20-Poly1305 encryption **before** persistent enqueue → QueueWorker and Onion transport over Tor → recipient SMTP. **Inbound path:** SMTP acceptance → E2EE decryption where applicable → signature validation → classification/store → GUI/IMAP. Transport retries and errors must preserve message integrity. A message in **Sent** means accepted/saved by the local application, **not** proof of remote delivery. `Retry pending` advances retry eligibility; it is not a delivery receipt or direct send.

**Identities are separate:** Onion Service identity, Ed25519 signing identity, X25519 encryption identity. Cryptographically valid signatures do not automatically establish social trust. Unexpected pinned-peer key changes must not silently replace a trusted key. A first-contact TOFU decision has inherent trust limitations.

## 5. At-rest storage, authentication and recovery invariants

`IMPLEMENTED/TESTED` within documented paths: Received `data/mailboxes.db`, Sent `data/sent.db` and Queue `state/queue.db` use SQLCipher with a mandatory **32-byte DEK**; standard observed paths fail closed rather than falling back to plaintext SQLite. `garlicsmtp/security/encrypted_sqlite.py` historically centralizes SQLCipher connection and keying. `AttachmentStore` uses GSAT v1 (`GSAT` + version byte), a 12-byte nonce and ChaCha20-Poly1305; HKDF-SHA256 derives an attachment subkey from the DEK, and AEAD binds identifying context. File content and metadata are protected in the application blob. Legacy plaintext attachment formats are rejected in the documented reader.

The password is verified via salted Scrypt and a separate password-derived KEK wraps the DEK; an offline recovery secret independently permits recovery of the **same** DEK. A password reset or recovery-key replacement must not regenerate DEK, Onion identity or Ed25519/X25519 identities. Recovery confirmation and fail-closed GUI behavior are important invariants. Account credentials were historically stored at `state/account-credentials.json` with restrictive permissions and atomic-update protections; inspect actual current code and filesystem semantics before relying on that detail.

`NOT VERIFIED` as universally encrypted: private identity files, logs, backups, exported attachments, SQLite journal/WAL/temp remnants, caches, all CLI paths, third-party integrations and arbitrary host files. A non-plaintext database header is supporting evidence only. Exported attachments are readable at the selected destination. No certified backup/restore or legacy plaintext migration procedure is established. **Never delete a database or reinstall to solve forgotten credentials; use the supported recovery flow when available and preserve the original data.**

The Book 11 targeted standard-path DEK propagation audit found no bypass in inspected GUI, builder, Bootstrap and mailbox CLI paths; it did **not** audit arbitrary injected backends. Book 11 also recorded a **possible functional anomaly**: the no-subcommand CLI server route may construct Bootstrap without a DEK. This was not reproduced with a dedicated test, may be legacy/intentional and is **not** evidence of an encryption bypass. Inspect and reproduce before treating it as a defect.

## 6. GUI, runtime lifecycle and Tor

The GUI must remain hidden until account setup/login and DEK unlock succeed. Build failures should destroy the Tk root; receiving must not start before authentication. Closing the GUI should stop the application's receiving services, while system Tor may remain running. The asynchronous compose/send flow uses a worker thread and Tk-safe result polling; it should report errors and clear compose fields only after application acceptance. Changes to thread handling require focused race/lifecycle tests.

Tor is a system prerequisite in the validated profile; historical local Tor Control endpoint: `127.0.0.1:9051` with SAFECOOKIE. The application dynamically manages its persistent Onion Service. Local Tor readiness does **not** guarantee reachability of a remote `.onion` endpoint. Never make Tor cookies world-readable, run the application as root, or regenerate Onion identity to address a transient timeout. The GUI may require logout/login after `debian-tor` group membership changes.

## 7. New `v0.1.1-alpha` capability: optional Onion HTML presence page

The latest reported checkpoint adds a configurable **custom Onion HTML presence page** with GUI preferences. When enabled, the preference must specify a nonempty path; the validated configuration requires a meaningful HTML file path. Changes require a restart of the relevant services; do not imply hot reload. The presence page is not a replacement for SMTP/IMAP or the Onion cryptographic identity. Inspect the implementation and tests for path validation, enabled/disabled behavior, file access, error reporting and lifecycle before changing it. Never publish secret keys, personal identifiers or externally fetched resources unintentionally. No independent review of arbitrary HTML content is documented.

This capability is associated with development commit `8faf1c6` and the reported `1,974 passed` suite. Neither constitutes certification of a clean Ubuntu 24.04 installation, upgrade or release publication. The repository document `docs/personalized_html/personalized_html.html` was explicitly excluded from this documentation production; do not copy it into the deliverable or treat it as reviewed evidence.

## 8. Validation matrix and what is still unknown

| Area | Evidence | Boundary |
|---|---|---|
| SMTP/IMAP, local and Onion delivery | historical unit/integration tests and real developer/VM send/receive | not a guarantee of every peer/network |
| E2EE/signatures and key pinning | implemented and tested paths reported | no independent security audit |
| Received/Sent/Queue SQLCipher | tests plus read-only header observations on developer and VM | not proof of entire disk coverage |
| GSAT v1 attachments | synthetic format tests and real attachment exchange | exports/backups outside encrypted store |
| Offline recovery | automated tests and historical manual developer/VM/physical tests | no certified disaster restore |
| Tkinter GUI | historical login, lifecycle, send and recovery tests | GUI variations and new packaging not all recertified |
| Optional Onion HTML | later implementation and full-suite report | no new clean-install/upgrade certification |
| Full development suite | 1,974 passed at latest reported checkpoint | do not assert rerun during Book 12 writing |
| Native Windows/macOS | not established | unsupported claim prohibited |

**Release gates still OPEN unless new evidence is supplied:** actual `v0.1.1-alpha` tag/release publication, clean Ubuntu 24.04 installation with current manifest, upgrade/migration behavior, recovery/backup restoration end-to-end, third-party dependency packaging on all target hosts, independent security review, and a fresh runtime test of the new HTML setting where needed. Do not relabel historical validation as a current release gate.

## 9. Strict development and review method

1. **Define one observable micro-goal** and whether it is a bug, requested feature, characterization or documentation task; record acceptance criteria and what is out of scope.
2. **Inspect existing source, tests and fixtures first**. Request only the relevant files or command outputs. Do not invent API names or propose patches based solely on this book.
3. **Establish baseline:** branch/HEAD/status, environment, relevant targeted tests. If behavior already exists, write a GREEN characterization test instead of manufacturing a RED.
4. **RED when justified:** introduce one focused test reproducing the missing behavior; confirm the expected failure and exclude unrelated environment failures.
5. **GREEN:** minimal localized fix; preserve security, persistence and delivery invariants. No opportunistic core rewrites or cosmetic refactoring.
6. **Verify:** focused tests → related regressions → full `python -m pytest -q` at a relevant gate → real Ubuntu VM test only if the changed boundary requires it. Stop and investigate unexpected failures.
7. **Review diff and evidence:** `git diff --check`, list changed files, describe before/after behavior, update documentation and risks; propose commit only with user approval.
8. **Handoff:** record SHA, test commands and results, remaining questions, next single action and a new-chat opening declaration.

**Collaboration rule from the historical books:** the user manually applies source/test changes and explicitly approves Git operations. Provide inspectable, small diffs and copyable commands; do not execute scripts that rewrite repository code. Documentation artifacts may be produced separately without touching the repository. A third-party maintainer may adopt a different workflow on their own authorized branch, but must state that deviation explicitly and respect licenses, safety invariants and evidence standards.

## 10. Work items and decision log for the next branch

**Confirmed development status:** package version `0.1.1a0`, reported code checkpoint `8faf1c6`, optional HTML presence page, reported `1,974 passed`. **Not confirmed:** a new published `v0.1.1-alpha` release or complete release certification. Do not automatically re-open completed historical work or declare an old issue still present without current inspection.

**Recommended first work package:** read-only checkout inventory; compare `pyproject.toml`, `garlicsmtp/__init__.py`, installer manifest, GUI HTML preferences, runtime serving path and relevant tests; capture a focused test baseline; decide whether the next task is a release gate, an actual bug or a separate feature. If a new branch is desired, agree on base commit, branch name, license permissions, review owner and test target first.

**Known decision points:** (a) is `v0.1.1-alpha` to be tagged and published, and on which exact SHA? (b) which Ubuntu release(s) are explicitly supported after current installer testing? (c) is the no-subcommand CLI server entrypoint supported or legacy? (d) what backup/restore and migration policy is acceptable? (e) which threat model and security review are required before broader claims? (f) which HTML exposure and validation behaviors are part of the public contract? These are questions, not implied approvals.

## 11. Source map for a third-party contributor

Start with `README`, `CONTRIBUTING`, `SECURITY`, `LICENSE`, `NOTICE`, `THIRD_PARTY_LICENSES`, `CHANGELOG`, installation documentation and the current `pyproject.toml`; read the current files, not just the translated review copies. Then inspect only the subsystem being changed. Typical clusters: GUI (`garlicsmtp/gui/`, `tests/test_gui_*`), account/DEK (`garlicsmtp/security/auth/`, `garlicsmtp/security/encrypted_sqlite.py`), mail stores (`garlicsmtp/storage/`, `garlicsmtp/queue/`), delivery (`garlicsmtp/core/pipeline/`, `garlicsmtp/application/`, transport/Tor code), installer (`install.sh`, manifest tests). Verify names with `git ls-files` rather than assuming every historical path still exists.

Keep fixtures and test data synthetic. Do not upload secrets, actual messages, real `.onion` identities or SQLCipher databases to an issue, pull request or AI chat. Separate external dependencies' copyright notices from project licensing. Document architecture changes and backward compatibility impacts explicitly.

## 12. Continuity packet to attach to a new chat

**Minimum:** this Book 12, the exact Git HEAD and branch, `git status --short`, package version from actual files, latest full and focused test output, a concise description of the next micro-goal, and the relevant existing source/test files. **If needed:** the last diff, installer/environment logs with secrets removed, failing traceback and reproducible steps. Do not attach the entire repository, private data or credentials indiscriminately. State whether the new session may only advise or may modify files.

**First assistant response expected:** acknowledge the evidence hierarchy; summarize the currently known baseline and uncertainties; ask for missing *targeted* source/tests before proposing edits; select one small next action. Do not assume the assistant has access to the previous chat, the local checkout or the runtime.

## 13. Handoff checklist

- [ ] Confirm checkout path, branch, HEAD, remote and dirty/untracked files.
- [ ] Confirm package and installer versions against the chosen commit.
- [ ] Separate published `v0.1.0-alpha.1` from candidate `v0.1.1-alpha`.
- [ ] Record exactly when/where `1,974 passed` was obtained; rerun only if appropriate.
- [ ] Identify the single task, acceptance criteria and tests to inspect.
- [ ] Preserve credentials, DEK, recovery key, Onion and signing/encryption identities.
- [ ] Review applicable source and third-party licensing before a fork/distribution.
- [ ] Obtain explicit permission before edits, commits, tags, release or destructive actions.
- [ ] Update this book after material changes; never erase historical evidence.

## 14. COMPLETE DECLARATION TO OPEN A NEW WORK SESSION

> **Copy the following text into a new chat and attach this Development Book 12. Replace bracketed fields with actual current observations; do not guess.**

```text
START OF NEW GARLICSMTP DEVELOPMENT SESSION — DECLARATION

I am resuming development of GarlicSMTP (https://github.com/giulsign/GarlicSMTP.git).
The attached GarlicSMTP Development Book 12 is the continuity reference, not a substitute for reading current code.

HISTORICAL AND CURRENT CONTEXT
- Published historical milestone reported in Book 11: v0.1.0-alpha.1, release commit 212b9dd, package 0.1.0a1; application baseline 9bfc2f7.
- Later development target: v0.1.1-alpha candidate, package 0.1.1a0; latest reported main/origin/main commit 8faf1c6.
- Latest reported complete development suite: 1,974 passed. This is historical evidence until rerun in this session.
- New work includes an optional configurable Onion HTML presence page in the Tkinter GUI, with enabled-path validation and restart requirement.
- No published v0.1.1-alpha tag/release, independent security audit, certified clean install, upgrade or migration is established by this document.

ARCHITECTURE AND INVARIANTS
- Python SMTP/IMAP application; Tor Onion transport; distinct Onion, Ed25519 and X25519 identities; E2EE prepared before remote enqueue; persistent queue and retries.
- SQLCipher Received/Sent/Queue and GSAT v1 attachments use the application DEK within documented boundaries.
- Password and offline recovery wrap the same DEK. Recovery/reset must preserve keys, identities and data. Fail closed on missing/invalid DEK.
- GUI is Tkinter. Login/setup precedes receiving; Sent is not proof of remote delivery; Retry pending is not a delivery receipt.
- No blanket claims of anonymity, all-files encryption, audited security or supported Windows/macOS builds.

WORKING RULES
- FIRST inspect the existing relevant source code and tests; do not propose speculative changes.
- One observable micro-goal at a time: targeted RED when a defect is demonstrated, minimal GREEN, regressions, full suite at a relevant gate.
- The user applies source changes manually and approves Git actions; no automatic source rewrites, no git add ., reset, clean or destructive operations.
- Preserve all unrelated working-tree changes, real data, recovery secrets and Onion identities. Never ask to disclose secrets.
- Distinguish documented historical checks from tests actually executed in this session.

CURRENT CHECKOUT — FILL FROM REAL COMMANDS
Checkout path: [TO VERIFY]
Branch / HEAD / remote: [TO VERIFY]
Git status including untracked files: [TO VERIFY]
Python and package version: [TO VERIFY]
Last targeted and full test commands/results: [TO VERIFY]
Next single objective and acceptance criteria: [TO DECIDE]
Authorized scope of edits / Git actions: [TO CONFIRM]

YOUR FIRST ACTION
Confirm the context and unresolved evidence. Ask for the smallest set of current source files, tests and read-only command outputs needed to assess the chosen objective. Do not patch, refactor, stage, commit, tag or publish before inspecting the implementation and obtaining explicit authorization.

END OF NEW SESSION DECLARATION
```

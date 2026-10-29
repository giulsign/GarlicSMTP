# GarlicSMTP — Static Audit Report

**Report date:** 27 October 2026
**Assessment type:** AI-assisted, read-only static review
**Project:** GarlicSMTP
**Repository:** https://github.com/giulsign/GarlicSMTP
**Review status:** Completed for the agreed static-review scope
**Document status:** Release-supporting technical report; not a security certification

> **Important disclosure:** This report records an AI-assisted review of source code, tests, installation configuration, Git metadata, and project documentation. It is **not** an independent professional security audit, penetration test, formal verification, or certification. No tests, installations, live Tor experiments, or deployment exercises were executed as part of this review. Findings describe the examined code and the limits of the available evidence; they do not establish the security of any deployed instance.

## 1. Executive summary

The review covered four agreed areas:

- **A — Architecture and component lifecycle:** application orchestration, storage, persistence, resource cleanup, and failure handling.
- **B — Static assessment of tests:** test organization, potential coverage gaps, and test-definition integrity.
- **C — Tor integration and continuity:** Onion identity persistence, Tor control lifecycle, simulated integration coverage, and recovery behavior.
- **D — Release readiness and documentation:** installer profiles, release provenance, public claims, and documentation consistency.

The review identified **two high-priority issues**: possible reuse of IMAP UIDs by the SQLite backend (**A-14**), and an incomplete Ubuntu installation profile in the reviewed Git HEAD manifest (**D-09**). The latter was already structurally corrected in the local, uncommitted working-tree manifest at the time of review; this does **not** mean the correction was present in HEAD or in the tagged release.

Other findings concern service shutdown after exceptions, bounded thread joins, Tor-control resource cleanup, persistence consistency, test shadowing, and release-documentation accuracy. Several are risks inferred from control flow rather than failures reproduced in a running environment.

**Overall assessment:** The reviewed project provides a substantive experimental Alpha implementation with identifiable defensive mechanisms and a nontrivial test suite. The static evidence does not justify claims of security certification, uninterrupted Tor availability, or production readiness. Prioritize the two high-priority findings, then lifecycle robustness and release-documentation alignment.

## 2. Scope, method, and evidence levels

### 2.1 Method

The assessment used read-only inspection of selected Python modules, test modules, TOML configuration, documentation, and Git metadata. Commands used for the review did not intentionally modify the repository. No automated test suite, installer, network service, or live Tor daemon was run by the reviewer.

This is a **targeted static review**, not an exhaustive line-by-line review of every project file. A finding may be valid without having been dynamically reproduced; conversely, an unobserved failure cannot be assumed to occur in production.

### 2.2 Evidence terminology

- **Confirmed statically:** directly supported by the reviewed source/configuration or by read-only parsing of local files.
- **Potential / conditional:** a plausible failure mode derived from code paths, not dynamically reproduced.
- **Not established:** available evidence does not demonstrate whether a property holds in live operation.
- **Author-reported:** historical or operational information provided by the project author, not independently repeated during this assessment.

### 2.3 Revision boundaries

| Reference | Observed state |
| --- | --- |
| Repository | `https://github.com/giulsign/GarlicSMTP` |
| Local prerelease tag | `v0.1.1-alpha` |
| Tag commit | `f8ad5eeb72c626302ec373f8943ed0d21f06b441` |
| Reviewed HEAD | `a472969ac9a18a9b60587ab57e3318f99aac6689` |
| Kali 2026.1 profile in tag | Not present in the reviewed tag |
| Kali 2026.1 profile in HEAD | Present |
| Ubuntu/Kali manifest correction | Present in the locally modified working-tree file, not in the reviewed HEAD |
| GitHub Release publication and downloadable assets | Not independently verified |

The working tree contained other modifications and untracked material; this report does not treat those files as part of a published release. In particular, **HEAD, the local working tree, and the `v0.1.1-alpha` tag are distinct states**.

## 3. Priority and disposition

Priority is an engineering recommendation, not a CVSS score or an independently validated exploit severity.

| Priority | IDs | Recommended disposition |
| --- | --- | --- |
| **High** | A-14, D-09 | Address and verify before distributing an affected revision as installable/reliable |
| **Medium** | A-02, A-03/C-07, A-08, A-11, C-REC, D-DOC | Improve lifecycle handling and clarify operational/release claims |
| **Low / follow-up** | A-08a, A-13, B-01, B-03, D-05, D-06 | Strengthen cleanup, test clarity, and usability |
| **Coverage gap** | B-02, D-04 | Add targeted tests or document the chosen validation strategy |

**Note:** The IDs in this report follow the working audit notes. Related observations are grouped rather than counted as separate independent defects. `C-REC` and `D-DOC` are editorial grouping labels, not new original finding IDs.

## 4. Detailed findings — high priority

### A-14 — SQLite IMAP UID allocation may reuse an existing historical UID

**Priority:** High
**Evidence level:** Confirmed statically; not reproduced dynamically
**Location:** `garlicsmtp/storage/sqlite/backend.py`, `_next_uid`

**Observation.** The reviewed SQLite implementation derives the next message UID from the maximum UID currently present in a mailbox plus one (`MAX(uid) + 1`). If the highest-UID message is deleted, a later insert can reuse that same UID while the mailbox's `UIDVALIDITY` remains unchanged.

**Why it matters.** IMAP clients rely on stable, monotonically increasing UIDs within a given `UIDVALIDITY` epoch. Reuse may produce stale-cache associations or incorrect synchronization behavior. This finding concerns the SQLite backend; it should not be generalized to the in-memory backend without separate evidence.

**Recommendations.** Persist a per-mailbox next-UID counter independent of surviving messages; allocate and advance it transactionally; add a regression test covering insert → delete highest UID → insert, and verify persistence across database reopen and mailbox lifecycle events.

**Verification required.** Execute the new regression tests against SQLite and confirm UID behavior under the application's supported concurrency model.

### D-09 — Ubuntu manifest profile incomplete in reviewed HEAD

**Priority:** High for the affected HEAD revision
**Evidence level:** Confirmed statically, including read-only TOML parsing of the corrected local file
**Locations:** `install/manifest.toml`, `install/installer.py`, `install/validator.py`

**Observation.** In the reviewed HEAD, the Ubuntu 24.04 and Kali 2026.1 `[[platform.profiles]]` entries are followed by nested `[platform.profiles.*]` sections only after the Kali entry. Under TOML array-of-tables semantics, these sections attach to the most recently declared profile: Kali. The HEAD Ubuntu entry consequently lacks `system_prerequisites` and related configuration.

The ordinary `run_installation()` path loads the manifest and passes it to `execute_installation()` without an explicit call to the semantic manifest validator. The latter accesses `profile["system_prerequisites"]` on its default path. For the affected Ubuntu profile, this leads to a missing-key failure before system installation proceeds.

**Local correction observed.** The working-tree `install/manifest.toml` had separate Python and prerequisite sections for both Ubuntu and Kali. Read-only `tomllib` parsing confirmed that both profiles contained the expected prerequisite categories and that their reviewed common configuration fields were equivalent. This validates structure and selected values, **not** an actual installation.

**Recommendations.** Review and commit the corrected manifest before distributing an affected revision; validate every platform profile semantically in CI and/or before installer side effects; add a regression that loads the real repository manifest rather than only a synthetic fixture.

**Revision caution.** This finding concerns the reviewed **HEAD**, which is later than `v0.1.1-alpha`. It must not be described as a demonstrated defect of that tag without examining the tag's own manifest and installation behavior.

## 5. Architecture and lifecycle findings

### A-03 / C-07 — Unhandled runtime-loop exception may bypass service shutdown

**Priority:** Medium
**Evidence level:** Potential / conditional

An unhandled exception from a runtime tick can terminate the loop without the expected orderly shutdown of services; no general supervising restart mechanism was established in the reviewed path.

**Recommendation:** Put lifecycle cleanup in a guaranteed `finally` path, make shutdown idempotent, and define whether individual tick failures should be logged, retried, isolated, or treated as fatal. Add failure-injection tests.

### A-02 — Controller may clear a still-live runtime thread reference

**Priority:** Medium
**Evidence level:** Confirmed static control-flow concern

The application controller uses a bounded `join(timeout=3)` and can clear its runtime-thread reference without first establishing that the thread has actually terminated.

**Recommendation:** Check `is_alive()` after the join, retain an accurate lifecycle state, and define explicit handling for shutdown timeouts.

### A-08 — Tor control resources may survive exceptional start paths

**Priority:** Medium
**Evidence level:** Potential / conditional

The reviewed `OnionServiceManager.start()` path lacks general exception cleanup guaranteeing closure of an established Tor-control connection after all intermediate failures.

**Recommendation:** Use explicit exception cleanup or an ownership/context-management pattern covering partial initialization. Verify that repeated start/stop and failed-start paths do not retain sockets.

### A-11 — FileTrustStore persistence failure can leave memory and disk inconsistent

**Priority:** Medium
**Evidence level:** Confirmed static ordering concern

The trust-store implementation mutates in-memory state before persisting the change; failure of the persistence operation does not restore the previous in-memory state.

**Recommendation:** Stage changes and publish them to memory only after successful persistence, or implement rollback on write failure. Add fault-injection tests.

### A-08a — Socket setup failure cleanup

**Priority:** Low
**Evidence level:** Potential / conditional

If a local socket's timeout configuration fails during early initialization, the socket is not explicitly closed in the examined path.

**Recommendation:** Ensure ownership and cleanup begin immediately after socket creation.

### A-13 — Attachment deletion suppresses filesystem errors

**Priority:** Low
**Evidence level:** Confirmed static behavior

Attachment cleanup uses `shutil.rmtree(..., ignore_errors=True)`, which may conceal residual files when deletion fails.

**Recommendation:** Consider reporting or logging cleanup failures without turning recoverable cleanup issues into unsafe crashes. Decide whether residual attachments require a later reconciliation process.

### Additional provisional lifecycle observations

The review also noted possible partial-start rollback concerns and a potentially stale authentication flag after transport closure. These were **not established as independently reproduced defects** and should be handled as follow-up review questions rather than release-blocking findings without further evidence.

## 6. Test-suite assessment

### B-01 — Duplicate module-level test names shadow earlier definitions

**Priority:** Low to medium for test reliability
**Evidence level:** Confirmed statically

The review identified six duplicated module-level pytest test names and seven shadowed definitions. In Python, later definitions replace earlier bindings with the same module-level name, so some intended tests may not be collected as originally written.

**Recommendation:** Rename or consolidate duplicated tests, recover any lost assertions, and check test collection after the change.

### B-02 — Missing targeted SQLite UID regression

**Priority:** Coverage gap supporting A-14
**Evidence level:** Not found in the reviewed tests

No targeted test was identified for deletion of the highest SQLite IMAP UID followed by insertion of another message.

**Recommendation:** Add this regression alongside the A-14 fix, including database-reopen behavior.

### B-03 — Some tests have weak behavioral assertions

**Priority:** Low
**Evidence level:** Confirmed in reviewed examples

At least one examined test mainly exercised a close/cleanup path without a strong assertion about final state.

**Recommendation:** Where practical, assert observable state changes, resource closure, or error behavior rather than only absence of an exception.

### Installer-test interpretation

`tests/test_install_installer.py` includes extensive tests of installation sequencing, Tor configuration inputs, runtime configuration, and adapter wiring. However, the examined `run_installation()` tests inject fake loaders and a fake installation function, sometimes using an empty manifest. They verify argument forwarding and adapter selection, not semantic validity of the repository's real manifest. The inspected Tor-path test uses a synthetic `_manifest()` fixture. This explains a plausible coverage gap without claiming that the full suite was executed or exhaustively searched.

### Historical test results

The author reported **1,974 passing tests** in prior project work. This number was **not independently revalidated** in the present audit; no tests were run.

## 7. Tor integration and continuity

### Positive mechanisms observed

The reviewed implementation and tests contain mechanisms relating to Onion identity persistence, file-permission checks, rejection of disallowed symbolic-link paths, and atomic identity-file writes. Tests exercise relevant behavior with fake Tor control components and local loopback/simulated SOCKS paths.

These are meaningful static and simulated-test signals, but they are **not equivalent to a live Tor resilience test**.

### C-REC — Automatic recovery after Tor-control loss is not established

**Priority:** Medium if continuous automatic recovery is a product requirement; otherwise a documented limitation
**Evidence level:** Not established

The review did not identify a verified supervisor/republication mechanism that automatically restores Onion Service publication following a live Tor Control disconnection. The review also did not demonstrate that the application fails to recover in every environment.

**Recommendation:** Define the expected Alpha behavior explicitly: persistence across application restarts versus automatic recovery during a running session. If automatic recovery is required, design a controlled live-Tor test for disconnection, reconnection, and republication while checking identity continuity.

### Tor verification boundaries

The following were **not** performed: live Tor startup, real Onion reachability tests, induced Tor Control disconnects, network outage simulations, or live service-republication observation.

## 8. Installer platforms and release documentation

### D-04 — Kali-specific automated coverage versus empirical validation

The author described Kali 2026.1 validation as an **empirical installation strategy**, reflecting shared Debian-family installation behavior. No Kali-specific tests were identified in the two reviewed platform/manifest test modules. The platform selector matches exact `ID` and `VERSION_ID` values; profile order is not a selector dependency. Some Ubuntu-focused tests nevertheless select the first manifest profile, creating a test-fixture ordering assumption.

**Recommendation:** Retain empirical Kali installation checks if that is the chosen strategy, and record the environment, revision, steps, and result in release notes. Automated Kali-specific tests may be added later but are not a prerequisite imposed by this audit.

### D-DOC — Release and documentation alignment

**Priority:** Medium
**Evidence level:** Confirmed static inconsistencies

Reviewed README, changelog, security, and related documentation included wording suggesting that the release tag was not yet confirmed, although a local `v0.1.1-alpha` tag was observed. The HEAD Kali profile postdates the tag, and the reviewed documentation did not consistently explain that boundary. Minor editorial inconsistencies, including platform naming/capitalization, were also noted.

**Recommendations:**

1. State the exact revision and platform matrix applicable to each release.
2. Separate local tag existence from **GitHub Release publication**, which was not verified.
3. Do not attribute the HEAD Kali profile or uncommitted manifest fixes to `v0.1.1-alpha`.
4. Update current-state documentation while preserving historically accurate release notes.
5. Describe licensing accurately: **PolyForm Noncommercial 1.0.0** makes source available under noncommercial terms; it is **not** an OSI-approved open-source license.

### D-05 — Late empty-password validation

**Priority:** Low
**Evidence level:** Static usability/ordering observation

Empty-password rejection occurs after some preparatory work in the reviewed installation path.

**Recommendation:** Consider rejecting invalid input earlier, before avoidable preparation or side effects.

### D-06 — First-run Tor resource lifecycle

**Priority:** Low / provisional
**Evidence level:** Conditional

An explicit `OnionServiceManager.stop()` was not observed in the examined first-run subprocess path. Process termination closes process-owned resources, so this is not evidence of a persistent leak across process exit.

**Recommendation:** Document the intended subprocess lifecycle; add explicit cleanup if the code may later run within a long-lived process.

## 9. Recommended remediation plan

### Phase 1 — Correctness and affected-release safety

- Fix **A-14** with a persistent, transactionally updated UID allocator and focused SQLite regressions.
- Incorporate the corrected **D-09** manifest into the intended distribution revision after reviewing the working-tree diff.
- Add a real-manifest semantic validation check before installer side effects and in CI.
- Verify that the documentation and installer instructions describe the exact revision being distributed.

**Suggested exit criteria:** UID regression passes; every shipped platform profile validates; Ubuntu/Kali installation claims match the shipped artifact and documented evidence.

### Phase 2 — Failure handling and resource ownership

- Guarantee runtime shutdown after fatal tick exceptions.
- Preserve correct controller state after bounded thread-join timeouts.
- Close Tor-control resources on partial startup failures.
- Make trust-store persistence failure behavior explicit and testable.

**Suggested exit criteria:** Targeted fault-injection tests demonstrate cleanup, predictable state, and no orphaned runtime ownership in the covered paths.

### Phase 3 — Tor continuity requirements

- Decide whether automatic recovery from live Tor Control loss is in scope for Alpha.
- If required, implement and verify reconnect/republication behavior with a controlled Tor instance.
- Distinguish stable Onion identity from uninterrupted availability in public claims.

### Phase 4 — Test and release hygiene

- Resolve shadowed pytest definitions.
- Improve weak assertions and targeted regressions.
- Record empirical Ubuntu/Kali installation evidence against specific commits or artifacts.
- Align README, changelog, security statements, license descriptions, and release provenance.

## 10. Limitations and non-claims

This review **does not claim**:

- That GarlicSMTP is secure, vulnerability-free, production-ready, or formally certified.
- That all tests pass at the reviewed HEAD or at the local working-tree state.
- That the GitHub Release or its downloadable assets were published or independently inspected.
- That live Tor service availability, reconnection, or anonymity properties were experimentally verified.
- That user-reported successful installations on Ubuntu 24.04 and Kali 2026.1 were independently reproduced.
- That every possible code path, dependency, cryptographic primitive, or deployment configuration was exhaustively examined.

The author reported working installations on Ubuntu 24.04 and Kali 2026.1. Those reports are relevant operational context but remain **author-reported** in this document.

## 11. Final assessment

The agreed static-review scope is complete. The clearest corrective actions are **A-14 (SQLite IMAP UID monotonicity)** and **D-09 (HEAD Ubuntu manifest completeness)**. The latter's structural correction was present locally at review time but should not be assumed to exist in a tagged or published artifact.

Further work should prioritize lifecycle resilience, define Tor recovery requirements, and make release documentation accurately reflect the code and artifacts actually distributed. Until those activities are completed and independently verified as appropriate, GarlicSMTP should continue to be described as **experimental Alpha software**, without claims of security certification or production-grade availability.

---

### Suggested repository placement

`docs/audits/2026-10-27-static-audit.md`

This path is a **suggestion only**. The audit did not modify the repository or commit this report. If the document is included in a release, maintainers should ensure its revision table and claims remain accurate for that release.

---

## 12. Post-audit follow-up comment — 29 October 2026

**Status:** Subsequent project work and documentation review for the proposed `v0.1.2-alpha` release. This addendum supplements, but does not retroactively change, the evidence or conclusions of the 27 October read-only static audit. The outcomes below reflect subsequent project work and checks reported and discussed in the development conversation; they are not an independent security assessment.

### Remediation and verification reported after the static audit

- **B-01 and B-03 — Test quality:** Duplicate/shadowed pytest definitions were addressed and weak behavioral assertions strengthened.
- **D-05 — Installer validation:** IMAP password validation was moved before avoidable installation side effects.
- **A-08a and related resource ownership:** Cleanup and lifecycle handling were improved for TCPServer, SOCKS5 client/connection, text connections, SMTP transport, and IMAP/SMTP startup and shutdown paths. These changes do not, by themselves, establish that every broader lifecycle concern in A-02, A-03/C-07, or A-08 is resolved.
- **S-01 — Logging privacy:** The examined logging behavior did not reveal a defect requiring a fix in that check.
- **S-02 — Queue resilience:** Unexpected queue-processing exceptions were addressed with retry/backoff handling.
- **S-03 — SQLCipher queue transactions:** Duplicate-insert recovery behavior was checked.
- **S-04 — IMAP session handling:** Authentication and session-state behavior was checked.
- **S-05/S-06 — Local listener exposure:** SMTP and IMAP listeners were checked to reject non-loopback bind addresses while accepting loopback addresses in the `127.0.0.x` range.
- **S-07 — Incomplete SMTP DATA:** EOF handling was inspected; no defect was identified in the examined path.
- **S-08 — SMTP input limits:** The reviewed implementation enforces a 64 KiB SMTP line limit, a 2 MiB (2,097,152-byte) message limit, and a 1 MiB (1,048,576-byte) attachment limit.

**Regression result reported for the subsequent development baseline:** `1,993 passed` in the complete pytest suite. This is a later result than the `1,974` historical passes noted in Section 6. It is not evidence that a release wheel, source distribution, published tag, or clean installation was tested.

### Installer and platform status

The later `install/manifest.toml` was reported and inspected as declaring three platform profiles: **Ubuntu 24.04**, **Kali 2026.1**, and **Debian 13**. The Debian 13 installation was separately reported as verified. These observations must not be projected backward onto the original audited HEAD or `v0.1.1-alpha` tag. The presence of three manifest profiles does not establish fresh-install verification of the `v0.1.2-alpha` candidate on all three platforms.

Read-only source searches during the documentation review confirmed references to the persistent paths `account-credentials.json`, `mailboxes.db`, `sent.db`, `queue.db`, and the attachments directory in `ApplicationPaths`, as well as the uninstaller's `DELETE` confirmation and references to the `debian-tor` group and `garlicsmtp-gui` launcher. These searches were not a full dynamic test of installation or uninstallation.

### Documentation review status

The following documents were reviewed and approved sequentially for the `v0.1.2-alpha` documentation effort: `project-tree.txt`, `THIRD_PARTY_LICENSES.md`, `CONTRIBUTING.md`, `SECURITY.md`, `README.md`, `CHANGELOG.md`, `CLA.md`, `installation-architecture-en.md`, `quicklaunch-en.md`, `COMMERCIAL-LICENSE.md`, and `NOTICE`. English-only documentation was adopted for this effort.

The `LICENSE` text was reviewed as the PolyForm Noncommercial License 1.0.0, with its project-specific `Required Notice` lines preserved unchanged; **explicit approval of that document had not yet been recorded at the time of this follow-up**. No rights or obligations in the license were changed.

### Outstanding release and audit boundaries

- **A-14 (SQLite IMAP UID monotonicity):** No subsequent resolution or targeted regression evidence was established in the documentation-review record; retain the original finding pending code/test verification.
- **D-09 (manifest completeness):** Later profile structure was reported corrected, but the original HEAD finding remains historically accurate. A release-artifact/real-manifest validation should be tied to the exact distribution revision.
- **Other original findings:** A-02, A-03/C-07, A-08, A-11, A-13, C-REC, D-04, and D-06 should not be marked closed solely because related improvements or documentation checks occurred. Their disposition requires finding-specific evidence.
- **Version and publication:** `pyproject.toml` was still reported as declaring `0.1.1a0` during documentation review, while the documentation target was `v0.1.2-alpha`. Final version alignment, Git consolidation, tagging, packaging, and GitHub publication had **not** been confirmed completed.
- **Security assurance:** No independent security audit, penetration test, comprehensive backup/temporary-file assessment, verified legacy plaintext migration, or live Tor continuity certification is claimed. GarlicSMTP remains experimental Alpha software.

**Follow-up conclusion:** The later engineering checks and 1,993-test regression provide stronger development evidence than was available to the original static reviewer, and the release documentation has been substantially reconciled. They do **not** erase unresolved findings, establish production readiness, or replace verification against the exact artifacts ultimately distributed.

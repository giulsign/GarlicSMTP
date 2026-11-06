# GarlicSMTP — Rapporto integrale di audit e verifica operativa

**Data di consolidamento:** 5 novembre 2026  
**Progetto:** GarlicSMTP — https://github.com/giulsign/GarlicSMTP  
**Tipologia:** audit statico assistito da AI, follow-up di sviluppo e verifiche sperimentali Tor/SMTP  
**Stato:** documento tecnico di progetto; **non** certificazione di sicurezza, anonimato o idoneità alla produzione  
**Collocazione proposta:** `docs/audits/2026-11-05-integrated-audit-t8.md`

## Sintesi esecutiva aggiornata — 5 novembre 2026

**Esito sperimentale:** **PASS** per il funzionamento Onion-to-Onion SMTP nelle configurazioni provate, inclusi DNS convenzionale TCP/UDP 53 bloccato (T0–T4) e filtraggio bilaterale del traffico in uscita non-Tor (T8). **NON CERTIFICATO** l'isolamento assoluto di ogni percorso di rete, l'assenza di ogni forma di DNS, la resistenza a tutte le interruzioni o l'anonimato dell'intero sistema.

La verifica T8 dimostra che, nelle due macchine provate, GarlicSMTP ha inviato e ricevuto email Onion-to-Onion in entrambe le direzioni mentre una tabella `nftables` `inet` bloccava il traffico esterno in uscita non associato all'UID Tor. Sono stati osservati sia il fallimento di connessioni dirette sia il successo di connessioni tramite SOCKS5 Tor. La tabella temporanea è stata infine rimossa e l'assenza di tabelle `inet` è stata verificata su entrambi gli host.

**Formulazione pubblicabile suggerita:** «In prove sperimentali su WSL2 Ubuntu e Ubuntu 24.04 VirtualBox, GarlicSMTP ha scambiato correttamente messaggi SMTP tra servizi Onion in entrambe le direzioni, anche con il traffico Internet diretto in uscita dei processi non-Tor bloccato mediante nftables. La fattibilità operativa di una configurazione con accesso esterno mediato da Tor è stata verificata per gli scenari testati.»

**Precisazione:** Tor utilizza necessariamente la connettività IP sottostante verso i relay. «Solo Tor» descrive il percorso applicativo verso la rete, non l'assenza di TCP/IP. Le prove non hanno filtrato completamente traffico `input`/`forward`, né hanno escluso tutti i possibili proxy, privilegi elevati, vie alternative o perdite applicative. Non è stata svolta una verifica di sicurezza indipendente.

### Provenienza e limiti dell'evidenza

- Il rapporto del 27 ottobre è un esame statico *read-only*: le sue affermazioni storiche restano valide per quella data.
- Il follow-up del 29 ottobre registra modifiche e regressioni riferite nel lavoro di sviluppo, non una nuova ispezione completa dei binari distribuiti.
- I test T0–T4 e T8 sono verifiche operative eseguite dall'operatore con comandi e output riportati in sessione; alcuni esiti GUI sono confermati dall'operatore. Non è stato acquisito un bundle completo e firmato di log, commit e hash dei pacchetti eseguiti.
- Nessuna evidenza dei test di rete chiude automaticamente finding di codice che richiedono una regressione specifica.

---

# Parte I — Rapporto statico originale (27 ottobre 2026)

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

# Parte II — Follow-up delle correzioni (29 ottobre 2026)

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


---

# Parte III — Verifiche Tor e DNS T0–T4 (4 novembre 2026)

# Addendum A — Post-audit empirical verification and finding disposition

**Addendum date:** 4 November 2026

**Related audit:** GarlicSMTP — Static Audit Report, 27 October 2026

**Verification scope:** Tor bootstrap without conventional DNS on port 53; Onion-to-Onion SMTP delivery; operational observations reported by the project author

**Status:** Experimental verification completed for T0–T4; original static findings retained pending issue-specific remediation evidence

**Evidence provenance:** Interactive, operator-executed commands and terminal outputs reviewed in the technical session; application-level receipt and supplementary tests confirmed by the operator. No independent third-party laboratory certification is claimed.

## A.1 Purpose, document integrity, and scope

This addendum supplements rather than retrospectively rewrites the static audit. The original audit's statements that no live Tor tests were performed **during the 27 October static review** remain historically accurate. The experiments described below were performed subsequently and are therefore new evidence, not evidence available to the original reviewer. The addendum does not assert that the reviewed Git HEAD, a tagged release, or a published release artifact is identical to the code executed in the later experiments; no matching commit hash or reproducible artifact digest was recorded for the live test environment.

The narrow experimental question was whether GarlicSMTP can exchange SMTP messages over Tor Onion Services when ordinary outbound DNS queries to TCP/UDP destination port 53 are blocked, including when an isolated Tor process starts with an initially empty data directory. The tests were not designed to evaluate DNS-over-HTTPS, DNS-over-TLS, all resolver paths, traffic anonymity, or every possible Tor network condition.

## A.2 Test environment and isolation controls

| **Item**                | **Recorded configuration**                                                                                                              |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| Endpoint 1              | Windows WSL2 Ubuntu; GarlicSMTP project under /mnt/c/garlicsmtp; ordinary Tor SOCKS 127.0.0.1:9050, Control 9051                        |
| Endpoint 2              | Ubuntu 24.04 VirtualBox VM; GarlicSMTP project under /home/ubuntu/Downloads/GarlicSMTP                                                  |
| VM ordinary Tor         | tor@default.service; SOCKS 9050, Control 9051; remained distinct from the experimental process                                          |
| Experimental Tor        | Tor 0.4.9.11; configuration /etc/tor/torrc-garlicsmtp-t3; data /var/lib/tor-garlicsmtp-t3; SOCKS 127.0.0.1:9350; Control 127.0.0.1:9351 |
| Experimental GarlicSMTP | Separate profile /home/ubuntu/.local/share/garlicsmtp-t3; SMTP 127.0.0.1:3525; IMAP 127.0.0.1:2143; Onion HTTP target 8083              |
| Tor authentication      | Local Tor Control with SAFECOOKIE; experimental cookie readable by the authorized application user, without making it world-readable    |
| DNS restriction         | Dedicated nftables table inet garlicsmtp_t3, outbound UDP and TCP destination port 53 dropped and counted                               |
| Isolation               | Original application profile, credentials, mail databases and Onion identity were not copied into the experimental profile              |

The isolated Tor configuration used DataDirectory, SocksPort, ControlPort, CookieAuthentication 1 and ClientOnly 1; cookie group readability was configured and the experimental cookie permissions were checked. The application was launched by explicitly passing ApplicationPaths(root_dir=Path('/home/ubuntu/.local/share/garlicsmtp-t3')), rather than relying on the default user or development profile. A new experimental Onion identity was created at state/onion-service.key with file mode 0600 and a recorded size of 99 bytes. The private key itself was not disclosed.

## A.3 Executed test matrix

| **Test**                 | **Procedure / condition**                                                                                                    | **Observed outcome**                                                                   | **Evidence classification**                                               |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| T0 — Baseline            | Ordinary WSL2-to-VM Onion SMTP transfer                                                                                      | Message delivered                                                                      | Operator-confirmed live test                                              |
| T1-A                     | VM outbound TCP/UDP 53 blocked after Tor was already bootstrapped                                                            | Onion service and WSL2-to-VM delivery succeeded                                        | Operator-confirmed live test                                              |
| T1-B                     | Outbound TCP/UDP 53 blocked on both WSL2 and VM                                                                              | Email delivered                                                                        | Operator-confirmed live test                                              |
| T2-A                     | Isolated Tor bootstrap using copied cache; DNS 53 blocked before startup                                                     | Bootstrap reached 100%; SOCKS connection to check.torproject.org:443 succeeded         | Operator-confirmed live test                                              |
| T2-B                     | Isolated Tor bootstrap from empty data directory; DNS 53 blocked before startup                                              | Bootstrap reached 100%; SOCKS connection to check.torproject.org:443 succeeded         | Operator-confirmed live test                                              |
| T3 — Integrated receiver | Tor T3 started from empty directory with DNS 53 blocked; independent GarlicSMTP profile and Onion identity; WSL2-to-T3 email | Bootstrap 100%; Onion SMTP reachable via SOCKS 9350; email received and readable in T3 | Terminal outputs plus operator-confirmed GUI receipt                      |
| T4 — Reverse direction   | VM T3-to-WSL2 Onion email during the T3 session                                                                              | Delivered and readable according to operator                                           | Operator-reported parallel test; no separate terminal transcript recorded |

The T2-A/T2-B configuration artifacts were no longer present after a subsequent VM reboot. Their outcomes are retained as previously observed results, not presented as presently re-executable evidence from those files.

## A.4 T3 chronological verification record

6.  An empty, permission-restricted Tor data directory was created under /var/lib/tor-garlicsmtp-t3. Configuration validity was checked before the experimental daemon started.

7.  The dedicated nftables output chain was installed with policy accept and explicit drop rules for TCP and UDP destination port 53. A resolver query timed out, and rule counters increased, demonstrating interception of port-53 traffic.

8.  The isolated Tor process started with the DNS block already active. Its bootstrap log progressed from 0% to 100%; an independent SOCKS5 connection through 127.0.0.1:9350 succeeded.

9.  A separate GarlicSMTP T3 profile was initialized with dedicated ports and a fresh Onion identity. The application GUI opened, account setup completed, and the Onion service was reported active.

10. Local TCP connection checks succeeded on ports 3525 (SMTP), 2143 (IMAP), 9350 (Tor SOCKS) and 9351 (Tor Control). These checks establish listening endpoint reachability, not by themselves full application functionality.

11. A SOCKS5 CONNECT to the experimental Onion address, virtual port 25, returned success. This confirmed Onion SMTP endpoint reachability through the experimental Tor SOCKS interface.

12. An email with subject TEST-T3-DNS53 was sent from WSL2 to GarlicSMTP T3 and was confirmed readable in the T3 mailbox. The operator also independently confirmed the reverse T3-to-WSL2 delivery (T4).

13. After message delivery, the DNS-drop rules remained installed. Final counters were 301 UDP packets / 25,418 bytes and 1,015 TCP packets / 61,480 bytes, totaling 1,316 packets / 86,898 bytes dropped for destination port 53. Counters are aggregate firewall observations; they do not establish which individual process generated every blocked packet.

14. The experimental GUI was closed, the experimental Tor process was stopped, and the dedicated nftables table was removed. A subsequent sudo nft list ruleset returned an empty ruleset. systemctl is-active tor@default.service returned active, confirming the ordinary Tor service remained running at the final check.

**Result:** The T3/T4 evidence supports successful bidirectional Onion-to-Onion SMTP message exchange under the recorded experimental conditions. It does not prove uninterrupted service availability, successful delivery under every network failure, or absence of DNS use via other ports or protocols.

## A.5 Operational evidence supplied by the author

The author additionally reported that (i) Onion identities remain persistent in ordinary operational use; (ii) numerous project pytest cases already exercise interruption, queueing and retry behavior; (iii) real usage after service suspension or interruption results in eventual message delivery, sometimes delayed by Tor congestion; and (iv) sequences of messages are delivered, although arrival order can differ, with a GUI queue-retry control used to restart pending delivery attempts when needed.

These statements provide relevant operational context, but the addendum did **not** independently inspect test IDs, execute the current suite, measure delivery latency, or validate duplicate-free delivery under controlled fault injection. They therefore must not be conflated with independently observed T3 terminal evidence. Arrival order is not generally guaranteed by SMTP, and successful eventual delivery does not establish an upper latency bound.

## A.6 Mapping to the original audit findings

The statuses below distinguish **new empirical coverage** from **verified source-code remediation**. The latter requires issue-specific code, revision and regression evidence not produced by this DNS/Tor campaign.

| **Original finding / concern**                                                                                    | **Post-audit evidence**                                                                                                                                                              | **Disposition as of 4 November 2026**                                                                                                                    |
|-------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Section 7 — No live Tor startup / real Onion reachability previously tested                                       | T2-A/T2-B and T3: bootstrap, live SOCKS and Onion SMTP connection; T3/T4 real delivery                                                                                               | Evidence gap addressed for the tested configurations; original audit statement remains valid for its earlier review date                                 |
| Section 7 — Onion identity mechanisms only statically/simulated tested                                            | T3 fresh identity created, mode 0600, active Onion service; ordinary identity persistence author-reported                                                                            | Partially addressed empirically; persistence of the specific T3 identity across a restart was not separately tested                                      |
| C-REC — Automatic recovery after Tor Control loss not established                                                 | Author reports recovery/retry in ordinary usage and pytest coverage; T3 demonstrates normal startup and shutdown, not an induced live Control disconnect and automatic republication | Not closed as originally defined; if autonomous live Control reconnection is a requirement, it still needs a dedicated acceptance criterion and evidence |
| A-08 — Exceptional Tor Control startup cleanup                                                                    | Successful T3 startup and controlled shutdown only                                                                                                                                   | Open / not revalidated; normal success does not exercise partial-start exception paths                                                                   |
| A-03/C-07 — Runtime exception may bypass shutdown                                                                 | Operational interruption/retry reports; no injected fatal runtime tick exception in this campaign                                                                                    | Open / not revalidated                                                                                                                                   |
| A-02 — Bounded join may lose live thread ownership                                                                | No targeted thread-shutdown timeout test in this campaign                                                                                                                            | Open / not revalidated                                                                                                                                   |
| A-11 — Trust-store memory/disk consistency                                                                        | No forced persistence-failure test                                                                                                                                                   | Open / not revalidated                                                                                                                                   |
| A-14 and B-02 — SQLite IMAP UID monotonicity and regression                                                       | Email receipt is not a delete-highest-UID/reinsert regression                                                                                                                        | Open / not revalidated; remains high-priority for affected backend                                                                                       |
| D-09 — Ubuntu installer manifest completeness                                                                     | T3 launched an existing installed environment; no real-manifest CI validation or fresh installation against a fixed revision                                                         | Original finding not closed; locally corrected manifest observed in the 27 October audit, but no release-level verification provided here                |
| B-01 / B-03 — Shadowed pytest definitions / weak assertions                                                       | Author reports extensive tests, but no current collection or assertion review was performed here                                                                                     | Open / not revalidated                                                                                                                                   |
| D-04 / D-DOC / D-05 / D-06 — Platform validation, release documentation, installer ordering and first-run cleanup | No fresh Kali install, release artifact inspection or installer fault-injection in this campaign                                                                                     | Open or informational as originally classified                                                                                                           |
| A-08a / A-13 — Socket setup and attachment cleanup                                                                | No targeted failures induced                                                                                                                                                         | Open / not revalidated                                                                                                                                   |

**Resolution statement:** The experiments resolve the **specific uncertainty that GarlicSMTP/Tor Onion-to-Onion delivery might require conventional DNS on port 53, including after an empty-cache Tor bootstrap**, within the tested environment. They do **not** resolve unrelated static code defects simply by demonstrating successful delivery.

## A.7 Engineering interpretation and recommendations

The live results materially strengthen the earlier static audit's Tor integration assessment. The product has now been observed operating over real Onion endpoints with conventional DNS port 53 blocked, including a fresh isolated Tor bootstrap and bidirectional email delivery. This supports a narrowly worded release note such as: \*“In an Ubuntu 24.04 VM/WSL2 experimental setup, GarlicSMTP successfully exchanged Onion-to-Onion SMTP email while outbound TCP/UDP DNS port 53 was blocked; an isolated Tor instance bootstrapped from an empty data directory.”\*

Avoid broader claims such as “GarlicSMTP never needs DNS,” “all Tor outages recover automatically,” “message order is preserved,” or “the original static audit is fully remediated.” The original high-priority A-14 and D-09 issues and other unverified code paths retain their audit status until separately addressed with revision-specific evidence.

For formal closure of those remaining findings, maintain an issue-by-issue remediation ledger containing the affected revision, code change or accepted limitation, targeted regression name, observed test result, and release artifact/commit identifier. The present addendum supplies a completed empirical Tor/DNS test record, not a substitute for that ledger.

## A.8 Reproducibility, limitations and preservation

The experiment was interactive and operator-executed. Full raw terminal logs, cryptographic hashes of source artifacts, exact WSL2/VM network interfaces, timestamps for every test stage, and a CI-generated test report were not attached to this addendum. T4 and the operational queue observations were confirmed by the author rather than independently logged. The DNS firewall rules covered destination port 53 for the VM in T3, not all possible DNS transport variants or every host in every test.

The experimental Tor configuration/data and GarlicSMTP profile were deliberately kept separate from ordinary installation state. After the experiment, the experimental application and Tor instance were stopped, the dedicated firewall table was removed, the VM ruleset was empty, and the ordinary Tor service was active. Experimental files were retained rather than deleted. No private Onion keys, Tor authentication cookies, passwords or recovery secrets are reproduced in this document.

**Final addendum assessment:** **PASS** for the defined conventional-DNS-port-53-blocked Onion-to-Onion SMTP test objective (T0–T4, with the evidence qualifications above). **NO CHANGE** to unresolved source-level findings A-14, D-09 and other issue-specific recommendations unless separately substantiated.


---

# Addendum B — T8: isolamento bilaterale Tor-only, 5 novembre 2026

## B.1 Obiettivo e perimetro

Verificare che due istanze GarlicSMTP già installate possano scambiarsi email SMTP attraverso Onion Services mentre il traffico in uscita verso interfacce non-loopback viene negato ai processi diversi da Tor su **entrambe** le macchine. Conservare configurazioni, credenziali, profili e chiavi Onion esistenti; non modificare il firewall Windows; rendere reversibili le regole temporanee.

**Host A:** Ubuntu in Windows WSL2, utente `giuliano`, progetto `/mnt/c/garlicsmtp`, Tor UID **106**, SOCKS `127.0.0.1:9050`, Control `127.0.0.1:9051`, interfaccia `eth0` IPv4 `192.168.158.209`; nessuna route IPv6 predefinita rilevata in preparazione.  
**Host B:** Ubuntu 24.04 VirtualBox, utente `ubuntu`, host `ubuntu2204`, Tor UID **123**, SOCKS `127.0.0.1:9050`, Control `127.0.0.1:9051`, interfaccia `enp0s3` IPv4 `10.0.2.15`; route IPv6 predefinita presente nella verifica preparatoria.

`nftables` v1.0.9 su entrambi. La verifica preliminare aveva mostrato ruleset vuoti e assenza di tabelle `inet`. È stata verificata l'accettazione sintattica di `meta skuid` e dei due file prima dell'applicazione. I timer di ripristino automatico `garlicsmtp-t8-rollback` sono stati predisposti e rinnovati dall'operatore su entrambi gli host, con rimozione della sola tabella `inet garlicsmtp_t8`.

## B.2 Regole effettivamente applicate

**WSL2:**

```nft
 table inet garlicsmtp_t8 {
   chain output {
     type filter hook output priority 0; policy accept;
     oifname "lo" accept
     meta skuid 106 counter accept
     counter drop
   }
 }
```

**VM Ubuntu:** identica struttura, con `meta skuid 123 counter accept`.

Queste regole filtrano l'hook **OUTPUT** sia per IPv4 sia per IPv6; permettono loopback e traffico associato all'UID Tor, e scartano il restante traffico in uscita. Non impongono una policy `input` o `forward`; non dimostrano che ogni pacchetto accettato per UID sia effettivamente destinato a un relay Tor. L'accettazione su loopback permette le comunicazioni GarlicSMTP–Tor, ma può permettere anche l'accesso ad altri servizi locali eventualmente presenti.

## B.3 Matrice cronologica delle verifiche

| ID | Verifica | Evidenza osservata | Esito |
| --- | --- | --- | --- |
| T8-01 | Sintassi regole WSL2/VM | `sudo nft -c -f ...` terminato senza errori su entrambi | PASS |
| T8-02 | Regole WSL2 attive | `oifname "lo" accept`; `meta skuid 106`; `counter drop` | PASS |
| T8-03 | Blocco diretto IPv4 WSL2 | `curl -4 --noproxy '*' ... https://example.com` → timeout dopo 5002 ms; contatore drop da 0 a **6 pacchetti / 360 byte** | PASS, blocco osservato |
| T8-04 | Regole VM attive | `meta skuid 123` e `counter drop` presenti | PASS |
| T8-05 | Blocco diretto IPv4 VM | `curl` non installato (nessun test effettuato con curl); Python `connect_ex(("1.1.1.1",443))` → **11**; drop da 0 a **114 pacchetti / 8.096 byte** | PASS, blocco osservato |
| T8-06 | SOCKS locale WSL2/VM | Handshake SOCKS5 `0500` su `127.0.0.1:9050` in entrambi gli host | PASS |
| T8-07 | Uscita TCP mediata da Tor WSL2/VM | SOCKS CONNECT a `example.com:443` → `05000001 SUCCESS` su entrambi | PASS |
| T8-08 | Avvio applicativo | `python -m garlicsmtp.gui` avviato su entrambe le macchine, confermato dall'operatore | PASS |
| T8-09 | SMTP Onion WSL2 → VM | Oggetto `T8-WSL2-TO-VM-001`; invio e ricezione confermati dall'operatore | PASS |
| T8-10 | SMTP Onion VM → WSL2 | Oggetto `T8-VM-TO-WSL2-002`; invio e ricezione confermati dall'operatore | PASS |
| T8-11 | Tentativo IPv6 diretto VM | Python TCP verso `2606:4700:4700::1111:443` → `connect_ex = 11` | FALLIMENTO CONNESSIONE, coerente con filtro; attribuzione specifica non isolata |
| T8-12 | Contatori finali VM | Tor accettati **539 pacchetti / 478.556 byte**; scartati **800 pacchetti / 54.912 byte** | PASS, traffico consentito e scartato coesistenti |
| T8-13 | Ripristino | `sudo nft delete table inet garlicsmtp_t8` eseguito su entrambi; `sudo nft list tables inet` senza output su entrambi | PASS |

L'assenza di connessioni TCP `ESTABLISHED` in un controllo puntuale `ss` non è stata interpretata come guasto: le successive connessioni SOCKS hanno verificato operativamente Tor. Il contatore finale VM è aggregato, non separa IPv4 e IPv6, e comprende traffico generato durante più operazioni. L'esito IPv6 non prova da solo che ogni possibile connessione IPv6 sia impossibile. Su WSL2 non era stata rilevata una route IPv6 predefinita, perciò una prova negativa IPv6 su quell'host sarebbe stata meno significativa.

## B.4 Conclusione T8 e ripristino

**PASS — obiettivo applicativo T8:** comunicazione SMTP Onion-to-Onion bidirezionale riuscita con filtraggio OUTPUT bilaterale attivo e blocchi diretti osservati. **PASS — reversibilità:** la tabella `inet garlicsmtp_t8` è stata eliminata e l'assenza di tabelle `inet` è stata verificata su entrambi gli host. Non sono state richieste modifiche a Tor, profili o chiavi Onion; non sono state esposte chiavi private o credenziali nel rapporto.

**Limiti residui:** nessuna prova di isolamento totale dei namespace di rete o dei percorsi di ingresso/inoltro; nessuna verifica sistematica di UDP, ICMP, IPv6 per ogni host, proxy locali, processi privilegiati, traffico kernel o applicazioni secondarie; nessun avvio Tor da directory dati vuota **durante T8** (tale condizione era stata verificata nei test T2/T3 con blocco DNS 53); nessun test di perdita di anonimato, fingerprinting o disconnessione/ripubblicazione automatica Tor Control.

## B.5 Dichiarazione tecnica consentita

**Sì, con riserva sperimentale:** i test minimi T0–T4 + T8 supportano la conclusione che GarlicSMTP **può presumibilmente operare in una configurazione nella quale l'accesso esterno applicativo avviene tramite Tor e le connessioni dirette ordinarie sono filtrate**. Si tratta di compatibilità e fattibilità osservate nei due ambienti provati, non di garanzia universale né di certificazione di sicurezza.

## B.6 Follow-up consigliato, non condizione retroattiva del PASS

1. Associare ai test i commit Git esatti, versione Tor/GarlicSMTP e hash degli artefatti.
2. Automatizzare una regressione di rete con contatori distinti IPv4/IPv6 e controlli su `input`/`forward`, namespace e possibili proxy locali.
3. Verificare un bootstrap Tor da dati vuoti **con T8 attivo** su entrambi gli host, se si vuole rivendicare anche quella specifica proprietà.
4. Eseguire test mirati dei finding ancora aperti (in particolare A-14/B-02, D-09, A-02, A-03/C-07, A-08, A-11, C-REC), senza considerarli risolti per effetto dei soli test SMTP.
5. Registrare le prove contro un pacchetto di release identificato e conservare log redatti, senza segreti.

---

## Stato finale di audit — 5 novembre 2026

| Area | Stato | Interpretazione |
| --- | --- | --- |
| Revisione statica 27 ottobre | Completata | Finding originali preservati |
| Follow-up correttivi 29 ottobre | Registrati, in parte riferiti | Non sostituiscono regressioni legate a una release |
| T0–T4, DNS 53 e Onion | PASS nelle configurazioni provate | Inclusi bootstrap Tor isolato e messaggi nei due sensi |
| T8, filtro Tor-only bilaterale | PASS per l'obiettivo applicativo | Non è prova di isolamento universale |
| Ripristino firewall T8 | PASS | Nessuna tabella `inet` residua osservata |
| Sicurezza/anonimato certificati | NON STABILITI | Nessuna certificazione indipendente |
| Readiness produzione | NON STABILITA | Restano finding e verifiche di release |

**Valutazione finale:** evidenza sperimentale favorevole alla fattibilità di GarlicSMTP su trasporto Onion-to-Onion con accesso diretto esterno filtrato; mantenere la classificazione **Alpha sperimentale** e le cautele sui finding di codice e sulla provenienza degli artefatti.

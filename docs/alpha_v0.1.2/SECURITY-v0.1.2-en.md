# GarlicSMTP Security Policy

## Purpose and release status

GarlicSMTP is security-sensitive Alpha software designed to transport email through Tor Onion Services. Responsible security and privacy reports are welcome, including reports from independent researchers and auditors.

This policy describes the **v0.1.2-alpha release candidate**. The corresponding Git tag, published release, and final package metadata must be verified during release consolidation; this document does not claim that they already exist. The project and application version declarations are now aligned to `0.1.2a0`; previously inspected installed metadata and distribution archives reflected earlier versions and have not yet been revalidated. Those artifacts are not evidence of a completed v0.1.2-alpha release.

GarlicSMTP has **not undergone an independent professional security audit**. Internal review, automated tests, and successful Tor communication cannot guarantee anonymity, confidentiality, integrity, or resistance to endpoint compromise. Assess the deployment environment and threat model before using GarlicSMTP for sensitive communications.

## Security properties and their limits

The Alpha implementation uses a password-unlocked 32-byte data-encryption key (DEK) and SQLCipher for the Received, Sent, and Queue databases. Local attachment content and metadata use authenticated GSAT v1 files. GUI and mailbox CLI flows unlock the DEK before database access; SMTP reception uses an application builder supplied with the DEK. These are descriptions of the implementation and its intended protections, **not an independent cryptographic certification**.

Earlier read-only checks of selected development databases did not find plaintext SQLite headers, and selected attachment files were identified as GSAT v1. Those observations do not cover every database, temporary file, backup, export, private key, or deployment configuration and do not prove that all data at rest is encrypted.

A previously documented CLI `start` bootstrap behavior failed closed when no DEK was available. Its exact behavior in the v0.1.2-alpha candidate remains a release-verification item; this policy does not assert that the limitation persists or has been resolved. No migration of legacy plaintext data has been certified here.

The reviewed development environment included `sqlcipher3` 0.6.3, with SQLCipher `4.12.0 community` and SQLite `3.51.1` previously observed. Native extension inspection found no direct dynamic links to system `libsqlcipher` or `libcrypto`; this does **not** establish the complete set of statically incorporated libraries or their build properties. See `THIRD_PARTY_LICENSES.md` for dependency and licensing details.

Protect recovery material, passwords, private keys, local backups, and the host operating system. Security depends on their handling as well as on application code.

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** to:

**giulisign@gmail.com**

Avoid public disclosure until the maintainer has had a reasonable opportunity to investigate and coordinate a response. This is a request for coordinated disclosure, not a fixed embargo or guaranteed response deadline.

Where possible, provide:

- the affected version or source commit and operating environment;
- the affected component and a clear description of the issue;
- minimal reproducible steps or a safe proof of concept;
- expected and observed behavior, and potential security or privacy impact;
- relevant diagnostics with personal information and secrets removed;
- a proposed mitigation or patch, if available.

**Do not send** Onion Service private keys, Tor authentication cookies, passwords, recovery secrets, private cryptographic keys, mailbox contents, or other credentials. If evidence contains sensitive material, describe it first and request a safe handling procedure. Ordinary email should not be assumed to provide end-to-end confidentiality.

## Issues in scope

Security-relevant reports include, but are not limited to:

- exposure of a user's network address or Onion Service identity;
- bypass of intended Tor routing or unexpected clearnet connections;
- authentication or authorization bypass and unauthorized mailbox access;
- remote code execution, command or protocol injection, and unsafe message parsing;
- exposure of messages, attachments, metadata, or cryptographic material;
- failures in encryption, authentication, signature verification, or key handling;
- unsafe logs, temporary files, backups, or configuration that materially expose sensitive information;
- resource exhaustion or availability failures with a plausible security impact;
- weaknesses that materially undermine intended privacy or anonymity protections.

Ordinary functional defects without a plausible security impact may be reported through the normal issue process. If unsure, report privately.

## Third-party vulnerabilities

GarlicSMTP relies on Python dependencies, SQLCipher-related components, the external Tor daemon, and operating-system prerequisites such as Tkinter/Tcl/Tk. Vulnerabilities originating upstream should generally also be reported through the relevant upstream security channel. GarlicSMTP reports are welcome when its integration introduces or amplifies the impact.

The declared Python runtime dependencies are `dnspython>=2.8,<3`, `cryptography>=46,<47`, and `sqlcipher3==0.6.3`. The installation manifest declares profiles for Ubuntu 24.04, Kali 2026.1, and Debian 13. A package present in a developer's virtual environment is not necessarily shipped with GarlicSMTP; determine distributed contents from the final artifacts, not `pip freeze` alone.

## Tor and anonymity boundaries

Tor Onion Services can reduce exposure of communicating endpoints' network locations, but **do not provide absolute anonymity**. Relevant threats include compromised endpoints or operating systems, malicious dependencies, traffic analysis or correlation, application-level metadata, persistent Onion Service identities, unsafe logging, configuration errors, cryptographic weaknesses, and disclosure of stored messages or keys.

Tor cannot protect information compromised at an endpoint before entering or after leaving the Tor-protected path. Neither Tor connectivity nor a passing test suite establishes that a deployment is anonymous or secure.

## Sensitive information and operational precautions

An installation may contain Onion Service identity keys, Tor authentication material, recovery material, mailbox databases, queued messages, attachments, sender and recipient identifiers, metadata, and configuration. Never commit these materials to source control, attach them to public issues, or disclose them in unredacted diagnostics.

Restrict filesystem permissions, protect the host and backups, inspect logging and exported files, and conduct security testing in controlled environments. These are operational precautions, not evidence of a completed security assessment.

## Supported versions and security maintenance

**v0.1.2-alpha is a release candidate, not a confirmed published security-maintenance branch.** No guaranteed security-support period has been established for it or for historical Alpha releases. Older commits, prereleases, and development snapshots should not be assumed to receive security fixes.

After publication, update this section to identify the actual release tag and source commit and to state any explicit maintenance commitment. A version number or passing tests alone does not create a security-support guarantee.

## Coordinated disclosure and security research

The maintainer intends to make reasonable efforts to acknowledge credible reports, investigate their impact, coordinate appropriate fixes, protect reporter information where feasible, and communicate material security findings when useful to users. **No particular acknowledgment, remediation, or disclosure deadline is guaranteed.**

Good-faith research is welcome when lawful and conducted without intentionally harming people, systems, or networks. Prefer testing against systems and Onion Services you control; avoid accessing third-party data or disrupting services.

## v0.1.2-alpha security review and release checks

The internal audit addressed targeted reliability and security-sensitive behaviors, including socket and thread lifecycle cleanup, queue retry handling, SQLCipher transaction recovery, IMAP session authentication, loopback-only SMTP/IMAP listeners, SMTP incomplete-DATA handling, and SMTP input-size limits. The reviewed implementation enforces a **64 KiB SMTP line limit** and a **2 MiB SMTP message limit**; the attachment limit remains **1 MiB**. These limits are implementation controls, not guarantees against all resource-exhaustion attacks.

The latest reported complete development test run passed **1,993 tests**. This is a historical test result for the reviewed code, **not** proof that the final release artifacts have been tested or independently audited.

Before publishing v0.1.2-alpha, confirm against the final source and distribution artifacts:

- the actual package version, Git tag, source commit, and security-support wording;
- the current CLI `start`/DEK bootstrap behavior and any documented limitation;
- DEK unlock paths, SQLCipher database behavior, GSAT v1 handling, and recovery paths;
- Onion HTML page paths and other externally influenced configuration;
- logging, temporary files, backups, permissions, and error paths;
- exact packaged dependencies and any statically incorporated native components;
- installation behavior on the claimed target profiles, to the extent tested;
- the full test results and security-relevant known limitations for the final release candidate.

These are **verification items**, not assertions of known vulnerabilities or failed tests. Document any remaining limitations accurately rather than implying that internal testing constitutes an independent security audit.

## No security warranty

Original GarlicSMTP code is provided subject to the warranty and liability provisions of the **PolyForm Noncommercial License 1.0.0**. Third-party components retain their own license terms.

Nothing in this policy guarantees that GarlicSMTP is secure, anonymous, or suitable for any particular threat model.

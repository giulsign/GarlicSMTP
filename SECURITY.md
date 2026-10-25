# GarlicSMTP Security Policy

## Purpose and project status

GarlicSMTP is security-sensitive software designed to transport email through Tor Onion Services. Security and privacy reports are welcome.

This policy is being reviewed for the **0.1.1a0 development version**, intended for a future **v0.1.1-alpha** release. At the time of this review, the v0.1.1-alpha Git tag and public release have **not** been confirmed. The previously documented v0.1.0-alpha.1 baseline (source commit `9bfc2f7`) is historical, not evidence that v0.1.1-alpha has been released. The latest development changes discussed during this review are associated with commit `8faf1c6`; that commit is not presented here as a certified security baseline.

GarlicSMTP has not undergone an independent professional security audit. Its design and test results do not guarantee anonymity, confidentiality, integrity, or resistance to endpoint compromise. Evaluate the deployment environment and threat model before using it for sensitive communications.

## Security properties and their limits

The previously validated Alpha implementation uses a password-unlocked 32-byte data-encryption key (DEK) and SQLCipher for the Received, Sent, and Queue databases. Local attachment content and metadata are stored in authenticated GSAT v1 files. GUI and mailbox CLI flows unlock the DEK before database access; SMTP reception uses an application builder equipped with the DEK.

Historical read-only checks on a development machine and Ubuntu VM found no plaintext SQLite headers in the checked databases and identified the GSAT v1 format in checked attachment files. These checks were limited observations: they were **not** a comprehensive cryptographic audit, forensic assessment, or verification of every file, temporary artifact, backup, private key, or deployment configuration. They must not be interpreted as proof that all data at rest is encrypted.

The earlier policy recorded a CLI `start` bootstrap limitation: it failed closed when no DEK was available. Whether this limitation still applies to the candidate release must be rechecked against current code and tests before publication. No migration of existing plaintext data has been certified by this policy.

The installed development environment was observed to load `sqlcipher3` 0.6.3 with SQLCipher `4.12.0 community` and SQLite `3.51.1`. This establishes the versions observed in that environment; it does not independently verify all packaged binaries, build flags, or cryptographic properties. See `THIRD_PARTY_LICENSES.md` for dependency and licensing information.

Protect recovery material, passwords, private keys, local backups, and the host operating system. Security depends on their handling as well as on application code.

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** to:

**giulisign@gmail.com**

Avoid public disclosure until the maintainer has had a reasonable opportunity to investigate and coordinate an appropriate response. This is a request for coordinated disclosure, not a promise of a fixed embargo or response deadline.

Where possible, include:

- the affected GarlicSMTP version or commit and operating environment;
- the affected component and a clear description of the issue;
- minimal, reproducible steps or a safe proof of concept;
- the expected and observed behavior and potential security or privacy impact;
- relevant diagnostic details with secrets and personal information removed;
- a proposed mitigation or patch, if available.

**Do not send** Onion Service private keys, Tor authentication cookies, passwords, recovery secrets, private cryptographic keys, mailbox contents, or other credentials. If evidence contains sensitive material, describe it without attaching it and request a safe handling procedure first. Email itself should not be assumed to provide end-to-end confidentiality.

## Issues in scope

Examples of security-relevant reports include:

- disclosure of a user's network address or Onion Service identity;
- bypass of intended Tor routing or unexpected clearnet connections;
- authentication or authorization bypass and unauthorized mailbox access;
- remote code execution, command injection, protocol injection, or unsafe message parsing;
- exposure of message content, attachments, metadata, or cryptographic material;
- failures in encryption, authentication, signature verification, or key handling;
- unsafe logs, temporary files, backups, or application configuration that materially expose sensitive information;
- vulnerabilities that materially weaken intended privacy or anonymity protections.

Functional bugs without a plausible security impact may be handled through the ordinary issue-reporting process. If unsure, report privately.

## Third-party vulnerabilities

GarlicSMTP relies on third-party components, including Python packages, SQLCipher, and the external Tor daemon. Vulnerabilities originating in those components should generally also be reported through the relevant upstream security channels. Reports are welcome when GarlicSMTP's integration exposes or amplifies the impact of such an issue.

A package installed in a developer's virtual environment is not necessarily a dependency shipped with GarlicSMTP. The runtime manifest and the actual release artifacts, rather than `pip freeze` alone, determine the distribution's contents.

## Tor and anonymity boundaries

Tor Onion Services can reduce exposure of communicating endpoints' network locations, but **do not provide absolute anonymity**. Threats include endpoint or operating-system compromise, malicious dependencies, traffic analysis or correlation, application-level metadata, persistent Onion Service identities, unsafe logging, configuration mistakes, cryptographic errors, and disclosure of stored messages or keys.

Tor does not protect information compromised at an endpoint before entering or after leaving the Tor-protected communication path. Do not assume that application content, identity information, or local data are safe solely because Tor is in use.

## Sensitive information and operational precautions

An installation may contain Onion Service identity keys, Tor authentication material, recovery material, mailbox databases, queued messages, attachments, sender and recipient identifiers, metadata, and configuration. Do not commit these materials to source control, attach them to public issues, or share them in unredacted logs.

Restrict filesystem permissions, protect the host and backups, review logging and exported files, and use a controlled environment for security testing. These are operational precautions, not evidence of a completed security assessment.

## Supported versions and security maintenance

The **v0.1.1-alpha candidate is not yet a confirmed public release**. This policy does not designate it as a supported security-maintenance branch. The earlier `v0.1.0-alpha.1` baseline is historical; no guaranteed support period has been established for it. Older commits, prereleases, and development snapshots should not be assumed to receive security fixes.

When a public release is made, this section should be updated to identify the actual released tag, relevant source commit, and any support commitment. Until then, do not infer a security-support guarantee from a version string or passing tests.

## Coordinated disclosure and security research

The maintainer intends to make a reasonable effort to acknowledge credible reports, investigate their impact, coordinate fixes when appropriate, protect reporter information where feasible, and communicate security-relevant findings when doing so helps users. **No specific acknowledgment, remediation, or publication deadline is guaranteed.**

Good-faith research is welcome when lawful and performed without intentionally harming other people, systems, or networks. Test preferably against systems and Onion Services you control; avoid accessing third-party data or disrupting services.

## Release security review: outstanding checks

Before publishing v0.1.1-alpha, verify against the current code and final release artifacts:

- the actual version, Git tag, source commit, and security-support wording;
- whether the documented CLI `start` limitation remains present;
- the current DEK unlock paths, database encryption behavior, and GSAT v1 handling;
- the handling of Onion HTML page paths and other externally influenced configuration;
- logging, temporary files, backups, key permissions, and error paths;
- the precise packaged runtime dependencies and bundled native components;
- the final test results and any security-relevant known limitations.

These are **open review items**, not claims of failed tests or discovered vulnerabilities. The previously reported 1,974 passing tests are a functional test result, not a substitute for a security audit.

## No security warranty

GarlicSMTP is provided subject to the warranty and liability terms of its applicable license, PolyForm Noncommercial License 1.0.0, for the original project code. Third-party components retain their own license terms.

Nothing in this policy guarantees that GarlicSMTP is secure, anonymous, or suitable for any particular threat model.

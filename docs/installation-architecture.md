# GarlicSMTP Installation Architecture

**Status:** Design baseline  
**Project version at baseline:** 0.1.0-alpha  
**Baseline date:** 2026-09-06

## 1. Purpose

This document defines the approved architectural requirements for
GarlicSMTP installation, first-run configuration, repair, upgrade, and
release automation.

The existing GarlicSMTP application pipeline is considered functional
and protected. Installation work must not alter application behaviour
unless a concrete functional requirement is demonstrated and covered by
tests.

The installer is infrastructure around GarlicSMTP. It must not duplicate
or replace responsibilities already owned by tested application
components.

## 2. Installation principles

### P1 — Mandatory isolated virtual environment

A virgin Linux installation must:

- verify or install a compatible Python before creating the environment;
- create a dedicated virtual environment automatically;
- install Python dependencies only inside that environment.

There is no fallback to global Python installation.

The installer must not use `sudo pip`, `pip --user`, or
`--break-system-packages`.

Virtual-environment enforcement belongs to bootstrap/installation, not
to `ApplicationBuilder`, GUI startup, runtime, or the delivery pipeline.

### P2 — GarlicSMTP never runs as root

GarlicSMTP runtime processes run as a normal user.

Administrative privileges may be requested only by bootstrap operations
that genuinely require system modification.

Application state, databases, identities, private keys, credentials, and
the GarlicSMTP virtual environment must not be created as root.

### P3 — Detect before modifying

The installer detects compatible prerequisites before modifying the
system.

Existing compatible software should be reused.

The installer must not perform unnecessary upgrades, removals, system
Python modifications, or silent system changes.

### P4 — Bootstrap is idempotent

Re-running bootstrap must not destroy or regenerate a valid installation.

In particular, re-running bootstrap must not regenerate signing keys,
encryption keys, Onion identity, databases, or credentials merely
because bootstrap was executed again.

Install, update, repair, and credential reset are distinct operations.

### P5 — Installation is phased and verifiable

The conceptual installation sequence is:

    CHECK
      -> SYSTEM PREREQUISITES
      -> PYTHON
      -> CREATE VENV
      -> INSTALL DEPENDENCIES
      -> VERIFY ENVIRONMENT
      -> FIRST-RUN CONFIGURATION
      -> VERIFY GARLICSMTP
      -> COMPLETE

Installation is complete only after final verification succeeds.

Diagnostic output must not expose secrets or message content.

### P6 — Deterministic versions and dependencies

Installation must not depend on an unspecified "latest" version.

Compatible Python and dependency versions come from authoritative
project metadata.

Release facts must not be independently duplicated across installer
scripts.

### P7 — No implicit remote script execution

Installation must not use patterns such as `curl | sh`.

System packages and prerequisites must be obtained through supported
package managers or other explicitly declared and verified mechanisms.

### P8 — Installation manifest as a source of release truth

Variable installation and release facts must be represented by a
declarative, versioned installation/release description.

Installer scripts must not become independent stores of release facts.

### P9 — Detect project/installer divergence

Before release, automated or semi-automated validation must compare
project metadata with the installation manifest and fail when relevant
changes have not been classified.

Some information can be detected automatically, including Python
requirements, Python dependencies, project version, and entry points.

Other information requires explicit declaration or review, including
Linux packages, Tor requirements, ports, migrations, and new persistent
secrets.

### P10 — Installer is generated

The intended architecture has three layers:

    PROJECT
      pyproject.toml, source, configuration, tests

    RELEASE / INSTALL MANIFEST
      installation-specific declarations

    GENERATOR
      reads and validates project + manifest
      and emits installation artifacts

Generated installer artifacts are not the source of truth and must not
be maintained as independent monolithic scripts.

### P11 — Contemporaneous versioned documentation

Installation, first-run, upgrade, repair, packaging, and release
decisions are documented as they are developed.

Machine-readable version and dependency facts should not be duplicated
in prose documentation.

Stable requirement identifiers such as P1, P2, and so on are used so
tests and release validation can refer to architectural requirements.

### P12 — Upgrade is not reinstall

Upgrade must not, by default, regenerate, delete, or overwrite:

- Onion Service identity;
- Ed25519 signing keys;
- X25519 encryption keys;
- trust store;
- remote key pins;
- mailbox database;
- delivery queue;
- user configuration;
- persistent authentication credentials.

Replaceable software and persistent state are separate concerns.

## 3. Persistent state and filesystem

### P13 — Software and persistent state are separated

Replaceable application software and dependencies must be separable from
persistent user state.

Updating software must not imply replacing application state.

### P14 — Persistent state belongs to the runtime user

Persistent GarlicSMTP files are owned by the user that runs GarlicSMTP.

If bootstrap temporarily uses administrative privileges for system
prerequisites, it must return to the normal user before creating
GarlicSMTP configuration, keys, databases, credentials, or virtual
environment state.

### P15 — Restrictive secret permissions

Private keys, credentials, and other secrets use restrictive filesystem
permissions.

Unsafe permissions must result in safe failure or an explicit,
controlled correction.

They must not be silently ignored.

### P16 — ApplicationPaths.for_user() is authoritative for V1

For GarlicSMTP V1, `ApplicationPaths.for_user()` defines the persistent
filesystem layout.

Current layout:

    ~/.local/share/garlicsmtp/
    ├── config/
    │   └── settings.toml
    ├── data/
    │   └── mailboxes.db
    ├── state/
    │   ├── queue.db
    │   ├── onion-service.key
    │   └── logs/
    └── cache/

The installer must not independently reproduce or reinterpret these
paths.

Changing this layout in the future requires an explicit, versioned,
tested migration.

### P17 — No persistent writes outside declared layout

GarlicSMTP bootstrap and application components must not create
unrelated persistent files elsewhere in the repository, home directory,
or system filesystem.

System-level prerequisite configuration is treated separately from
GarlicSMTP persistent application state.

### P18 — Persistent layout changes are migrations

Future persistent path changes must be explicit and tested migrations.

Persistent data must never be silently relocated.

## 4. First-run state

### P19 — First-run is determined from real state

A completion marker may be used as supporting information but must not
be the sole authority for deciding whether first-run has completed.

Required artifacts and state must be validated.

### P20 — No default or shared secrets

There is no default GarlicSMTP password.

Passwords and other installation-specific secrets must not be embedded
in source code, installer artifacts, manifests, or documentation.

Each installation receives unique secret state.

### P21 — Cryptographic secrets are generated by their responsible components

First-run must not reimplement Onion, Ed25519, or X25519 private-key
generation in shell scripts.

Existing tested GarlicSMTP components remain responsible for their
cryptographic material and existing atomic-write, symlink, and
permission protections must remain effective.

### P22 — Creation is not regeneration

A valid existing key is reused.

A missing key may be generated only in the appropriate first-run path.

An invalid key or unsafe state must cause explicit failure or recovery;
it must not trigger silent deletion and regeneration.

### P23 — Generated configuration is minimal

First-run should persist only required or user-specific configuration
rather than copying every application default into `settings.toml`.

This allows future application defaults to evolve without unnecessary
configuration drift.

### P24 — Existing configuration is not silently overwritten

Valid existing configuration is reused.

Invalid configuration produces a diagnostic error.

Older configuration requiring structural changes uses an explicit
migration.

A parse failure must never be interpreted as permission to rewrite the
file with defaults.

### P25 — First-run is resumable

First-run is logically transactional and phase-aware.

If a later phase fails, already valid configuration, credentials,
identities, and keys are preserved.

A subsequent run resumes or repairs safely rather than destructively
starting over.

## 5. Local IMAP authentication

### P26 — Persistent local IMAP credentials

GarlicSMTP V1 has persistent local IMAP credentials established during
first-run.

There is no default password and no plaintext password persistence.

The password is chosen during first-run.

### P27 — Passwords use a dedicated password-hashing scheme

Persistent authentication must use an appropriate password-hashing
construction with algorithm information, parameters, random salt, and
derived value.

Direct SHA-256/SHA-512 password hashing and reversible password storage
are not acceptable.

The concrete algorithm remains an open implementation decision until
dependency and platform requirements are finalized.

### P28 — Credential state is separate from settings.toml

Authentication credential state is stored separately from general
application configuration.

Its final path must be represented by application path infrastructure
rather than hard-coded independently by the installer.

### P29 — Credentials are created once

Missing credentials during legitimate first-run may be created.

Valid existing credentials are reused.

Corrupt or permission-unsafe credential state causes explicit failure.

Authentication failure must never authorize automatic credential
replacement.

### P30 — Password reset is not reinstall

Password reset changes only local authentication credential state.

It must not alter Onion identity, signing or encryption keys, mailbox
data, queue data, trust/pinning state, or unrelated configuration.

### P31 — Authentication remains separate from IMAP protocol logic

The IMAP protocol continues to depend on the `Authenticator` interface.

Persistent authentication is introduced as an implementation behind
that interface, without reopening or redesigning the IMAP protocol
server.

### Approved V1 username decision

The V1 local IMAP username is:

    garlicsmtp

It is not a secret.

The Onion hostname is explicitly not used as the IMAP username.

The IMAP account identifies local access; it does not define GarlicSMTP
network identity.

## 6. Onion identity and mail identity

### P32 — Onion Service is the network-identity authority

The installer does not generate, calculate, or invent an Onion hostname.

The Onion Service established through the existing GarlicSMTP Tor
integration is authoritative.

### P33 — Canonical V1 mail address derives from the real Onion hostname

The canonical GarlicSMTP V1 sender identity is:

    garlicsmtp@<onion-hostname>

This preserves the existing application behaviour.

V1 does not introduce multiple local mail accounts or aliases as part of
installation work.

### P34 — test.onion is not an installed identity

The current `test.onion` application default must not be presented by
the installer as the user's real Onion mail identity.

A usable Onion identity exists only after the real Onion Service
hostname has been obtained.

### P35 — Onion identity is persistent

The Onion Service private identity is persistent state.

Initial creation occurs through the existing Onion Service component.

Subsequent application starts, repair operations, and upgrades reuse the
existing valid identity.

An invalid identity must not be silently deleted or regenerated.

### P36 — GUI sender remains backend-derived

The installer does not write or independently persist a GUI sender
address.

The existing Onion Service -> application ViewModel -> compose sender
flow remains authoritative.

### P37 — IMAP authentication identity and Onion identity are distinct

The local IMAP username and password authenticate local access.

They do not determine Onion identity, cryptographic keys, or the public
mail address.

### P38 — First-run verifies the real Onion identity

When Tor is enabled, successful first-run includes verification that
GarlicSMTP can establish its Onion Service and obtain a valid Onion
hostname.

This does not imply that every later upgrade operation must recreate or
republish the identity merely to manipulate replaceable software.

## 7. Tor integration

### P39 — Tor is a system prerequisite

Tor is infrastructure external to the Python virtual environment.

Bootstrap detects a compatible Tor installation before modifying the
system.

If installation is required, system privileges are limited to the
system-prerequisite phase.

### P40 — GarlicSMTP owns the Onion Service lifecycle

The installer must not configure a duplicate static Hidden Service in
`torrc`.

It prepares Tor infrastructure required by the existing
`OnionServiceManager`.

GarlicSMTP remains responsible for creating or restoring the Onion
Service through Tor Control.

### P41 — Tor Control remains local

V1 Tor Control access is local.

Installation must not expose the Tor Control endpoint on LAN or public
interfaces merely to simplify setup.

### P42 — SAFECOOKIE is mandatory

GarlicSMTP Tor Control authentication uses SAFECOOKIE.

Installation must not weaken this requirement by falling back to null
authentication, simple COOKIE authentication, or a Control password.

### P43 — Tor's advertised cookie is authoritative

The installer does not copy the Tor control cookie into GarlicSMTP
persistent state.

GarlicSMTP authenticates using the cookie belonging to the Tor instance
it contacted.

If an explicit cookie path is configured, it must match the path
advertised by Tor.

### P44 — SAFECOOKIE access without root runtime

The runtime user must have legitimate access to the Tor SAFECOOKIE.

If operating-system configuration or group membership is required, that
work occurs explicitly during the privileged bootstrap phase.

GarlicSMTP must not run as root.

The installer must not solve permission problems by making the cookie
world-readable.

### P45 — Detect Tor state before modifying it

Bootstrap distinguishes at least:

    Tor absent
      -> install prerequisite

    Tor present, compatible, correctly configured
      -> reuse without modification

    Tor present and compatible but Control/SAFECOOKIE unavailable
      -> minimal explicit configuration

    Tor present but incompatible or ambiguous
      -> diagnostic failure / explicit recovery

Existing Tor configuration must not be indiscriminately replaced.

### P46 — First-run performs end-to-end Tor verification

First-run is not complete merely because a Tor executable or service
exists.

The intended verification path is:

    Control endpoint reachable
      -> PROTOCOLINFO
      -> SAFECOOKIE available
      -> cookie readable
      -> SAFECOOKIE challenge verified
      -> authentication successful
      -> ADD_ONION successful
      -> valid .onion hostname obtained
      -> Onion identity persisted

Verification should exercise the normal GarlicSMTP integration rather
than reimplementing the Tor Control protocol in installer shell code.

## 8. Current project metadata observations

At this baseline the project declares:

    project version: 0.1.0-alpha
    Python requirement: >=3.12
    build backend: setuptools.build_meta

Runtime Python dependencies are declared in `pyproject.toml`.

The repository currently also contains `requirements.txt` with the same
runtime dependency declarations. This is a potential divergence point
and must eventually be covered by P6/P9 rather than silently maintained
as independent installer truth.

The project version is currently declared both in `pyproject.toml` and
in the Python package. This is another potential divergence point for
release validation.

The source tree contains a CLI `__main__.py` and GUI application module,
but the inspected `pyproject.toml` does not yet declare
`[project.scripts]` or `[project.gui-scripts]`.

These observations describe the current repository. They are not
authorization to refactor packaging as part of this documentation
change.

## 9. Open decisions

The following decisions are intentionally not finalized by this
baseline:

- concrete password-hashing algorithm and parameters;
- final persistent credential-store format and path;
- exact Linux distributions supported by V1 bootstrap;
- distribution-specific Tor package installation;
- distribution-specific Tor configuration file handling;
- mechanism for granting the runtime user SAFECOOKIE access;
- supported Tor version range;
- exact release/install manifest schema;
- installer generator implementation;
- generated installer artifact format;
- installed CLI/GUI entry-point declarations;
- update and migration implementation details.

Each decision must be resolved incrementally and, where applicable,
covered by focused tests before installer implementation relies on it.

## 10. Protected application boundary

The current GarlicSMTP backend, application/service layer, GUI
composition, SMTP -> Store -> IMAP path, Tor/E2EE integration, key
management, queue behaviour, and protocol implementations are considered
a protected functional pipeline.

Installer development must prefer composition around these components.

Existing application code is changed only when an installer requirement
demonstrates a real missing boundary or API, and such a change follows
the normal RED -> minimal implementation -> GREEN process.

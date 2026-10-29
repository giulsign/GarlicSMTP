# GarlicSMTP — Third-Party Software and License Review

**Target release:** v0.1.2-alpha (planned Python package version `0.1.2a0`)
**Status:** Maintainer-review draft; release-artifact compliance checks remain open
**Review updated:** 29 October 2026

Copyright © 2026 Giuliano Signorelli — GarlicSMTP Project.

## 1. Scope and licensing principle

Original GarlicSMTP code is licensed under **PolyForm Noncommercial License 1.0.0**, identified in `pyproject.toml` as `LicenseRef-PolyForm-Noncommercial-1.0.0` and documented in the project's `LICENSE`. This does **not** relicense third-party software. Each dependency retains its own license, copyright, conditions and notices. This inventory separates direct dependencies, transitive dependencies, operating-system prerequisites and development-only packages. A package listed in the development environment is not necessarily shipped.

This review describes the inspected **Python 3.12 WSL development environment**, not a completed v0.1.2 release artifact or a legal certification.

## 2. Evidence and version alignment

Evidence supplied by the maintainer: `pyproject.toml`, `requirements.txt`, `install/manifest.toml`, `pip list --format=freeze`, `dist/` filenames, installed distribution license metadata and paths, extension-module paths, `ldd` output, and the earlier inspection of the `sqlcipher3` license and SQLCipher runtime. License-file presence was confirmed; full text for every dependency was **not** independently reviewed in this update.

The current `pyproject.toml` specifies **`0.1.2a0`**, the installed GarlicSMTP distribution reports **`0.1.0a0`**, and `dist/` contains **`garlicsmtp-0.1.0a0-py3-none-any.whl`** and **`garlicsmtp-0.1.0a0.tar.gz`**. These are not v0.1.2 release artifacts. The planned `0.1.2a0` version and fresh artifacts must be verified during release consolidation.

## 3. Direct runtime dependencies

`pyproject.toml` and `requirements.txt` agree on the following declarations:

| Package | Declared requirement | Observed version | License evidence |
|---|---|---|---|
| **dnspython** | `>=2.8,<3` | `2.8.0` | **ISC**; installed `LICENSE` present |
| **cryptography** | `>=46,<47` | `46.0.7` | **Apache-2.0 OR BSD-3-Clause** (SPDX expression); `LICENSE`, `LICENSE.APACHE`, `LICENSE.BSD` present |
| **sqlcipher3** | `==0.6.3` | `0.6.3` | Installed binding `LICENSE` present; previously inspected zlib-style terms crediting Gerhard Häring (2004–2007); separate SQLCipher native-code notices apply |

The first two declarations are version ranges, not exact locks. Installed package versions may differ on a fresh installation. License texts and obligations must be checked against the exact artifacts redistributed.

### SQLCipher Community Edition and binding

Earlier runtime queries returned `PRAGMA cipher_version` = **`4.12.0 community`** and `sqlite_version()` = **`3.51.1`**. This identifies the inspected runtime, not all compiled-in components or a future build. The `sqlcipher3` Python binding license is separate from SQLCipher Community Edition's **BSD-style** licensing. For redistribution of applicable SQLCipher code, preserve its complete copyright notice, license conditions and disclaimer, together with applicable notices for incorporated third-party code. Naming the library in this document is not a substitute for those notices. Do not assume commercial/trial builds have identical terms.

References: https://pypi.org/project/sqlcipher3/0.6.3/ ; https://www.zetetic.net/sqlcipher/license/ ; https://www.zetetic.net/sqlcipher/community/

## 4. Transitive Python dependencies

| Package | Observed version | Installed metadata and file |
|---|---|---|
| **cffi** | `2.1.1` | **MIT-0** (`License-Expression`); `LICENSE` present |
| **pycparser** | `3.0` | **BSD-3-Clause** (`License-Expression`); `LICENSE` present |

These are present in the environment as dependencies of the Python runtime stack, not direct requirements in GarlicSMTP's project metadata. **MIT-0** is the observed metadata for cffi 2.1.1; it must not be replaced with a generic “MIT” attribution. Preserve the corresponding license and copyright information when applicable to redistributed artifacts.

## 5. Native extensions and limits of inspection

The following compiled modules were found in the Python 3.12 environment:

- `sqlcipher3/_sqlite3.cpython-312-x86_64-linux-gnu.so`
- `cryptography/hazmat/bindings/_rust.abi3.so`
- `_cffi_backend.cpython-312-x86_64-linux-gnu.so`

`ldd` reported no direct dynamic dependencies on `libsqlcipher.so` or `libcrypto.so` for these modules. The SQLCipher extension listed `libm` and `libc`; the cryptography extension listed `libgcc_s` and `libc`; the cffi extension listed `libpthread` and `libc` (along with the Linux loader/runtime entries). **This does not prove which libraries or cryptographic components are statically linked, vendored or otherwise incorporated.** Inspect the actual wheels, source distributions, build provenance and relevant bundled native license notices before redistributing those binaries. In particular, assess any applicable SQLCipher, SQLite, OpenSSL and Rust-component notices based on the actual artifact; do not presume their presence or absence from `ldd` alone.

## 6. Operating-system prerequisites and GUI

`install/manifest.toml` declares three Linux installation profiles: **Ubuntu 24.04**, **Kali 2026.1**, and **Debian 13**. Each lists system-installed `tor`, `python3-venv` and `python3-tk`; the GUI uses Tkinter. Tor, Python, Tcl and Tk retain their own licenses and notices. If installed separately through the operating system, these are not automatically files redistributed inside GarlicSMTP's Python wheel. If a future bundle or image includes them, its distribution obligations must be assessed separately.

References: https://www.torproject.org/ ; https://docs.python.org/3/license.html ; https://www.tcl-lang.org/software/tcltk/license.html

## 7. Development-only and unrelated environment packages

The development environment additionally contains tools such as `build`, `pytest`, `pluggy`, `iniconfig`, `packaging`, `Pygments`, `pyproject_hooks`, `PyYAML`, `PySocks`, and Qt/PySide6-related packages (`PySide6`, `PySide6_Addons`, `PySide6_Essentials`, `shiboken6`, version `6.11.1`). The maintainer reports that **PySide6 is no longer used**; it is absent from the declared application dependencies. None of these packages should be treated as redistributed application components solely because they appear in `pip list`. The build requirement `setuptools>=77` likewise does not by itself establish that setuptools is bundled with the installed application.

## 8. Preliminary compatibility assessment

No inherent conflict has been identified between GarlicSMTP's PolyForm Noncommercial 1.0.0 licensing and the **declared** permissively licensed Python dependencies, provided all applicable third-party terms are respected. This is **not** a determination that the future release artifacts are legally cleared for redistribution. A source distribution, a Python wheel and a bundled executable/image may have different contents and obligations. The installed native extensions and complete release-artifact notices still require verification.

## 9. Release compliance checklist — v0.1.2-alpha

- [x] Compare declared runtime dependencies in `pyproject.toml` and `requirements.txt`.
- [x] Record observed Python package versions and installed license metadata/file paths.
- [x] Confirm the previously inspected `sqlcipher3` binding license and SQLCipher Community Edition runtime version.
- [x] Identify native extension paths and inspect their direct dynamic linkage with `ldd`.
- [x] Update installer profile inventory to Ubuntu 24.04, Kali 2026.1 and Debian 13.
- [x] Update and verify the project/package version as `0.1.2a0`.
- [ ] Build and inspect fresh release artifacts; historical `0.1.0a0` outputs do not validate this candidate.
- [ ] Inspect exact release wheel and source archive, their file inventories, provenance, dependencies and hashes; check any future bundled image separately.
- [ ] Review complete authoritative license/copyright texts for the exact versions and any incorporated native components; determine whether SQLCipher, SQLite, OpenSSL or other notices must be included with distributed binaries.
- [ ] Supply the complete applicable third-party license texts, conditions, disclaimers and notices in the appropriate release distribution or accessible notices location; references in this review alone are insufficient.
- [ ] Confirm whether Tor, Python, Tcl/Tk, Qt/PySide6 or other system components are actually bundled; do not infer inclusion from the development environment.
- [ ] Verify final release packaging includes the project `LICENSE`, `NOTICE`, and `THIRD_PARTY_LICENSES.md`, and that all published copies are consistent.

## 10. Disclaimer

This document is a technical third-party software inventory and preliminary licensing review. It is **not** a complete software bill of materials, a replacement for the original third-party license texts, a legal opinion, or a certification of compliance. The authoritative terms are those of the relevant copyright holders. Seek qualified legal review before asserting complete redistribution compliance.

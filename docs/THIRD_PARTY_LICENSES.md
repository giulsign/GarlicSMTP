# GarlicSMTP — Third-Party Software and License Review

**Release candidate:** v0.1.1-alpha (Python package version `0.1.1a0`)
**Status:** Draft for maintainer review — not a compliance certification
**Review date:** 24 October 2026

Copyright © 2026 Giuliano Signorelli — GarlicSMTP Project.

## 1. Scope and licensing principle

Original GarlicSMTP code is offered under **PolyForm Noncommercial License 1.0.0**, as declared by `pyproject.toml` (`LicenseRef-PolyForm-Noncommercial-1.0.0`) and the project's `LICENSE` file. This license **does not relicense third-party components**. Each dependency retains its own copyright, license, conditions, and notices. A noncommercial license for GarlicSMTP does not automatically make third-party components noncommercial.

This inventory distinguishes declared application dependencies, their transitive dependencies, system prerequisites, and packages merely present in the developer's virtual environment. Presence in `pip freeze` alone is **not** evidence that a package is required or redistributed by GarlicSMTP.

## 2. Evidence and version scope

Sources reviewed: the supplied `THIRD_PARTY_LICENSES.md`; `pyproject.toml`; `requirements.txt`; `install/manifest.toml`; `pip show` / `pip freeze`; the installed `sqlcipher3` LICENSE text; and runtime SQLCipher/SQLite version queries from the Python 3.12 WSL development environment. The latter is **not** a release artifact manifest or an inventory of an Ubuntu installation.

The package declares `dnspython>=2.8,<3`, `cryptography>=46,<47`, and `sqlcipher3==0.6.3`. The observed development environment contains `dnspython==2.8.0`, `cryptography==46.0.7`, `sqlcipher3==0.6.3`, `cffi==2.1.1`, and `pycparser==3.0`. Except for `sqlcipher3`, declared version ranges do not lock exact future installation versions.

## 3. Declared runtime dependencies

| Component | Declared requirement | Observed version | License / assessment |
|---|---|---|---|
| **dnspython** | `>=2.8,<3` | 2.8.0 | **ISC** (confirmed by installed metadata). Permissive; preserve copyright and license notice when redistributing. |
| **cryptography** | `>=46,<47` | 46.0.7 | Upstream uses **Apache-2.0 OR BSD-3-Clause** licensing. Preserve the notices applicable to the exact artifact and any included native components. Installed `pip show` has an empty `License` field, which does not establish absence of a license. |
| **sqlcipher3** | `==0.6.3` | 0.6.3 | Python binding to SQLCipher. The installed distribution includes `sqlcipher3-0.6.3.dist-info/licenses/LICENSE`, containing the permissive zlib-style license with copyright © 2004–2007 Gerhard Häring. Installed package metadata has empty `License` and `License-Expression` fields, but the actual license text was inspected. SQLCipher native-code notices remain a separate obligation. |

### SQLCipher Community Edition

SQLCipher Community Edition is distributed under a **BSD-style license**, generally compatible with noncommercial application licensing. Zetetic requires the applicable **full copyright notice, license conditions and disclaimer** to be reproduced in a user-accessible place, with relevant notices for bundled components (such as SQLite and cryptographic libraries). Merely naming SQLCipher here does **not** discharge that requirement. The installed module was tested: `PRAGMA cipher_version` returned `4.12.0 community`, and `SELECT sqlite_version()` returned `3.51.1`. This confirms the SQLCipher Community Edition runtime in the observed environment, but does not inventory every native component embedded in the installation artifact. Ship the corresponding complete legal notices. Do not assume a trial or commercial build has the same rights.

References: https://pypi.org/project/sqlcipher3/0.6.3/ ; https://www.zetetic.net/sqlcipher/license/ ; https://www.zetetic.net/sqlcipher/community/

### Binding license confirmed locally

The installed `sqlcipher3==0.6.3` license file credits **Gerhard Häring (2004–2007)** and grants use, modification and redistribution, including commercially, subject to three conditions: do not misrepresent authorship; clearly mark altered source versions; and do not remove or alter the notice in source distributions. Product documentation acknowledgment is appreciated but **not required** by this binding license. This is distinct from SQLCipher Community Edition’s own BSD-style notices. The complete binding license text must be preserved where applicable.

## 4. Transitive Python runtime dependencies

`cryptography==46.0.7` declares a dependency on **cffi**, and the observed environment includes `cffi==2.1.1` and **pycparser==3.0** (a dependency of cffi). Their license texts and any bundled native notices must be collected from the actual distribution artifacts before redistribution. Common upstream licensing is MIT for cffi and BSD-3-Clause for pycparser, subject to artifact verification. These packages are **not directly declared** in GarlicSMTP's `pyproject.toml`.

## 5. System components, GUI, and Python

- **Tor:** external system prerequisite installed through the operating system (`tor`); its own license and notices apply. Confirm whether Tor is installed separately or included in any distributed image or bundle. https://www.torproject.org/
- **Tkinter / Tcl / Tk:** the current GUI uses Tkinter; the Ubuntu install manifest specifies the `python3-tk` system package. Python, Tcl and Tk have separate license notices. The obligations depend on how they are supplied or redistributed. https://docs.python.org/3/license.html ; https://www.tcl-lang.org/software/tcltk/license.html
- **Python Standard Library / interpreter:** subject to the PSF license and any other notices in the specific Python distribution; importing standard-library modules does not itself imply bundling a Python interpreter.

The installer profile in `install/manifest.toml` specifies **Ubuntu 24.04**; testing on Ubuntu 22.04 does not change that declared profile.

## 6. Development-environment packages are not automatically shipped

The supplied `pip freeze` also lists `build`, `pytest`, `pluggy`, `iniconfig`, `packaging`, `Pygments`, `pyproject_hooks`, `PyYAML`, `PySocks`, `setuptools`-related build tooling, and **PySide6 / PySide6_Addons / PySide6_Essentials / shiboken6 (6.11.1), which the maintainer confirms are no longer used by GarlicSMTP**. Their presence is **not proof** that they are application runtime dependencies or included in the release.

**Qt/PySide6 exclusion:** The maintainer confirms PySide6 is no longer used by GarlicSMTP, and it is absent from the declared runtime dependencies. It is therefore **excluded from the current application dependency inventory**. Its residual presence in the development virtual environment does not create a GarlicSMTP redistribution obligation unless Qt/PySide6 files are actually shipped.

Build-system requirement: **`setuptools>=77`** is specified by `pyproject.toml` for building the package; its presence as a build requirement does not by itself mean it is bundled with the installed application.

## 7. Compatibility assessment

**Preliminary result: no inherent license conflict identified** between GarlicSMTP's PolyForm Noncommercial 1.0.0 license and the declared runtime stack **provided** the selected components are used under their applicable permissive terms and all notices are preserved. The application may remain noncommercial-licensed without relicensing permissively licensed third-party code.

This is **conditional, not a clearance to publish binaries**. The installed `sqlcipher3` binding license and SQLCipher Community Edition runtime version have been verified. Inspection of the actual release artifacts, complete SQLCipher notices and any bundled native cryptographic libraries is still outstanding. PySide6 is not used by the project and is outside the current dependency inventory.

## 8. Release compliance checklist — v0.1.1-alpha

- [ ] Freeze the actual release environment and record exact installed package versions and artifact filenames/hashes.
- [x] Inspect the installed `sqlcipher3==0.6.3` binding license text and query the runtime SQLCipher version (`4.12.0 community`; SQLite `3.51.1`).
- [ ] Inspect the exact wheel/source artifact intended for release to determine native linkage and included libraries; preserve the binding license text.
- [ ] Include the complete SQLCipher Community Edition copyright, license conditions and disclaimer for any distributed copy, plus applicable SQLite/OpenSSL and other embedded-component notices.
- [ ] Obtain and preserve authoritative license texts and copyright notices for dnspython, cryptography, cffi, pycparser and any other redistributed components.
- [ ] Check whether the release includes Tor, Python, Tcl/Tk or other system components, rather than merely requiring separately installed packages; confirm PySide6/Qt is absent from the release artifacts.
- [ ] Verify installer, source archive, wheel and any future bundled distribution separately; account for transitive and build dependencies actually shipped.
- [ ] Make the required third-party notices available to end users in the distribution and/or an accessible application-linked location.
- [ ] Confirm that the final package includes `LICENSE`, `NOTICE` and the applicable third-party notices, and update this review to match the final artifacts.

## 9. Disclaimer

This document is an attribution and preliminary technical license review, **not** a complete software bill of materials, a substitute for upstream license texts, or a legal opinion. The authoritative terms are those supplied by each third-party copyright holder. Seek qualified legal review before asserting full distribution compliance.

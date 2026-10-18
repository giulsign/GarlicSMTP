# GarlicSMTP Third-Party Software

Copyright © 2026 Giuliano Signorelli
GarlicSMTP Project

GarlicSMTP contains or depends on software developed by third
parties.

The PolyForm Noncommercial License 1.0.0 applies to the original
GarlicSMTP software made available under that license. It does not
replace, modify, or relicense the terms applicable to third-party
components.

## Runtime dependencies

### dnspython

GarlicSMTP uses dnspython for DNS resolution functionality.

dnspython is third-party software distributed under the ISC
license.

GarlicSMTP does not claim copyright ownership of dnspython.

Official project:
https://www.dnspython.org/

Official source repository:
https://github.com/rthalley/dnspython

### cryptography

GarlicSMTP uses the Python `cryptography` package for cryptographic
primitives and key handling. Its applicable upstream license and notices
must be verified against the exact version included in a distribution.

Official project: https://cryptography.io/

### SQLCipher and Python SQLCipher bindings

GarlicSMTP uses SQLCipher-backed SQLite through the `sqlcipher3` Python
binding for encrypted persistent databases. SQLCipher and its binding are
distinct third-party components; their actual versions, linkage and
license obligations must be checked in the release environment.

SQLCipher upstream: https://www.zetetic.net/sqlcipher/

### Tkinter / Tcl / Tk

The desktop GUI uses Tkinter and the underlying Tcl/Tk components.
Licensing and redistribution obligations for the actual Python and Tcl/Tk
packages supplied with the distribution must be checked.

### Tor

GarlicSMTP uses the Tor daemon and Onion Services for transport.
Tor is an external system component with its own licensing and notices.

Official project: https://www.torproject.org/

## Python Standard Library

GarlicSMTP uses numerous modules from the Python Standard Library.
Python itself is third-party software and is subject to the Python
Software Foundation License and other notices applicable to the
particular Python distribution.

Official licensing information:
https://docs.python.org/3/license.html

## Development and Test Dependencies

Development and test tools such as pytest and their dependencies
are not licensed under the GarlicSMTP license merely because they
are used to develop or test GarlicSMTP.

Their respective upstream licenses continue to apply.

## Release compliance gate for v0.1.0-alpha.1

This document is a dependency notice, **not a completed software bill of
materials or legal compliance certification**. Before publishing binaries,
check `pyproject.toml`, requirements and lock/install manifests for all
actual runtime, installer and bundled dependencies; record their exact
versions, authoritative license identifiers, bundled license texts and
any attribution or source-availability requirements. Historical PySide6
references do not by themselves establish that it is part of the current
Tkinter runtime distribution.

## Other Components

Additional dependencies introduced in future versions of
GarlicSMTP must be reviewed for license compatibility before being
added to the project's runtime or distribution dependencies.

Third-party copyright notices and license texts required by an
applicable license must be preserved when GarlicSMTP is
distributed.

This document is informational and does not replace the
authoritative license terms supplied by third-party projects.

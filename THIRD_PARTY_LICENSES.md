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

### Qt for Python / PySide6

GarlicSMTP uses Qt for Python (PySide6) for its graphical user
interface.

Modules currently used by GarlicSMTP include:

- PySide6.QtCore
- PySide6.QtWidgets

Qt for Python and the Qt libraries are third-party software and
remain subject to their respective licensing terms.

Qt for Python is available under licensing terms including the
GNU Lesser General Public License version 3 (LGPLv3), the GNU
General Public License version 3 (GPLv3), and commercial licensing,
depending on the component and distribution.

GarlicSMTP does not claim copyright ownership of Qt, PySide6,
Shiboken, or related Qt components.

Official licensing information:
https://doc.qt.io/qtforpython-6/licenses.html

Before distributing packaged GarlicSMTP binaries, the applicable
Qt/PySide6 license obligations must be reviewed and satisfied,
including preservation and distribution of required license
notices and applicable license texts.

### dnspython

GarlicSMTP uses dnspython for DNS resolution functionality.

dnspython is third-party software distributed under the ISC
license.

GarlicSMTP does not claim copyright ownership of dnspython.

Official project:
https://www.dnspython.org/

Official source repository:
https://github.com/rthalley/dnspython

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

## Other Components

Additional dependencies introduced in future versions of
GarlicSMTP must be reviewed for license compatibility before being
added to the project's runtime or distribution dependencies.

Third-party copyright notices and license texts required by an
applicable license must be preserved when GarlicSMTP is
distributed.

This document is informational and does not replace the
authoritative license terms supplied by third-party projects.

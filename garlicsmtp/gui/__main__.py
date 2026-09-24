# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.configuration import (
    ApplicationPaths,
)
from garlicsmtp.gui.application import (
    run_gui,
)


if __name__ == "__main__":
    raise SystemExit(
        run_gui(
            paths=ApplicationPaths.for_development(),
        )
    )

# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import sys

from garlicsmtp.configuration import (
    ApplicationPaths,
    ConfigurationLoader,
)
from garlicsmtp.first_run import (
    run_first_run,
)
from garlicsmtp.tor.onion_service_factory import (
    build_onion_service_manager,
)


def main(
    *,
    stdin=None,
    paths_factory=ApplicationPaths.for_user,
    configuration_loader=None,
    onion_service_factory=build_onion_service_manager,
    first_run=run_first_run,
) -> int:
    if stdin is None:
        stdin = sys.stdin

    if configuration_loader is None:
        configuration_loader = ConfigurationLoader()

    paths = paths_factory()

    settings = configuration_loader.load(
        paths.settings_file
    )

    onion_service = onion_service_factory(
        paths=paths,
        settings=settings,
    )

    password = stdin.readline().rstrip("\n")

    if password == "":
        password = None

    first_run(
        paths=paths,
        password=password,
        onion_service=onion_service,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

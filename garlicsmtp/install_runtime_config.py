# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

from garlicsmtp.configuration import ApplicationPaths
from garlicsmtp.runtime_config import (
    create_runtime_configuration,
    detect_tor_runtime_configuration,
)
from garlicsmtp.configuration import (
    ApplicationPaths,
    ConfigurationLoader,
)
from garlicsmtp.runtime_config import (
    create_runtime_configuration,
    detect_tor_runtime_configuration,
    validate_runtime_configuration,
)


def main(
    *,
    paths_factory=ApplicationPaths.for_user,
    configuration_loader=None,
    validate_runtime_config=validate_runtime_configuration,
    detect_tor_runtime=detect_tor_runtime_configuration,
    create_runtime_config=create_runtime_configuration,
) -> int:
    paths = paths_factory()

    if paths.settings_file.exists():
        if configuration_loader is None:
            configuration_loader = ConfigurationLoader()

        settings = configuration_loader.load(
            paths.settings_file,
        )

        validate_runtime_config(
            settings,
        )

        return 0

    tor_configuration = detect_tor_runtime(
        control_host="127.0.0.1",
        control_port=9051,
    )

    create_runtime_config(
        settings_file=paths.settings_file,
        tor_configuration=tor_configuration,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
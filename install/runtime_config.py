# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

from pathlib import Path


def create_runtime_configuration(
    *,
    settings_file: Path,
    tor_configuration: dict,
) -> None:
    settings_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cookie_file = tor_configuration["cookie_file"]

    content = (
        "[tor]\n"
        "control_enabled = true\n"
        f'control_host = "{tor_configuration["control_host"]}"\n'
        f'control_port = {tor_configuration["control_port"]}\n'
        f'cookie_file = "{cookie_file}"\n'
    )

    with settings_file.open(
        "x",
        encoding="utf-8",
    ) as file:
        file.write(content)


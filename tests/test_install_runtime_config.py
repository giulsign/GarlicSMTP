# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

from pathlib import Path
import tomllib

import pytest

from install.runtime_config import (
    create_runtime_configuration,
)


def test_create_runtime_configuration_writes_minimal_tor_settings(
    tmp_path,
):
    settings_file = tmp_path / "config" / "default.toml"

    create_runtime_configuration(
        settings_file=settings_file,
        tor_configuration={
            "control_host": "127.0.0.1",
            "control_port": 9051,
            "cookie_file": Path(
                "/run/tor/control.authcookie"
            ),
        },
    )

    data = tomllib.loads(
        settings_file.read_text(encoding="utf-8")
    )

    assert data == {
        "tor": {
            "control_enabled": True,
            "control_host": "127.0.0.1",
            "control_port": 9051,
            "cookie_file": (
                "/run/tor/control.authcookie"
            ),
        }
    }


def test_create_runtime_configuration_creates_parent_directory(
    tmp_path,
):
    settings_file = (
        tmp_path
        / "missing"
        / "config"
        / "default.toml"
    )

    create_runtime_configuration(
        settings_file=settings_file,
        tor_configuration={
            "control_host": "127.0.0.1",
            "control_port": 9051,
            "cookie_file": Path(
                "/run/tor/control.authcookie"
            ),
        },
    )

    assert settings_file.exists()


def test_create_runtime_configuration_does_not_overwrite_existing_file(
    tmp_path,
):
    settings_file = tmp_path / "config" / "default.toml"
    settings_file.parent.mkdir(parents=True)

    settings_file.write_text(
        "[tor]\nenabled = false\n",
        encoding="utf-8",
    )

    with pytest.raises(FileExistsError):
        create_runtime_configuration(
            settings_file=settings_file,
            tor_configuration={
                "control_host": "127.0.0.1",
                "control_port": 9051,
                "cookie_file": Path(
                    "/run/tor/control.authcookie"
                ),
            },
        )

    assert settings_file.read_text(
        encoding="utf-8"
    ) == "[tor]\nenabled = false\n"


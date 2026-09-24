# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

from garlicsmtp.configuration import ApplicationPaths
from garlicsmtp.install_runtime_config import main


def test_main_detects_tor_and_creates_runtime_configuration(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    tor_configuration = {
        "control_host": "127.0.0.1",
        "control_port": 9051,
        "cookie_file": "/run/tor/control.authcookie",
    }

    calls = []

    def detect_tor_runtime(
        *,
        control_host,
        control_port,
    ):
        calls.append(
            (
                "detect",
                control_host,
                control_port,
            )
        )
        return tor_configuration

    def create_runtime_config(
        *,
        settings_file,
        tor_configuration,
    ):
        calls.append(
            (
                "create",
                settings_file,
                tor_configuration,
            )
        )

    result = main(
        paths_factory=lambda: paths,
        detect_tor_runtime=detect_tor_runtime,
        create_runtime_config=create_runtime_config,
    )

    assert result == 0

    assert calls == [
        (
            "detect",
            "127.0.0.1",
            9051,
        ),
        (
            "create",
            paths.settings_file,
            tor_configuration,
        ),
    ]


def test_main_validates_existing_runtime_configuration(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    paths.settings_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.settings_file.write_text(
        "[tor]\ncontrol_enabled = true\n",
        encoding="utf-8",
    )

    settings = object()
    calls = []

    class ConfigurationLoader:
        def load(
            self,
            path,
        ):
            calls.append(
                (
                    "load",
                    path,
                )
            )
            return settings

    def validate_runtime_config(
        loaded_settings,
    ):
        calls.append(
            (
                "validate",
                loaded_settings,
            )
        )

    def detect_tor_runtime(**kwargs):
        raise AssertionError(
            "existing runtime configuration must not trigger Tor detection"
        )

    def create_runtime_config(**kwargs):
        raise AssertionError(
            "existing runtime configuration must not be rewritten"
        )

    result = main(
        paths_factory=lambda: paths,
        configuration_loader=ConfigurationLoader(),
        validate_runtime_config=validate_runtime_config,
        detect_tor_runtime=detect_tor_runtime,
        create_runtime_config=create_runtime_config,
    )

    assert result == 0
    assert calls == [
        (
            "load",
            paths.settings_file,
        ),
        (
            "validate",
            settings,
        ),
    ]
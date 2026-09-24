# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import io

from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
)
from garlicsmtp.install_first_run import (
    main,
)


def test_main_runs_first_run_from_installed_application_state(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    settings = ApplicationSettings()
    onion_service = object()

    calls = []

    def paths_factory():
        calls.append("paths")
        return paths

    class FakeConfigurationLoader:
        def load(
            self,
            settings_file,
        ):
            calls.append(
                (
                    "load",
                    settings_file,
                )
            )
            return settings

    def onion_service_factory(
        *,
        paths,
        settings,
    ):
        calls.append(
            (
                "onion",
                paths,
                settings,
            )
        )
        return onion_service

    def first_run(
        *,
        paths,
        password,
        onion_service,
    ):
        calls.append(
            (
                "first-run",
                paths,
                password,
                onion_service,
            )
        )

    result = main(
        stdin=io.StringIO(
            "secret-password\n"
        ),
        paths_factory=paths_factory,
        configuration_loader=(
            FakeConfigurationLoader()
        ),
        onion_service_factory=(
            onion_service_factory
        ),
        first_run=first_run,
    )

    assert result == 0

    assert calls == [
        "paths",
        (
            "load",
            paths.settings_file,
        ),
        (
            "onion",
            paths,
            settings,
        ),
        (
            "first-run",
            paths,
            "secret-password",
            onion_service,
        ),
    ]


def test_main_passes_none_password_when_stdin_is_empty(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    settings = ApplicationSettings()
    onion_service = object()

    calls = []

    def first_run(
        *,
        paths,
        password,
        onion_service,
    ):
        calls.append(
            (
                paths,
                password,
                onion_service,
            )
        )

    result = main(
        stdin=io.StringIO(""),
        paths_factory=lambda: paths,
        configuration_loader=type(
            "Loader",
            (),
            {
                "load": lambda self, path: settings,
            },
        )(),
        onion_service_factory=lambda **kwargs: onion_service,
        first_run=first_run,
    )

    assert result == 0

    assert calls == [
        (
            paths,
            None,
            onion_service,
        )
    ]
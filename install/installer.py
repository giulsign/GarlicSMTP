# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from pathlib import Path

from install.environment import (
    build_environment_actions,
    execute_environment_actions,
)
from install.platform import detect_platform_profile
from install.system import execute_machine_system_installation
from install.first_run import run_first_run


def execute_installation(
    *,
    manifest: dict,
    project_metadata: dict,
    os_release: str,
    venv_dir: Path,
    project_root: Path,
    command_exists,
    python_version,
    python_venv_available,
    system_run,
    environment_run,
    application_context=None,
    password: str | None = None,
    first_run=run_first_run,
) -> None:
    execute_machine_system_installation(
        manifest,
        project_metadata,
        os_release,
        command_exists=command_exists,
        python_version=python_version,
        python_venv_available=python_venv_available,
        run=system_run,
    )

    profile = detect_platform_profile(
        os_release,
        manifest["platform"]["profiles"],
    )

    actions = build_environment_actions(
        profile=profile,
        venv_dir=venv_dir,
        project_root=project_root,
    )

    execute_environment_actions(
        actions,
        run=environment_run,
    )

    if application_context is not None:
        if password is None:
            raise ValueError(
                "IMAP password is required for first-run"
            )

        first_run(
            paths=application_context.paths,
            password=password,
            onion_service=application_context.onion_service,
        )
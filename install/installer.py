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
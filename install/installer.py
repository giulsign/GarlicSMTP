# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from pathlib import Path
import getpass

from install.environment import (
    build_environment_actions,
    execute_environment_actions,
)
from install.platform import detect_platform_profile
from install.system import execute_machine_system_installation
from garlicsmtp.first_run import run_first_run
from install.runtime_config import create_runtime_configuration
from install.tor_runtime import detect_tor_runtime_configuration


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
    runtime_user: str | None = None,
    torrc_path: Path | None = None,
    tor_configuration_compatible=None,
    runtime_user_resolver=getpass.getuser,
    system_installation=execute_machine_system_installation,
    application_context=None,
    password: str | None = None,
    detect_tor_runtime=detect_tor_runtime_configuration,
    create_runtime_config=create_runtime_configuration,
    first_run=run_first_run,
) -> None:

    profile = detect_platform_profile(
        os_release,
        manifest["platform"]["profiles"],
    )

    if runtime_user is None:
        runtime_user = runtime_user_resolver()

    if torrc_path is None:
        torrc_path = Path(
            profile["system_prerequisites"]["tor"]["torrc_path"]
        )

    system_installation(
        manifest,
        project_metadata,
        os_release,
        command_exists=command_exists,
        python_version=python_version,
        python_venv_available=python_venv_available,
        run=system_run,
        runtime_user=runtime_user,
        torrc_path=torrc_path,
        tor_configuration_compatible=(
            tor_configuration_compatible
        ),
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
        credentials_file = getattr(
            application_context.paths,
            "imap_credentials_file",
            None,
        )

        if (
            password is None
            and (
                credentials_file is None
                or not credentials_file.exists()
            )
        ):
            raise ValueError(
                "IMAP password is required for first-run"
            )

        settings_file = application_context.paths.settings_file

        if not settings_file.exists():
            tor_control = (
                profile["system_prerequisites"]["tor"]["control"]
            )

            tor_configuration = detect_tor_runtime(
                control_host=tor_control["host"],
                control_port=tor_control["port"],
            )

            create_runtime_config(
                settings_file=settings_file,
                tor_configuration=tor_configuration,
            )

        first_run(
            paths=application_context.paths,
            password=password,
            onion_service=application_context.onion_service,
        )
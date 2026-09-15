# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from pathlib import Path
import getpass
import subprocess

from garlicsmtp.configuration import ApplicationPaths
from install.prerequisites import (
        command_exists_on_path,
        probe_python_version,
        probe_python_venv_available,
    )
from install.environment import (
    build_environment_actions,
    execute_environment_actions,
)
from install.platform import (
    detect_platform_profile,
    read_os_release,
)
from install.system import execute_machine_system_installation
from install.system import (
    build_refreshed_user_action,
    execute_system_action,
)
from install.validator import (
    load_install_manifest,
    load_project_metadata,
)


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
    application_paths=None,
    password: str | None = None,
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

    if application_paths is not None:
        credentials_file = getattr(
            application_paths,
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

        settings_file = application_paths.settings_file

        
        runtime_config_action = build_refreshed_user_action(
                runtime_user=runtime_user,
                command=[
                    str(venv_dir / "bin" / "python"),
                    "-m",
                    "garlicsmtp.install_runtime_config",
                ],
            )

        execute_system_action(
                runtime_config_action,
                run=system_run,
            )

        first_run_action = build_refreshed_user_action(
            runtime_user=runtime_user,
            command=[
                str(venv_dir / "bin" / "python"),
                "-m",
                "garlicsmtp.install_first_run",
            ],
            input=(
                f"{password}\n"
                if password is not None
                else ""
            ),
        )

        execute_system_action(
            first_run_action,
            run=system_run,
        )


def run_installation(
    *,
    project_root: Path,
    venv_dir: Path,
    load_manifest=load_install_manifest,
    load_metadata=load_project_metadata,
    read_platform=read_os_release,
    installation=execute_installation,
    command_exists=command_exists_on_path,
    python_version=probe_python_version,
    python_venv_available=probe_python_venv_available,
    system_run=subprocess.run,
    environment_run=subprocess.run,
    paths_factory=ApplicationPaths.for_user,
    password: str | None = None,
) -> None:
    installation(
        manifest=load_manifest(
            project_root / "install" / "manifest.toml"
        ),
        project_metadata=load_metadata(
            project_root / "pyproject.toml"
        ),
        os_release=read_platform(),
        project_root=project_root,
        venv_dir=venv_dir,
        command_exists=command_exists,
        python_version=python_version,
        python_venv_available=python_venv_available,
        system_run=system_run,
        environment_run=environment_run,
        application_paths=paths_factory(),
        password=password,
    )


def main(
    *,
    project_root: Path | None = None,
    paths_factory=ApplicationPaths.for_user,
    installation=run_installation,
    password_reader=getpass.getpass,
) -> None:
    if project_root is None:
        project_root = (
            Path(__file__).resolve().parents[1]
        )

    paths = paths_factory()
    password = password_reader(
        "IMAP password: "
    )

    installation(
        project_root=project_root,
        venv_dir=paths.root_dir / "venv",
        paths_factory=paths_factory,
        password=password,
    )


if __name__ == "__main__":
    main()  
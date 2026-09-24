# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


import subprocess
from install.platform import detect_platform_profile
from install.prerequisites import (
    build_detected_installation_plan,
    detect_tor_configuration_state,
    shared_library_exists,
)
from pathlib import Path

from install.tor_config import (
    build_tor_configuration_plan,
    execute_tor_configuration_plan,
)   

def build_package_install_action(
    profile: dict,
    plan: dict,
) -> dict | None:
    if not plan["packages"]:
        return None

    package_manager = profile["package_manager"]

    if package_manager != "apt-get":
        raise ValueError(
            f"unsupported package manager: {package_manager}"
        )

    system_prerequisites = profile.get("system_prerequisites")

    if system_prerequisites is None:
        raise ValueError(
            "profile system_prerequisites is required"
        )

    declared_packages = {
        prerequisite["package"]
        for prerequisite in system_prerequisites.values()
    }

    for package in plan["packages"]:
        if package not in declared_packages:
            raise ValueError(
                f"package not declared by profile: {package}"
            )

    return {
        "command": [
            package_manager,
            "install",
            "-y",
            *plan["packages"],
        ],
        "requires_privileges": True,
    }


def execute_system_action(
    action: dict,
    run,
    elevate=None,
) -> None:
    command = action["command"]

    if action["requires_privileges"]:
        if elevate is None:
            raise ValueError(
                "privileged system action requires explicit elevation"
            )

        command = elevate(command)

    run_kwargs = {
        "check": True,
    }

    if "input" in action:
        run_kwargs["input"] = action["input"]
        run_kwargs["text"] = True

    run(
        command,
        **run_kwargs,
    )


def build_privilege_elevator(
    privilege_elevation: str,
):
    if privilege_elevation == "sudo":
        def elevate(command):
            return ["sudo", *command]

        return elevate

    raise ValueError(
        "unsupported privilege elevation: "
        f"{privilege_elevation}"
    )


def build_refreshed_user_action(
    *,
    runtime_user: str,
    command: list[str],
    input: str | None = None,
) -> dict:
    action = {
        "command": [
            "sudo",
            "-u",
            runtime_user,
            "--",
            *command,
        ],
        "requires_privileges": False,
    }

    if input is not None:
        action["input"] = input

    return action


def build_profile_privilege_elevator(
    profile: dict,
):
    return build_privilege_elevator(
        profile["privilege_elevation"]
    )


def execute_profile_system_action(
    profile: dict,
    action: dict,
    run=None,
) -> None:
    if run is None:
        run = subprocess.run

    elevate = build_profile_privilege_elevator(profile)

    execute_system_action(
        action,
        run=run,
        elevate=elevate,
    )


def build_machine_system_install_action(
    manifest: dict,
    project_metadata: dict,
    os_release: str,
    command_exists,
    python_version,
    python_venv_available,
) -> dict | None:
    profile = detect_platform_profile(
        os_release,
        manifest["platform"]["profiles"],
    )

    plan = build_detected_installation_plan(
        profile,
        project_metadata,
        command_exists=command_exists,
        python_version=python_version,
        python_venv_available=python_venv_available,
    )

    return build_package_install_action(
        profile,
        plan,
    )


def configure_profile_tor(
    *,
    profile: dict,
    runtime_user: str,
    torrc_path: Path,
    run,
    build_plan=build_tor_configuration_plan,
    execute_plan=execute_tor_configuration_plan,
    execute_action=execute_profile_system_action,
) -> None:
    tor_control = (
        profile["system_prerequisites"]["tor"]["control"]
    )

    plan = build_plan(
        tor_state="configuration_required",
        torrc_path=torrc_path,
        runtime_user=runtime_user,
        control_host=tor_control["host"],
        control_port=tor_control["port"],
    )

    execute_plan(
        plan,
        profile=profile,
        run=run,
        execute_action=execute_action,
    )


def execute_machine_system_installation(
    manifest: dict,
    project_metadata: dict,
    os_release: str,
    command_exists,
    python_version,
    python_venv_available,
    python_module_available,
    run,
    shared_library_available=shared_library_exists,
    tor_configuration_compatible=None,
    tor_configuration_state=None,
    runtime_user: str | None = None,
    torrc_path: Path | None = None,
    configure_tor=configure_profile_tor,
) -> None:
    profile = detect_platform_profile(
        os_release,
        manifest["platform"]["profiles"],
    )

    plan = build_detected_installation_plan(
        profile,
        project_metadata,
        command_exists=command_exists,
        python_version=python_version,
        python_venv_available=python_venv_available,
        python_module_available=python_module_available,
        shared_library_available=shared_library_available,
        tor_configuration_compatible=(
            tor_configuration_compatible
        ),
        tor_configuration_state=(
            tor_configuration_state
        ),
    )

    action = build_package_install_action(
        profile,
        plan,
    )

    if action is not None:
        execute_profile_system_action(
            profile,
            action,
            run=run,
        )

    if tor_configuration_compatible is None:
        return

    tor = profile["system_prerequisites"]["tor"]

    tor_was_installed = (
        tor["package"] in plan["packages"]
    )

    if tor_was_installed:
        tor_state = detect_tor_configuration_state(
            tor_present=lambda: command_exists(
                tor["command"]
            ),
            configuration_compatible=(
                tor_configuration_compatible
            ),
            configuration_state=(
                tor_configuration_state
            ),
        )

        tor_configuration_required = (
            tor_state == "configuration_required"
        )
    else:
        tor_configuration_required = plan.get(
            "tor_configuration_required",
            False,
        )

    if not tor_configuration_required:
        return

    if runtime_user is None:
        raise ValueError(
            "runtime_user is required for Tor configuration"
        )

    if torrc_path is None:
        raise ValueError(
            "torrc_path is required for Tor configuration"
        )

    if configure_tor is None:
        raise ValueError(
            "configure_tor is required for Tor configuration"
        )

    configure_tor(
        profile=profile,
        runtime_user=runtime_user,
        torrc_path=torrc_path,
        run=run,
    )
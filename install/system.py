# Copyright (c) Giuliano Signorelli
#
# See LICENSE for the full license terms.

import subprocess
from install.platform import detect_platform_profile
from install.prerequisites import build_detected_installation_plan

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

    run(
        command,
        check=True,
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


def execute_machine_system_installation(
    manifest: dict,
    project_metadata: dict,
    os_release: str,
    command_exists,
    python_version,
    python_venv_available,
    run,
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
    )

    action = build_package_install_action(
        profile,
        plan,
    )

    if action is None:
        return

    execute_profile_system_action(
        profile,
        action,
        run=run,
    )
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import shutil
import subprocess
from install.platform import detect_platform_profile

def check_prerequisite(
    prerequisite: dict,
    command_exists,
) -> dict:
    satisfied = command_exists(prerequisite["command"])

    return {
        "satisfied": satisfied,
        "installation_required": not satisfied,
    }


def build_installation_plan(
    prerequisites: dict,
    command_exists,
    python_venv_available=None,
    python_version=None,
    python_requirement=None,
) -> dict:
    if (
        python_version is not None
        and python_requirement is not None
        and not is_python_version_compatible(
            python_version,
            python_requirement,
        )
    ):
        raise ValueError(
            "Python version does not satisfy project requirement"
        )

    packages = []

    for name, prerequisite in prerequisites.items():
        if name == "python_venv":
            if python_venv_available is None:
                raise ValueError(
                    "python_venv_available detector is required"
                )

            installation_required = not python_venv_available()
        else:
            result = check_prerequisite(
                prerequisite,
                command_exists=command_exists,
            )
            installation_required = result["installation_required"]

        if installation_required:
            packages.append(prerequisite["package"])

    return {
        "packages": packages,
    }


def is_python_version_compatible(
    version: tuple[int, ...],
    requirement: str,
) -> bool:
    if not requirement.startswith(">="):
        raise ValueError(
            f"unsupported Python version requirement: {requirement}"
        )

    required_version = tuple(
        int(part)
        for part in requirement[2:].split(".")
    )

    return version >= required_version


def is_python_venv_available(
    module_available,
) -> bool:
    return module_available("venv")


def command_exists_on_path(
    command: str,
    which=shutil.which,
) -> bool:
    return which(command) is not None


def detect_python_version(
    executable: str,
    run_version_check,
) -> tuple[int, ...]:
    return run_version_check(executable)


def probe_python_version(
    executable: str,
    run=subprocess.run,
) -> tuple[int, ...]:
    result = run(
        [
            executable,
            "-c",
            (
                "import sys; "
                "print('.'.join(str(part) "
                "for part in sys.version_info[:3]))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    return tuple(
        int(part)
        for part in result.stdout.strip().split(".")
    )


def probe_python_venv_available(
    executable: str,
    run=subprocess.run,
) -> bool:
    result = run(
        [
            executable,
            "-c",
            "import venv",
        ],
        capture_output=True,
        text=True,
    )

    return result.returncode == 0


def build_detected_installation_plan(
    profile: dict,
    project_metadata: dict,
    command_exists=command_exists_on_path,
    python_version=probe_python_version,
    python_venv_available=probe_python_venv_available,
) -> dict:
    executable = profile["python"]["executable"]

    detected_python_version = python_version(executable)
    detected_python_venv_available = python_venv_available(
        executable
    )

    return build_installation_plan(
        profile["system_prerequisites"],
        command_exists=command_exists,
        python_venv_available=(
            lambda: detected_python_venv_available
        ),
        python_version=detected_python_version,
        python_requirement=project_metadata["requires-python"],
    )


def build_machine_installation_plan(
    manifest: dict,
    project_metadata: dict,
    os_release: str,
    command_exists=command_exists_on_path,
    python_version=probe_python_version,
    python_venv_available=probe_python_venv_available,
) -> dict:
    profile = detect_platform_profile(
        os_release,
        manifest["platform"]["profiles"],
    )

    return build_detected_installation_plan(
        profile,
        project_metadata,
        command_exists=command_exists,
        python_version=python_version,
        python_venv_available=python_venv_available,
    )
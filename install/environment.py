# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from pathlib import Path


def build_create_venv_action(
    profile: dict,
    venv_dir: Path,
) -> dict:
    return {
        "command": [
            profile["python"]["executable"],
            "-m",
            "venv",
            str(venv_dir),
        ],
        "requires_privileges": False,
    }

def execute_environment_action(
    action: dict,
    run,
) -> None:
    run(
        action["command"],
        check=True,
    )


def build_install_project_action(
    *,
    venv_dir: Path,
    project_root: Path,
) -> dict:
    return {
        "command": [
            str(venv_dir / "bin" / "python"),
            "-m",
            "pip",
            "install",
            str(project_root),
        ],
        "requires_privileges": False,
    }


def build_verify_environment_action(
    *,
    venv_dir: Path,
) -> dict:
    return {
        "command": [
            str(venv_dir / "bin" / "python"),
            "-c",
            "import garlicsmtp",
        ],
        "requires_privileges": False,
    }


def build_environment_actions(
    *,
    profile: dict,
    venv_dir: Path,
    project_root: Path,
) -> list[dict]:
    return [
        build_create_venv_action(
            profile,
            venv_dir,
        ),
        build_install_project_action(
            venv_dir=venv_dir,
            project_root=project_root,
        ),
        build_verify_environment_action(
            venv_dir=venv_dir,
        ),
    ]


def execute_environment_actions(
    actions: list[dict],
    *,
    run,
) -> None:
    for action in actions:
        execute_environment_action(
            action,
            run=run,
        )
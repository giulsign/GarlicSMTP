# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from pathlib import Path

from install.environment import build_create_venv_action


def test_build_create_venv_action_uses_profile_python():
    profile = {
        "python": {
            "executable": "/usr/bin/python3",
        },
    }

    venv_dir = Path("/home/alice/.local/share/garlicsmtp/venv")

    action = build_create_venv_action(
        profile,
        venv_dir,
    )

    assert action == {
        "command": [
            "/usr/bin/python3",
            "-m",
            "venv",
            str(venv_dir),
        ],
        "requires_privileges": False,
    }


def test_execute_environment_action_runs_without_privilege_elevation():
    calls = []

    def run(command, check):
        calls.append(
            {
                "command": command,
                "check": check,
            }
        )

    action = {
        "command": [
            "/usr/bin/python3",
            "-m",
            "venv",
            "/home/alice/.local/share/garlicsmtp/venv",
        ],
        "requires_privileges": False,
    }

    from install.environment import execute_environment_action

    execute_environment_action(
        action,
        run=run,
    )

    assert calls == [
        {
            "command": action["command"],
            "check": True,
        }
    ]


def test_build_install_project_action_uses_venv_python():
    from install.environment import build_install_project_action

    venv_dir = Path(
        "/home/alice/.local/share/garlicsmtp/venv"
    )
    project_root = Path(
        "/home/alice/src/garlicsmtp"
    )

    action = build_install_project_action(
        venv_dir=venv_dir,
        project_root=project_root,
    )

    assert action == {
        "command": [
            str(venv_dir / "bin" / "python"),
            "-m",
            "pip",
            "install",
            str(project_root),
        ],
        "requires_privileges": False,
    }


def test_build_verify_environment_action_uses_venv_python():
    from install.environment import build_verify_environment_action

    venv_dir = Path(
        "/home/alice/.local/share/garlicsmtp/venv"
    )

    action = build_verify_environment_action(
        venv_dir=venv_dir,
    )

    assert action == {
        "command": [
            str(venv_dir / "bin" / "python"),
            "-c",
            "import garlicsmtp",
        ],
        "requires_privileges": False,
    }


def test_build_environment_actions_orders_create_install_and_verify():
    from install.environment import build_environment_actions

    profile = {
        "python": {
            "executable": "/usr/bin/python3",
        },
    }

    venv_dir = Path(
        "/home/alice/.local/share/garlicsmtp/venv"
    )
    project_root = Path(
        "/home/alice/src/garlicsmtp"
    )

    actions = build_environment_actions(
        profile=profile,
        venv_dir=venv_dir,
        project_root=project_root,
    )

    assert actions == [
        {
            "command": [
                "/usr/bin/python3",
                "-m",
                "venv",
                str(venv_dir),
            ],
            "requires_privileges": False,
        },
        {
            "command": [
                str(venv_dir / "bin" / "python"),
                "-m",
                "pip",
                "install",
                str(project_root),
            ],
            "requires_privileges": False,
        },
        {
            "command": [
                str(venv_dir / "bin" / "python"),
                "-c",
                "import garlicsmtp",
            ],
            "requires_privileges": False,
        },
    ]


def test_execute_environment_actions_preserves_order():
    from install.environment import execute_environment_actions

    calls = []

    def run(command, check):
        calls.append(command)

    actions = [
        {
            "command": ["create"],
            "requires_privileges": False,
        },
        {
            "command": ["install"],
            "requires_privileges": False,
        },
        {
            "command": ["verify"],
            "requires_privileges": False,
        },
    ]

    execute_environment_actions(
        actions,
        run=run,
    )

    assert calls == [
        ["create"],
        ["install"],
        ["verify"],
    ]
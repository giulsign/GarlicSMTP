# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from pathlib import Path

from install.environment import (
    build_create_venv_action,
    execute_environment_action,
    build_install_project_action,
    build_verify_environment_action,
    build_environment_actions,
    execute_environment_actions,
)


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
            (
                "import garlicsmtp; "
                "import garlicsmtp.cli.__main__; "
                "import garlicsmtp.gui.application; "
                "import garlicsmtp.install_runtime_config; "
                "import garlicsmtp.install_first_run"
            ),
        ],
        "requires_privileges": False,
    }


def test_build_environment_actions_orders_create_install_and_verify():

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
                (
                    "import garlicsmtp; "
                    "import garlicsmtp.cli.__main__; "
                    "import garlicsmtp.gui.application; "
                    "import garlicsmtp.install_runtime_config; "
                    "import garlicsmtp.install_first_run"
                ),
            ],
            "requires_privileges": False,
        }
    ]


def test_execute_environment_actions_preserves_order():

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


def test_execute_environment_actions_stops_after_verification_failure():

    calls = []

    def run(command, check):
        calls.append(command)

        if command == ["verify"]:
            raise RuntimeError("environment verification failed")

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
        {
            "command": ["after-verify"],
            "requires_privileges": False,
        },
    ]

    try:
        execute_environment_actions(
            actions,
            run=run,
        )
    except RuntimeError as exc:
        assert str(exc) == "environment verification failed"
    else:
        raise AssertionError(
            "expected environment verification failure"
        )

    assert calls == [
        ["create"],
        ["install"],
        ["verify"],
    ]
# Copyright (c) Giuliano Signorelli
#
# See LICENSE for the full license terms.

import pytest

from install.system import (
    build_package_install_action,
    build_privilege_elevator,
    build_profile_privilege_elevator,
    execute_system_action,
    execute_profile_system_action,
    build_machine_system_install_action,
)


def test_build_package_install_action_uses_profile_package_manager_and_plan():
    profile = {
        "package_manager": "apt-get",
        "system_prerequisites": {
            "tor": {
                "required": True,
                "command": "tor",
                "package": "tor",
            },
            "python_venv": {
                "required": True,
                "command": "python3",
                "package": "python3-venv",
            },
        },
    }
    plan = {
        "packages": [
            "tor",
            "python3-venv",
        ],
    }

    action = build_package_install_action(
        profile,
        plan,
    )

    assert action == {
        "command": [
            "apt-get",
            "install",
            "-y",
            "tor",
            "python3-venv",
        ],
        "requires_privileges": True,
    }


def test_build_package_install_action_returns_none_when_no_packages_required():
    profile = {
        "package_manager": "apt-get",
    }
    plan = {
        "packages": [],
    }

    action = build_package_install_action(
        profile,
        plan,
    )

    assert action is None


def test_build_package_install_action_rejects_unsupported_package_manager():
    profile = {
        "package_manager": "unknown-manager",
    }
    plan = {
        "packages": [
            "tor",
        ],
    }

    with pytest.raises(
        ValueError,
        match="unsupported package manager: unknown-manager",
    ):
        build_package_install_action(
            profile,
            plan,
        )


def test_build_package_install_action_rejects_package_not_declared_by_profile():
    profile = {
        "package_manager": "apt-get",
        "system_prerequisites": {
            "tor": {
                "required": True,
                "command": "tor",
                "package": "tor",
            },
            "python_venv": {
                "required": True,
                "command": "python3",
                "package": "python3-venv",
            },
        },
    }
    plan = {
        "packages": [
            "unexpected-package",
        ],
    }

    with pytest.raises(
        ValueError,
        match="package not declared by profile: unexpected-package",
    ):
        build_package_install_action(
            profile,
            plan,
        )


def test_build_package_install_action_rejects_missing_system_prerequisites():
    profile = {
        "package_manager": "apt-get",
    }
    plan = {
        "packages": [
            "tor",
        ],
    }

    with pytest.raises(
        ValueError,
        match="profile system_prerequisites is required",
    ):
        build_package_install_action(
            profile,
            plan,
        )


def test_execute_system_action_invokes_runner_with_command_and_check():
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))

    def elevate(command):
        return ["elevate", *command]

    action = {
        "command": [
            "apt-get",
            "install",
            "-y",
            "tor",
        ],
        "requires_privileges": True,
    }

    execute_system_action(
        action,
        run=run,
        elevate=elevate,
    )

    assert calls == [
        (
            [
                "elevate",
                "apt-get",
                "install",
                "-y",
                "tor",
            ],
            {
                "check": True,
            },
        ),
    ]


def test_execute_system_action_propagates_runner_failure():
    def run(command, **kwargs):
        raise RuntimeError("system command failed")

    action = {
        "command": [
            "apt-get",
            "install",
            "-y",
            "tor",
        ],
        "requires_privileges": True,
    }

    with pytest.raises(
        RuntimeError,
        match="system command failed",
    ):
        execute_system_action(
            action,
            run=run,
            elevate=lambda command: command,
        )


def test_execute_system_action_rejects_privileged_action_without_elevation():
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))

    action = {
        "command": [
            "apt-get",
            "install",
            "-y",
            "tor",
        ],
        "requires_privileges": True,
    }

    with pytest.raises(
        ValueError,
        match="privileged system action requires explicit elevation",
    ):
        execute_system_action(
            action,
            run=run,
        )

    assert calls == []


def test_execute_system_action_runs_unprivileged_action_without_elevation():
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))

    action = {
        "command": [
            "example-command",
            "--check",
        ],
        "requires_privileges": False,
    }

    execute_system_action(
        action,
        run=run,
    )

    assert calls == [
        (
            [
                "example-command",
                "--check",
            ],
            {
                "check": True,
            },
        ),
    ]


def test_build_privilege_elevator_builds_sudo_command():
    elevate = build_privilege_elevator("sudo")

    command = elevate([
        "apt-get",
        "install",
        "-y",
        "tor",
    ])

    assert command == [
        "sudo",
        "apt-get",
        "install",
        "-y",
        "tor",
    ]


def test_build_privilege_elevator_rejects_unsupported_strategy():
    with pytest.raises(
        ValueError,
        match="unsupported privilege elevation: unknown",
    ):
        build_privilege_elevator("unknown")


def test_build_profile_privilege_elevator_uses_profile_policy():
    profile = {
        "privilege_elevation": "sudo",
    }

    elevate = build_profile_privilege_elevator(profile)

    command = elevate([
        "apt-get",
        "install",
        "-y",
        "tor",
    ])

    assert command == [
        "sudo",
        "apt-get",
        "install",
        "-y",
        "tor",
    ]


def test_build_profile_privilege_elevator_requires_profile_policy():
    profile = {}

    with pytest.raises(KeyError):
        build_profile_privilege_elevator(profile)


def test_execute_profile_system_action_uses_profile_elevation_and_runner():
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))

    profile = {
        "privilege_elevation": "sudo",
    }

    action = {
        "command": [
            "apt-get",
            "install",
            "-y",
            "tor",
        ],
        "requires_privileges": True,
    }

    execute_profile_system_action(
        profile,
        action,
        run=run,
    )

    assert calls == [
        (
            [
                "sudo",
                "apt-get",
                "install",
                "-y",
                "tor",
            ],
            {
                "check": True,
            },
        ),
    ]


def test_execute_profile_system_action_uses_subprocess_run_by_default(
    monkeypatch,
):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))

    monkeypatch.setattr(
        "install.system.subprocess.run",
        run,
    )

    profile = {
        "privilege_elevation": "sudo",
    }

    action = {
        "command": [
            "true",
        ],
        "requires_privileges": False,
    }

    execute_profile_system_action(
        profile,
        action,
    )

    assert calls == [
        (
            [
                "true",
            ],
            {
                "check": True,
            },
        ),
    ]


def test_build_machine_system_install_action_connects_profile_plan_and_action():
    manifest = {
        "platform": {
            "profiles": [
                {
                    "id": "ubuntu",
                    "version_id": "24.04",
                    "package_manager": "apt-get",
                    "privilege_elevation": "sudo",
                    "python": {
                        "executable": "/usr/bin/python3",
                    },
                    "system_prerequisites": {
                        "tor": {
                            "required": True,
                            "command": "tor",
                            "package": "tor",
                        },
                        "python_venv": {
                            "required": True,
                            "command": "python3",
                            "package": "python3-venv",
                        },
                    },
                },
            ],
        },
    }

    project_metadata = {
        "requires-python": ">=3.12",
    }

    action = build_machine_system_install_action(
        manifest,
        project_metadata,
        (
            'ID=ubuntu\n'
            'VERSION_ID="24.04"\n'
        ),
        command_exists=lambda command: command != "tor",
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
    )

    assert action == {
        "command": [
            "apt-get",
            "install",
            "-y",
            "tor",
        ],
        "requires_privileges": True,
    }


def test_build_machine_system_install_action_returns_none_when_satisfied():
    manifest = {
        "platform": {
            "profiles": [
                {
                    "id": "ubuntu",
                    "version_id": "24.04",
                    "package_manager": "apt-get",
                    "privilege_elevation": "sudo",
                    "python": {
                        "executable": "/usr/bin/python3",
                    },
                    "system_prerequisites": {
                        "tor": {
                            "required": True,
                            "command": "tor",
                            "package": "tor",
                        },
                        "python_venv": {
                            "required": True,
                            "command": "python3",
                            "package": "python3-venv",
                        },
                    },
                },
            ],
        },
    }

    project_metadata = {
        "requires-python": ">=3.12",
    }

    action = build_machine_system_install_action(
        manifest,
        project_metadata,
        (
            'ID=ubuntu\n'
            'VERSION_ID="24.04"\n'
        ),
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
    )

    assert action is None
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

from pathlib import Path

from install.installer import execute_installation


def _manifest():
    return {
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


def _project_metadata():
    return {
        "requires-python": ">=3.12",
    }


def test_execute_installation_runs_system_before_environment():
    calls = []

    def run(command, **kwargs):
        calls.append(command)

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=Path("/home/alice/.local/share/garlicsmtp/venv"),
        project_root=Path("/home/alice/src/garlicsmtp"),
        command_exists=lambda command: command != "tor",
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=run,
        environment_run=run,
    )

    assert calls == [
        [
            "sudo",
            "apt-get",
            "install",
            "-y",
            "tor",
        ],
        [
            "/usr/bin/python3",
            "-m",
            "venv",
            "/home/alice/.local/share/garlicsmtp/venv",
        ],
        [
            "/home/alice/.local/share/garlicsmtp/venv/bin/python",
            "-m",
            "pip",
            "install",
            "/home/alice/src/garlicsmtp",
        ],
        [
            "/home/alice/.local/share/garlicsmtp/venv/bin/python",
            "-c",
            "import garlicsmtp",
        ],
    ]


def test_execute_installation_runs_environment_when_system_is_satisfied():
    calls = []

    def system_run(command, **kwargs):
        calls.append(("system", command))

    def environment_run(command, **kwargs):
        calls.append(("environment", command))

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=Path("/home/alice/.local/share/garlicsmtp/venv"),
        project_root=Path("/home/alice/src/garlicsmtp"),
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=system_run,
        environment_run=environment_run,
    )

    assert [kind for kind, command in calls] == [
        "environment",
        "environment",
        "environment",
    ]


def test_execute_installation_stops_before_environment_when_system_fails():
    environment_calls = []

    def system_run(command, **kwargs):
        raise RuntimeError("system installation failed")

    def environment_run(command, **kwargs):
        environment_calls.append(command)

    try:
        execute_installation(
            manifest=_manifest(),
            project_metadata=_project_metadata(),
            os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
            venv_dir=Path("/home/alice/.local/share/garlicsmtp/venv"),
            project_root=Path("/home/alice/src/garlicsmtp"),
            command_exists=lambda command: command != "tor",
            python_version=lambda executable: (3, 12, 3),
            python_venv_available=lambda executable: True,
            system_run=system_run,
            environment_run=environment_run,
        )
    except RuntimeError as exc:
        assert str(exc) == "system installation failed"
    else:
        raise AssertionError("expected system installation failure")

    assert environment_calls == []

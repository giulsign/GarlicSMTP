# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import pytest
from pathlib import Path

from install.installer import execute_installation
from garlicsmtp.configuration import ApplicationPaths


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
                            "torrc_path": "/etc/tor/torrc",
                            "control": {
                                "host": "127.0.0.1",
                                "port": 9051,
                                "authentication": "safecookie",
                                "cookie_path_source": "protocolinfo",
                                "cookie_access": {
                                    "runtime_user_rootless": True,
                                },
                            },
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
            (
                "import garlicsmtp; "
                "import garlicsmtp.cli.__main__; "
                "import garlicsmtp.gui.application; "
                "import garlicsmtp.install_runtime_config; "
                "import garlicsmtp.install_first_run"
            )
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


def test_execute_installation_runs_first_run_after_environment(
    tmp_path,
):
    calls = []

    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    paths.settings_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.settings_file.write_text(
        "[tor]\n",
        encoding="utf-8",
    )

    class Context:
        onion_service = object()

    context = Context()
    context.paths = paths

    def environment_run(command, **kwargs):
        calls.append(
            (
                "environment",
                command,
                kwargs,
            )
        )

    def system_run(command, **kwargs):
        calls.append(
            (
                "system",
                command,
                kwargs,
            )
        )

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=system_run,
        environment_run=environment_run,
        runtime_user="alice",
        system_installation=lambda *args, **kwargs: None,
        application_context=context,
        password="secret-password",
    )

    assert calls[-1][0] == "system"
    assert calls[-1][1] == [
        "sudo",
        "-u",
        "alice",
        "--",
        str(tmp_path / "venv" / "bin" / "python"),
        "-m",
        "garlicsmtp.install_first_run",
    ]


def test_execute_installation_passes_password_to_first_run_stdin(
    tmp_path,
):
    calls = []

    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    paths.settings_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.settings_file.write_text(
        "[tor]\n",
        encoding="utf-8",
    )

    class Context:
        onion_service = object()

    context = Context()
    context.paths = paths

    def system_run(command, **kwargs):
        calls.append(
            (
                command,
                kwargs,
            )
        )

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=system_run,
        environment_run=lambda command, **kwargs: None,
        runtime_user="alice",
        system_installation=lambda *args, **kwargs: None,
        application_context=context,
        password="secret-password",
    )

    assert calls == [
        (
            [
                "sudo",
                "-u",
                "alice",
                "--",
                str(tmp_path / "venv" / "bin" / "python"),
                "-m",
                "garlicsmtp.install_runtime_config",
            ],
            {
                "check": True,
            },
        ),
        (
            [
                "sudo",
                "-u",
                "alice",
                "--",
                str(tmp_path / "venv" / "bin" / "python"),
                "-m",
                "garlicsmtp.install_first_run",
            ],
            {
                "check": True,
                "input": "secret-password\n",
                "text": True,
            },
        ),
    ]


def test_execute_installation_does_not_run_first_run_when_environment_fails(
    tmp_path,
):

    class Context:
        paths = object()
        onion_service = object()

    def environment_run(command, **kwargs):
        raise RuntimeError(
            "environment installation failed"
        )

    with pytest.raises(
        RuntimeError,
        match="environment installation failed",
    ):
        execute_installation(
            manifest=_manifest(),
            project_metadata=_project_metadata(),
            os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
            venv_dir=tmp_path / "venv",
            project_root=tmp_path / "project",
            command_exists=lambda command: True,
            python_version=lambda executable: (3, 12, 3),
            python_venv_available=lambda executable: True,
            system_run=lambda command, **kwargs: None,
            environment_run=environment_run,
            application_context=Context(),
            password="secret-password",
        )


def test_execute_installation_requires_password_for_first_run(
    tmp_path,
):
    class Context:
        paths = object()
        onion_service = object()

    with pytest.raises(
        ValueError,
        match="IMAP password is required for first-run",
    ):
        execute_installation(
            manifest=_manifest(),
            project_metadata=_project_metadata(),
            os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
            venv_dir=tmp_path / "venv",
            project_root=tmp_path / "project",
            command_exists=lambda command: True,
            python_version=lambda executable: (3, 12, 3),
            python_venv_available=lambda executable: True,
            system_run=lambda command, **kwargs: None,
            environment_run=lambda command, **kwargs: None,
            application_context=Context(),
        )


def test_execute_installation_passes_tor_provisioning_inputs_to_system(
    tmp_path,
):
    received = {}

    def system_installation(*args, **kwargs):
        received.update(kwargs)

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=lambda command, **kwargs: None,
        environment_run=lambda command, **kwargs: None,
        runtime_user="alice",
        torrc_path=Path("/etc/tor/torrc"),
        tor_configuration_compatible=lambda: True,
        system_installation=system_installation,
    )

    assert received["runtime_user"] == "alice"
    assert received["torrc_path"] == Path("/etc/tor/torrc")
    assert received["tor_configuration_compatible"] is not None


def test_execute_installation_completes_system_provisioning_before_environment(
    tmp_path,
):
    calls = []

    def system_installation(*args, **kwargs):
        calls.append("system")

    def environment_run(command, **kwargs):
        calls.append("environment")

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=lambda command, **kwargs: None,
        environment_run=environment_run,
        runtime_user="alice",
        torrc_path=Path("/etc/tor/torrc"),
        tor_configuration_compatible=lambda: True,
        system_installation=system_installation,
    )

    assert calls == [
        "system",
        "environment",
        "environment",
        "environment",
    ]


def test_execute_installation_derives_runtime_user_for_system_provisioning(
    tmp_path,
):
    received = {}

    def system_installation(*args, **kwargs):
        received.update(kwargs)

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=lambda command, **kwargs: None,
        environment_run=lambda command, **kwargs: None,
        tor_configuration_compatible=lambda: True,
        runtime_user_resolver=lambda: "alice",
        system_installation=system_installation,
    )

    assert received["runtime_user"] == "alice"


def test_execute_installation_derives_torrc_path_from_profile(
    tmp_path,
):
    received = {}

    def system_installation(*args, **kwargs):
        received.update(kwargs)

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=lambda command, **kwargs: None,
        environment_run=lambda command, **kwargs: None,
        tor_configuration_compatible=lambda: True,
        runtime_user_resolver=lambda: "alice",
        system_installation=system_installation,
    )

    assert received["torrc_path"] == Path(
        "/etc/tor/torrc"
    )


def test_execute_installation_creates_runtime_configuration_before_first_run(
    tmp_path,
):
    calls = []

    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    class ApplicationContext:
        onion_service = object()

    context = ApplicationContext()
    context.paths = paths

    def system_run(command, **kwargs):
        calls.append(
            (
                command,
                kwargs,
            )
        )

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=system_run,
        environment_run=lambda command, **kwargs: None,
        runtime_user="alice",
        system_installation=lambda *args, **kwargs: None,
        application_context=context,
        password="secret",
    )

    assert calls == [
        (
            [
                "sudo",
                "-u",
                "alice",
                "--",
                str(tmp_path / "venv" / "bin" / "python"),
                "-m",
                "garlicsmtp.install_runtime_config",
            ],
            {
                "check": True,
            },
        ),
        (
            [
                "sudo",
                "-u",
                "alice",
                "--",
                str(tmp_path / "venv" / "bin" / "python"),
                "-m",
                "garlicsmtp.install_first_run",
            ],
            {
                "check": True,
                "input": "secret\n",
                "text": True,
            },
        ),
    ]


def test_execute_installation_reuses_existing_runtime_configuration(
    tmp_path,
):
    calls = []

    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    paths.settings_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.settings_file.write_text(
        "[tor]\n"
        "control_enabled = true\n",
        encoding="utf-8",
    )

    class ApplicationContext:
        onion_service = object()

    context = ApplicationContext()
    context.paths = paths

    def system_run(command, **kwargs):
        calls.append(
            (
                command,
                kwargs,
            )
        )

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=system_run,
        environment_run=lambda command, **kwargs: None,
        runtime_user="alice",
        system_installation=lambda *args, **kwargs: None,
        application_context=context,
        password="secret",
    )

    assert calls == [
        (
            [
                "sudo",
                "-u",
                "alice",
                "--",
                str(tmp_path / "venv" / "bin" / "python"),
                "-m",
                "garlicsmtp.install_runtime_config",
            ],
            {
                "check": True,
            },
        ),
        (
            [
                "sudo",
                "-u",
                "alice",
                "--",
                str(tmp_path / "venv" / "bin" / "python"),
                "-m",
                "garlicsmtp.install_first_run",
            ],
            {
                "check": True,
                "input": "secret\n",
                "text": True,
            },
        ),
    ]


def test_execute_installation_resumes_existing_first_run_without_password(
    tmp_path,
):
    calls = []

    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    paths.settings_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.settings_file.write_text(
        "[tor]\n"
        "control_enabled = true\n",
        encoding="utf-8",
    )

    paths.imap_credentials_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.imap_credentials_file.write_text(
        "existing-credentials",
        encoding="utf-8",
    )

    class ApplicationContext:
        onion_service = object()

    context = ApplicationContext()
    context.paths = paths

    def system_run(command, **kwargs):
        calls.append(
            (
                command,
                kwargs,
            )
        )

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=system_run,
        environment_run=lambda command, **kwargs: None,
        runtime_user="alice",
        system_installation=lambda *args, **kwargs: None,
        application_context=context,
        password=None,
    )

    assert calls == [
        (
            [
                "sudo",
                "-u",
                "alice",
                "--",
                str(tmp_path / "venv" / "bin" / "python"),
                "-m",
                "garlicsmtp.install_runtime_config",
            ],
            {
                "check": True,
            },
        ),
        (
            [
                "sudo",
                "-u",
                "alice",
                "--",
                str(tmp_path / "venv" / "bin" / "python"),
                "-m",
                "garlicsmtp.install_first_run",
            ],
            {
                "check": True,
                "input": "",
                "text": True,
            },
        ),
    ]


def test_execute_installation_runs_first_run_in_refreshed_user_process(
    tmp_path,
):
    calls = []

    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    paths.settings_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.settings_file.write_text(
        "[tor]\n",
        encoding="utf-8",
    )

    class ApplicationContext:
        onion_service = object()

    context = ApplicationContext()
    context.paths = paths

    def system_run(command, **kwargs):
        calls.append(
            (
                command,
                kwargs,
            )
        )

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=system_run,
        environment_run=lambda command, **kwargs: None,
        runtime_user="alice",
        system_installation=lambda *args, **kwargs: None,
        application_context=context,
        password="secret-password",
    )

    assert calls == [
        (
            [
                "sudo",
                "-u",
                "alice",
                "--",
                str(
                    tmp_path
                    / "venv"
                    / "bin"
                    / "python"
                ),
                "-m",
                "garlicsmtp.install_runtime_config",
            ],
            {
                "check": True,
            },
        ),
        (
            [
                "sudo",
                "-u",
                "alice",
                "--",
                str(
                    tmp_path
                    / "venv"
                    / "bin"
                    / "python"
                ),
                "-m",
                "garlicsmtp.install_first_run",
            ],
            {
                "check": True,
                "input": "secret-password\n",
                "text": True,
            },
        ),
    ]


def test_execute_installation_runs_runtime_config_in_refreshed_user_process(
    tmp_path,
):
    calls = []

    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    class ApplicationContext:
        onion_service = object()

    context = ApplicationContext()
    context.paths = paths

    def system_run(command, **kwargs):
        calls.append(
            (
                command,
                kwargs,
            )
        )

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=system_run,
        environment_run=lambda command, **kwargs: None,
        runtime_user="alice",
        system_installation=lambda *args, **kwargs: None,
        application_context=context,
        password="secret-password",
    )

    assert calls[0] == (
        [
            "sudo",
            "-u",
            "alice",
            "--",
            str(tmp_path / "venv" / "bin" / "python"),
            "-m",
            "garlicsmtp.install_runtime_config",
        ],
        {
            "check": True,
        },
    ) 


def test_execute_installation_does_not_run_first_run_when_runtime_config_fails(
    tmp_path,
):
    calls = []

    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    paths.settings_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.settings_file.write_text(
        "[tor]\n",
        encoding="utf-8",
    )

    class ApplicationContext:
        onion_service = object()

    context = ApplicationContext()
    context.paths = paths

    def system_run(command, **kwargs):
        calls.append(
            (
                command,
                kwargs,
            )
        )

        if command[-1] == "garlicsmtp.install_runtime_config":
            raise RuntimeError(
                "runtime configuration invalid"
            )

    with pytest.raises(
        RuntimeError,
        match="runtime configuration invalid",
    ):
        execute_installation(
            manifest=_manifest(),
            project_metadata=_project_metadata(),
            os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
            venv_dir=tmp_path / "venv",
            project_root=tmp_path / "project",
            command_exists=lambda command: True,
            python_version=lambda executable: (3, 12, 3),
            python_venv_available=lambda executable: True,
            system_run=system_run,
            environment_run=lambda command, **kwargs: None,
            runtime_user="alice",
            system_installation=lambda *args, **kwargs: None,
            application_context=context,
            password="secret-password",
        )

    assert len(calls) == 1
    assert calls[0][0][-1] == (
        "garlicsmtp.install_runtime_config"
    )
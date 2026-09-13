# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import pytest
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
                "import garlicsmtp.gui.application"
            ),
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

    class Paths:
        settings_file = tmp_path / "settings.toml"

    class Context:
        paths = Paths()
        onion_service = object()    

    context = Context()

    def run(command, **kwargs):
        calls.append(("environment", command))

    def first_run(*, paths, password, onion_service):
        calls.append(
            (
                "first-run",
                paths,
                password,
                onion_service,
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
        system_run=run,
        environment_run=run,
        application_context=context,
        password="secret-password",
        first_run=first_run,
        detect_tor_runtime=lambda **kwargs: {
            "control_host": "127.0.0.1",
            "control_port": 9051,
            "cookie_file": "/run/tor/control.authcookie",
        },
        create_runtime_config=lambda **kwargs: None,
        )

    assert calls[-1] == (
        "first-run",
        context.paths,
        "secret-password",
        context.onion_service,
    )


def test_execute_installation_passes_context_state_to_first_run(
    tmp_path,
):
    received = {}

    class Paths:
        settings_file = tmp_path / "settings.toml"

    class Context:
        paths = Paths()
        onion_service = object()

    context = Context()

    def first_run(*, paths, password, onion_service):
        received["paths"] = paths
        received["password"] = password
        received["onion_service"] = onion_service

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
        application_context=context,
        password="secret-password",
        first_run=first_run,
        detect_tor_runtime=lambda **kwargs: {
            "control_host": "127.0.0.1",
            "control_port": 9051,
            "cookie_file": "/run/tor/control.authcookie",
        },
        create_runtime_config=lambda **kwargs: None,
    )

    assert received == {
        "paths": context.paths,
        "password": "secret-password",
        "onion_service": context.onion_service,
    }


def test_execute_installation_does_not_run_first_run_when_environment_fails(
    tmp_path,
):
    first_run_calls = []

    class Context:
        paths = object()
        onion_service = object()

    def environment_run(command, **kwargs):
        raise RuntimeError(
            "environment installation failed"
        )

    def first_run(**kwargs):
        first_run_calls.append(kwargs)

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
            first_run=first_run,
        )

    assert first_run_calls == []


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

    class Paths:
        settings_file = tmp_path / "settings.toml"

    class ApplicationContext:
        paths = Paths()
        onion_service = object()

    detected_tor_configuration = {
        "control_host": "127.0.0.1",
        "control_port": 9051,
        "cookie_file": "/run/tor/control.authcookie",
    }

    def detect_tor_runtime_configuration(**kwargs):
        calls.append(("detect_tor_runtime", kwargs))
        return detected_tor_configuration

    def create_runtime_configuration(**kwargs):
        calls.append(("create_runtime_config", kwargs))

    def first_run(**kwargs):
        calls.append(("first_run", kwargs))

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
        application_context=ApplicationContext(),
        password="secret",
        detect_tor_runtime=detect_tor_runtime_configuration,
        create_runtime_config=create_runtime_configuration,
        first_run=first_run,
    )

    assert calls[0] == (
        "detect_tor_runtime",
        {
            "control_host": "127.0.0.1",
            "control_port": 9051,
        },
    )

    assert calls[1] == (
        "create_runtime_config",
        {
            "settings_file": tmp_path / "settings.toml",
            "tor_configuration": detected_tor_configuration,
        },
    )

    assert calls[2][0] == "first_run"


def test_execute_installation_reuses_existing_runtime_configuration(
    tmp_path,
):
    calls = []

    settings_file = tmp_path / "settings.toml"
    settings_file.write_text(
        "[tor]\n"
        "control_enabled = true\n",
        encoding="utf-8",
    )

    class Paths:
        pass

    Paths.settings_file = settings_file

    class ApplicationContext:
        paths = Paths()
        onion_service = object()

    def detect_tor_runtime(**kwargs):
        calls.append("detect")

    def create_runtime_config(**kwargs):
        calls.append("create")

    def first_run(**kwargs):
        calls.append("first-run")

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
        application_context=ApplicationContext(),
        password="secret",
        detect_tor_runtime=detect_tor_runtime,
        create_runtime_config=create_runtime_config,
        first_run=first_run,
    )

    assert calls == ["first-run"]


def test_execute_installation_resumes_existing_first_run_without_password(
    tmp_path,
):
    settings_file = tmp_path / "settings.toml"
    settings_file.write_text(
        "[tor]\ncontrol_enabled = true\n",
        encoding="utf-8",
    )

    credentials_file = tmp_path / "imap-credentials.json"
    credentials_file.write_text(
        "existing-credentials",
        encoding="utf-8",
    )

    class Paths:
        pass

    Paths.settings_file = settings_file
    Paths.imap_credentials_file = credentials_file

    class ApplicationContext:
        paths = Paths()
        onion_service = object()

    received = {}

    def first_run(**kwargs):
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
        application_context=ApplicationContext(),
        password=None,
        first_run=first_run,
    )

    assert received["password"] is None
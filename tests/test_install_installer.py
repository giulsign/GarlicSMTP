# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import pytest
from pathlib import Path
import subprocess

from install.prerequisites import (
        command_exists_on_path,
        probe_python_version,
        probe_python_venv_available,
        shared_library_exists, 
    )
from install.installer import (
    execute_installation,
    run_installation,
    main,
)
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
        tor_configuration_compatible=lambda: True,
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
        application_paths=paths,
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
        application_paths=paths,
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

    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

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
            application_paths=paths,
            password="secret-password",
        )


def test_execute_installation_requires_password_for_first_run(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

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
            application_paths=paths,
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
        application_paths=paths,
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
        application_paths=paths,
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
        application_paths=paths,
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
        application_paths=paths,
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
        application_paths=paths,
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
            application_paths=paths,
            password="secret-password",
        )

    assert len(calls) == 1
    assert calls[0][0][-1] == (
        "garlicsmtp.install_runtime_config"
    )


def test_run_installation_loads_repository_and_machine_inputs(
    tmp_path,
):
    from install.installer import run_installation

    received = {}

    def installation(**kwargs):
        received.update(kwargs)

    run_installation(
        project_root=tmp_path / "project",
        venv_dir=tmp_path / "venv",
        load_manifest=lambda path: {"manifest": str(path)},
        load_metadata=lambda path: {"metadata": str(path)},
        read_platform=lambda: 'ID=ubuntu\nVERSION_ID="24.04"\n',
        installation=installation,
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        system_run=lambda command, **kwargs: None,
        environment_run=lambda command, **kwargs: None,
    )

    assert received["manifest"] == {
        "manifest": str(
            tmp_path / "project" / "install" / "manifest.toml"
        ),
    }
    assert received["project_metadata"] == {
        "metadata": str(
            tmp_path / "project" / "pyproject.toml"
        ),
    }
    assert received["os_release"] == (
        'ID=ubuntu\nVERSION_ID="24.04"\n'
    )
    assert received["project_root"] == tmp_path / "project"
    assert received["venv_dir"] == tmp_path / "venv"


def test_run_installation_uses_production_adapters_by_default(
    tmp_path,
):
    received = {}

    def installation(**kwargs):
        received.update(kwargs)

    run_installation(
        project_root=tmp_path / "project",
        venv_dir=tmp_path / "venv",
        load_manifest=lambda path: {},
        load_metadata=lambda path: {},
        read_platform=lambda: "",
        installation=installation,
    )

    assert received["command_exists"] is command_exists_on_path
    assert received["python_version"] is probe_python_version
    assert (
        received["python_venv_available"]
        is probe_python_venv_available
    )
    assert received["system_run"] is subprocess.run
    assert received["environment_run"] is subprocess.run


def test_run_installation_passes_user_paths_and_password(
    tmp_path,
):
    received = {}

    def installation(**kwargs):
        received.update(kwargs)

    paths = ApplicationPaths.for_user(
        home=tmp_path / "home",
    )

    run_installation(
        project_root=tmp_path / "project",
        venv_dir=tmp_path / "venv",
        load_manifest=lambda path: {},
        load_metadata=lambda path: {},
        read_platform=lambda: "",
        installation=installation,
        paths_factory=lambda: paths,
        password="secret-password",
    )

    assert received["application_paths"] is paths
    assert received["password"] == "secret-password"


def test_execute_installation_accepts_application_paths(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path / "home",
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
        system_run=lambda command, **kwargs: None,
        environment_run=lambda command, **kwargs: None,
        runtime_user="alice",
        system_installation=lambda *args, **kwargs: None,
        application_paths=paths,
        password="secret-password",
    )


def test_main_runs_installation_with_user_venv(
    tmp_path,
):
    calls = []

    paths = ApplicationPaths.for_user(
        home=tmp_path / "home",
    )

    def paths_factory():
        return paths

    def installation(**kwargs):
        calls.append(kwargs)

    main(
        project_root=tmp_path / "project",
        paths_factory=paths_factory,
        installation=installation,
        password_reader=lambda prompt: "secret-password",
    )

    assert calls == [
        {
            "project_root": tmp_path / "project",
            "venv_dir": paths.root_dir / "venv",
            "paths_factory": paths_factory,
            "password": "secret-password",
        }
    ]


def test_main_discovers_project_root(
    tmp_path,
):
    calls = []

    paths = ApplicationPaths.for_user(
        home=tmp_path / "home",
    )

    def paths_factory():
        return paths

    def installation(**kwargs):
        calls.append(kwargs)

    main(
        paths_factory=paths_factory,
        installation=installation,
        password_reader=lambda prompt: "secret-password",
    )

    assert calls[0]["project_root"] == (
        Path(__file__).resolve().parents[1]
    )


def test_installer_module_has_main_guard():
    source = (
        Path(__file__).resolve().parents[1]
        / "install"
        / "installer.py"
    ).read_text(encoding="utf-8")

    assert 'if __name__ == "__main__":' in source
    assert "    main()" in source


def test_execute_installation_builds_default_tor_configuration_probe(
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
        torrc_path=tmp_path / "torrc",
        system_installation=system_installation,
    )

    torrc_path = tmp_path / "torrc"
    torrc_path.write_text(
        "ControlPort 127.0.0.1:9051\n",
        encoding="utf-8",
    )

    assert received["tor_configuration_compatible"]() is True


def test_execute_installation_passes_shared_library_detector_to_system(
    tmp_path,
):
    received = {}

    def system_installation(*args, **kwargs):
        received.update(kwargs)

    shared_library_available = lambda library: True

    execute_installation(
        manifest=_manifest(),
        project_metadata=_project_metadata(),
        os_release='ID=ubuntu\nVERSION_ID="24.04"\n',
        venv_dir=tmp_path / "venv",
        project_root=tmp_path / "project",
        command_exists=lambda command: True,
        python_version=lambda executable: (3, 12, 3),
        python_venv_available=lambda executable: True,
        shared_library_available=shared_library_available,
        system_run=lambda command, **kwargs: None,
        environment_run=lambda command, **kwargs: None,
        runtime_user="alice",
        tor_configuration_compatible=lambda: True,
        system_installation=system_installation,
    )

    assert (
        received["shared_library_available"]
        is shared_library_available
    )


def test_run_installation_uses_production_shared_library_adapter_by_default(
    tmp_path,
):
    received = {}

    def installation(**kwargs):
        received.update(kwargs)

    run_installation(
        project_root=tmp_path / "project",
        venv_dir=tmp_path / "venv",
        load_manifest=lambda path: {},
        load_metadata=lambda path: {},
        read_platform=lambda: "",
        installation=installation,
    )

    assert (
        received["shared_library_available"]
        is shared_library_exists
    )
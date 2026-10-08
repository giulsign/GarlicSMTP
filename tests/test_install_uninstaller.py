# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import pytest
from pathlib import Path

from garlicsmtp.configuration import ApplicationPaths
from install.uninstaller import (
    uninstall_application,
    uninstall_user_data,
    uninstall_user_desktop_launcher,
    uninstall_tor_configuration,
    execute_uninstallation,
    run_uninstallation,
    run_application_uninstallation,
    main,
    cli,
)


def test_uninstall_user_data_removes_entire_garlicsmtp_root(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    paths.create_directories()

    (
        paths.root_dir
        / "venv"
    ).mkdir()

    paths.mailbox_database.write_bytes(
        b"received"
    )
    paths.sent_mailbox_database.write_bytes(
        b"sent"
    )
    paths.queue_database.write_bytes(
        b"queue"
    )

    uninstall_user_data(
        paths=paths,
    )

    assert not paths.root_dir.exists()



def test_uninstall_user_data_does_not_hide_removal_failure(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )
    paths.create_directories()

    def fail_removal(path):
        raise PermissionError(
            "removal denied"
        )

    monkeypatch.setattr(
        "install.uninstaller.shutil.rmtree",
        fail_removal,
    )

    with pytest.raises(
        PermissionError,
        match="removal denied",
    ):
        uninstall_user_data(
            paths=paths,
        )


def test_uninstall_user_data_succeeds_when_garlicsmtp_root_is_absent(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    assert not paths.root_dir.exists()

    uninstall_user_data(
        paths=paths,
    )

    assert not paths.root_dir.exists()


def test_uninstall_user_desktop_launcher_removes_garlicsmtp_launcher(
    tmp_path,
):
    user_home = tmp_path / "alice"
    desktop_dir = user_home / "Desktop"
    desktop_dir.mkdir(parents=True)

    launcher_path = (
        desktop_dir
        / "GarlicSMTP.desktop"
    )
    launcher_path.write_text(
        "GarlicSMTP launcher",
        encoding="utf-8",
    )

    other_launcher = (
        desktop_dir
        / "Other.desktop"
    )
    other_launcher.write_text(
        "Other application",
        encoding="utf-8",
    )

    class UserAccount:
        pw_dir = str(user_home)

    uninstall_user_desktop_launcher(
        runtime_user="alice",
        get_user_account=lambda username: UserAccount(),
    )

    assert not launcher_path.exists()
    assert other_launcher.exists()


def test_uninstall_user_desktop_launcher_does_not_hide_removal_failure(
    tmp_path,
    monkeypatch,
):
    user_home = tmp_path / "alice"
    desktop_dir = user_home / "Desktop"
    desktop_dir.mkdir(parents=True)

    launcher_path = (
        desktop_dir
        / "GarlicSMTP.desktop"
    )
    launcher_path.write_text(
        "GarlicSMTP launcher",
        encoding="utf-8",
    )

    class UserAccount:
        pw_dir = str(user_home)

    def fail_removal(path):
        raise PermissionError(
            "removal denied"
        )

    monkeypatch.setattr(
        "pathlib.Path.unlink",
        fail_removal,
    )

    with pytest.raises(
        PermissionError,
        match="removal denied",
    ):
        uninstall_user_desktop_launcher(
            runtime_user="alice",
            get_user_account=lambda username: UserAccount(),
        )


def test_uninstall_application_removes_owned_artifacts():
    calls = []

    def remove_tor_configuration():
        calls.append("tor")

    def remove_desktop_launcher():
        calls.append("launcher")

    def remove_user_data():
        calls.append("data")

    uninstall_application(
        remove_tor_configuration=remove_tor_configuration,
        remove_desktop_launcher=remove_desktop_launcher,
        remove_user_data=remove_user_data,
    )

    assert calls == [
        "tor",
        "launcher",
        "data",
    ]


def test_uninstall_tor_configuration_reads_and_removes_managed_configuration(
    tmp_path,
):
    torrc_path = tmp_path / "torrc"
    torrc_path.write_text(
        (
            "ControlPort 127.0.0.1:9999\n"
            "\n"
            "# GarlicSMTP Tor Control\n"
            "ControlPort 127.0.0.1:19051\n"
            "\n"
            "SocksPort 9050\n"
        ),
        encoding="utf-8",
    )

    profile = {
        "privilege_elevation": "sudo",
    }

    calls = []

    def remove_configuration(**kwargs):
        calls.append(kwargs)

    uninstall_tor_configuration(
        profile=profile,
        torrc_path=torrc_path,
        run="runner",
        remove_configuration=remove_configuration,
    )

    assert calls == [
        {
            "profile": profile,
            "torrc_path": torrc_path,
            "configuration_text": (
                "ControlPort 127.0.0.1:9999\n"
                "\n"
                "# GarlicSMTP Tor Control\n"
                "ControlPort 127.0.0.1:19051\n"
                "\n"
                "SocksPort 9050\n"
            ),
            "run": "runner",
        },
    ]


def test_execute_uninstallation_resolves_profile_and_owned_artifacts(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    manifest = {
        "platform": {
            "profiles": {
                "ubuntu": {
                    "match": {},
                },
            },
        },
    }

    profile = {
        "system_prerequisites": {
            "tor": {
                "torrc_path": "/etc/tor/torrc",
            },
        },
    }

    calls = []

    def detect_profile(os_release, profiles):
        assert os_release == "ubuntu-release"
        assert profiles is manifest["platform"]["profiles"]
        return profile

    def remove_tor(**kwargs):
        calls.append(
            (
                "tor",
                kwargs,
            )
        )

    def remove_launcher(**kwargs):
        calls.append(
            (
                "launcher",
                kwargs,
            )
        )

    def remove_data(**kwargs):
        calls.append(
            (
                "data",
                kwargs,
            )
        )

    execute_uninstallation(
        manifest=manifest,
        os_release="ubuntu-release",
        runtime_user="alice",
        paths=paths,
        run="runner",
        detect_profile=detect_profile,
        remove_tor=remove_tor,
        remove_launcher=remove_launcher,
        remove_data=remove_data,
    )

    assert calls == [
        (
            "tor",
            {
                "profile": profile,
                "torrc_path": Path("/etc/tor/torrc"),
                "run": "runner",
            },
        ),
        (
            "launcher",
            {
                "runtime_user": "alice",
            },
        ),
        (
            "data",
            {
                "paths": paths,
            },
        ),
    ]


def test_run_uninstallation_does_nothing_when_not_confirmed():
    calls = []

    def confirm():
        calls.append("confirm")
        return False

    def uninstall():
        calls.append("uninstall")

    result = run_uninstallation(
        confirm=confirm,
        uninstall=uninstall,
    )

    assert result is False
    assert calls == [
        "confirm",
    ]


def test_run_uninstallation_executes_once_when_confirmed():
    calls = []

    def confirm():
        calls.append("confirm")
        return True

    def uninstall():
        calls.append("uninstall")

    result = run_uninstallation(
        confirm=confirm,
        uninstall=uninstall,
    )

    assert result is True
    assert calls == [
        "confirm",
        "uninstall",
    ]


def test_run_application_uninstallation_resolves_runtime_inputs_after_confirmation(
    tmp_path,
):
    project_root = tmp_path / "project"
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    manifest = {
        "platform": {
            "profiles": [],
        },
    }

    calls = []

    def load_manifest(path):
        calls.append(
            (
                "manifest",
                path,
            )
        )
        return manifest

    def read_platform():
        calls.append("platform")
        return "ubuntu-release"

    def resolve_user():
        calls.append("user")
        return "alice"

    def paths_factory():
        calls.append("paths")
        return paths

    def execute(**kwargs):
        calls.append(
            (
                "execute",
                kwargs,
            )
        )

    result = run_application_uninstallation(
        project_root=project_root,
        confirm=lambda: True,
        load_manifest=load_manifest,
        read_platform=read_platform,
        runtime_user_resolver=resolve_user,
        paths_factory=paths_factory,
        run="runner",
        execute=execute,
    )

    assert result is True
    assert calls == [
        (
            "manifest",
            project_root / "install" / "manifest.toml",
        ),
        "platform",
        "user",
        "paths",
        (
            "execute",
            {
                "manifest": manifest,
                "os_release": "ubuntu-release",
                "runtime_user": "alice",
                "paths": paths,
                "run": "runner",
            },
        ),
    ]


def test_main_requires_explicit_destructive_confirmation(
    tmp_path,
):
    calls = []

    def input_reader(prompt):
        calls.append(
            (
                "prompt",
                prompt,
            )
        )
        return "DELETE"

    def run_uninstaller(**kwargs):
        calls.append(
            (
                "run",
                kwargs,
            )
        )
        return True

    result = main(
        project_root=tmp_path,
        input_reader=input_reader,
        run_uninstaller=run_uninstaller,
        output=lambda message: None,
    )

    assert result is True
    assert calls == [
        (
            "prompt",
            (
                "This will permanently delete all GarlicSMTP data, "
                "including messages, credentials, keys, attachments, "
                "and Onion identity. Type DELETE to continue: "
            ),
        ),
        (
            "run",
            {
                "project_root": tmp_path,
                "confirm": True,
            },
        ),
    ]


def test_run_application_uninstallation_accepts_confirmed_boolean(
    tmp_path,
):
    calls = []

    def execute(**kwargs):
        calls.append(kwargs)

    result = run_application_uninstallation(
        project_root=tmp_path,
        confirm=True,
        load_manifest=lambda path: {"platform": {"profiles": []}},
        read_platform=lambda: "ubuntu-release",
        runtime_user_resolver=lambda: "alice",
        paths_factory=lambda: ApplicationPaths.for_user(
            home=tmp_path,
        ),
        run="runner",
        execute=execute,
    )

    assert result is True
    assert len(calls) == 1


def test_run_application_uninstallation_resolves_nothing_when_not_confirmed(
    tmp_path,
):
    calls = []

    def load_manifest(path):
        calls.append("manifest")
        raise AssertionError(
            "manifest must not be loaded"
        )

    def read_platform():
        calls.append("platform")
        raise AssertionError(
            "platform must not be read"
        )

    def resolve_user():
        calls.append("user")
        raise AssertionError(
            "user must not be resolved"
        )

    def paths_factory():
        calls.append("paths")
        raise AssertionError(
            "paths must not be resolved"
        )

    def execute(**kwargs):
        calls.append("execute")
        raise AssertionError(
            "uninstallation must not execute"
        )

    result = run_application_uninstallation(
        project_root=tmp_path,
        confirm=False,
        load_manifest=load_manifest,
        read_platform=read_platform,
        runtime_user_resolver=resolve_user,
        paths_factory=paths_factory,
        run="runner",
        execute=execute,
    )

    assert result is False
    assert calls == []


def test_main_does_not_uninstall_without_exact_confirmation(
    tmp_path,
):
    calls = []

    def run_uninstaller(**kwargs):
        calls.append(kwargs)
        return kwargs["confirm"]

    result = main(
        project_root=tmp_path,
        input_reader=lambda prompt: "delete",
        run_uninstaller=run_uninstaller,
        output=lambda message: None,
    )

    assert result is False
    assert calls == [
        {
            "project_root": tmp_path,
            "confirm": False,
        },
    ]


def test_cli_returns_success_when_uninstallation_is_cancelled():
    result = cli(
        run_main=lambda: False,
    )

    assert result == 0


def test_uninstaller_has_direct_execution_entrypoint():
    source = (
        Path("install/uninstaller.py")
        .read_text(encoding="utf-8")
    )

    assert (
        'if __name__ == "__main__":\n'
        "    raise SystemExit(cli())"
    ) in source
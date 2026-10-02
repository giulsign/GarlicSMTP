from pathlib import Path
import sys

from garlicsmtp.gui.folder_opener import (
    FolderOpener,
)
from garlicsmtp.gui.folder_opener import (
    FolderOpener,
    open_directory,
)


def test_folder_opener_opens_existing_directory(
    tmp_path,
):
    calls = []

    opener = FolderOpener(
        open_directory=lambda path: (
            calls.append(path)
        )
    )

    directory = (
        tmp_path
        / "attachments"
        / "message-123"
    )
    directory.mkdir(
        parents=True
    )

    opener.open(directory)

    assert calls == [
        directory,
    ]


def test_folder_opener_does_not_open_missing_directory(
    tmp_path,
):
    calls = []

    opener = FolderOpener(
        open_directory=lambda path: (
            calls.append(path)
        )
    )

    directory = (
        tmp_path
        / "attachments"
        / "missing-message"
    )

    opener.open(directory)

    assert calls == []


def test_open_directory_uses_xdg_open_on_linux(
    tmp_path,
):
    calls = []

    open_directory(
        tmp_path,
        platform="linux",
        system_run=lambda command: (
            calls.append(command)
        ),
        is_wsl=False,
    )

    assert calls == [
        [
            "xdg-open",
            str(tmp_path),
        ],
    ]


def test_open_directory_uses_startfile_on_windows(
    tmp_path,
):
    calls = []

    open_directory(
        tmp_path,
        platform="win32",
        startfile=lambda path: (
            calls.append(path)
        ),
    )

    assert calls == [
        str(tmp_path),
    ]


def test_open_directory_uses_open_on_macos(
    tmp_path,
):
    calls = []

    open_directory(
        tmp_path,
        platform="darwin",
        system_run=lambda command: (
            calls.append(command)
        ),
    )

    assert calls == [
        [
            "open",
            str(tmp_path),
        ],
    ]


def test_open_directory_uses_current_platform_by_default(
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        "garlicsmtp.gui.folder_opener.sys.platform",
        "linux",
    )

    open_directory(
        Path("/attachments/message-1"),
        system_run=lambda command: calls.append(
            command
        ),
        is_wsl=False,
    )

    assert calls == [
        [
            "xdg-open",
            "/attachments/message-1",
        ],
    ]


def test_open_directory_uses_explorer_on_wsl(
    tmp_path,
):
    calls = []

    def run(command, **kwargs):
        calls.append(command)

        if command == [
            "wslpath",
            "-w",
            str(tmp_path),
        ]:
            class Result:
                stdout = (
                    "C:\\attachments\\message-1\n"
                )

            return Result()

    open_directory(
        tmp_path,
        platform="linux",
        system_run=run,
        is_wsl=True,
    )

    assert calls == [
        [
            "wslpath",
            "-w",
            str(tmp_path),
        ],
        [
            "explorer.exe",
            "C:\\attachments\\message-1",
        ],
    ]


def test_running_on_wsl_detects_wsl_distro_name():
    from garlicsmtp.gui.folder_opener import running_on_wsl

    assert running_on_wsl(
        environ={
            "WSL_DISTRO_NAME": "Ubuntu",
        }
    ) is True


def test_running_on_wsl_returns_false_without_wsl_environment():
    from garlicsmtp.gui.folder_opener import running_on_wsl

    assert running_on_wsl(
        environ={}
    ) is False
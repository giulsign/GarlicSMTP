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
    )

    assert calls == [
        [
            "xdg-open",
            "/attachments/message-1",
        ],
    ]
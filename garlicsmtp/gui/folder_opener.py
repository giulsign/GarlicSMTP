# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
from typing import Callable
import subprocess
import os
import sys


def running_on_wsl(
    *,
    environ=os.environ,
) -> bool:
    return bool(
        environ.get("WSL_DISTRO_NAME")
        or environ.get("WSL_INTEROP")
    )

def open_directory(
    directory: Path,
    *,
    platform: str | None = None,
    system_run=subprocess.run,
    startfile=None,
    is_wsl: bool | None = None,
) -> None:
    platform = (
        sys.platform
        if platform is None
        else platform
    )

    if is_wsl is None:
        is_wsl = running_on_wsl()

    if platform == "linux" and is_wsl:
        result = system_run(
            [
                "wslpath",
                "-w",
                str(directory),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        windows_path = result.stdout.strip()

        system_run(
            [
                "explorer.exe",
                windows_path,
            ]
        )
        return

    if platform == "linux":
        system_run(
            ["xdg-open", str(directory)]
        )
        return

    if platform == "win32":
        opener = startfile or os.startfile
        opener(str(directory))
        return

    if platform == "darwin":
        system_run(
            ["open", str(directory)]
        )


class FolderOpener:

    def __init__(
        self,
        *,
        open_directory: Callable[
            [Path],
            None,
        ],
    ) -> None:
        self.open_directory = (
            open_directory
        )

    def open(
        self,
        directory: Path,
    ) -> None:
        if not directory.is_dir():
            return

        self.open_directory(
            directory
        )

    def running_on_wsl(
        *,
        environ=os.environ,
    ) -> bool:
        return bool(
            environ.get("WSL_DISTRO_NAME")
            or environ.get("WSL_INTEROP")
        )
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
from typing import Callable
import subprocess
import os
import sys

def open_directory(
    directory: Path,
    *,
    platform: str | None = None,
    system_run=subprocess.run,
    startfile=None,
) -> None:
    platform = (
        sys.platform
        if platform is None
        else platform
    )

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
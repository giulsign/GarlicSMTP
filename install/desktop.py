# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import pwd
from pathlib import Path


def build_desktop_launcher(
    *,
    venv_dir: Path,
) -> str:
    executable = (
        venv_dir
        / "bin"
        / "garlicsmtp-gui"
    )

    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=GarlicSMTP\n"
        f"Exec={executable}\n"
        "Terminal=false\n"
    )


def install_desktop_launcher(
    *,
    desktop_dir: Path,
    venv_dir: Path,
) -> Path:
    launcher_path = (
        desktop_dir
        / "GarlicSMTP.desktop"
    )

    launcher_path.write_text(
        build_desktop_launcher(
            venv_dir=venv_dir,
        ),
        encoding="utf-8",
    )

    launcher_path.chmod(0o755)

    return launcher_path


def resolve_user_home(
    *,
    runtime_user: str,
    get_user_account,
) -> Path:
    account = get_user_account(
        runtime_user
    )

    return Path(account.pw_dir)


def resolve_desktop_dir(
    *,
    user_home: Path,
) -> Path:
    user_dirs_file = (
        user_home
        / ".config"
        / "user-dirs.dirs"
    )

    if not user_dirs_file.exists():
        return user_home / "Desktop"

    for line in user_dirs_file.read_text(
        encoding="utf-8",
    ).splitlines():
        prefix = "XDG_DESKTOP_DIR="

        if not line.startswith(prefix):
            continue

        value = line[len(prefix):].strip()

        if (
            value.startswith('"')
            and value.endswith('"')
        ):
            value = value[1:-1]

        value = value.replace(
            "$HOME",
            str(user_home),
        )

        return Path(value)

    raise ValueError(
        "XDG_DESKTOP_DIR is not configured"
    )


def install_user_desktop_launcher(
    *,
    runtime_user: str,
    venv_dir: Path,
    get_user_account=None,
) -> Path:
    if get_user_account is None:
        get_user_account = pwd.getpwnam

    user_home = resolve_user_home(
        runtime_user=runtime_user,
        get_user_account=get_user_account,
    )

    desktop_dir = resolve_desktop_dir(
        user_home=user_home,
    )

    return install_desktop_launcher(
        desktop_dir=desktop_dir,
        venv_dir=venv_dir,
    )

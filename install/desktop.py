# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import pwd
from pathlib import Path
import shutil


def build_desktop_launcher(
    *,
    venv_dir: Path,
    icon_path: Path,
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
        f"Icon={icon_path}\n"
        "Terminal=false\n"
    )


def install_desktop_launcher(
    *,
    desktop_dir: Path,
    venv_dir: Path,
    icon_source: Path,
    application_root: Path,
) -> Path:
    installed_icon = (
        application_root
        / "garlicsmtp.ico"
    )

    shutil.copy2(
        icon_source,
        installed_icon,
    )

    launcher_path = (
        desktop_dir
        / "GarlicSMTP.desktop"
    )

    launcher_path.write_text(
        build_desktop_launcher(
            venv_dir=venv_dir,
            icon_path=installed_icon,
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
    project_root: Path,
    application_root: Path,
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

    icon_source = (
        project_root
        / "install"
        / "assets"
        / "garlicsmtp.ico"
    )

    return install_desktop_launcher(
        desktop_dir=desktop_dir,
        venv_dir=venv_dir,
        icon_source=icon_source,
        application_root=application_root,
    )

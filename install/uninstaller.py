# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import shutil
import pwd
from pathlib import Path
import getpass
import subprocess

from install.platform import (
    detect_platform_profile,
)

from install.desktop import (
    resolve_desktop_dir,
    resolve_user_home,
)
from install.system import (
    remove_managed_profile_tor_configuration,
)
from garlicsmtp.configuration import ApplicationPaths
from install.platform import (
    detect_platform_profile,
    read_os_release,
)
from install.validator import (
    load_install_manifest,
)


def uninstall_user_data(
    *,
    paths,
) -> None:
    try:
        shutil.rmtree(
            paths.root_dir,
        )
    except FileNotFoundError:
        pass

def uninstall_user_desktop_launcher(
    *,
    runtime_user: str,
    get_user_account=None,
) -> None:
    if get_user_account is None:
        get_user_account = pwd.getpwnam

    user_home = resolve_user_home(
        runtime_user=runtime_user,
        get_user_account=get_user_account,
    )

    desktop_dir = resolve_desktop_dir(
        user_home=user_home,
    )

    launcher_path = (
        desktop_dir
        / "GarlicSMTP.desktop"
    )

    try:
        launcher_path.unlink()
    except FileNotFoundError:
        pass

def uninstall_tor_configuration(
    *,
    profile: dict,
    torrc_path,
    run,
    remove_configuration=remove_managed_profile_tor_configuration,
) -> None:
    configuration_text = torrc_path.read_text(
        encoding="utf-8",
    )

    remove_configuration(
        profile=profile,
        torrc_path=torrc_path,
        configuration_text=configuration_text,
        run=run,
    )

def run_uninstallation(
    *,
    confirm,
    uninstall,
) -> bool:
    if not confirm():
        return False

    uninstall()
    return True


def execute_uninstallation(
    *,
    manifest: dict,
    os_release: str,
    runtime_user: str,
    paths,
    run,
    detect_profile=detect_platform_profile,
    remove_tor=uninstall_tor_configuration,
    remove_launcher=uninstall_user_desktop_launcher,
    remove_data=uninstall_user_data,
) -> None:
    profile = detect_profile(
        os_release,
        manifest["platform"]["profiles"],
    )

    torrc_path = Path(
        profile["system_prerequisites"]["tor"]["torrc_path"]
    )

    uninstall_application(
        remove_tor_configuration=lambda: remove_tor(
            profile=profile,
            torrc_path=torrc_path,
            run=run,
        ),
        remove_desktop_launcher=lambda: remove_launcher(
            runtime_user=runtime_user,
        ),
        remove_user_data=lambda: remove_data(
            paths=paths,
        ),
    )

def run_application_uninstallation(
    *,
    project_root: Path,
    confirm,
    load_manifest=load_install_manifest,
    read_platform=read_os_release,
    runtime_user_resolver=getpass.getuser,
    paths_factory=ApplicationPaths.for_user,
    run=subprocess.run,
    execute=execute_uninstallation,
) -> bool:
    def uninstall():
        execute(
            manifest=load_manifest(
                project_root / "install" / "manifest.toml"
            ),
            os_release=read_platform(),
            runtime_user=runtime_user_resolver(),
            paths=paths_factory(),
            run=run,
        )

    return run_uninstallation(
        confirm=lambda: confirm,
        uninstall=uninstall,
    )

def uninstall_application(
    *,
    remove_tor_configuration,
    remove_desktop_launcher,
    remove_user_data,
) -> None:
    remove_tor_configuration()
    remove_desktop_launcher()
    remove_user_data()

def main(
    *,
    project_root: Path | None = None,
    input_reader=input,
    run_uninstaller=run_application_uninstallation,
    output=print,
) -> bool:
    if project_root is None:
        project_root = (
            Path(__file__).resolve().parents[1]
        )

    confirmation = input_reader(
        "This will permanently delete all GarlicSMTP data, "
        "including messages, credentials, keys, attachments, "
        "and Onion identity. Type DELETE to continue: "
    )

    return run_uninstaller(
        project_root=project_root,
        confirm=confirmation == "DELETE",
    )

def cli(
    *,
    run_main=main,
) -> int:
    run_main()
    return 0

if __name__ == "__main__":
    raise SystemExit(cli())
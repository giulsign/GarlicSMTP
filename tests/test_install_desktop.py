from pathlib import Path

from install.desktop import (
    build_desktop_launcher,
    install_desktop_launcher,
    resolve_desktop_dir,
    resolve_user_home,
    install_user_desktop_launcher,
)


def test_build_desktop_launcher_starts_installed_gui():
    venv_dir = Path(
        "/home/alice/.local/share/garlicsmtp/venv"
    )

    launcher = build_desktop_launcher(
        venv_dir=venv_dir,
    )

    assert launcher == (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=GarlicSMTP\n"
        "Exec=/home/alice/.local/share/garlicsmtp/venv/bin/garlicsmtp-gui\n"
        "Terminal=false\n"
    )


def test_install_desktop_launcher_writes_launcher_to_desktop(
    tmp_path,
):
    from install.desktop import (
        install_desktop_launcher,
    )

    desktop_dir = tmp_path / "Desktop"
    desktop_dir.mkdir()

    venv_dir = (
        tmp_path
        / ".local"
        / "share"
        / "garlicsmtp"
        / "venv"
    )

    launcher_path = install_desktop_launcher(
        desktop_dir=desktop_dir,
        venv_dir=venv_dir,
    )

    expected_path = (
        desktop_dir
        / "GarlicSMTP.desktop"
    )

    assert launcher_path == expected_path
    assert expected_path.read_text(
        encoding="utf-8",
    ) == build_desktop_launcher(
        venv_dir=venv_dir,
    )


def test_install_desktop_launcher_makes_launcher_executable(
    tmp_path,
):
    desktop_dir = tmp_path / "Desktop"
    desktop_dir.mkdir()

    launcher_path = install_desktop_launcher(
        desktop_dir=desktop_dir,
        venv_dir=tmp_path / "venv",
    )

    assert launcher_path.stat().st_mode & 0o111


def test_resolve_user_home_uses_runtime_user_account():

    class UserAccount:
        pw_dir = "/home/alice"

    received = {}

    def get_user_account(username):
        received["username"] = username
        return UserAccount()

    home = resolve_user_home(
        runtime_user="alice",
        get_user_account=get_user_account,
    )

    assert received["username"] == "alice"
    assert home == Path("/home/alice")


def test_resolve_desktop_dir_uses_xdg_user_configuration(
    tmp_path,
):
    from install.desktop import (
        resolve_desktop_dir,
    )

    config_dir = tmp_path / ".config"
    config_dir.mkdir()

    (
        config_dir
        / "user-dirs.dirs"
    ).write_text(
        'XDG_DESKTOP_DIR="$HOME/Scrivania"\n',
        encoding="utf-8",
    )

    desktop_dir = resolve_desktop_dir(
        user_home=tmp_path,
    )

    assert desktop_dir == (
        tmp_path / "Scrivania"
    )


def test_resolve_desktop_dir_falls_back_to_desktop_when_xdg_config_is_missing(
    tmp_path,
):
    desktop_dir = resolve_desktop_dir(
        user_home=tmp_path,
    )

    assert desktop_dir == (
        tmp_path / "Desktop"
    )


def test_install_user_desktop_launcher_uses_runtime_user_desktop(
    tmp_path,
):

    user_home = tmp_path / "alice"
    desktop_dir = user_home / "Desktop"
    desktop_dir.mkdir(parents=True)

    class UserAccount:
        pw_dir = str(user_home)

    launcher_path = install_user_desktop_launcher(
        runtime_user="alice",
        venv_dir=tmp_path / "venv",
        get_user_account=lambda username: UserAccount(),
    )

    assert launcher_path == (
        desktop_dir / "GarlicSMTP.desktop"
    )
    assert launcher_path.read_text(
        encoding="utf-8",
    ) == build_desktop_launcher(
        venv_dir=tmp_path / "venv",
    )
    assert launcher_path.stat().st_mode & 0o111


def test_install_user_desktop_launcher_uses_system_user_account_by_default(
    tmp_path,
    monkeypatch,
):
    user_home = tmp_path / "alice"
    desktop_dir = user_home / "Desktop"
    desktop_dir.mkdir(parents=True)

    class UserAccount:
        pw_dir = str(user_home)

    received = {}

    def getpwnam(username):
        received["username"] = username
        return UserAccount()

    monkeypatch.setattr(
        "install.desktop.pwd.getpwnam",
        getpwnam,
    )

    launcher_path = install_user_desktop_launcher(
        runtime_user="alice",
        venv_dir=tmp_path / "venv",
    )

    assert received["username"] == "alice"
    assert launcher_path == (
        desktop_dir / "GarlicSMTP.desktop"
    )
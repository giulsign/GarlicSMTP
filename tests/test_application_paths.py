# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path

from garlicsmtp.configuration import (
    ApplicationPaths,
)

def test_application_paths_derive_directories():
    paths = ApplicationPaths(
        root_dir=Path("/tmp/garlicsmtp")
    )

    assert paths.config_dir == Path(
        "/tmp/garlicsmtp/config"
    )

    assert paths.data_dir == Path(
        "/tmp/garlicsmtp/data"
    )

    assert paths.state_dir == Path(
        "/tmp/garlicsmtp/state"
    )

    assert paths.cache_dir == Path(
        "/tmp/garlicsmtp/cache"
    )

    assert paths.log_dir == Path(
        "/tmp/garlicsmtp/state/logs"
    )


def test_application_paths_derive_files():
    paths = ApplicationPaths(
        root_dir=Path("/tmp/garlicsmtp")
    )

    assert paths.settings_file == Path(
        "/tmp/garlicsmtp/config/settings.toml"
    )

    assert paths.mailbox_database == Path(
        "/tmp/garlicsmtp/data/mailboxes.db"
    )

    assert paths.queue_database == Path(
        "/tmp/garlicsmtp/state/queue.db"
    )


def test_application_paths_for_user():
    paths = ApplicationPaths.for_user(
        home=Path("/home/alice")
    )

    assert paths.root_dir == Path(
        "/home/alice/.local/share/garlicsmtp"
    )


def test_application_paths_create_directories(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp"
    )

    paths.create_directories()

    assert paths.config_dir.is_dir()
    assert paths.data_dir.is_dir()
    assert paths.state_dir.is_dir()
    assert paths.cache_dir.is_dir()
    assert paths.log_dir.is_dir()


def test_create_directories_is_idempotent(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp"
    )

    paths.create_directories()
    paths.create_directories()

    assert paths.root_dir.is_dir()


def test_application_paths_for_development(
    tmp_path,
):
    project_root = (
        tmp_path
        / "GarlicSMTP"
    )

    paths = (
        ApplicationPaths
        .for_development(
            project_root=project_root,
            home=tmp_path / "home",
        )
    )

    assert paths.settings_file == (
        project_root
        / "config"
        / "default.toml"
    )

    assert paths.root_dir == (
        tmp_path
        / "home"
        / ".local"
        / "share"
        / "garlicsmtp"
    )


def test_application_paths_for_user_uses_runtime_settings(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path
    )

    assert paths.settings_file == (
        tmp_path
        / ".local"
        / "share"
        / "garlicsmtp"
        / "config"
        / "settings.toml"
    )


def test_application_paths_exposes_onion_identity_file(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path
    )

    assert (
        paths.onion_identity_file
        == (
            paths.state_dir
            / "onion-service.key"
        )
    )
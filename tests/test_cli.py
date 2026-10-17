# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import getpass

import pytest

from garlicsmtp.cli import main
from garlicsmtp.configuration import ApplicationPaths
from garlicsmtp.security.at_rest_key_manager import AtRestKeyManager
from garlicsmtp.security.auth.account_credentials import AccountCredentialStore
from garlicsmtp.storage.sqlite import SQLiteMessageStoreBackend


@pytest.fixture
def cli_account(tmp_path, monkeypatch):
    paths = ApplicationPaths(root_dir=tmp_path / "garlicsmtp")
    paths.create_directories()

    monkeypatch.setattr(
        "garlicsmtp.configuration.paths.ApplicationPaths.for_user",
        lambda: paths,
    )

    credentials = AccountCredentialStore(path=paths.account_credentials_file)
    credentials.create(username="alice", password="Garlic1!")
    credentials.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=AtRestKeyManager().generate_recovery_key(),
    )

    dek = credentials.unlock_dek_with_password(
        username="alice", password="Garlic1!"
    )

    monkeypatch.setattr("builtins.input", lambda _: "alice")
    monkeypatch.setattr("getpass.getpass", lambda _: "Garlic1!")

    return paths, dek


def test_cli_mailbox_list(cli_account, message, capsys):
    paths, dek = cli_account
    backend = SQLiteMessageStoreBackend(paths.mailbox_database, dek=dek)
    backend.save("bob@test.onion", message)
    backend.close()

    result = main(["mailbox", "list"])
    output = capsys.readouterr().out

    assert result == 0
    assert "bob@test.onion" in output
    assert "Messages: 1" in output


def test_cli_mailbox_messages(cli_account, message, capsys):
    paths, dek = cli_account
    backend = SQLiteMessageStoreBackend(paths.mailbox_database, dek=dek)
    message.headers.fields["Subject"] = "CLI integration"
    backend.save("bob@test.onion", message)
    backend.close()

    result = main(["mailbox", "messages", "bob@test.onion"])
    output = capsys.readouterr().out

    assert result == 0
    assert "CLI integration" in output


def test_cli_mailbox_show(cli_account, message, capsys):
    paths, dek = cli_account
    backend = SQLiteMessageStoreBackend(paths.mailbox_database, dek=dek)
    message.headers.fields["Subject"] = "CLI show"
    message.body = "Visible body"
    backend.save("bob@test.onion", message)
    backend.close()

    result = main(["mailbox", "show", "bob@test.onion", "1"])
    output = capsys.readouterr().out

    assert result == 0
    assert "Subject: CLI show" in output
    assert "Visible body" in output


def test_cli_mailbox_flags(cli_account, message, capsys):
    paths, dek = cli_account
    backend = SQLiteMessageStoreBackend(paths.mailbox_database, dek=dek)
    backend.save("bob@test.onion", message)
    backend.close()

    result = main(["mailbox", "flags", "bob@test.onion", "1", "add", "\\Seen"])
    output = capsys.readouterr().out

    assert result == 0
    assert "UID 1 flags: \\Seen" in output


def test_cli_mailbox_without_credentials_does_not_create_database(
    tmp_path, monkeypatch
):
    paths = ApplicationPaths(root_dir=tmp_path / "garlicsmtp")
    monkeypatch.setattr(
        "garlicsmtp.configuration.paths.ApplicationPaths.for_user",
        lambda: paths,
    )

    database = paths.mailbox_database
    result = main(["--mailbox-db", str(database), "mailbox", "list"])

    assert result != 0
    assert not database.exists()


def test_cli_mailbox_wrong_password_does_not_open_database(
    tmp_path, monkeypatch
):
    paths = ApplicationPaths(root_dir=tmp_path / "garlicsmtp")
    paths.create_directories()
    monkeypatch.setattr(
        "garlicsmtp.configuration.paths.ApplicationPaths.for_user",
        lambda: paths,
    )

    credentials = AccountCredentialStore(path=paths.account_credentials_file)
    credentials.create(username="alice", password="Garlic1!")
    credentials.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=AtRestKeyManager().generate_recovery_key(),
    )

    monkeypatch.setattr("builtins.input", lambda _: "alice")
    monkeypatch.setattr("getpass.getpass", lambda _: "Wrong1!")

    result = main(["--mailbox-db", str(paths.mailbox_database), "mailbox", "list"])

    assert result != 0
    assert not paths.mailbox_database.exists()


def test_cli_mailbox_with_valid_credentials_reads_encrypted_database(
    tmp_path, monkeypatch, capsys
):
    paths = ApplicationPaths(root_dir=tmp_path / "garlicsmtp")
    paths.create_directories()
    monkeypatch.setattr(
        "garlicsmtp.configuration.paths.ApplicationPaths.for_user",
        lambda: paths,
    )

    credentials = AccountCredentialStore(path=paths.account_credentials_file)
    credentials.create(username="alice", password="Garlic1!")
    credentials.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=AtRestKeyManager().generate_recovery_key(),
    )

    dek = credentials.unlock_dek_with_password(
        username="alice", password="Garlic1!"
    )
    backend = SQLiteMessageStoreBackend(paths.mailbox_database, dek=dek)
    backend.close()

    monkeypatch.setattr("builtins.input", lambda _: "alice")
    monkeypatch.setattr("getpass.getpass", lambda _: "Garlic1!")

    result = main(["mailbox", "list"])
    output = capsys.readouterr().out

    assert result == 0
    assert "No mailboxes found." in output
    assert paths.mailbox_database.read_bytes()[:16] != b"SQLite format 3\x00"


def test_cli_mailbox_reads_persisted_encrypted_message(
    tmp_path, monkeypatch, capsys, message
):
    paths = ApplicationPaths(root_dir=tmp_path / "garlicsmtp")
    paths.create_directories()
    monkeypatch.setattr(
        "garlicsmtp.configuration.paths.ApplicationPaths.for_user",
        lambda: paths,
    )

    credentials = AccountCredentialStore(path=paths.account_credentials_file)
    credentials.create(username="alice", password="Garlic1!")
    credentials.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=AtRestKeyManager().generate_recovery_key(),
    )

    dek = credentials.unlock_dek_with_password(
        username="alice", password="Garlic1!"
    )
    message.headers.fields["Subject"] = "Encrypted CLI integration"

    backend = SQLiteMessageStoreBackend(paths.mailbox_database, dek=dek)
    backend.save("bob@test.onion", message)
    backend.close()

    reopened = SQLiteMessageStoreBackend(paths.mailbox_database, dek=dek)
    try:
        assert reopened.count("bob@test.onion") == 1
    finally:
        reopened.close()

    monkeypatch.setattr("builtins.input", lambda _: "alice")
    monkeypatch.setattr("getpass.getpass", lambda _: "Garlic1!")

    assert credentials.unlock_dek_with_password(
        username="alice", password="Garlic1!"
    ) == dek
    assert paths.mailbox_database.exists()

    result = main(["mailbox", "messages", "bob@test.onion"])
    output = capsys.readouterr().out

    assert result == 0
    assert "Encrypted CLI integration" in output
    assert paths.mailbox_database.read_bytes()[:16] != b"SQLite format 3\x00"

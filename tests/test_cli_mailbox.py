# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.cli.mailbox import (
    list_mailboxes,
    list_messages,
    show_message,
    update_flags,
)
from garlicsmtp.storage.sqlite import SQLiteMessageStoreBackend


def create_mailbox_database(
    path,
    message,
    *,
    dek: bytes,
):
    backend = SQLiteMessageStoreBackend(
        path,
        dek=dek,
    )

    message.headers.fields[
        "Subject"
    ] = "CLI mailbox test"

    message.body = "Message body"

    try:
        message_id = backend.save(
            "bob@test.onion",
            message,
        )
    finally:
        backend.close()

    return message_id


def test_cli_lists_mailboxes(
    tmp_path,
    message,
    capsys,
    dek,
):
    database = tmp_path / "mailboxes.db"

    create_mailbox_database(
        database,
        message,
        dek=dek,
    )

    result = list_mailboxes(
        str(database),
        dek=dek,
    )

    output = capsys.readouterr().out

    assert result == 0
    assert "bob@test.onion" in output
    assert "Messages: 1" in output


def test_cli_lists_messages(
    tmp_path,
    message,
    capsys,
    dek,
):
    database = tmp_path / "mailboxes.db"

    message_id = create_mailbox_database(
        database,
        message,
        dek=dek,
    )

    result = list_messages(
        str(database),
        "bob@test.onion",
        dek=dek,
    )

    output = capsys.readouterr().out

    assert result == 0
    assert message_id in output
    assert "alice@test.onion" in output
    assert "CLI mailbox test" in output


def test_cli_shows_message_by_position(
    tmp_path,
    message,
    capsys,
    dek,
):
    database = tmp_path / "mailboxes.db"

    create_mailbox_database(
        database,
        message,
        dek=dek,
    )

    result = show_message(
        str(database),
        "bob@test.onion",
        "1",
        dek=dek,
    )

    output = capsys.readouterr().out

    assert result == 0
    assert "From: alice@test.onion" in output
    assert "To: bob@test.onion" in output
    assert "Subject: CLI mailbox test" in output
    assert "Message body" in output


def test_cli_show_returns_error_for_missing_message(
    tmp_path,
    capsys,
    dek,
):
    database = tmp_path / "mailboxes.db"

    result = show_message(
        str(database),
        "bob@test.onion",
        "1",
        dek=dek,
    )

    output = capsys.readouterr().out

    assert result == 1
    assert "Message not found." in output


def test_cli_updates_message_flags(
    tmp_path,
    message,
    capsys,
    dek,
):
    database = tmp_path / "mailboxes.db"

    create_mailbox_database(
        database,
        message,
        dek=dek,
    )

    result = update_flags(
        database_path=str(database),
        mailbox="bob@test.onion",
        message_reference="1",
        operation="add",
        flags={
            "\\Seen",
        },
        dek=dek,
    )

    output = capsys.readouterr().out

    assert result == 0
    assert "UID 1 flags: \\Seen" in output

    backend = SQLiteMessageStoreBackend(
        database,
        dek=dek,
    )

    try:
        entries = backend.list_entries(
            "bob@test.onion"
        )

        assert entries[0].flags == {
            "\\Seen",
        }

    finally:
        backend.close()

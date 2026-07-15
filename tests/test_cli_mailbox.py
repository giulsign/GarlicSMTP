from garlicsmtp.cli.mailbox import (
    list_mailboxes,
    list_messages,
    show_message,
)
from garlicsmtp.storage.sqlite import (
    SQLiteMessageStoreBackend,
)


def create_mailbox_database(
    path,
    message,
):
    backend = SQLiteMessageStoreBackend(
        path
    )

    message.headers.fields[
        "Subject"
    ] = "CLI mailbox test"

    message.body = "Message body"

    message_id = backend.save(
        "bob@test.onion",
        message,
    )

    backend.close()

    return message_id


def test_cli_lists_mailboxes(
    tmp_path,
    message,
    capsys,
):
    database = tmp_path / "mailboxes.db"

    create_mailbox_database(
        database,
        message,
    )

    result = list_mailboxes(
        str(database)
    )

    output = capsys.readouterr().out

    assert result == 0
    assert "bob@test.onion" in output
    assert "Messages: 1" in output


def test_cli_lists_messages(
    tmp_path,
    message,
    capsys,
):
    database = tmp_path / "mailboxes.db"

    message_id = create_mailbox_database(
        database,
        message,
    )

    result = list_messages(
        str(database),
        "bob@test.onion",
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
):
    database = tmp_path / "mailboxes.db"

    create_mailbox_database(
        database,
        message,
    )

    result = show_message(
        str(database),
        "bob@test.onion",
        "1",
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
):
    database = tmp_path / "mailboxes.db"

    result = show_message(
        str(database),
        "bob@test.onion",
        "1",
    )

    output = capsys.readouterr().out

    assert result == 1
    assert "Message not found." in output
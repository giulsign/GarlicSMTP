from garlicsmtp.cli import main
from garlicsmtp.storage.sqlite import (
    SQLiteMessageStoreBackend,
)


def test_cli_mailbox_list(
    tmp_path,
    message,
    capsys,
):
    database = tmp_path / "mailboxes.db"

    backend = SQLiteMessageStoreBackend(
        database
    )

    backend.save(
        "bob@test.onion",
        message,
    )

    backend.close()

    result = main(
        [
            "--mailbox-db",
            str(database),
            "mailbox",
            "list",
        ]
    )

    output = capsys.readouterr().out

    assert result == 0
    assert "bob@test.onion" in output
    assert "Messages: 1" in output


def test_cli_mailbox_messages(
    tmp_path,
    message,
    capsys,
):
    database = tmp_path / "mailboxes.db"

    backend = SQLiteMessageStoreBackend(
        database
    )

    message.headers.fields[
        "Subject"
    ] = "CLI integration"

    backend.save(
        "bob@test.onion",
        message,
    )

    backend.close()

    result = main(
        [
            "--mailbox-db",
            str(database),
            "mailbox",
            "messages",
            "bob@test.onion",
        ]
    )

    output = capsys.readouterr().out

    assert result == 0
    assert "CLI integration" in output


def test_cli_mailbox_show(
    tmp_path,
    message,
    capsys,
):
    database = tmp_path / "mailboxes.db"

    backend = SQLiteMessageStoreBackend(
        database
    )

    message.headers.fields[
        "Subject"
    ] = "CLI show"

    message.body = "Visible body"

    backend.save(
        "bob@test.onion",
        message,
    )

    backend.close()

    result = main(
        [
            "--mailbox-db",
            str(database),
            "mailbox",
            "show",
            "bob@test.onion",
            "1",
        ]
    )

    output = capsys.readouterr().out

    assert result == 0
    assert "Subject: CLI show" in output
    assert "Visible body" in output

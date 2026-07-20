from garlicsmtp.imap.server import IMAPServer
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.security.auth import MemoryAuthenticator


class FakeConnection:

    def __init__(self):
        self.lines = [
            "A001 CAPABILITY",
            "A002 NOOP",
            "A003 LOGOUT",
        ]

        self.sent = []
        self.closed = False

    def receive_line(self):
        if not self.lines:
            return None

        return self.lines.pop(0)

    def send(self, text):
        self.sent.append(text)

    def close(self):
        self.closed = True

    def send_bytes(
        self,
        data,
    ):
        self.sent.append(data)


def test_imap_server_handles_connection():

    server = IMAPServer()

    connection = FakeConnection()

    server.running = True

    server.connection_factory = (
        lambda connected_socket: connection
    )

    server._serve_connection(
        object(),
        ("127.0.0.1", 10000),
    )

    assert connection.sent == [
        "* OK GarlicSMTP IMAP ready\r\n",
        (
            "* CAPABILITY "
            "IMAP4rev1 UIDPLUS UNSELECT MOVE\r\n"
        ),
        (
            "A001 OK "
            "CAPABILITY completed\r\n"
        ),
        "A002 OK NOOP completed\r\n",
        "* BYE Logging out\r\n",
        "A003 OK LOGOUT completed\r\n",
    ]

    assert connection.closed is True


class FakeAppendConnection:
    def __init__(
        self,
        lines,
        literal,
    ):
        self.lines = list(lines)
        self.literal = literal
        self.sent = []
        self.closed = False
        self.received_sizes = []

    def receive_line(self):
        if not self.lines:
            return None

        return self.lines.pop(0)

    def receive_bytes(
        self,
        size,
    ):
        self.received_sizes.append(
            size
        )

        if len(self.literal) < size:
            return None

        result = self.literal[:size]

        self.literal = self.literal[
            size:
        ]

        return result

    def send(
        self,
        value,
    ):
        self.sent.append(
            value
        )

    def close(self):
        self.closed = True


def test_imap_server_handles_append_literal(
    message,
):
    literal = (
        b"From: alice@test.onion\r\n"
        b"To: bob@test.onion\r\n"
        b"Subject: APPEND test\r\n"
        b"\r\n"
        b"Stored through IMAP."
    )

    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    connection = FakeAppendConnection(
        [
            "A001 LOGIN alice secret",
            (
                'A002 APPEND '
                '"archive@test.onion" '
                f"{{{len(literal)}}}"
            ),
            "A003 LOGOUT",
        ],
        literal,
    )

    server = IMAPServer(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    server.running = True

    server.connection_factory = (
        lambda connected_socket: (
            connection
        )
    )

    server._serve_connection(
        object(),
        ("127.0.0.1", 10000),
    )

    assert connection.received_sizes == [
        len(literal),
    ]

    assert (
        "+ Ready for literal data\r\n"
        in connection.sent
    )

    assert any(
        (
            "A002 OK "
            "[APPENDUID 1 2] "
            "APPEND completed"
        )
        in sent
        for sent in connection.sent
    )

    mailbox = store.open_mailbox(
        "archive@test.onion"
    )

    appended = mailbox.get_by_uid(
        2
    )

    assert appended is not None

    assert appended.message.body == (
        "Stored through IMAP."
    )


def test_imap_server_handles_non_synchronizing_append(
    message,
):
    literal = (
        b"Subject: Draft\r\n"
        b"\r\n"
        b"Draft body"
    )

    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    connection = FakeAppendConnection(
        [
            "A001 LOGIN alice secret",
            (
                'A002 APPEND '
                '"archive@test.onion" '
                f"{{{len(literal)}+}}"
            ),
            "A003 LOGOUT",
        ],
        literal,
    )

    server = IMAPServer(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    server.running = True

    server.connection_factory = (
        lambda connected_socket: (
            connection
        )
    )

    server._serve_connection(
        object(),
        ("127.0.0.1", 10000),
    )

    assert connection.received_sizes == [
        len(literal),
    ]

    assert (
        "+ Ready for literal data\r\n"
        not in connection.sent
    )

    assert any(
        (
            "A002 OK "
            "[APPENDUID 1 2] "
            "APPEND completed"
        )
        in sent
        for sent in connection.sent
    )


def test_imap_server_handles_multiappend(
    message,
):
    first_literal = (
        b"Subject: First\r\n"
        b"\r\n"
        b"First body"
    )

    second_literal = (
        b"Subject: Second\r\n"
        b"\r\n"
        b"Second body"
    )

    combined_literals = (
        first_literal
        + second_literal
    )

    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    connection = FakeAppendConnection(
        [
            "A001 LOGIN alice secret",
            (
                'A002 APPEND '
                '"archive@test.onion" '
                f"{{{len(first_literal)}}} "
                f"{{{len(second_literal)}}}"
            ),
            "A003 LOGOUT",
        ],
        combined_literals,
    )

    server = IMAPServer(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    server.running = True

    server.connection_factory = (
        lambda connected_socket: (
            connection
        )
    )

    server._serve_connection(
        object(),
        ("127.0.0.1", 10000),
    )

    assert connection.received_sizes == [
        len(first_literal),
        len(second_literal),
    ]

    assert connection.sent.count(
        "+ Ready for literal data\r\n"
    ) == 2

    assert any(
        (
            "A002 OK "
            "[APPENDUID 1 2,3] "
            "APPEND completed"
        )
        in sent
        for sent in connection.sent
    )

    mailbox = store.open_mailbox(
        "archive@test.onion"
    )

    first = mailbox.get_by_uid(2)
    second = mailbox.get_by_uid(3)

    assert first is not None
    assert second is not None

    assert first.message.body == (
        "First body"
    )

    assert second.message.body == (
        "Second body"
    )


def test_imap_server_handles_multiappend_mixed_literal_modes(
    message,
):
    first_literal = (
        b"Subject: First\r\n"
        b"\r\n"
        b"First body"
    )

    second_literal = (
        b"Subject: Second\r\n"
        b"\r\n"
        b"Second body"
    )

    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    connection = FakeAppendConnection(
        [
            "A001 LOGIN alice secret",
            (
                'A002 APPEND '
                '"archive@test.onion" '
                f"{{{len(first_literal)}+}} "
                f"{{{len(second_literal)}}}"
            ),
            "A003 LOGOUT",
        ],
        first_literal + second_literal,
    )

    server = IMAPServer(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    server.running = True

    server.connection_factory = (
        lambda connected_socket: (
            connection
        )
    )

    server._serve_connection(
        object(),
        ("127.0.0.1", 10000),
    )

    assert connection.received_sizes == [
        len(first_literal),
        len(second_literal),
    ]

    assert connection.sent.count(
        "+ Ready for literal data\r\n"
    ) == 1

    assert any(
        (
            "A002 OK "
            "[APPENDUID 1 2,3] "
            "APPEND completed"
        )
        in sent
        for sent in connection.sent
    )
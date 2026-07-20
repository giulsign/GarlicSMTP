import socket
import threading
import time

from garlicsmtp.imap.server import IMAPServer
from garlicsmtp.security.auth import (
    MemoryAuthenticator,
)
from garlicsmtp.storage.serializer import (
    MessageSerializer,
)
from garlicsmtp.storage.store import MessageStore


def receive_line(sock) -> str:
    data = bytearray()

    while not data.endswith(b"\r\n"):
        chunk = sock.recv(1)

        if not chunk:
            break

        data.extend(chunk)

    return data.decode("utf-8")


def receive_exactly(
    sock,
    size: int,
) -> bytes:
    data = bytearray()

    while len(data) < size:
        chunk = sock.recv(
            size - len(data)
        )

        if not chunk:
            break

        data.extend(chunk)

    return bytes(data)


def test_imap_server_real_connection(
    message,
):
    store = MessageStore()

    store.save(
        "bob@test.onion",
        message,
    )

    server = IMAPServer(
        host="127.0.0.1",
        port=0,
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    server.start()

    port = server.server.socket.getsockname()[1]

    stop_event = threading.Event()

    def run_server():
        while not stop_event.is_set():
            server.tick()
            time.sleep(0.01)

    thread = threading.Thread(
        target=run_server,
        daemon=True,
    )

    thread.start()

    try:
        with socket.create_connection(
            ("127.0.0.1", port),
            timeout=5,
        ) as client:
            assert receive_line(client) == (
                "* OK GarlicSMTP IMAP ready\r\n"
            )

            client.sendall(
                b"A001 CAPABILITY\r\n"
            )

            assert receive_line(client) == (
                "* CAPABILITY "
                "IMAP4rev1 UIDPLUS "
                "UNSELECT MOVE\r\n"
            )

            assert receive_line(client) == (
                "A001 OK "
                "CAPABILITY completed\r\n"
            )

            client.sendall(
                b"A002 LOGIN alice secret\r\n"
            )

            assert receive_line(client) == (
                "A002 OK LOGIN completed\r\n"
            )

            client.sendall(
                b'A003 LIST "" "*"\r\n'
            )

            assert receive_line(client) == (
                '* LIST () "/" '
                '"bob@test.onion"\r\n'
            )

            assert receive_line(client) == (
                "A003 OK LIST completed\r\n"
            )

            client.sendall(
                b'A004 SELECT "bob@test.onion"\r\n'
            )

            assert receive_line(client) == (
                "* FLAGS "
                "(\\Seen \\Answered \\Flagged "
                "\\Deleted \\Draft)\r\n"
            )

            assert receive_line(client) == (
                "* 1 EXISTS\r\n"
            )

            assert receive_line(client) == (
                "* 0 RECENT\r\n"
            )

            assert receive_line(client) == (
                "* OK [UIDNEXT 2] "
                "Predicted next UID\r\n"
            )

            assert receive_line(client) == (
                "* OK [UNSEEN 1] "
                "First unseen message\r\n"
            )

            assert receive_line(client) == (
                "A004 OK [READ-WRITE] "
                "SELECT completed\r\n"
            )

            content = (
                MessageSerializer.to_rfc5322(
                    message
                ).encode("utf-8")
            )

            client.sendall(
                (
                    "A005 UID FETCH 1 "
                    "(UID FLAGS BODY[])\r\n"
                ).encode("utf-8")
            )

            assert receive_line(client) == (
                "* 1 FETCH "
                f"(UID 1 FLAGS (\\Seen) BODY[] "
                f"{{{len(content)}}}\r\n"
            )

            assert receive_exactly(
                client,
                len(content),
            ) == content

            assert receive_line(client) == "\r\n"

            assert receive_line(client) == ")\r\n"

            assert receive_line(client) == (
                "A005 OK UID FETCH completed\r\n"
            )

            expected_size = len(content)

            client.sendall(
                (
                    "A006 UID FETCH 1 "
                    "(UID FLAGS RFC822.SIZE)\r\n"
                ).encode("utf-8")
            )

            assert receive_line(client) == (
                "* 1 FETCH "
                f"(UID 1 FLAGS (\\Seen) "
                f"RFC822.SIZE {expected_size})\r\n"
            )

            assert receive_line(client) == (
                "A006 OK UID FETCH completed\r\n"
            )

            client.sendall(
                b"A007 NOOP\r\n"
            )

            assert receive_line(client) == (
                "A007 OK NOOP completed\r\n"
            )

            client.sendall(
                b"A008 LOGOUT\r\n"
            )

            assert receive_line(client) == (
                "* BYE Logging out\r\n"
            )

            assert receive_line(client) == (
                "A008 OK LOGOUT completed\r\n"
            )

    finally:
        stop_event.set()
        server.stop()
        thread.join(timeout=2)


def test_imap_server_real_append(
    message,
):
    literal = (
        b"From: alice@test.onion\r\n"
        b"To: bob@test.onion\r\n"
        b"Subject: APPEND socket test\r\n"
        b"\r\n"
        b"Real socket APPEND."
    )

    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    server = IMAPServer(
        host="127.0.0.1",
        port=0,
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    server.start()

    port = server.server.socket.getsockname()[1]

    stop_event = threading.Event()

    def run_server():
        while not stop_event.is_set():
            server.tick()
            time.sleep(0.01)

    thread = threading.Thread(
        target=run_server,
        daemon=True,
    )

    thread.start()

    try:
        with socket.create_connection(
            ("127.0.0.1", port),
            timeout=5,
        ) as client:
            assert receive_line(client) == (
                "* OK GarlicSMTP IMAP ready\r\n"
            )

            client.sendall(
                b"A001 LOGIN alice secret\r\n"
            )

            assert receive_line(client) == (
                "A001 OK LOGIN completed\r\n"
            )

            client.sendall(
                (
                    'A002 APPEND '
                    '"archive@test.onion" '
                    f"{{{len(literal)}}}\r\n"
                ).encode("ascii")
            )

            assert receive_line(client) == (
                "+ Ready for literal data\r\n"
            )

            client.sendall(
                literal
            )

            assert receive_line(client) == (
                "A002 OK "
                "[APPENDUID 1 2] "
                "APPEND completed\r\n"
            )

            client.sendall(
                b"A003 LOGOUT\r\n"
            )

            assert receive_line(client) == (
                "* BYE Logging out\r\n"
            )

            assert receive_line(client) == (
                "A003 OK LOGOUT completed\r\n"
            )

    finally:
        stop_event.set()
        server.stop()
        thread.join(timeout=2)

    appended = (
        store.open_mailbox(
            "archive@test.onion"
        )
        .get_by_uid(2)
    )

    assert appended is not None

    assert appended.message.body == (
        "Real socket APPEND."
    )
import pytest

from garlicsmtp.tor.control import (
    TorControlClient,
    TorControlProtocolError,
    TorReplyParser,
)
from garlicsmtp.tor.control import (
    SafeCookieEngine,
    TorControlSecurityError,
)



class FakeConnection:

    def __init__(
        self,
        lines=None,
    ):
        self.lines = list(
            lines or []
        )

        self.sent = []
        self.connected = False
        self.closed = False

    def connect(
        self,
    ):
        self.connected = True

    def close(
        self,
    ):
        self.connected = False
        self.closed = True

    def send_line(
        self,
        line,
    ):
        self.sent.append(
            line
        )

    def receive_line(
        self,
    ):
        if not self.lines:
            return None

        return self.lines.pop(0)


def test_tor_control_client_connects_and_closes():
    connection = FakeConnection()

    client = TorControlClient(
        connection=connection
    )

    client.connect()

    assert client.connected is True

    client.close()

    assert client.connected is False
    assert connection.closed is True


def test_tor_control_client_context_manager():
    connection = FakeConnection()

    with TorControlClient(
        connection=connection
    ) as client:
        assert client.connected is True

    assert connection.closed is True


def test_tor_control_client_reads_protocol_info():
    connection = FakeConnection(
        lines=[
            "250-PROTOCOLINFO 1",
            (
                "250-AUTH "
                "METHODS=SAFECOOKIE "
                'COOKIEFILE="/run/tor/'
                'control.authcookie"'
            ),
            '250-VERSION Tor="0.4.8.12"',
            "250 OK",
        ]
    )

    client = TorControlClient(
        connection=connection
    )

    client.connect()

    info = client.protocol_info()

    assert connection.sent == [
        "PROTOCOLINFO 1",
    ]

    assert info.protocol_version == 1
    assert info.tor_version == "0.4.8.12"
    assert info.supports_safecookie is True


def test_tor_control_client_requires_connection():
    client = TorControlClient(
        connection=FakeConnection()
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        client.protocol_info()


def test_tor_control_client_rejects_second_protocol_info():
    connection = FakeConnection(
        lines=[
            "250-PROTOCOLINFO 1",
            "250-AUTH METHODS=SAFECOOKIE",
            "250 OK",
        ]
    )

    client = TorControlClient(
        connection=connection
    )

    client.connect()
    client.protocol_info()

    with pytest.raises(
        TorControlProtocolError
    ):
        client.protocol_info()

    assert connection.sent == [
        "PROTOCOLINFO 1",
    ]


def test_tor_control_client_skips_async_event():
    connection = FakeConnection(
        lines=[
            "650 CIRC 18 BUILT",
            "250-PROTOCOLINFO 1",
            "250-AUTH METHODS=SAFECOOKIE",
            "250 OK",
        ]
    )

    events = []

    client = TorControlClient(
        connection=connection
    )

    client.subscribe_events(
        events.append
    )

    client.connect()

    info = client.protocol_info()

    assert info.protocol_version == 1

    assert len(events) == 1
    assert events[0].status == 650
    assert events[0].message == (
        "CIRC 18 BUILT"
    )


def test_tor_control_client_skips_multiple_async_events():
    connection = FakeConnection(
        lines=[
            "650 CIRC 18 BUILT",
            "650 STREAM 10 SUCCEEDED",
            "250-PROTOCOLINFO 1",
            "250-AUTH METHODS=SAFECOOKIE",
            "250 OK",
        ]
    )

    events = []

    client = TorControlClient(
        connection=connection
    )

    client.subscribe_events(
        events.append
    )

    client.connect()
    client.protocol_info()

    assert [
        event.message
        for event in events
    ] == [
        "CIRC 18 BUILT",
        "STREAM 10 SUCCEEDED",
    ]


def test_tor_control_client_unsubscribes_event_listener():
    connection = FakeConnection(
        lines=[
            "650 CIRC 18 BUILT",
            "250-PROTOCOLINFO 1",
            "250-AUTH METHODS=SAFECOOKIE",
            "250 OK",
        ]
    )

    events = []

    client = TorControlClient(
        connection=connection
    )

    client.subscribe_events(
        events.append
    )

    client.unsubscribe_events(
        events.append
    )

    client.connect()
    client.protocol_info()

    assert events == []


def test_tor_control_client_unsubscribes_event_listener():
    connection = FakeConnection(
        lines=[
            "650 CIRC 18 BUILT",
            "250-PROTOCOLINFO 1",
            "250-AUTH METHODS=SAFECOOKIE",
            "250 OK",
        ]
    )

    events = []
    listener = events.append

    client = TorControlClient(
        connection=connection
    )

    client.subscribe_events(
        listener
    )

    client.unsubscribe_events(
        listener
    )

    client.connect()
    client.protocol_info()

    assert events == []


def test_tor_control_client_propagates_protocol_info_error():
    connection = FakeConnection(
        lines=[
            "514 Authentication required",
        ]
    )

    client = TorControlClient(
        connection=connection
    )

    client.connect()

    with pytest.raises(
        TorControlProtocolError
    ):
        client.protocol_info()


def test_tor_control_client_uses_injected_reply_parser():
    connection = FakeConnection(
        lines=[
            "250-PROTOCOLINFO 1",
            "250-AUTH METHODS=SAFECOOKIE",
            "250 OK",
        ]
    )

    parser = TorReplyParser()

    client = TorControlClient(
        connection=connection,
        reply_parser=parser,
    )

    assert client.reply_parser is parser


def test_tor_control_client_requests_auth_challenge():
    client_nonce = b"A" * 32
    server_hash = b"B" * 32
    server_nonce = b"C" * 32

    connection = FakeConnection(
        lines=[
            (
                "250 AUTHCHALLENGE "
                f"SERVERHASH={server_hash.hex()} "
                f"SERVERNONCE={server_nonce.hex()}"
            ),
        ]
    )

    client = TorControlClient(
        connection=connection
    )

    client.connect()

    challenge = client.auth_challenge(
        client_nonce
    )

    assert connection.sent == [
        (
            "AUTHCHALLENGE SAFECOOKIE "
            f"{client_nonce.hex().upper()}"
        ),
    ]

    assert challenge.client_nonce == (
        client_nonce
    )

    assert challenge.server_hash == (
        server_hash
    )


def test_tor_control_client_authenticates_hash():
    connection = FakeConnection(
        lines=[
            (
                "250 AUTHCHALLENGE "
                f"SERVERHASH={'B' * 64} "
                f"SERVERNONCE={'C' * 64}"
            ),
            "250 OK",
        ]
    )

    client = TorControlClient(
        connection=connection
    )

    client.connect()

    client.auth_challenge(
        b"A" * 32
    )

    client_hash = b"D" * 32

    client.authenticate_safecookie_hash(
        client_hash
    )

    assert connection.sent[-1] == (
        "AUTHENTICATE "
        f"{client_hash.hex().upper()}"
    )

    assert client.authenticated is True


def test_tor_control_client_closes_on_authentication_failure():
    connection = FakeConnection(
        lines=[
            (
                "250 AUTHCHALLENGE "
                f"SERVERHASH={'B' * 64} "
                f"SERVERNONCE={'C' * 64}"
            ),
            "515 Bad authentication",
        ]
    )

    client = TorControlClient(
        connection=connection
    )

    client.connect()

    client.auth_challenge(
        b"A" * 32
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        client.authenticate_safecookie_hash(
            b"D" * 32
        )

    assert client.connected is False
    assert client.authenticated is False
    assert connection.closed is True



def test_tor_control_client_rejects_second_auth_challenge():
    connection = FakeConnection(
        lines=[
            (
                "250 AUTHCHALLENGE "
                f"SERVERHASH={'B' * 64} "
                f"SERVERNONCE={'C' * 64}"
            ),
        ]
    )

    client = TorControlClient(
        connection=connection
    )

    client.connect()

    client.auth_challenge(
        b"A" * 32
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        client.auth_challenge(
            b"D" * 32
        )


def authenticate_fake_client(
    client,
):
    client._authenticated = True



def test_tor_control_client_reads_get_info():
    connection = FakeConnection(
        lines=[
            "250-version=0.4.8.12",
            (
                "250-status/bootstrap-phase="
                'NOTICE BOOTSTRAP PROGRESS=100 '
                'TAG=done SUMMARY="Done"'
            ),
            "250 OK",
        ]
    )

    client = TorControlClient(
        connection=connection
    )

    client.connect()
    authenticate_fake_client(client)

    values = client.get_info(
        "version",
        "status/bootstrap-phase",
    )

    assert connection.sent == [
        (
            "GETINFO version "
            "status/bootstrap-phase"
        ),
    ]

    assert values["version"] == (
        "0.4.8.12"
    )

    assert (
        values["status/bootstrap-phase"]
        ==
        (
            "NOTICE BOOTSTRAP "
            "PROGRESS=100 TAG=done "
            'SUMMARY="Done"'
        )
    )


def test_tor_control_client_reads_multiline_get_info():
    connection = FakeConnection(
        lines=[
            "250+circuit-status=",
            (
                "18 BUILT "
                "$AAAA~Guard,$BBBB~Middle "
                "PURPOSE=GENERAL"
            ),
            (
                "19 LAUNCHED "
                "PURPOSE=GENERAL"
            ),
            ".",
            "250 OK",
        ]
    )

    client = TorControlClient(
        connection=connection
    )

    client.connect()
    authenticate_fake_client(client)

    values = client.get_info(
        "circuit-status"
    )

    assert values[
        "circuit-status"
    ].splitlines()[0].startswith(
        "18 BUILT"
    )


def test_tor_control_client_rejects_get_info_before_authentication():
    client = TorControlClient(
        connection=FakeConnection()
    )

    client.connect()

    with pytest.raises(
        TorControlSecurityError
    ):
        client.get_info(
            "version"
        )



@pytest.mark.parametrize(
    "key",
    [
        "",
        "version status",
        "version\nSIGNAL NEWNYM",
        "version\r\nQUIT",
    ],
)
def test_tor_control_client_rejects_invalid_get_info_key(
    key,
):
    client = TorControlClient(
        connection=FakeConnection()
    )

    client.connect()
    authenticate_fake_client(client)

    with pytest.raises(
        TorControlProtocolError
    ):
        client.get_info(
            key
        )

from garlicsmtp.tor.onion_service_manager import (
    OnionServiceManager,
)


class FakeClient:

    def __init__(self):
        self.calls = []
        self.connected = False
        self.closed = False

    def connect(self):
        self.connected = True

    def close(self):
        self.connected = False
        self.closed = True

    def add_onion(
        self,
        *,
        key,
        virtual_port,
        target_host,
        target_port,
    ):
        self.calls.append(
            {
                "key": key,
                "virtual_port": virtual_port,
                "target_host": target_host,
                "target_port": target_port,
            }
        )

        return type(
            "OnionService",
            (),
            {
                "service_id": "a" * 56,
                "private_key": (
                    "ED25519-V3:test-private-key"
                ),
            },
        )()

class FakeAuthenticator:

    def __init__(self):
        self.calls = 0

    def authenticate(self):
        self.calls += 1

def test_onion_service_manager_creates_and_persists_identity(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "onion-service.key"
    )

    client = FakeClient()

    manager = OnionServiceManager(
        client=client,
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    hostname = manager.ensure_service()

    assert hostname == (
        ("a" * 56)
        + ".onion"
    )

    assert client.calls == [
        {
            "key": "NEW:ED25519-V3",
            "virtual_port": 25,
            "target_host": "127.0.0.1",
            "target_port": 2525,
        }
    ]

    assert identity_file.read_text(
        encoding="utf-8"
    ) == (
        "ED25519-V3:test-private-key"
    )


def test_onion_service_manager_reuses_existing_identity(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "onion-service.key"
    )

    identity_file.write_text(
        "ED25519-V3:existing-private-key",
        encoding="utf-8",
    )

    client = FakeClient()

    manager = OnionServiceManager(
        client=client,
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    hostname = manager.ensure_service()

    assert hostname == (
        ("a" * 56)
        + ".onion"
    )

    assert client.calls == [
        {
            "key": (
                "ED25519-V3:"
                "existing-private-key"
            ),
            "virtual_port": 25,
            "target_host": "127.0.0.1",
            "target_port": 2525,
        }
    ]

    assert identity_file.read_text(
        encoding="utf-8"
    ) == (
        "ED25519-V3:"
        "existing-private-key"
    )


def test_onion_service_manager_starts_service(
    tmp_path,
):
    client = FakeClient()
    authenticator = FakeAuthenticator()

    manager = OnionServiceManager(
        client=client,
        authenticator=authenticator,
        identity_file=(
            tmp_path
            / "onion-service.key"
        ),
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    manager.start()

    assert client.connected is True
    assert authenticator.calls == 1

    assert manager.hostname == (
        ("a" * 56)
        + ".onion"
    )

    assert len(client.calls) == 1


def test_onion_service_manager_stops_service(
    tmp_path,
):
    client = FakeClient()
    authenticator = FakeAuthenticator()

    manager = OnionServiceManager(
        client=client,
        authenticator=authenticator,
        identity_file=(
            tmp_path
            / "onion-service.key"
        ),
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    manager.start()

    assert client.connected is True

    manager.stop()

    assert client.connected is False
    assert client.closed is True


def test_onion_service_manager_publishes_hostname(
    tmp_path,
):
    client = FakeClient()
    authenticator = FakeAuthenticator()

    hostnames = []

    manager = OnionServiceManager(
        client=client,
        authenticator=authenticator,
        identity_file=(
            tmp_path
            / "onion-service.key"
        ),
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
        hostname_callback=(
            hostnames.append
        ),
    )

    manager.start()

    assert hostnames == [
        ("a" * 56) + ".onion"
    ]
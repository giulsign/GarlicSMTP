from garlicsmtp.security.auth import (
    MemoryAuthenticator,
    RejectingAuthenticator,
)


def test_memory_authenticator_accepts_valid_credentials():

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    assert authenticator.authenticate(
        "alice",
        "secret",
    ) is True


def test_memory_authenticator_rejects_invalid_password():

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    assert authenticator.authenticate(
        "alice",
        "wrong",
    ) is False


def test_memory_authenticator_rejects_unknown_user():

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    assert authenticator.authenticate(
        "bob",
        "secret",
    ) is False


def test_memory_authenticator_can_add_user():

    authenticator = MemoryAuthenticator()

    authenticator.add_user(
        "alice",
        "secret",
    )

    assert authenticator.authenticate(
        "alice",
        "secret",
    ) is True


def test_rejecting_authenticator_rejects_everything():

    authenticator = RejectingAuthenticator()

    assert authenticator.authenticate(
        "alice",
        "secret",
    ) is False
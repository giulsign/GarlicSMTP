from garlicsmtp.imap import (
    IMAPSession,
    IMAPSessionState,
)


def test_imap_session_initial_state():

    session = IMAPSession()

    assert session.state is (
        IMAPSessionState.NOT_AUTHENTICATED
    )

    assert session.username is None
    assert session.selected_mailbox is None


def test_imap_session_authenticates():

    session = IMAPSession()

    session.authenticate(
        "alice"
    )

    assert session.state is (
        IMAPSessionState.AUTHENTICATED
    )

    assert session.username == "alice"


def test_imap_session_selects_mailbox():

    session = IMAPSession()

    session.authenticate(
        "alice"
    )

    session.select(
        "INBOX"
    )

    assert session.state is (
        IMAPSessionState.SELECTED
    )

    assert (
        session.selected_mailbox
        == "INBOX"
    )


def test_imap_session_logout():

    session = IMAPSession()

    session.authenticate(
        "alice"
    )

    session.select(
        "INBOX"
    )

    session.logout()

    assert session.state is (
        IMAPSessionState.LOGOUT
    )

    assert session.selected_mailbox is None


def test_imap_session_closes_selected_mailbox():
    session = IMAPSession()

    session.authenticate(
        "bob@test.onion"
    )

    session.select(
        "bob@test.onion"
    )

    session.close_mailbox()

    assert session.state is (
        IMAPSessionState.AUTHENTICATED
    )

    assert session.selected_mailbox is None


def test_imap_session_cannot_close_without_selected_mailbox():
    session = IMAPSession()

    session.authenticate(
        "bob@test.onion"
    )

    try:
        session.close_mailbox()
    except RuntimeError as exc:
        assert str(exc) == (
            "Mailbox not selected"
        )
    else:
        raise AssertionError(
            "RuntimeError not raised"
        )
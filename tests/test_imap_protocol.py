# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.imap import (
    IMAPProtocol,
    IMAPSessionState,
    IMAPSession,
)
from garlicsmtp.security.auth import (
    MemoryAuthenticator,
)
from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
    Metadata,
)
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.storage.serializer import (
    MessageSerializer,
)
from garlicsmtp.imap import (
    IMAPLiteralResponse,
)
from datetime import timedelta

from garlicsmtp.imap.append import (
    IMAPAppendParser,
)
from garlicsmtp.imap.command_result import (
    IMAPCommandAction,
)


def serialize(replies):

    return [
        reply.serialize()
        for reply in replies
    ]


def test_imap_greeting():

    protocol = IMAPProtocol()

    assert serialize(
        protocol.greeting()
    ) == [
        "* OK GarlicSMTP IMAP ready\r\n"
    ]


def test_imap_capability():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            "A001 CAPABILITY"
        )
    )

    assert replies == [
        (
            "* CAPABILITY "
            "IMAP4rev1 "
            "UIDPLUS "
            "UNSELECT "
            "MOVE "
            "NAMESPACE "
            "ID "
            "ENABLE "
            "IDLE\r\n"
        ),
        (
            "A001 OK "
            "CAPABILITY completed\r\n"
        ),
    ]


def test_imap_noop():

    protocol = IMAPProtocol()

    replies = serialize(

        protocol.execute(
            "A001 NOOP"
        )

    )

    assert replies == [

        "A001 OK NOOP completed\r\n"

    ]


def test_check_selected_mailbox(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 CHECK"
        )
    )

    assert replies == [
        "A003 OK CHECK completed\r\n",
    ]

    assert protocol.session.state is (
        IMAPSessionState.SELECTED
    )

    assert (
        protocol.session.selected_mailbox
        == "bob@test.onion"
    )


def test_check_requires_selected_mailbox():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        )
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 CHECK"
        )
    )

    assert replies == [
        (
            "A002 NO "
            "Mailbox not selected\r\n"
        ),
    ]


def test_check_rejects_arguments(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 CHECK unexpected"
        )
    )

    assert replies == [
        (
            "A003 BAD CHECK does not "
            "accept arguments\r\n"
        ),
    ]

    assert protocol.session.state is (
        IMAPSessionState.SELECTED
    )


def test_imap_logout():

    protocol = IMAPProtocol()

    replies = serialize(

        protocol.execute(
            "A001 LOGOUT"
        )

    )

    assert replies == [

        "* BYE Logging out\r\n",

        "A001 OK LOGOUT completed\r\n",

    ]

    assert protocol.session.state is (

        IMAPSessionState.LOGOUT

    )


def test_imap_unknown_command():

    protocol = IMAPProtocol()

    replies = serialize(

        protocol.execute(
            "A001 BANANA"
        )

    )

    assert replies == [

        "A001 BAD Unsupported command BANANA\r\n"

    ]


def test_imap_parse_error():

    protocol = IMAPProtocol()

    replies = serialize(

        protocol.execute(
            "A001"
        )

    )

    assert replies == [

        "* BAD IMAP command requires tag and name\r\n"

    ]


def test_imap_login():

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
    )

    replies = serialize(
        protocol.execute(
            "A001 LOGIN alice secret"
        )
    )

    assert replies == [
        "A001 OK LOGIN completed\r\n"
    ]

    assert protocol.session.state is (
        IMAPSessionState.AUTHENTICATED
    )

    assert protocol.session.username == "alice"


def test_imap_login_rejects_invalid_credentials():

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
    )

    replies = serialize(
        protocol.execute(
            "A001 LOGIN alice wrong"
        )
    )

    assert replies == [
        "A001 NO Authentication failed\r\n"
    ]

    assert protocol.session.state is (
        IMAPSessionState.NOT_AUTHENTICATED
    )


def test_imap_login_rejects_missing_arguments():

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator()
    )

    replies = serialize(
        protocol.execute(
            "A001 LOGIN alice"
        )
    )

    assert replies == [
        (
            "A001 BAD LOGIN requires "
            "username and password\r\n"
        )
    ]


def test_imap_login_rejects_second_login():

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 LOGIN alice secret"
        )
    )

    assert replies == [
        "A002 BAD Already authenticated\r\n"
    ]


def test_imap_default_authenticator_rejects_login():

    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            "A001 LOGIN alice secret"
        )
    )

    assert replies == [
        "A001 NO Authentication failed\r\n"
    ]


def test_imap_list_requires_authentication():

    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            'A001 LIST "" "*"'
        )
    )

    assert replies == [
        "A001 NO Authentication required\r\n"
    ]


def test_imap_list_returns_mailboxes(
    message,
):

    store = MessageStore()

    store.save(
        "bob@test.onion",
        message,
    )

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 LIST "" "*"'
        )
    )

    assert replies == [
        (
            '* LIST () "/" '
            '"bob@test.onion"\r\n'
        ),
        "A002 OK LIST completed\r\n",
    ]


def test_imap_select_mailbox(
    message,
):

    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        first.id,
        {
            "\\Seen",
        },
    )

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 SELECT "bob@test.onion"'
        )
    )

    assert replies == [
        (
            "* FLAGS "
            "(\\Seen \\Answered \\Flagged "
            "\\Deleted \\Draft)\r\n"
        ),
        (
            "* OK [PERMANENTFLAGS "
            "(\\Seen \\Answered \\Flagged "
            "\\Deleted \\Draft)] "
            "Permanent flags\r\n"
        ),
        "* 2 EXISTS\r\n",
        "* 0 RECENT\r\n",
        (
            "* OK [UIDVALIDITY 1] "
            "UID validity\r\n"
        ),
        (
            "* OK [UIDNEXT 3] "
            "Predicted next UID\r\n"
        ),
        (
            f"* OK [UNSEEN {second.uid}] "
            "First unseen message\r\n"
        ),
        (
            "A002 OK [READ-WRITE] "
            "SELECT completed\r\n"
        ),
    ]

    assert protocol.session.state is (
        IMAPSessionState.SELECTED
    )

    assert (
        protocol.session.selected_mailbox
        == "bob@test.onion"
    )


def test_imap_examine_mailbox(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        first.id,
        {
            "\\Seen",
        },
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 EXAMINE "bob@test.onion"'
        )
    )

    assert replies == [
        (
            "* FLAGS "
            "(\\Seen \\Answered \\Flagged "
            "\\Deleted \\Draft)\r\n"
        ),
        (
            "* OK [PERMANENTFLAGS "
            "(\\Seen \\Answered \\Flagged "
            "\\Deleted \\Draft)] "
            "Permanent flags\r\n"
        ),
        "* 2 EXISTS\r\n",
        "* 0 RECENT\r\n",
        (
            "* OK [UIDVALIDITY 1] "
            "UID validity\r\n"
        ),
        (
            "* OK [UIDNEXT 3] "
            "Predicted next UID\r\n"
        ),
        (
            f"* OK [UNSEEN {second.uid}] "
            "First unseen message\r\n"
        ),
        (
            "A002 OK [READ-ONLY] "
            "EXAMINE completed\r\n"
        ),
    ]

    assert protocol.session.state is (
        IMAPSessionState.SELECTED
    )

    assert (
        protocol.session.selected_mailbox
        == "bob@test.onion"
    )

def test_imap_examine_rejects_uid_store(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 EXAMINE "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID STORE {entry.uid} "
                "+FLAGS (\\Seen)"
            )
        )
    )

    assert replies == [
        "A003 NO Mailbox is read-only\r\n"
    ]

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_examine_rejects_expunge(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {entry.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    protocol.execute(
        'A004 EXAMINE "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A005 EXPUNGE"
        )
    )

    assert replies == [
        "A005 NO Mailbox is read-only\r\n"
    ]

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None


def test_imap_select_rejects_missing_mailbox():

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 SELECT missing"
        )
    )

    assert replies == [
        "A002 NO Mailbox not found\r\n"
    ]

def test_status_returns_mailbox_values(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        first.id,
        {
            "\\Seen",
        },
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            (
                'A002 STATUS "bob@test.onion" '
                "(MESSAGES UIDNEXT UNSEEN)"
            )
        )
    )

    assert replies == [
        (
            '* STATUS "bob@test.onion" '
            "(MESSAGES 2 UIDNEXT 3 UNSEEN 1)"
            "\r\n"
        ),
        (
            "A002 OK "
            "STATUS completed\r\n"
        ),
    ]

    assert protocol.session.state is (
        IMAPSessionState.AUTHENTICATED
    )

    assert (
        protocol.session.selected_mailbox
        is None
    )


def test_status_preserves_requested_item_order(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            (
                'A002 STATUS "bob@test.onion" '
                "(UNSEEN MESSAGES)"
            )
        )
    )

    assert replies == [
        (
            '* STATUS "bob@test.onion" '
            "(UNSEEN 1 MESSAGES 1)\r\n"
        ),
        (
            "A002 OK "
            "STATUS completed\r\n"
        ),
    ]


def test_status_does_not_change_selected_mailbox(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 STATUS "bob@test.onion" '
                "(MESSAGES UNSEEN)"
            )
        )
    )

    assert replies == [
        (
            '* STATUS "bob@test.onion" '
            "(MESSAGES 1 UNSEEN 1)\r\n"
        ),
        (
            "A003 OK "
            "STATUS completed\r\n"
        ),
    ]

    assert protocol.session.state is (
        IMAPSessionState.SELECTED
    )

    assert (
        protocol.session.selected_mailbox
        == "bob@test.onion"
    )


def test_status_requires_authentication():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            (
                'A001 STATUS "bob@test.onion" '
                "(MESSAGES)"
            )
        )
    )

    assert replies == [
        (
            "A001 NO "
            "Authentication required\r\n"
        ),
    ]


def test_status_rejects_missing_items():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        )
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 STATUS "bob@test.onion"'
        )
    )

    assert replies == [
        (
            "A002 BAD STATUS requires "
            "mailbox and data items\r\n"
        ),
    ]


def test_status_rejects_unsupported_item(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            (
                'A002 STATUS "bob@test.onion" '
                "(MESSAGES RECENT)"
            )
        )
    )

    assert replies == [
        (
            "A002 BAD Unsupported "
            "STATUS item RECENT\r\n"
        ),
    ]


def test_status_rejects_missing_mailbox():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        )
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            (
                'A002 STATUS "missing" '
                "(MESSAGES)"
            )
        )
    )

    assert replies == [
        (
            "A002 NO "
            "Mailbox not found\r\n"
        ),
    ]

def test_imap_uid_fetch_requires_selected_mailbox():

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            (
                "A002 UID FETCH 1 "
                "(UID FLAGS RFC822.SIZE)"
            )
        )
    )

    assert replies == [
        "A002 NO Mailbox not selected\r\n"
    ]



def test_imap_uid_fetch_returns_message_metadata(
    message,
):

    message.headers.fields[
        "Subject"
    ] = "First IMAP fetch"

    message.body = "Hello through IMAP"

    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Seen",
        },
    )

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    serialized = MessageSerializer.to_rfc5322(
        message
    )

    expected_size = len(
        serialized.encode("utf-8")
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID FETCH 1 "
                "(UID FLAGS RFC822.SIZE)"
            )
        )
    )

    assert replies == [
        (
            "* 1 FETCH "
            f"(UID 1 FLAGS (\\Seen) "
            f"RFC822.SIZE {expected_size})\r\n"
        ),
        "A003 OK UID FETCH completed\r\n",
    ]



def test_imap_uid_fetch_missing_uid_returns_only_completion(
    message,
):

    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UID FETCH 99 (UID FLAGS)"
        )
    )

    assert replies == [
        "A003 OK UID FETCH completed\r\n"
    ]


def test_imap_uid_fetch_rejects_unsupported_item(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID FETCH 1 "
                "(BODYSTRUCTURE)"
            )
        )
    )

    assert replies == [
        (
            "A003 BAD Unsupported FETCH "
            "item BODYSTRUCTURE\r\n"
        )
    ]


def test_imap_uid_fetch_returns_body_literal(
    message,
):

    message.headers.fields[
        "Subject"
    ] = "Literal message"

    message.body = "Hello literal"

    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            "A003 UID FETCH 1 "
            "(UID FLAGS BODY[])"
        )
    )

    assert len(replies) == 2

    literal = replies[0]

    assert isinstance(
        literal,
        IMAPLiteralResponse,
    )

    expected = (
        MessageSerializer.to_rfc5322(
            message
        ).encode("utf-8")
    )

    assert literal.prefix == (
        "* 1 FETCH (UID 1 FLAGS (\\Seen) BODY[]"
    )

    assert literal.content == expected

    assert replies[1].serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )


def test_imap_body_fetch_marks_message_seen(
    message,
):

    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        "A003 UID FETCH 1 (BODY[])"
    )

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert "\\Seen" in restored.flags


def test_imap_body_peek_does_not_mark_message_seen(
    message,
):

    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            "A003 UID FETCH 1 "
            "(BODY.PEEK[])"
        )
    )

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert "\\Seen" not in restored.flags


def test_imap_rfc822_text_marks_message_seen(
    message,
):

    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            "A003 UID FETCH 1 "
            "(RFC822.TEXT)"
        )
    )

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert "\\Seen" in restored.flags


def test_imap_rfc822_header_does_not_mark_seen(
    message,
):

    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    authenticator = MemoryAuthenticator(
        {
            "alice": "secret",
        }
    )

    protocol = IMAPProtocol(
        authenticator=authenticator,
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            "A003 UID FETCH 1 "
            "(RFC822.HEADER)"
        )
    )

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert "\\Seen" not in restored.flags


def test_imap_uid_store_adds_flags(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID STORE 1 "
                "+FLAGS (\\Seen \\Flagged)"
            )
        )
    )

    assert replies == [
        (
            "* 1 FETCH "
            "(UID 1 FLAGS "
            "(\\Flagged \\Seen))\r\n"
        ),
        "A003 OK UID STORE completed\r\n",
    ]

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert restored.flags == {
        "\\Seen",
        "\\Flagged",
    }


def test_imap_uid_store_removes_flags(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.set_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Seen",
            "\\Flagged",
        },
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID STORE 1 "
                "-FLAGS (\\Flagged)"
            )
        )
    )

    assert replies == [
        (
            "* 1 FETCH "
            "(UID 1 FLAGS (\\Seen))\r\n"
        ),
        "A003 OK UID STORE completed\r\n",
    ]

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert restored.flags == {
        "\\Seen",
    }


def test_imap_uid_store_replaces_flags(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.set_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Seen",
        },
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID STORE 1 "
                "FLAGS (\\Draft)"
            )
        )
    )

    assert replies == [
        (
            "* 1 FETCH "
            "(UID 1 FLAGS (\\Draft))\r\n"
        ),
        "A003 OK UID STORE completed\r\n",
    ]

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert restored.flags == {
        "\\Draft",
    }


def test_imap_uid_store_silent_does_not_return_fetch(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID STORE 1 "
                "+FLAGS.SILENT (\\Seen)"
            )
        )
    )

    assert replies == [
        "A003 OK UID STORE completed\r\n"
    ]

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert restored.flags == {
        "\\Seen",
    }


def test_imap_uid_store_requires_selected_mailbox():

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        )
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            (
                "A002 UID STORE 1 "
                "+FLAGS (\\Seen)"
            )
        )
    )

    assert replies == [
        "A002 NO Mailbox not selected\r\n"
    ]


def test_imap_uid_copy_copies_message_and_flags(
    message,
):
    store = MessageStore()

    source = store.save_entry(
        "source@test.onion",
        message,
    )

    store.set_flags(
        "source@test.onion",
        source.id,
        {
            "\\Seen",
            "\\Flagged",
        },
    )

    destination_seed = store.save_entry(
        "destination@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID COPY 1 "
                '"destination@test.onion"'
            )
        )
    )

    destination_uid = (
        destination_seed.uid + 1
    )

    assert replies == [
        (
            "A003 OK [COPYUID 1 "
            f"{source.uid} "
            f"{destination_uid}] "
            "UID COPY completed\r\n"
        ),
    ]

    source_entries = store.list_entries(
        "source@test.onion"
    )

    assert [
        entry.id
        for entry in source_entries
    ] == [
        source.id,
    ]

    destination_entries = (
        store.list_entries(
            "destination@test.onion"
        )
    )

    assert len(destination_entries) == 2

    copied = destination_entries[-1]

    assert copied.id != source.id
    assert copied.uid == destination_uid
    assert copied.flags == {
        "\\Seen",
        "\\Flagged",
    }

    assert (
        copied.internal_date
        == source.internal_date
    )


def test_imap_uid_copy_requires_existing_destination(
    message,
):
    store = MessageStore()

    store.save_entry(
        "source@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID COPY 1 "
                '"missing@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 NO Destination "
            "mailbox not found\r\n"
        ),
    ]


def test_imap_uid_copy_returns_no_for_missing_uid(
    message,
):
    store = MessageStore()

    store.save_entry(
        "source@test.onion",
        message,
    )

    store.save_entry(
        "destination@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID COPY 999 "
                '"destination@test.onion"'
            )
        )
    )

    assert replies == [
        "A003 NO Message not found\r\n",
    ]


def test_imap_uid_copy_rejects_invalid_uid(
    message,
):
    store = MessageStore()

    store.save_entry(
        "source@test.onion",
        message,
    )

    store.save_entry(
        "destination@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID COPY banana "
                '"destination@test.onion"'
            )
        )
    )

    assert replies == [
        "A003 BAD Invalid UID\r\n",
    ]


def test_imap_uid_copy_rejects_missing_destination(
    message,
):
    store = MessageStore()

    store.save_entry(
        "source@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UID COPY 1"
        )
    )

    assert replies == [
        (
            "A003 BAD UID COPY requires "
            "UID and destination mailbox\r\n"
        ),
    ]


def test_imap_uid_search_all(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UID SEARCH ALL"
        )
    )

    assert replies == [
        "* SEARCH 1 2\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_unseen(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        first.id,
        {
            "\\Seen",
        },
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UID SEARCH UNSEEN"
        )
    )

    assert replies == [
        "* SEARCH 2\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_returns_empty_result(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Seen",
        },
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UID SEARCH UNSEEN"
        )
    )

    assert replies == [
        "* SEARCH\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_requires_selected_mailbox():

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        )
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 UID SEARCH ALL"
        )
    )

    assert replies == [
        "A002 NO Mailbox not selected\r\n"
    ]


def test_imap_uid_search_subject(
    message,
):
    first_message = message

    first_message.headers.fields[
        "Subject"
    ] = "GarlicSMTP news"

    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        first_message,
    )

    second_message = MailMessage(
        envelope=Envelope(
            sender="carol@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Other message",
            }
        ),
        metadata=Metadata(),
        body="Different content",
    )

    store.save_entry(
        "bob@test.onion",
        second_message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 UID SEARCH '
                'SUBJECT "garlicsmtp"'
            )
        )
    )

    assert replies == [
        "* SEARCH 1\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_text(
    message,
):
    message.body = (
        "GarlicSMTP over Tor works"
    )

    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 UID SEARCH '
                'TEXT "over Tor"'
            )
        )
    )

    assert replies == [
        "* SEARCH 1\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_move_moves_message_and_emits_expunge(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "source@test.onion",
        message,
    )

    moved_source = store.save_entry(
        "source@test.onion",
        message,
    )

    third = store.save_entry(
        "source@test.onion",
        message,
    )

    store.set_flags(
        "source@test.onion",
        moved_source.id,
        {
            "\\Seen",
            "\\Flagged",
        },
    )

    destination_seed = store.save_entry(
        "destination@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID MOVE "
                f"{moved_source.uid} "
                '"destination@test.onion"'
            )
        )
    )

    destination_uid = (
        destination_seed.uid + 1
    )

    assert replies == [
        "* 2 EXPUNGE\r\n",
        (
            "A003 OK [COPYUID 1 "
            f"{moved_source.uid} "
            f"{destination_uid}] "
            "UID MOVE completed\r\n"
        ),
    ]

    source_entries = store.list_entries(
        "source@test.onion"
    )

    assert [
        entry.id
        for entry in source_entries
    ] == [
        first.id,
        third.id,
    ]

    destination_entries = (
        store.list_entries(
            "destination@test.onion"
        )
    )

    assert len(destination_entries) == 2

    moved = destination_entries[-1]

    assert moved.id != moved_source.id
    assert moved.uid == destination_uid

    assert moved.flags == {
        "\\Seen",
        "\\Flagged",
    }

    assert (
        moved.internal_date
        == moved_source.internal_date
    )

    assert protocol.session.state is (
        IMAPSessionState.SELECTED
    )

    assert (
        protocol.session.selected_mailbox
        == "source@test.onion"
    )


def test_imap_uid_move_uses_current_sequence_number(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "source@test.onion",
        message,
    )

    second = store.save_entry(
        "source@test.onion",
        message,
    )

    third = store.save_entry(
        "source@test.onion",
        message,
    )

    store.save_entry(
        "destination@test.onion",
        message,
    )

    store.delete_entry(
        "source@test.onion",
        first.id,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID MOVE "
                f"{third.uid} "
                '"destination@test.onion"'
            )
        )
    )

    assert replies[0] == (
        "* 2 EXPUNGE\r\n"
    )

    remaining = store.list_entries(
        "source@test.onion"
    )

    assert [
        entry.id
        for entry in remaining
    ] == [
        second.id,
    ]


def test_imap_uid_move_requires_existing_destination(
    message,
):
    store = MessageStore()

    store.save_entry(
        "source@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID MOVE 1 "
                '"missing@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 NO Destination "
            "mailbox not found\r\n"
        ),
    ]

    assert len(
        store.list_entries(
            "source@test.onion"
        )
    ) == 1


def test_imap_uid_move_rejects_selected_mailbox_as_destination(
    message,
):
    store = MessageStore()

    source = store.save_entry(
        "source@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID MOVE 1 "
                '"source@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 NO Destination mailbox "
            "must differ from selected mailbox\r\n"
        ),
    ]

    restored = store.get_entry(
        "source@test.onion",
        source.id,
    )

    assert restored is not None


def test_imap_uid_move_returns_no_for_missing_uid(
    message,
):
    store = MessageStore()

    store.save_entry(
        "source@test.onion",
        message,
    )

    store.save_entry(
        "destination@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID MOVE 999 "
                '"destination@test.onion"'
            )
        )
    )

    assert replies == [
        "A003 NO Message not found\r\n",
    ]

    assert len(
        store.list_entries(
            "source@test.onion"
        )
    ) == 1

    assert len(
        store.list_entries(
            "destination@test.onion"
        )
    ) == 1


def test_imap_uid_move_rejects_invalid_uid(
    message,
):
    store = MessageStore()

    store.save_entry(
        "source@test.onion",
        message,
    )

    store.save_entry(
        "destination@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID MOVE banana "
                '"destination@test.onion"'
            )
        )
    )

    assert replies == [
        "A003 BAD Invalid UID\r\n",
    ]


def test_imap_uid_move_rejects_missing_destination(
    message,
):
    store = MessageStore()

    store.save_entry(
        "source@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "source@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UID MOVE 1"
        )
    )

    assert replies == [
        (
            "A003 BAD UID MOVE requires "
            "UID and destination mailbox\r\n"
        ),
    ]


def test_expunge_removes_deleted_messages(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        second.id,
        {"\\Deleted"},
    )

    store.add_flags(
        "bob@test.onion",
        third.id,
        {"\\Deleted"},
    )

    session = IMAPSession()
    session.authenticate(
        "bob@test.onion"
    )
    session.select(
        "bob@test.onion"
    )

    protocol = IMAPProtocol(
        session=session,
        store=store,
    )

    responses = protocol.execute(
        "A001 EXPUNGE"
    )

    assert [
        response.text
        for response in responses
    ] == [
        "* 2 EXPUNGE",
        "* 2 EXPUNGE",
        "A001 OK EXPUNGE completed",
    ]

    remaining = store.list_entries(
        "bob@test.onion"
    )

    assert [
        entry.id
        for entry in remaining
    ] == [
        first.id,
    ]


def test_expunge_requires_selected_mailbox():
    session = IMAPSession()
    session.authenticate(
        "bob@test.onion"
    )

    protocol = IMAPProtocol(
        session=session,
    )

    responses = protocol.execute(
        "A001 EXPUNGE"
    )

    assert responses[0].text == (
        "A001 NO Mailbox not selected"
    )


def test_expunge_rejects_arguments():
    session = IMAPSession()
    session.authenticate(
        "bob@test.onion"
    )
    session.select(
        "bob@test.onion"
    )

    protocol = IMAPProtocol(
        session=session,
    )

    responses = protocol.execute(
        "A001 EXPUNGE unexpected"
    )

    assert responses[0].text == (
        "A001 BAD "
        "EXPUNGE does not accept arguments"
    )


def test_close_expunges_deleted_messages_without_expunge_replies(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        second.id,
        {
            "\\Deleted",
        },
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 CLOSE"
        )
    )

    assert replies == [
        "A003 OK CLOSE completed\r\n",
    ]

    assert protocol.session.state is (
        IMAPSessionState.AUTHENTICATED
    )

    assert (
        protocol.session.selected_mailbox
        is None
    )

    remaining = store.list_entries(
        "bob@test.onion"
    )

    assert [
        entry.id
        for entry in remaining
    ] == [
        first.id,
        third.id,
    ]


def test_close_preserves_messages_not_marked_deleted(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 CLOSE"
        )
    )

    assert replies == [
        "A003 OK CLOSE completed\r\n",
    ]

    assert [
        entry.id
        for entry in store.list_entries(
            "bob@test.onion"
        )
    ] == [
        first.id,
        second.id,
    ]


def test_close_requires_selected_mailbox():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        )
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 CLOSE"
        )
    )

    assert replies == [
        "A002 NO Mailbox not selected\r\n",
    ]

    assert protocol.session.state is (
        IMAPSessionState.AUTHENTICATED
    )


def test_close_rejects_arguments(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 CLOSE unexpected"
        )
    )

    assert replies == [
        (
            "A003 BAD CLOSE does not "
            "accept arguments\r\n"
        ),
    ]

    assert protocol.session.state is (
        IMAPSessionState.SELECTED
    )

    assert (
        protocol.session.selected_mailbox
        == "bob@test.onion"
    )


def test_unselect_closes_mailbox_without_expunge(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        second.id,
        {
            "\\Deleted",
        },
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UNSELECT"
        )
    )

    assert replies == [
        (
            "A003 OK "
            "UNSELECT completed\r\n"
        ),
    ]

    assert protocol.session.state is (
        IMAPSessionState.AUTHENTICATED
    )

    assert (
        protocol.session.selected_mailbox
        is None
    )

    remaining = store.list_entries(
        "bob@test.onion"
    )

    assert [
        entry.id
        for entry in remaining
    ] == [
        first.id,
        second.id,
    ]

    assert remaining[1].flags == {
        "\\Deleted",
    }


def test_unselect_requires_selected_mailbox():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        )
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 UNSELECT"
        )
    )

    assert replies == [
        (
            "A002 NO "
            "Mailbox not selected\r\n"
        ),
    ]

    assert protocol.session.state is (
        IMAPSessionState.AUTHENTICATED
    )


def test_unselect_rejects_arguments(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Deleted",
        },
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UNSELECT unexpected"
        )
    )

    assert replies == [
        (
            "A003 BAD UNSELECT does not "
            "accept arguments\r\n"
        ),
    ]

    assert protocol.session.state is (
        IMAPSessionState.SELECTED
    )

    assert (
        protocol.session.selected_mailbox
        == "bob@test.onion"
    )

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert restored.flags == {
        "\\Deleted",
    }


def test_unselect_allows_another_mailbox_to_be_selected(
    message,
):
    store = MessageStore()

    store.save_entry(
        "first@test.onion",
        message,
    )

    store.save_entry(
        "second@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "first@test.onion"'
    )

    unselect_replies = serialize(
        protocol.execute(
            "A003 UNSELECT"
        )
    )

    assert unselect_replies == [
        (
            "A003 OK "
            "UNSELECT completed\r\n"
        ),
    ]

    select_replies = serialize(
        protocol.execute(
            'A004 SELECT "second@test.onion"'
        )
    )

    assert select_replies[-1] == (
        "A004 OK [READ-WRITE] "
        "SELECT completed\r\n"
    )

    assert protocol.session.state is (
        IMAPSessionState.SELECTED
    )

    assert (
        protocol.session.selected_mailbox
        == "second@test.onion"
    )

def append_request(
    literal: bytes,
    *,
    mailbox: str = "archive@test.onion",
    options: str = "",
):
    separator = (
        f" {options.strip()}"
        if options.strip()
        else ""
    )

    return IMAPAppendParser.parse(
        (
            f'A100 APPEND "{mailbox}"'
            f"{separator} "
            f"{{{len(literal)}}}"
        )
    )


def test_imap_append_literal(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    literal = (
        b"From: alice@test.onion\r\n"
        b"To: bob@test.onion\r\n"
        b"Subject: APPEND test\r\n"
        b"\r\n"
        b"Stored through IMAP."
    )

    request = append_request(
        literal
    )

    assert serialize(
        protocol.append_literal(
            request,
            literal,
        )
    ) == [
        (
            "A100 OK "
            "[APPENDUID 1 2] "
            "APPEND completed\r\n"
        )
    ]

    mailbox = store.open_mailbox(
        "archive@test.onion"
    )

    entries = mailbox.list_entries()

    assert len(entries) == 2

    appended = entries[1]

    assert appended.uid == 2

    assert appended.message.envelope.sender == (
        "alice@test.onion"
    )

    assert (
        appended.message.envelope.recipients
        == [
            "bob@test.onion",
        ]
    )

    assert appended.message.body == (
        "Stored through IMAP."
    )


def test_imap_multiappend_stores_multiple_messages(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

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

    request = IMAPAppendParser.parse(
        (
            'A100 APPEND '
            '"archive@test.onion" '
            f"{{{len(first_literal)}}} "
            f"{{{len(second_literal)}}}"
        )
    )

    replies = protocol.append_literals(
        request,
        [
            first_literal,
            second_literal,
        ],
    )

    assert serialize(replies) == [
        (
            "A100 OK "
            "[APPENDUID 1 2,3] "
            "APPEND completed\r\n"
        )
    ]

    entries = (
        store.open_mailbox(
            "archive@test.onion"
        )
        .list_entries()
    )

    assert len(entries) == 3

    assert entries[1].uid == 2
    assert entries[1].message.body == (
        "First body"
    )

    assert entries[2].uid == 3
    assert entries[2].message.body == (
        "Second body"
    )


def test_imap_multiappend_preserves_item_metadata(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    first_literal = (
        b"Subject: Seen\r\n"
        b"\r\n"
        b"Seen body"
    )

    second_literal = (
        b"Subject: Draft\r\n"
        b"\r\n"
        b"Draft body"
    )

    request = IMAPAppendParser.parse(
        (
            'A100 APPEND '
            '"archive@test.onion" '
            r"(\Seen) "
            '"15-Jul-2026 18:30:45 +0200" '
            f"{{{len(first_literal)}}} "
            r"(\Draft) "
            '"16-Jul-2026 09:15:00 +0200" '
            f"{{{len(second_literal)}}}"
        )
    )

    replies = protocol.append_literals(
        request,
        [
            first_literal,
            second_literal,
        ],
    )

    assert serialize(replies) == [
        (
            "A100 OK "
            "[APPENDUID 1 2,3] "
            "APPEND completed\r\n"
        )
    ]

    mailbox = store.open_mailbox(
        "archive@test.onion"
    )

    first = mailbox.get_by_uid(2)
    second = mailbox.get_by_uid(3)

    assert first is not None
    assert second is not None

    assert first.flags == {
        "\\Seen",
    }

    assert second.flags == {
        "\\Draft",
    }

    assert first.internal_date.day == 15
    assert second.internal_date.day == 16


def test_imap_multiappend_rejects_literal_count_mismatch(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

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

    request = IMAPAppendParser.parse(
        (
            'A100 APPEND '
            '"archive@test.onion" '
            f"{{{len(first_literal)}}} "
            f"{{{len(second_literal)}}}"
        )
    )

    replies = protocol.append_literals(
        request,
        [
            first_literal,
        ],
    )

    assert serialize(replies) == [
        (
            "A100 BAD "
            "APPEND literal count "
            "does not match\r\n"
        )
    ]

    assert (
        store.open_mailbox(
            "archive@test.onion"
        ).count()
        == 1
    )


def test_imap_multiappend_does_not_store_partial_result(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    valid_literal = (
        b"Subject: Valid\r\n"
        b"\r\n"
        b"Valid body"
    )

    invalid_literal = b""

    request = IMAPAppendParser.parse(
        (
            'A100 APPEND '
            '"archive@test.onion" '
            f"{{{len(valid_literal)}}} "
            "{0}"
        )
    )

    replies = protocol.append_literals(
        request,
        [
            valid_literal,
            invalid_literal,
        ],
    )

    assert serialize(replies) == [
        (
            "A100 NO "
            "APPEND literal is empty\r\n"
        )
    ]

    assert (
        store.open_mailbox(
            "archive@test.onion"
        ).count()
        == 1
    )


def test_imap_append_literal_preserves_metadata(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    literal = (
        b"Subject: Draft\r\n"
        b"\r\n"
        b"Draft body"
    )

    request = append_request(
        literal,
        options=(
            r"(\Seen \Draft) "
            '"15-Jul-2026 18:30:45 +0200"'
        ),
    )

    replies = protocol.append_literal(
        request,
        literal,
    )

    assert serialize(replies) == [
        (
            "A100 OK "
            "[APPENDUID 1 2] "
            "APPEND completed\r\n"
        )
    ]

    appended = (
        store.open_mailbox(
            "archive@test.onion"
        )
        .get_by_uid(2)
    )

    assert appended is not None

    assert appended.flags == {
        "\\Seen",
        "\\Draft",
    }

    assert (
        appended.internal_date.utcoffset()
        == timedelta(hours=2)
    )

    assert appended.internal_date.year == 2026
    assert appended.internal_date.month == 7
    assert appended.internal_date.day == 15


def test_imap_append_requires_authentication(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        store=store
    )

    literal = (
        b"Subject: Test\r\n"
        b"\r\n"
        b"Body"
    )

    request = append_request(
        literal
    )

    assert serialize(
        protocol.append_literal(
            request,
            literal,
        )
    ) == [
        (
            "A100 NO "
            "Authentication required\r\n"
        )
    ]

    assert (
        store.open_mailbox(
            "archive@test.onion"
        ).count()
        == 1
    )


def test_imap_append_rejects_missing_mailbox(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    literal = (
        b"Subject: Test\r\n"
        b"\r\n"
        b"Body"
    )

    request = append_request(
        literal,
        mailbox="missing@test.onion",
    )

    assert serialize(
        protocol.append_literal(
            request,
            literal,
        )
    ) == [
        (
            "A100 NO "
            "[TRYCREATE] Mailbox not found\r\n"
        )
    ]


def test_imap_append_rejects_wrong_literal_size(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    literal = (
        b"Subject: Test\r\n"
        b"\r\n"
        b"Body"
    )

    request = IMAPAppendParser.parse(
        (
            'A100 APPEND '
            '"archive@test.onion" '
            "{999}"
        )
    )

    assert serialize(
        protocol.append_literal(
            request,
            literal,
        )
    ) == [
        (
            "A100 BAD "
            "APPEND literal size "
            "does not match\r\n"
        )
    ]

    assert (
        store.open_mailbox(
            "archive@test.onion"
        ).count()
        == 1
    )


def test_imap_append_rejects_empty_message(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    request = IMAPAppendParser.parse(
        (
            'A100 APPEND '
            '"archive@test.onion" '
            "{0}"
        )
    )

    assert serialize(
        protocol.append_literal(
            request,
            b"",
        )
    ) == [
        (
            "A100 NO "
            "APPEND literal is empty\r\n"
        )
    ]


def test_create_creates_mailbox():
    store = MessageStore()

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 CREATE "Archive"'
        )
    )

    assert replies == [
        "A002 OK CREATE completed\r\n",
    ]

    assert store.list_mailboxes() == [
        "Archive",
    ]

    assert store.count(
        "Archive"
    ) == 0


def test_create_existing_mailbox_returns_no():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 CREATE "Archive"'
        )
    )

    assert replies == [
        (
            "A002 NO "
            "Mailbox already exists\r\n"
        ),
    ]

    assert store.list_mailboxes() == [
        "Archive",
    ]


def test_create_requires_authentication():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            'A001 CREATE "Archive"'
        )
    )

    assert replies == [
        (
            "A001 NO "
            "Authentication required\r\n"
        ),
    ]


def test_delete_removes_mailbox(
    message,
):
    store = MessageStore()

    store.save_entry(
        "Archive",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 DELETE "Archive"'
        )
    )

    assert replies == [
        "A002 OK DELETE completed\r\n",
    ]

    assert store.list_mailboxes() == []


def test_delete_missing_mailbox_returns_no():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 DELETE "Missing"'
        )
    )

    assert replies == [
        "A002 NO Mailbox not found\r\n",
    ]   


def test_delete_requires_authentication():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            'A001 DELETE "Archive"'
        )
    )

    assert replies == [
        "A001 NO Authentication required\r\n",
    ]


def test_delete_rejects_missing_mailbox_argument():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 DELETE"
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "DELETE requires mailbox\r\n"
        ),
    ]   


def test_rename_renames_mailbox(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "Archive",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 RENAME "Archive" "Old"'
        )
    )

    assert replies == [
        "A002 OK RENAME completed\r\n",
    ]

    assert store.list_mailboxes() == [
        "Old",
    ]

    renamed_entries = store.list_entries(
        "Old"
    )

    assert len(renamed_entries) == 1
    assert renamed_entries[0].id == entry.id
    assert renamed_entries[0].uid == entry.uid


def test_rename_missing_source_returns_no():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 RENAME "Missing" "Old"'
        )
    )

    assert replies == [
        (
            "A002 NO "
            "Unable to rename mailbox\r\n"
        ),
    ]


def test_rename_existing_destination_returns_no():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    store.create_mailbox(
        "Old"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 RENAME "Archive" "Old"'
        )
    )

    assert replies == [
        (
            "A002 NO "
            "Unable to rename mailbox\r\n"
        ),
    ]

    assert store.list_mailboxes() == [
        "Archive",
        "Old",
    ]


def test_rename_requires_authentication():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            'A001 RENAME "Archive" "Old"'
        )
    )

    assert replies == [
        "A001 NO Authentication required\r\n",
    ]

def test_rename_rejects_missing_destination():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 RENAME "Archive"'
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "RENAME requires source and destination\r\n"
        ),
    ]


def test_rename_rejects_too_many_arguments():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 RENAME "Archive" "Old" "Extra"'
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "RENAME requires source and destination\r\n"
        ),
    ]


def test_subscribe_subscribes_mailbox():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 SUBSCRIBE "Archive"'
        )
    )

    assert replies == [
        "A002 OK SUBSCRIBE completed\r\n",
    ]

    assert store.list_subscribed_mailboxes() == [
        "Archive",
    ]


def test_subscribe_is_idempotent():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SUBSCRIBE "Archive"'
    )

    replies = serialize(
        protocol.execute(
            'A003 SUBSCRIBE "Archive"'
        )
    )

    assert replies == [
        "A003 OK SUBSCRIBE completed\r\n",
    ]

    assert store.list_subscribed_mailboxes() == [
        "Archive",
    ]


def test_subscribe_missing_mailbox_returns_no():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 SUBSCRIBE "Missing"'
        )
    )

    assert replies == [
        "A002 NO Mailbox not found\r\n",
    ]


def test_subscribe_requires_authentication():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            'A001 SUBSCRIBE "Archive"'
        )
    )

    assert replies == [
        "A001 NO Authentication required\r\n",
    ]


def test_subscribe_rejects_missing_mailbox_argument():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 SUBSCRIBE"
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "SUBSCRIBE requires mailbox\r\n"
        ),
    ]


def test_subscribe_rejects_too_many_arguments():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 SUBSCRIBE "Archive" "Extra"'
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "SUBSCRIBE requires mailbox\r\n"
        ),
    ]


def test_unsubscribe_unsubscribes_mailbox():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    store.subscribe_mailbox(
        "Archive"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 UNSUBSCRIBE "Archive"'
        )
    )

    assert replies == [
        "A002 OK UNSUBSCRIBE completed\r\n",
    ]

    assert store.list_subscribed_mailboxes() == []


def test_unsubscribe_not_subscribed_mailbox_returns_no():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 UNSUBSCRIBE "Archive"'
        )
    )

    assert replies == [
        "A002 NO Mailbox not subscribed\r\n",
    ]


def test_unsubscribe_missing_mailbox_returns_no():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 UNSUBSCRIBE "Missing"'
        )
    )

    assert replies == [
        "A002 NO Mailbox not subscribed\r\n",
    ]


def test_unsubscribe_requires_authentication():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            'A001 UNSUBSCRIBE "Archive"'
        )
    )

    assert replies == [
        "A001 NO Authentication required\r\n",
    ]   


def test_unsubscribe_rejects_missing_mailbox_argument():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 UNSUBSCRIBE"
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "UNSUBSCRIBE requires mailbox\r\n"
        ),
    ]


def test_unsubscribe_rejects_too_many_arguments():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 UNSUBSCRIBE "Archive" "Extra"'
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "UNSUBSCRIBE requires mailbox\r\n"
        ),
    ]


def test_lsub_returns_subscribed_mailboxes():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    store.create_mailbox(
        "Work"
    )

    store.subscribe_mailbox(
        "Archive"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 LSUB "" "*"'
        )
    )

    assert replies == [
        '* LSUB () "/" "Archive"\r\n',
        "A002 OK LSUB completed\r\n",
    ]


def test_lsub_returns_empty_list():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 LSUB "" "*"'
        )
    )

    assert replies == [
        "A002 OK LSUB completed\r\n",
    ]


def test_lsub_requires_authentication():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            'A001 LSUB "" "*"'
        )
    )

    assert replies == [
        "A001 NO Authentication required\r\n",
    ]


def test_lsub_rejects_wrong_argument_count():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 LSUB ""'
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "LSUB requires reference and mailbox\r\n"
        ),
    ]


def test_namespace_returns_default_namespace():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 NAMESPACE"
        )
    )

    assert replies == [
        '* NAMESPACE (("" "/")) NIL NIL\r\n',
        "A002 OK NAMESPACE completed\r\n",
    ]


def test_namespace_requires_authentication():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            "A001 NAMESPACE"
        )
    )

    assert replies == [
        "A001 NO Authentication required\r\n",
    ]


def test_namespace_rejects_arguments():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 NAMESPACE extra'
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "NAMESPACE does not accept arguments\r\n"
        ),
    ]


def test_id_returns_server_identification():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 ID NIL"
        )
    )

    assert replies == [
        (
            '* ID ("name" "GarlicSMTP" '
            '"version" "1.0")\r\n'
        ),
        "A002 OK ID completed\r\n",
    ]


def test_id_accepts_no_arguments():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 ID"
        )
    )

    assert replies == [
        (
            '* ID ("name" "GarlicSMTP" '
            '"version" "1.0")\r\n'
        ),
        "A002 OK ID completed\r\n",
    ]


def test_id_requires_authentication():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            "A001 ID NIL"
        )
    )

    assert replies == [
        "A001 NO Authentication required\r\n",
    ]


def test_id_rejects_too_many_arguments():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 ID NIL extra'
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "ID accepts zero or one argument\r\n"
        ),
    ]


def test_enable_accepts_capabilities():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 ENABLE UTF8=ACCEPT"
        )
    )

    assert replies == [
        "A002 OK ENABLE completed\r\n",
    ]


def test_enable_accepts_multiple_capabilities():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 ENABLE UTF8=ACCEPT CONDSTORE"
        )
    )

    assert replies == [
        "A002 OK ENABLE completed\r\n",
    ]


def test_enable_requires_authentication():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            "A001 ENABLE UTF8=ACCEPT"
        )
    )

    assert replies == [
        "A001 NO Authentication required\r\n",
    ]


def test_enable_requires_capability():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 ENABLE"
        )
    )

    assert replies == [
        (
            "A002 BAD "
            "ENABLE requires one or more capabilities\r\n"
        ),
    ]


def test_imap_capability_advertises_supported_extensions():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            "A001 CAPABILITY"
        )
    )

    assert len(replies) == 2

    capability_reply = replies[0]

    assert capability_reply.startswith(
        "* CAPABILITY "
    )

    assert "IMAP4rev1" in capability_reply
    assert "MOVE" in capability_reply
    assert "NAMESPACE" in capability_reply
    assert "ID" in capability_reply
    assert "ENABLE" in capability_reply

    assert replies[1] == (
        "A001 OK CAPABILITY completed\r\n"
    )


def test_status_returns_uidvalidity(
    message,
):
    store = MessageStore()

    store.save_entry(
        "Archive",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 STATUS "Archive" (UIDVALIDITY)'
        )
    )

    assert replies == [
        (
            '* STATUS "Archive" '
            '(UIDVALIDITY 1)\r\n'
        ),
        "A002 OK STATUS completed\r\n",
    ]


def test_status_rejects_highestmodseq():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            (
                'A002 STATUS "Archive" '
                "(HIGHESTMODSEQ)"
            )
        )
    )

    assert replies == [
        (
            "A002 BAD Unsupported STATUS item "
            "HIGHESTMODSEQ\r\n"
        ),
    ]


def test_idle_enters_idle_without_replies():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            "A002 IDLE"
        )
    )

    assert replies == []


def test_idle_exposes_enter_idle_action():
    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        "A002 IDLE"
    )

    assert (
        protocol.command_action()
        is IMAPCommandAction.ENTER_IDLE
    )


def test_imap_examine_close_does_not_expunge(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        f"A003 UID STORE {entry.uid} +FLAGS (\\Deleted)"
    )

    protocol.execute(
        'A004 EXAMINE "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A005 CLOSE"
        )
    )

    assert replies == [
        "A005 OK CLOSE completed\r\n"
    ]

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None

    assert (
        protocol.session.state
        is IMAPSessionState.AUTHENTICATED
    )


def test_imap_examine_rejects_uid_move(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 EXAMINE "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID MOVE {entry.uid} "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        "A003 NO Mailbox is read-only\r\n"
    ]

    source_entry = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert source_entry is not None

    destination_entries = store.list_entries(
        "archive@test.onion"
    )

    assert destination_entries == []


def test_imap_examine_allows_uid_copy(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 EXAMINE "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f'A003 UID COPY {entry.uid} '
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        "A003 OK [COPYUID 1 1 1] UID COPY completed\r\n"
    ]

    source = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert source is not None

    copied = store.list_entries(
        "archive@test.onion"
    )

    assert len(copied) == 1


def test_imap_select_after_examine_restores_read_write(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 EXAMINE "bob@test.onion"'
    )

    protocol.execute(
        'A003 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A004 UID STORE {entry.uid} "
                "+FLAGS (\\Seen)"
            )
        )
    )

    assert replies == [
        "* 1 FETCH (UID 1 FLAGS (\\Seen))\r\n",
        "A004 OK UID STORE completed\r\n",
    ]

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_status_selected_mailbox(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            'A003 STATUS "bob@test.onion" '
            "(MESSAGES UIDNEXT UIDVALIDITY)"
        )
    )

    assert replies == [
        (
            '* STATUS "bob@test.onion" '
            "(MESSAGES 1 UIDNEXT 2 "
            "UIDVALIDITY 1)\r\n"
        ),
        "A003 OK STATUS completed\r\n",
    ]


def test_imap_status_returns_only_requested_items(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 STATUS "bob@test.onion" (UIDNEXT)'
        )
    )

    assert replies == [
        '* STATUS "bob@test.onion" (UIDNEXT 2)\r\n',
        "A002 OK STATUS completed\r\n",
    ]

def test_imap_uid_copy_to_same_mailbox(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f'A003 UID COPY {entry.uid} '
                '"bob@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 OK [COPYUID 1 1 2] "
            "UID COPY completed\r\n"
        ),
    ]

    entries = store.list_entries(
        "bob@test.onion"
    )

    assert len(entries) == 2
    assert entries[0].uid == 1
    assert entries[1].uid == 2


def test_imap_uid_copy_multiple_messages_returns_copyuid_mapping(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID COPY "
                f"{first.uid},{second.uid} "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 OK [COPYUID 1 1,2 1,2] "
            "UID COPY completed\r\n"
        ),
    ]

    copied = store.list_entries(
        "archive@test.onion"
    )

    assert len(copied) == 2
    assert copied[0].uid == 1
    assert copied[1].uid == 2


def test_imap_uid_copy_multiple_does_not_copy_partial_result(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID COPY "
                f"{first.uid},999 "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        "A003 NO Message not found\r\n",
    ]

    copied = store.list_entries(
        "archive@test.onion"
    )

    assert copied == []


def test_imap_uid_copy_accepts_uid_range(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID COPY "
                f"{first.uid}:{second.uid} "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 OK [COPYUID 1 1,2 1,2] "
            "UID COPY completed\r\n"
        ),
    ]

    copied = store.list_entries(
        "archive@test.onion"
    )

    assert len(copied) == 2
    assert copied[0].uid == 1
    assert copied[1].uid == 2


def test_imap_uid_copy_accepts_reverse_uid_range(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID COPY "
                f"{second.uid}:{first.uid} "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 OK [COPYUID 1 1,2 1,2] "
            "UID COPY completed\r\n"
        ),
    ]

    copied = store.list_entries(
        "archive@test.onion"
    )

    assert len(copied) == 2


def test_imap_uid_copy_accepts_star(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 UID COPY * '
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 OK [COPYUID 1 "
            f"{second.uid} 1] "
            "UID COPY completed\r\n"
        ),
    ]

    copied = store.list_entries(
        "archive@test.onion"
    )

    assert len(copied) == 1


def test_imap_uid_copy_accepts_range_to_star(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID COPY "
                f"{first.uid}:* "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 OK [COPYUID 1 "
            "1,2,3 1,2,3] "
            "UID COPY completed\r\n"
        ),
    ]

    copied = store.list_entries(
        "archive@test.onion"
    )

    assert len(copied) == 3
    assert [
        entry.uid
        for entry in copied
    ] == [1, 2, 3]


def test_imap_uid_copy_range_skips_missing_uids(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    protocol.execute(
        "A004 EXPUNGE"
    )

    replies = serialize(
        protocol.execute(
            (
                f"A005 UID COPY "
                f"{first.uid}:{third.uid} "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A005 OK [COPYUID 1 "
            "1,3 1,2] "
            "UID COPY completed\r\n"
        ),
    ]

    copied = store.list_entries(
        "archive@test.onion"
    )

    assert len(copied) == 2
    assert [
        entry.uid
        for entry in copied
    ] == [1, 2]


def test_imap_uid_copy_accepts_mixed_uid_sequence_set(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    fourth = store.save_entry(
        "bob@test.onion",
        message,
    )

    fifth = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID COPY "
                "1,3:4,* "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 OK [COPYUID 1 "
            "1,3,4,5 1,2,3,4] "
            "UID COPY completed\r\n"
        ),
    ]

    copied = store.list_entries(
        "archive@test.onion"
    )

    assert len(copied) == 4

    assert [
        entry.uid
        for entry in copied
    ] == [1, 2, 3, 4]


def test_imap_uid_move_multiple_messages_returns_copyuid_mapping(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID MOVE "
                f"{first.uid},{second.uid} "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        "* 1 EXPUNGE\r\n",
        "* 1 EXPUNGE\r\n",
        (
            "A003 OK [COPYUID 1 "
            "1,2 1,2] "
            "UID MOVE completed\r\n"
        ),
    ]

    source = store.list_entries(
        "bob@test.onion"
    )

    destination = store.list_entries(
        "archive@test.onion"
    )

    assert source == []
    assert len(destination) == 2
    assert [
        entry.uid
        for entry in destination
    ] == [1, 2]


def test_imap_uid_move_accepts_uid_range(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID MOVE "
                f"{first.uid}:{second.uid} "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        "* 1 EXPUNGE\r\n",
        "* 1 EXPUNGE\r\n",
        (
            "A003 OK [COPYUID 1 "
            "1,2 1,2] "
            "UID MOVE completed\r\n"
        ),
    ]

    assert store.list_entries(
        "bob@test.onion"
    ) == []

    moved = store.list_entries(
        "archive@test.onion"
    )

    assert len(moved) == 2
    assert [
        entry.uid
        for entry in moved
    ] == [1, 2]


def test_imap_uid_move_accepts_reverse_uid_range(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID MOVE "
                f"{second.uid}:{first.uid} "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        "* 1 EXPUNGE\r\n",
        "* 1 EXPUNGE\r\n",
        (
            "A003 OK [COPYUID 1 "
            "1,2 1,2] "
            "UID MOVE completed\r\n"
        ),
    ]

    assert store.list_entries(
        "bob@test.onion"
    ) == []

    moved = store.list_entries(
        "archive@test.onion"
    )

    assert len(moved) == 2


def test_imap_uid_move_accepts_star(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 UID MOVE * '
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        "* 2 EXPUNGE\r\n",
        (
            "A003 OK [COPYUID 1 "
            f"{second.uid} 1] "
            "UID MOVE completed\r\n"
        ),
    ]

    remaining = store.list_entries(
        "bob@test.onion"
    )

    assert len(remaining) == 1
    assert remaining[0].uid == first.uid

    moved = store.list_entries(
        "archive@test.onion"
    )

    assert len(moved) == 1
    assert moved[0].uid == 1


def test_imap_uid_move_range_skips_missing_uids(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    protocol.execute(
        "A004 EXPUNGE"
    )

    replies = serialize(
        protocol.execute(
            (
                f"A005 UID MOVE "
                f"{first.uid}:{third.uid} "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        "* 1 EXPUNGE\r\n",
        "* 1 EXPUNGE\r\n",
        (
            "A005 OK [COPYUID 1 "
            "1,3 1,2] "
            "UID MOVE completed\r\n"
        ),
    ]

    assert store.list_entries(
        "bob@test.onion"
    ) == []

    moved = store.list_entries(
        "archive@test.onion"
    )

    assert len(moved) == 2

    assert [
        entry.uid
        for entry in moved
    ] == [1, 2]


def test_imap_uid_move_multiple_does_not_move_partial_result(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID MOVE "
                f"{first.uid},999 "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        "A003 NO Message not found\r\n",
    ]

    source = store.list_entries(
        "bob@test.onion"
    )

    destination = store.list_entries(
        "archive@test.onion"
    )

    assert len(source) == 1
    assert source[0].uid == first.uid
    assert destination == []


def test_imap_uid_fetch_multiple_messages(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID FETCH "
                f"{first.uid},{second.uid} "
                "(UID FLAGS)"
            )
        )
    )

    assert replies == [
        "* 1 FETCH (UID 1 FLAGS ())\r\n",
        "* 2 FETCH (UID 2 FLAGS ())\r\n",
        "A003 OK UID FETCH completed\r\n",
    ]


def test_imap_uid_fetch_accepts_uid_range(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID FETCH "
                f"{first.uid}:{second.uid} "
                "(UID FLAGS)"
            )
        )
    )

    assert replies == [
        "* 1 FETCH (UID 1 FLAGS ())\r\n",
        "* 2 FETCH (UID 2 FLAGS ())\r\n",
        "A003 OK UID FETCH completed\r\n",
    ]


def test_imap_uid_fetch_accepts_star(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UID FETCH * (UID FLAGS)"
        )
    )

    assert replies == [
        (
            "* 2 FETCH "
            f"(UID {second.uid} FLAGS ())\r\n"
        ),
        "A003 OK UID FETCH completed\r\n",
    ]


def test_imap_uid_fetch_range_skips_missing_uids(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    protocol.execute(
        "A004 EXPUNGE"
    )

    replies = serialize(
        protocol.execute(
            (
                f"A005 UID FETCH "
                f"{first.uid}:{third.uid} "
                "(UID FLAGS)"
            )
        )
    )

    assert replies == [
        "* 1 FETCH (UID 1 FLAGS ())\r\n",
        "* 2 FETCH (UID 3 FLAGS ())\r\n",
        "A005 OK UID FETCH completed\r\n",
    ]


def test_imap_uid_store_multiple_messages(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID STORE "
                f"{first.uid},{second.uid} "
                "+FLAGS (\\Seen)"
            )
        )
    )

    assert replies == [
        "* 1 FETCH (UID 1 FLAGS (\\Seen))\r\n",
        "* 2 FETCH (UID 2 FLAGS (\\Seen))\r\n",
        "A003 OK UID STORE completed\r\n",
    ]


def test_imap_uid_store_accepts_uid_range(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID STORE "
                f"{first.uid}:{second.uid} "
                "+FLAGS (\\Seen)"
            )
        )
    )

    assert replies == [
        "* 1 FETCH (UID 1 FLAGS (\\Seen))\r\n",
        "* 2 FETCH (UID 2 FLAGS (\\Seen))\r\n",
        "A003 OK UID STORE completed\r\n",
    ]


def test_imap_uid_store_accepts_star(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UID STORE * "
            "+FLAGS (\\Seen)"
        )
    )

    assert replies == [
        (
            "* 2 FETCH "
            "(UID 2 FLAGS (\\Seen))\r\n"
        ),
        "A003 OK UID STORE completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    second_stored = store.get_entry(
        "bob@test.onion",
        second.id,
    )

    assert first_stored is not None
    assert second_stored is not None

    assert "\\Seen" not in first_stored.flags
    assert "\\Seen" in second_stored.flags


def test_imap_uid_store_range_skips_missing_uids(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    protocol.execute(
        "A004 EXPUNGE"
    )

    replies = serialize(
        protocol.execute(
            (
                f"A005 UID STORE "
                f"{first.uid}:{third.uid} "
                "+FLAGS (\\Seen)"
            )
        )
    )

    assert replies == [
        "* 1 FETCH (UID 1 FLAGS (\\Seen))\r\n",
        "* 2 FETCH (UID 3 FLAGS (\\Seen))\r\n",
        "A005 OK UID STORE completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    third_stored = store.get_entry(
        "bob@test.onion",
        third.id,
    )

    assert first_stored is not None
    assert third_stored is not None

    assert "\\Seen" in first_stored.flags
    assert "\\Seen" in third_stored.flags


def test_imap_uid_search_seen(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Seen)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH SEEN"
        )
    )

    assert replies == [
        f"* SEARCH {second.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    assert first_stored is not None
    assert "\\Seen" not in first_stored.flags


def test_imap_uid_search_deleted(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH DELETED"
        )
    )

    assert replies == [
        f"* SEARCH {second.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    assert first_stored is not None
    assert "\\Deleted" not in first_stored.flags


def test_imap_uid_search_combines_flag_criteria(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Seen)"
        )
    )

    protocol.execute(
        (
            f"A004 UID STORE {third.uid} "
            "+FLAGS (\\Seen \\Deleted)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A005 UID SEARCH SEEN DELETED"
        )
    )

    assert replies == [
        f"* SEARCH {third.uid}\r\n",
        "A005 OK UID SEARCH completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    assert first_stored is not None
    assert "\\Seen" not in first_stored.flags
    assert "\\Deleted" not in first_stored.flags


def test_imap_uid_search_undeleted(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH UNDELETED"
        )
    )

    assert replies == [
        f"* SEARCH {first.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_answered(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Answered)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH ANSWERED"
        )
    )

    assert replies == [
        f"* SEARCH {second.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    assert first_stored is not None
    assert "\\Answered" not in first_stored.flags


def test_imap_uid_search_unanswered(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Answered)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH UNANSWERED"
        )
    )

    assert replies == [
        f"* SEARCH {first.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_draft(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Draft)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH DRAFT"
        )
    )

    assert replies == [
        f"* SEARCH {second.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    assert first_stored is not None
    assert "\\Draft" not in first_stored.flags


def test_imap_uid_search_undraft(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Draft)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH UNDRAFT"
        )
    )

    assert replies == [
        f"* SEARCH {first.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_flagged(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Flagged)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH FLAGGED"
        )
    )

    assert replies == [
        f"* SEARCH {second.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    assert first_stored is not None
    assert "\\Flagged" not in first_stored.flags


def test_imap_uid_search_unflagged(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Flagged)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH UNFLAGGED"
        )
    )

    assert replies == [
        f"* SEARCH {first.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_body(
    message,
):
    store = MessageStore()

    first_message = message
    first_message.body = (
        "This message contains garlic."
    )

    second_message = MailMessage(
        envelope=Envelope(
            sender="garlic@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Garlic subject",
            }
        ),
        metadata=Metadata(),
        body="Nothing relevant here.",
    )

    first = store.save_entry(
        "bob@test.onion",
        first_message,
    )

    store.save_entry(
        "bob@test.onion",
        second_message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            'A003 UID SEARCH BODY "garlic"'
        )
    )

    assert replies == [
        f"* SEARCH {first.uid}\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_header(
    message,
):
    store = MessageStore()

    first_message = message
    first_message.headers.fields[
        "Subject"
    ] = "Garlic status"

    second_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "From": "garlic@test.onion",
                "Subject": "Other subject",
            }
        ),
        metadata=Metadata(),
        body="garlic",
    )

    first = store.save_entry(
        "bob@test.onion",
        first_message,
    )

    store.save_entry(
        "bob@test.onion",
        second_message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 UID SEARCH '
                'HEADER Subject "garlic"'
            )
        )
    )

    assert replies == [
        f"* SEARCH {first.uid}\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_header_name_is_case_insensitive(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 UID SEARCH '
                'HEADER subject "garlic"'
            )
        )
    )

    assert replies == [
        f"* SEARCH {entry.uid}\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_header_matches_list_value(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "X-Tag"
    ] = [
        "alpha",
        "garlic",
    ]

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 UID SEARCH '
                'HEADER X-Tag "garlic"'
            )
        )
    )

    assert replies == [
        f"* SEARCH {entry.uid}\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_cc(
    message,
):
    store = MessageStore()

    first_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Cc": "carol@test.onion",
            }
        ),
        metadata=Metadata(),
        body="",
    )

    second_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Cc": "dave@test.onion",
            }
        ),
        metadata=Metadata(),
        body="carol@test.onion",
    )

    first = store.save_entry(
        "bob@test.onion",
        first_message,
    )

    store.save_entry(
        "bob@test.onion",
        second_message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 UID SEARCH '
                'CC "carol@test.onion"'
            )
        )
    )

    assert replies == [
        f"* SEARCH {first.uid}\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_bcc(
    message,
):
    store = MessageStore()

    first_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Bcc": "carol@test.onion",
            }
        ),
        metadata=Metadata(),
        body="",
    )

    second_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Bcc": "dave@test.onion",
            }
        ),
        metadata=Metadata(),
        body="carol@test.onion",
    )

    first = store.save_entry(
        "bob@test.onion",
        first_message,
    )

    store.save_entry(
        "bob@test.onion",
        second_message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 UID SEARCH '
                'BCC "carol@test.onion"'
            )
        )
    )

    assert replies == [
        f"* SEARCH {first.uid}\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_not_seen(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Seen)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH NOT SEEN"
        )
    )

    assert replies == [
        f"* SEARCH {first.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_not_deleted(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH NOT DELETED"
        )
    )

    assert replies == [
        f"* SEARCH {first.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_not_subject(
    message,
):
    store = MessageStore()

    first_message = message
    first_message.headers.fields[
        "Subject"
    ] = "Garlic status"

    second_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Other subject",
            }
        ),
        metadata=Metadata(),
        body="",
    )

    store.save_entry(
        "bob@test.onion",
        first_message,
    )

    second = store.save_entry(
        "bob@test.onion",
        second_message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                'A003 UID SEARCH '
                'NOT SUBJECT "garlic"'
            )
        )
    )

    assert replies == [
        f"* SEARCH {second.uid}\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_not_header(
    message,
):
    store = MessageStore()

    first_message = message
    first_message.headers.fields[
        "Subject"
    ] = "Garlic status"

    second_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Other subject",
            }
        ),
        metadata=Metadata(),
        body="",
    )

    store.save_entry(
        "bob@test.onion",
        first_message,
    )

    second = store.save_entry(
        "bob@test.onion",
        second_message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID SEARCH "
                'NOT HEADER Subject "garlic"'
            )
        )
    )

    assert replies == [
        f"* SEARCH {second.uid}\r\n",
        "A003 OK UID SEARCH completed\r\n",
    ]



def test_imap_uid_search_or_seen_deleted(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Seen)"
        )
    )

    protocol.execute(
        (
            f"A004 UID STORE {third.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A005 UID SEARCH OR SEEN DELETED"
        )
    )

    assert replies == [
        (
            f"* SEARCH "
            f"{second.uid} {third.uid}\r\n"
        ),
        "A005 OK UID SEARCH completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    assert first_stored is not None
    assert "\\Seen" not in first_stored.flags
    assert "\\Deleted" not in first_stored.flags


def test_imap_uid_search_or_seen_subject(
    message,
):
    store = MessageStore()

    first_message = message
    first_message.headers.fields[
        "Subject"
    ] = "Garlic status"

    second_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Other subject",
            }
        ),
        metadata=Metadata(),
        body="",
    )

    third_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Nothing relevant",
            }
        ),
        metadata=Metadata(),
        body="",
    )

    first = store.save_entry(
        "bob@test.onion",
        first_message,
    )

    second = store.save_entry(
        "bob@test.onion",
        second_message,
    )

    store.save_entry(
        "bob@test.onion",
        third_message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Seen)"
        )
    )

    replies = serialize(
        protocol.execute(
            (
                "A004 UID SEARCH "
                'OR SEEN SUBJECT "garlic"'
            )
        )
    )

    assert replies == [
        (
            f"* SEARCH "
            f"{first.uid} {second.uid}\r\n"
        ),
        "A004 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_or_subject_body(
    message,
):
    store = MessageStore()

    first_message = message
    first_message.headers.fields[
        "Subject"
    ] = "Garlic status"

    second_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Other subject",
            }
        ),
        metadata=Metadata(),
        body="Onion transport active",
    )

    third_message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Nothing relevant",
            }
        ),
        metadata=Metadata(),
        body="Nothing relevant here",
    )

    first = store.save_entry(
        "bob@test.onion",
        first_message,
    )

    second = store.save_entry(
        "bob@test.onion",
        second_message,
    )

    store.save_entry(
        "bob@test.onion",
        third_message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 UID SEARCH "
                'OR SUBJECT "garlic" '
                'BODY "onion"'
            )
        )
    )

    assert replies == [
        (
            f"* SEARCH "
            f"{first.uid} {second.uid}\r\n"
        ),
        "A003 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_or_not_seen_deleted(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Seen)"
        )
    )

    protocol.execute(
        (
            f"A004 UID STORE {third.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    replies = serialize(
        protocol.execute(
            (
                "A005 UID SEARCH "
                "OR NOT SEEN DELETED"
            )
        )
    )

    assert replies == [
        (
            f"* SEARCH "
            f"{first.uid} {third.uid}\r\n"
        ),
        "A005 OK UID SEARCH completed\r\n",
    ]


def test_imap_uid_search_double_not_seen(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Seen)"
        )
    )

    replies = serialize(
        protocol.execute(
            "A004 UID SEARCH NOT NOT SEEN"
        )
    )

    assert replies == [
        f"* SEARCH {second.uid}\r\n",
        "A004 OK UID SEARCH completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    assert first_stored is not None
    assert "\\Seen" not in first_stored.flags


def test_imap_uid_search_nested_or(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Seen)"
        )
    )

    protocol.execute(
        (
            f"A004 UID STORE {third.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    replies = serialize(
        protocol.execute(
            (
                "A005 UID SEARCH "
                "OR OR SEEN DELETED ANSWERED"
            )
        )
    )

    assert replies == [
        (
            f"* SEARCH "
            f"{second.uid} {third.uid}\r\n"
        ),
        "A005 OK UID SEARCH completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    assert first_stored is not None


def test_imap_uid_fetch_missing_uid_returns_ok(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 UID FETCH 999 (UID FLAGS)"
        )
    )

    assert replies == [
        "A003 OK UID FETCH completed\r\n",
    ]


def test_imap_uid_fetch_body_marks_message_seen(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY[])"
        )
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_flags_does_not_mark_seen(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID FLAGS)"
        )
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_peek_does_not_mark_seen(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY.PEEK[])"
        )
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_rfc822_marks_message_seen(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID RFC822)"
        )
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_rfc822_peek_does_not_mark_seen(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID RFC822.PEEK)"
        )
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_rfc822_size_does_not_mark_seen(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID RFC822.SIZE)"
        )
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_internaldate_does_not_mark_seen(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID INTERNALDATE)"
        )
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_metadata_items_do_not_mark_seen(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID FLAGS RFC822.SIZE INTERNALDATE)"
        )
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_updates_flags_in_response(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID FLAGS BODY[])"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert "\\Seen" in fetch_reply.prefix
    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_body_peek_keeps_flags_in_response(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID FLAGS BODY.PEEK[])"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert "\\Seen" not in fetch_reply.prefix
    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_marks_multiple_messages_seen(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH "
            f"{first.uid},{second.uid} "
            "(UID FLAGS BODY[])"
        )
    )

    assert len(replies) == 3

    first_reply = replies[0]
    second_reply = replies[1]
    tagged_reply = replies[2]

    assert "* 1 FETCH" in first_reply.prefix
    assert "\\Seen" in first_reply.prefix

    assert "* 2 FETCH" in second_reply.prefix
    assert "\\Seen" in second_reply.prefix

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    second_stored = store.get_entry(
        "bob@test.onion",
        second.id,
    )

    assert first_stored is not None
    assert second_stored is not None

    assert "\\Seen" in first_stored.flags
    assert "\\Seen" in second_stored.flags


def test_imap_uid_fetch_body_handles_already_seen_message(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {first.uid} "
            "+FLAGS (\\Seen)"
        )
    )

    replies = protocol.execute(
        (
            f"A004 UID FETCH "
            f"{first.uid},{second.uid} "
            "(UID FLAGS BODY[])"
        )
    )

    assert len(replies) == 3

    first_reply = replies[0]
    second_reply = replies[1]
    tagged_reply = replies[2]

    assert "\\Seen" in first_reply.prefix
    assert "\\Seen" in second_reply.prefix

    assert tagged_reply.serialize() == (
        "A004 OK UID FETCH completed\r\n"
    )

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    second_stored = store.get_entry(
        "bob@test.onion",
        second.id,
    )

    assert first_stored is not None
    assert second_stored is not None

    assert "\\Seen" in first_stored.flags
    assert "\\Seen" in second_stored.flags


def test_imap_uid_fetch_rfc822_size_matches_message_size(
    message,
):
    store = MessageStore()

    message.body = "hello"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID FETCH {entry.uid} "
                "(UID RFC822.SIZE)"
            )
        )
    )

    assert replies == [
        (
            "* 1 FETCH "
            "(UID 1 RFC822.SIZE 7)\r\n"
        ),
        "A003 OK UID FETCH completed\r\n",
    ]


def test_imap_uid_fetch_internaldate_returns_value(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID FETCH {entry.uid} "
                "(UID INTERNALDATE)"
            )
        )
    )

    assert len(replies) == 2
    assert replies[0].startswith(
        "* 1 FETCH (UID 1 INTERNALDATE "
    )
    assert replies[1] == (
        "A003 OK UID FETCH completed\r\n"
    )


def test_imap_uid_fetch_internaldate_format(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID FETCH {entry.uid} "
                "(UID INTERNALDATE)"
            )
        )
    )

    expected_date = (
        entry.internal_date.strftime(
            "%d-%b-%Y %H:%M:%S %z"
        )
    )

    assert replies == [
        (
            "* 1 FETCH "
            f'(UID 1 INTERNALDATE "{expected_date}")'
            "\r\n"
        ),
        "A003 OK UID FETCH completed\r\n",
    ]


def test_imap_uid_fetch_rfc822_header_returns_only_headers(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.body = "secret body"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID RFC822.HEADER)"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == (
        b"Subject: Garlic status\r\n"
        b"\r\n"
    )

    assert b"secret body" not in (
        fetch_reply.content
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_rfc822_text_returns_only_body(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.body = "secret body"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID RFC822.TEXT)"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == (
        b"secret body"
    )

    assert b"Subject: Garlic status" not in (
        fetch_reply.content
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_rfc822_returns_full_message(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.body = "secret body"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID RFC822)"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert b"Subject: Garlic status\r\n" in (
        fetch_reply.content
    )

    assert b"\r\n\r\nsecret body" in (
        fetch_reply.content
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_rfc822_size_matches_rfc822_content(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.body = "secret body"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    rfc822_replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID RFC822)"
        )
    )

    rfc822_content = (
        rfc822_replies[0].content
    )

    size_replies = serialize(
        protocol.execute(
            (
                f"A004 UID FETCH {entry.uid} "
                "(UID RFC822.SIZE)"
            )
        )
    )

    assert size_replies == [
        (
            "* 1 FETCH "
            f"(UID 1 RFC822.SIZE "
            f"{len(rfc822_content)})\r\n"
        ),
        "A004 OK UID FETCH completed\r\n",
    ]


def test_imap_uid_fetch_body_text_returns_only_body(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.body = "secret body"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY[TEXT])"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == (
        b"secret body"
    )

    assert b"Subject: Garlic status" not in (
        fetch_reply.content
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_body_peek_text_does_not_mark_seen(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.body = "secret body"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY.PEEK[TEXT])"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == (
        b"secret body"
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_header_returns_only_headers(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.body = "secret body"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY[HEADER])"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == (
        b"Subject: Garlic status\r\n"
        b"\r\n"
    )

    assert b"secret body" not in (
        fetch_reply.content
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_peek_header_does_not_mark_seen(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.body = "secret body"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY.PEEK[HEADER])"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == (
        b"Subject: Garlic status\r\n"
        b"\r\n"
    )

    assert b"secret body" not in (
        fetch_reply.content
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_header_fields_returns_selected_headers(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.headers.fields[
        "From"
    ] = "alice@test.onion"

    message.headers.fields[
        "X-Test"
    ] = "ignore me"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY[HEADER.FIELDS "
            "(Subject From)])"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert b"Subject: Garlic status\r\n" in (
        fetch_reply.content
    )

    assert b"From: alice@test.onion\r\n" in (
        fetch_reply.content
    )

    assert b"X-Test: ignore me\r\n" not in (
        fetch_reply.content
    )

    assert fetch_reply.content.endswith(
        b"\r\n\r\n"
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_peek_header_fields_returns_selected_headers(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.headers.fields[
        "From"
    ] = "alice@test.onion"

    message.headers.fields[
        "X-Test"
    ] = "ignore me"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY.PEEK[HEADER.FIELDS "
            "(Subject From)])"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert b"Subject: Garlic status\r\n" in (
        fetch_reply.content
    )

    assert b"From: alice@test.onion\r\n" in (
        fetch_reply.content
    )

    assert b"X-Test: ignore me\r\n" not in (
        fetch_reply.content
    )

    assert fetch_reply.content.endswith(
        b"\r\n\r\n"
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_header_fields_not_excludes_selected_headers(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.headers.fields[
        "From"
    ] = "alice@test.onion"

    message.headers.fields[
        "X-Test"
    ] = "keep me"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY[HEADER.FIELDS.NOT "
            "(Subject From)])"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert b"Subject: Garlic status\r\n" not in (
        fetch_reply.content
    )

    assert b"From: alice@test.onion\r\n" not in (
        fetch_reply.content
    )

    assert b"X-Test: keep me\r\n" in (
        fetch_reply.content
    )

    assert fetch_reply.content.endswith(
        b"\r\n\r\n"
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_peek_header_fields_not_excludes_selected_headers(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.headers.fields[
        "From"
    ] = "alice@test.onion"

    message.headers.fields[
        "X-Test"
    ] = "keep me"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY.PEEK[HEADER.FIELDS.NOT "
            "(Subject From)])"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert b"Subject: Garlic status\r\n" not in (
        fetch_reply.content
    )

    assert b"From: alice@test.onion\r\n" not in (
        fetch_reply.content
    )

    assert b"X-Test: keep me\r\n" in (
        fetch_reply.content
    )

    assert fetch_reply.content.endswith(
        b"\r\n\r\n"
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_partial_returns_requested_slice(
    message,
):
    store = MessageStore()

    message.body = "abcdefghij"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY[]<0.5>)"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == (
        fetch_reply.content[:5]
    )

    assert len(fetch_reply.content) == 5

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_body_peek_partial_does_not_mark_seen(
    message,
):
    store = MessageStore()

    message.body = "abcdefghij"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY.PEEK[]<0.5>)"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert len(fetch_reply.content) == 5

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_partial_uses_offset(
    message,
):
    store = MessageStore()

    message.body = "abcdefghij"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY[]<3.4>)"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    full_content = (
        MessageSerializer.to_rfc5322(
            message
        ).encode("utf-8")
    )

    assert fetch_reply.content == (
        full_content[3:7]
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_body_partial_beyond_end_returns_empty(
    message,
):
    store = MessageStore()

    message.body = "abc"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY[]<999.5>)"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == b""

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_body_partial_zero_count_returns_empty(
    message,
):
    store = MessageStore()

    message.body = "abcdefghij"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY[]<3.0>)"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == b""

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_body_partial_rejects_invalid_range(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID FETCH {entry.uid} "
                "(UID BODY[]<x.5>)"
            )
        )
    )

    assert replies == [
        "A003 BAD Invalid BODY partial\r\n",
    ]

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_text_partial_returns_requested_slice(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.body = "abcdefghij"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY[TEXT]<3.4>)"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == (
        b"defg"
    )

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" in stored.flags


def test_imap_uid_fetch_body_peek_text_partial_does_not_mark_seen(
    message,
):
    store = MessageStore()

    message.body = "abcdefghij"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = protocol.execute(
        (
            f"A003 UID FETCH {entry.uid} "
            "(UID BODY.PEEK[TEXT]<3.4>)"
        )
    )

    assert len(replies) == 2

    fetch_reply = replies[0]
    tagged_reply = replies[1]

    assert fetch_reply.content == b"defg"

    assert tagged_reply.serialize() == (
        "A003 OK UID FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_fetch_by_sequence_number(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 FETCH 2 (UID FLAGS)"
        )
    )

    assert replies == [
        (
            "* 2 FETCH "
            f"(UID {second.uid} FLAGS ())\r\n"
        ),
        "A003 OK FETCH completed\r\n",
    ]

    assert second.uid != first.uid


def test_imap_fetch_missing_sequence_number_returns_ok(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 FETCH 999 (UID FLAGS)"
        )
    )

    assert replies == [
        "A003 OK FETCH completed\r\n",
    ]


def test_imap_fetch_multiple_sequence_numbers(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 FETCH 1,2 (UID FLAGS)"
        )
    )

    assert replies == [
        "* 1 FETCH (UID 1 FLAGS ())\r\n",
        "* 2 FETCH (UID 2 FLAGS ())\r\n",
        "A003 OK FETCH completed\r\n",
    ]


def test_imap_fetch_accepts_sequence_range(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 FETCH 1:2 (UID FLAGS)"
        )
    )

    assert replies == [
        "* 1 FETCH (UID 1 FLAGS ())\r\n",
        "* 2 FETCH (UID 2 FLAGS ())\r\n",
        "A003 OK FETCH completed\r\n",
    ]


def test_imap_fetch_accepts_star_sequence(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 FETCH * (UID FLAGS)"
        )
    )

    assert replies == [
        (
            "* 2 FETCH "
            f"(UID {second.uid} FLAGS ())\r\n"
        ),
        "A003 OK FETCH completed\r\n",
    ]


def test_imap_store_adds_flag_by_sequence_number(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 STORE 2 +FLAGS (\\Seen)"
        )
    )

    assert replies == [
        (
            "* 2 FETCH "
            f"(FLAGS (\\Seen))\r\n"
        ),
        "A003 OK STORE completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    second_stored = store.get_entry(
        "bob@test.onion",
        second.id,
    )

    assert first_stored is not None
    assert second_stored is not None

    assert "\\Seen" not in first_stored.flags
    assert "\\Seen" in second_stored.flags


def test_imap_store_multiple_sequence_numbers(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 STORE 1,2 +FLAGS (\\Seen)"
        )
    )

    assert replies == [
        "* 1 FETCH (FLAGS (\\Seen))\r\n",
        "* 2 FETCH (FLAGS (\\Seen))\r\n",
        "A003 OK STORE completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    second_stored = store.get_entry(
        "bob@test.onion",
        second.id,
    )

    assert first_stored is not None
    assert second_stored is not None

    assert "\\Seen" in first_stored.flags
    assert "\\Seen" in second_stored.flags


def test_imap_store_range_silent_updates_without_fetch_replies(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 STORE 1:2 "
                "+FLAGS.SILENT (\\Seen)"
            )
        )
    )

    assert replies == [
        "A003 OK STORE completed\r\n",
    ]

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    second_stored = store.get_entry(
        "bob@test.onion",
        second.id,
    )

    assert first_stored is not None
    assert second_stored is not None

    assert "\\Seen" in first_stored.flags
    assert "\\Seen" in second_stored.flags


def test_imap_store_accepts_star_sequence(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            "A003 STORE * "
            "+FLAGS (\\Seen)"
        )
    )

    first_stored = store.get_entry(
        "bob@test.onion",
        first.id,
    )

    second_stored = store.get_entry(
        "bob@test.onion",
        second.id,
    )

    assert first_stored is not None
    assert second_stored is not None

    assert "\\Seen" not in first_stored.flags
    assert "\\Seen" in second_stored.flags


def test_imap_search_all_returns_sequence_numbers(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 SEARCH ALL"
        )
    )

    assert replies == [
        "* SEARCH 1 2\r\n",
        "A003 OK SEARCH completed\r\n",
    ]


def test_imap_search_returns_updated_sequence_numbers_after_expunge(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    protocol.execute(
        (
            f"A003 UID STORE {second.uid} "
            "+FLAGS (\\Deleted)"
        )
    )

    protocol.execute(
        "A004 EXPUNGE"
    )

    replies = serialize(
        protocol.execute(
            "A005 SEARCH ALL"
        )
    )

    assert replies == [
        "* SEARCH 1 2\r\n",
        "A005 OK SEARCH completed\r\n",
    ]

    assert first.uid == 1
    assert third.uid == 3


def test_imap_copy_by_sequence_number(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 COPY 2 "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 OK [COPYUID 1 2 1] "
            "COPY completed\r\n"
        ),
    ]

    source = store.list_entries(
        "bob@test.onion"
    )

    destination = store.list_entries(
        "archive@test.onion"
    )

    assert len(source) == 2
    assert len(destination) == 1

    assert destination[0].uid == 1
    assert source[0].id == first.id
    assert source[1].id == second.id


def test_imap_copy_multiple_sequence_numbers_returns_copyuid(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.create_mailbox(
        "archive@test.onion"
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                "A003 COPY 1,2 "
                '"archive@test.onion"'
            )
        )
    )

    assert replies == [
        (
            "A003 OK [COPYUID 1 "
            f"{first.uid},{second.uid} "
            "1,2] COPY completed\r\n"
        ),
    ]

    copied = store.list_entries(
        "archive@test.onion"
    )

    assert len(copied) == 2
    assert [
        entry.uid
        for entry in copied
    ] == [1, 2]


def test_imap_select_reports_uidvalidity_and_permanentflags(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 SELECT "bob@test.onion"'
        )
    )

    assert (
        "* OK [UIDVALIDITY 1] "
        "UID validity\r\n"
    ) in replies

    assert (
        "* OK [PERMANENTFLAGS "
        "(\\Seen \\Answered \\Flagged "
        "\\Deleted \\Draft)] "
        "Permanent flags\r\n"
    ) in replies

    assert replies[-1] == (
        "A002 OK [READ-WRITE] "
        "SELECT completed\r\n"
    )


def test_imap_examine_reports_uidvalidity_and_permanentflags(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    replies = serialize(
        protocol.execute(
            'A002 EXAMINE "bob@test.onion"'
        )
    )

    assert (
        "* OK [UIDVALIDITY 1] "
        "UID validity\r\n"
    ) in replies

    assert (
        "* OK [PERMANENTFLAGS "
        "(\\Seen \\Answered \\Flagged "
        "\\Deleted \\Draft)] "
        "Permanent flags\r\n"
    ) in replies

    assert replies[-1] == (
        "A002 OK [READ-ONLY] "
        "EXAMINE completed\r\n"
    )


def test_imap_fetch_fast_macro(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 FETCH 1 FAST"
        )
    )

    assert len(replies) == 2

    assert replies[0].startswith(
        "* 1 FETCH ("
    )

    assert "FLAGS " in replies[0]
    assert "INTERNALDATE " in replies[0]
    assert "RFC822.SIZE " in replies[0]

    assert replies[1] == (
        "A003 OK FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_fetch_all_macro(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 FETCH 1 ALL"
        )
    )

    assert len(replies) == 2

    assert replies[0].startswith(
        "* 1 FETCH ("
    )

    assert "FLAGS " in replies[0]
    assert "INTERNALDATE " in replies[0]
    assert "RFC822.SIZE " in replies[0]
    assert "ENVELOPE " in replies[0]

    assert replies[1] == (
        "A003 OK FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_envelope_returns_message_metadata(
    message,
):
    store = MessageStore()

    message.headers.fields[
        "Subject"
    ] = "Garlic status"

    message.headers.fields[
        "From"
    ] = "Alice <alice@test.onion>"

    message.headers.fields[
        "To"
    ] = "Bob <bob@test.onion>"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID FETCH {entry.uid} "
                "(UID ENVELOPE)"
            )
        )
    )

    assert replies == [
        (
            "* 1 FETCH "
            "(UID 1 ENVELOPE "
            '(NIL "Garlic status" '
            '(("Alice" NIL "alice" "test.onion")) '
            '(("Alice" NIL "alice" "test.onion")) '
            '(("Alice" NIL "alice" "test.onion")) '
            '(("Bob" NIL "bob" "test.onion")) '
            "NIL NIL NIL NIL))\r\n"
        ),
        "A003 OK UID FETCH completed\r\n",
    ]


def test_imap_fetch_full_macro(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            "A003 FETCH 1 FULL"
        )
    )

    assert len(replies) == 2

    assert replies[0].startswith(
        "* 1 FETCH ("
    )

    assert "FLAGS " in replies[0]
    assert "INTERNALDATE " in replies[0]
    assert "RFC822.SIZE " in replies[0]
    assert "ENVELOPE " in replies[0]
    assert "BODY " in replies[0]

    assert replies[1] == (
        "A003 OK FETCH completed\r\n"
    )

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_uid_fetch_body_returns_singlepart_structure(
    message,
):
    store = MessageStore()

    message.body = "hello"

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    protocol = IMAPProtocol(
        authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
        store=store,
    )

    protocol.execute(
        "A001 LOGIN alice secret"
    )

    protocol.execute(
        'A002 SELECT "bob@test.onion"'
    )

    replies = serialize(
        protocol.execute(
            (
                f"A003 UID FETCH {entry.uid} "
                "(UID BODY)"
            )
        )
    )

    assert replies == [
        (
            "* 1 FETCH "
            '(UID 1 BODY '
            '("TEXT" "PLAIN" '
            '("CHARSET" "US-ASCII") '
            'NIL NIL "7BIT" 5 1))\r\n'
        ),
        "A003 OK UID FETCH completed\r\n",
    ]

    stored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert stored is not None
    assert "\\Seen" not in stored.flags


def test_imap_capability_advertises_idle():
    protocol = IMAPProtocol()

    replies = serialize(
        protocol.execute(
            "A001 CAPABILITY"
        )
    )

    assert "IDLE" in replies[0]
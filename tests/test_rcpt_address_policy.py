# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from types import SimpleNamespace
from unittest.mock import patch

from garlicsmtp.application.address_policy import AddressPolicy
from garlicsmtp.smtp.handlers.rcpt import RCPTHandler
from garlicsmtp.smtp.session import SMTPSession
from garlicsmtp.smtp.state import SMTPState
from garlicsmtp.smtp.handlers.register import create_dispatcher
from garlicsmtp.smtp.parser import SMTPParser
from garlicsmtp.smtp.protocol import SMTPProtocol
from garlicsmtp.smtp.server import SMTPServer


def test_rcpt_rejects_remote_onion_recipient_without_mutating_session():
    local_hostname = "a" * 56 + ".onion"
    remote_hostname = "b" * 56 + ".onion"

    policy = AddressPolicy()
    policy.set_local_hostname(local_hostname)

    session = SMTPSession(client_ip="127.0.0.1")
    session.state = SMTPState.WAIT_RCPT

    command = SimpleNamespace(
        arguments={
            "to": f"garlicsmtp@{remote_hostname}",
        }
    )

    reply = RCPTHandler(address_policy=policy).handle(
        session,
        command,
    )

    assert reply.code == 550
    assert session.message.envelope.recipients == []
    assert session.state == SMTPState.WAIT_RCPT


def test_dispatcher_rejects_remote_onion_recipient():
    local_hostname = "a" * 56 + ".onion"
    remote_hostname = "b" * 56 + ".onion"

    policy = AddressPolicy()
    policy.set_local_hostname(local_hostname)

    dispatcher = create_dispatcher(
        address_policy=policy,
    )

    session = SMTPSession(client_ip="127.0.0.1")

    dispatcher.dispatch(
        session,
        SMTPParser.parse("EHLO sender.onion"),
    )

    dispatcher.dispatch(
        session,
        SMTPParser.parse(
            f"MAIL FROM:<garlicsmtp@{remote_hostname}>"
        ),
    )

    reply = dispatcher.dispatch(
        session,
        SMTPParser.parse(
            f"RCPT TO:<garlicsmtp@{remote_hostname}>"
        ),
    )

    assert reply.code == 550
    assert session.message.envelope.recipients == []
    assert session.state == SMTPState.WAIT_RCPT


def test_smtp_protocol_passes_address_policy_to_dispatcher():
    local_hostname = "a" * 56 + ".onion"
    remote_hostname = "b" * 56 + ".onion"

    policy = AddressPolicy()
    policy.set_local_hostname(local_hostname)

    connection = SimpleNamespace(ip="127.0.0.1")

    protocol = SMTPProtocol(
        connection=connection,
        pipeline=object(),
        address_policy=policy,
    )

    session = protocol.session

    protocol.dispatcher.dispatch(
        session,
        SMTPParser.parse("EHLO sender.onion"),
    )

    protocol.dispatcher.dispatch(
        session,
        SMTPParser.parse(
            f"MAIL FROM:<garlicsmtp@{remote_hostname}>"
        ),
    )

    reply = protocol.dispatcher.dispatch(
        session,
        SMTPParser.parse(
            f"RCPT TO:<garlicsmtp@{remote_hostname}>"
        ),
    )

    assert reply.code == 550
    assert session.message.envelope.recipients == []
    assert session.state == SMTPState.WAIT_RCPT


def test_smtp_server_passes_address_policy_to_protocol():
    local_hostname = "a" * 56 + ".onion"

    policy = AddressPolicy()
    policy.set_local_hostname(local_hostname)

    server = SMTPServer(
        pipeline=object(),
        address_policy=policy,
    )

    with patch(
        "garlicsmtp.smtp.server.SMTPConnection"
    ) as connection_class, patch(
        "garlicsmtp.smtp.server.SMTPProtocol"
    ) as protocol_class:
        server.handle_connection(
            client=object(),
            address=("127.0.0.1", 12345),
        )

    connection_class.assert_called_once()

    assert (
        protocol_class.call_args.kwargs["address_policy"]
        is policy
    )

    protocol_class.return_value.serve.assert_called_once()


def test_rcpt_rejects_second_recipient_without_mutating_transaction():
    session = SMTPSession(client_ip="127.0.0.1")
    session.state = SMTPState.WAIT_RCPT

    handler = RCPTHandler()

    first_recipient = "alice@local.onion"
    second_recipient = "bob@local.onion"

    first_reply = handler.handle(
        session,
        SimpleNamespace(
            arguments={"to": first_recipient}
        ),
    )

    assert first_reply.code == 250
    assert session.message.envelope.recipients == [
        first_recipient
    ]
    assert session.state == SMTPState.WAIT_DATA

    second_reply = handler.handle(
        session,
        SimpleNamespace(
            arguments={"to": second_recipient}
        ),
    )

    assert second_reply.code == 503
    assert session.message.envelope.recipients == [
        first_recipient
    ]
    assert session.state == SMTPState.WAIT_DATA
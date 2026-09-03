# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.handlers.ehlo import EHLOHandler
from garlicsmtp.smtp.parser import SMTPParser
from garlicsmtp.smtp.session import SMTPSession
from garlicsmtp.smtp.handlers.register import create_dispatcher


def test_ehlo_handler_advertises_e2ee_capability():
    handler = EHLOHandler(
        e2ee_capability=(
            "v=1; "
            "alg=x25519; "
            "key=dGVzdA=="
        )
    )

    session = SMTPSession(
        "127.0.0.1"
    )

    command = SMTPParser.parse(
        "EHLO garlic.onion"
    )

    reply = handler.handle(
        session,
        command,
    )

    assert reply.code == 250
    assert reply.message == (
        "Hello garlic.onion\n"
        "GARLICSMTP-E2EE "
        "v=1; alg=x25519; key=dGVzdA=="
    )


def test_ehlo_handler_without_e2ee_capability():
    handler = EHLOHandler()

    session = SMTPSession(
        "127.0.0.1"
    )

    command = SMTPParser.parse(
        "EHLO garlic.onion"
    )

    reply = handler.handle(
        session,
        command,
    )

    assert reply.code == 250
    assert reply.message == (
        "Hello garlic.onion"
    )


def test_dispatcher_configures_e2ee_capability():
    dispatcher = create_dispatcher(
        e2ee_capability=(
            "v=1; "
            "alg=x25519; "
            "key=dGVzdA=="
        )
    )

    session = SMTPSession(
        "127.0.0.1"
    )

    command = SMTPParser.parse(
        "EHLO garlic.onion"
    )

    reply = dispatcher.dispatch(
        session,
        command,
    )

    assert reply.message == (
        "Hello garlic.onion\n"
        "GARLICSMTP-E2EE "
        "v=1; alg=x25519; key=dGVzdA=="
    )
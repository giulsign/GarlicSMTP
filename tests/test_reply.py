# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.replies import ReplyFactory
from garlicsmtp.models import SMTPReply

def test_reply_greeting():
    reply = ReplyFactory.greeting(
        "garlicsmtp.onion"
    )

    assert reply.code == 220
    assert reply.serialize() == (
        b"220 garlicsmtp.onion ready\r\n"
    )


def test_reply_serializes_multiline_response():
    reply = SMTPReply(
        250,
        (
            "Hello client\n"
            "GARLICSMTP-E2EE "
            "v=1; alg=x25519; key=dGVzdA=="
        ),
    )

    assert reply.serialize() == (
        b"250-Hello client\r\n"
        b"250 GARLICSMTP-E2EE "
        b"v=1; alg=x25519; key=dGVzdA==\r\n"
    )
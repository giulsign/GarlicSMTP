# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.replies import ReplyFactory


def test_reply_greeting():
    reply = ReplyFactory.greeting(
        "garlicsmtp.onion"
    )

    assert reply.code == 220
    assert reply.serialize() == (
        b"220 garlicsmtp.onion ready\r\n"
    )
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.imap import IMAPReply


def test_imap_untagged_reply():

    reply = IMAPReply.untagged(
        "OK",
        "GarlicSMTP IMAP ready",
    )

    assert reply.serialize() == (
        "* OK GarlicSMTP IMAP ready\r\n"
    )


def test_imap_tagged_reply():

    reply = IMAPReply.tagged(
        "A001",
        "OK",
        "CAPABILITY completed",
    )

    assert reply.serialize() == (
        "A001 OK CAPABILITY completed\r\n"
    )
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

"""
SMTP reply factory.
"""

from garlicsmtp.models import SMTPReply


class ReplyFactory:

    @staticmethod
    def greeting(hostname: str) -> SMTPReply:
        return SMTPReply(
            220,
            f"{hostname} ready",
        )

    @staticmethod
    def ok(message: str = "OK") -> SMTPReply:
        return SMTPReply(250, message)

    @staticmethod
    def start_data() -> SMTPReply:
        return SMTPReply(
            354,
            "End data with <CR><LF>.<CR><LF>"
        )

    @staticmethod
    def bye() -> SMTPReply:
        return SMTPReply(
            221,
            "Bye"
        )

    @staticmethod
    def syntax_error() -> SMTPReply:
        return SMTPReply(
            500,
            "Syntax error"
        )

    @staticmethod
    def bad_sequence() -> SMTPReply:
        return SMTPReply(
            503,
            "Bad sequence of commands"
        )

    @staticmethod
    def mailbox_unavailable() -> SMTPReply:
        return SMTPReply(
            550,
            "Mailbox unavailable"
        )

    @staticmethod
    def transaction_failed() -> SMTPReply:
        return SMTPReply(
            554,
            "Transaction failed"
        )

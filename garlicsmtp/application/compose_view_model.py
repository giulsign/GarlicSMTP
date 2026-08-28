# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

class ComposeViewModel:

    def __init__(
        self,
        composer,
    ) -> None:
        self.composer = composer

        self.sender = ""
        self.recipient = ""
        self.subject = ""
        self.body = ""

    def send(
        self,
    ) -> bool:
        result = self.composer.send(
            sender=self.sender,
            recipient=self.recipient,
            subject=self.subject,
            body=self.body,
        )

        if result:
            self.clear()

        return result

    def clear(
        self,
    ) -> None:
        self.sender = ""
        self.recipient = ""
        self.subject = ""
        self.body = ""

    def set_default_sender(
        self,
        hostname: str,
    ) -> None:
        if self.sender:
            return

        hostname = hostname.strip()

        if not hostname:
            return

        self.sender = (
            "garlicsmtp@"
            + hostname
        )

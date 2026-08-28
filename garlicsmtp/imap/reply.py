# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass

from garlicsmtp.imap.response import (
    IMAPResponse,
)
from garlicsmtp.network.text import (
    TextConnection,
)


@dataclass(slots=True)
class IMAPReply(IMAPResponse):

    text: str

    def serialize(self) -> str:
        return self.text + "\r\n"

    def send(
        self,
        connection: TextConnection,
    ) -> None:
        connection.send(
            self.serialize()
        )

    @classmethod
    def untagged(
        cls,
        status: str,
        message: str,
    ) -> "IMAPReply":
        return cls(
            f"* {status} {message}"
        )

    @classmethod
    def tagged(
        cls,
        tag: str,
        status: str,
        message: str,
    ) -> "IMAPReply":
        return cls(
            f"{tag} {status} {message}"
        )
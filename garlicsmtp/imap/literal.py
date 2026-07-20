from dataclasses import dataclass

from garlicsmtp.imap.response import (
    IMAPResponse,
)
from garlicsmtp.network.text import (
    TextConnection,
)


@dataclass(slots=True)
class IMAPLiteralResponse(IMAPResponse):

    prefix: str

    content: bytes

    suffix: str = ")"

    def send(
        self,
        connection: TextConnection,
    ) -> None:
        connection.send(
            f"{self.prefix} "
            f"{{{len(self.content)}}}\r\n"
        )

        connection.send_bytes(
            self.content
        )

        connection.send(
            f"\r\n{self.suffix}\r\n"
        )
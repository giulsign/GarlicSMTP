# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from socket import socket


class SMTPConnection:
    """
    Wrapper di una connessione TCP.

    Non contiene logica SMTP.
    """

    BUFFER_SIZE = 4096

    def __init__(
        self,
        client: socket,
        address: tuple[str, int],
    ):
        self.client = client
        self.address = address
        self._buffer = b""

    @property
    def ip(self) -> str:
        return self.address[0]

    @property
    def port(self) -> int:
        return self.address[1]

    def send(self, data: bytes) -> None:
        self.client.sendall(data)

    def receive(self) -> bytes:
        return self.client.recv(self.BUFFER_SIZE)

    def receive_line(self) -> str | None:
        while b"\n" not in self._buffer:
            data = self.receive()

            if not data:
                if not self._buffer:
                    return None

                line = self._buffer
                self._buffer = b""
                return line.decode("utf-8").rstrip("\r\n")

            self._buffer += data

        line, self._buffer = self._buffer.split(b"\n", 1)

        return line.decode("utf-8").rstrip("\r\n")

    def close(self) -> None:
        self.client.close()
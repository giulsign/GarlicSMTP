# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import socket


class TextConnection:

    def __init__(
        self,
        timeout: float = 30.0,
        connected_socket: socket.socket | None = None,
    ):
        self.timeout = timeout
        self.socket = connected_socket
        self._buffer = b""

        if self.socket is not None:
            self.socket.settimeout(timeout)

    def connect(
        self,
        host: str,
        port: int = 25,
    ) -> None:
        self.socket = socket.create_connection(
            (host, port),
            timeout=self.timeout,
        )

    def send(
        self,
        text: str,
    ) -> None:
        if self.socket is None:
            raise RuntimeError(
                "Text connection is not open"
            )

        self.socket.sendall(
            text.encode("utf-8")
        )



    def send_bytes(
        self,
        data: bytes,
    ) -> None:
        if self.socket is None:
            raise RuntimeError(
                "Text connection is not open"
            )

        self.socket.sendall(data)


    def receive(self) -> str:
        if self.socket is None:
            raise RuntimeError("Text connection is not open")

        return self.socket.recv(
            4096
        ).decode("utf-8")

    def receive_line(self) -> str | None:
            if self.socket is None:
                raise RuntimeError("Text connection is not open")

            while b"\n" not in self._buffer:
                chunk = self.socket.recv(4096)

                if not chunk:
                    if not self._buffer:
                        return None

                    line = self._buffer
                    self._buffer = b""

                    return line.decode("utf-8").rstrip("\r\n")

                self._buffer += chunk

            line, self._buffer = self._buffer.split(
                b"\n",
                1,
            )

            return line.decode("utf-8").rstrip("\r")
        


    def receive_bytes(
        self,
        size: int,
    ) -> bytes | None:
        if size < 0:
            raise ValueError(
                "size must not be negative"
            )

        if self.socket is None:
            raise RuntimeError(
                "Connection is not open"
            )

        if size == 0:
            return b""

        while len(self._buffer) < size:
            chunk = self.socket.recv(
                max(
                    4096,
                    size - len(self._buffer),
                )
            )

            if not chunk:
                return None

            self._buffer += chunk

        result = self._buffer[:size]

        self._buffer = self._buffer[
            size:
        ]

        return result

    def close(self) -> None:
        if self.socket is not None:
            self.socket.close()
            self.socket = None

        self._buffer = b""
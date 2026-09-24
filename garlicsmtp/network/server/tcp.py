# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import socket


class TCPServer:
    def __init__(self, host: str, port: int, backlog: int = 5):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.socket: socket.socket | None = None

    def start(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(self.backlog)

    def accept(self):
        if self.socket is None:
            raise RuntimeError("TCP server is not started")

        return self.socket.accept()

    def stop(self) -> None:
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def accept_once(self):
        if self.socket is None:
            raise RuntimeError("TCP server is not started")

        self.socket.settimeout(0.1)

        try:
            return self.socket.accept()
        except socket.timeout:
            return None
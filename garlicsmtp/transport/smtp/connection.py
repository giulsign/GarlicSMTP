"""import socket


class SMTPConnection:

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.socket = None

    def connect(self, host: str, port: int = 25):

        self.socket = socket.create_connection(
            (host, port),
            timeout=self.timeout,
        )

    def send(self, line: str):

        self.socket.sendall(
            line.encode("utf-8")
        )

    def receive(self) -> str:

        return self.socket.recv(
            4096
        ).decode("utf-8")

    def close(self):

        if self.socket:
            self.socket.close()"""

import socket


class SMTPConnection:

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

    def send(self, text: str) -> None:
        if self.socket is None:
            raise RuntimeError("SMTP connection is not open")

        self.socket.sendall(
            text.encode("utf-8")
        )

    def receive(self) -> str:
        if self.socket is None:
            raise RuntimeError("SMTP connection is not open")

        return self.socket.recv(
            4096
        ).decode("utf-8")

    def receive_line(self) -> str | None:
        if self.socket is None:
            raise RuntimeError("SMTP connection is not open")

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

    def close(self) -> None:
        if self.socket is not None:
            self.socket.close()
            self.socket = None

        self._buffer = b""
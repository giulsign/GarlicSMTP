import socket

from garlicsmtp.network.socks5.exceptions import Socks5ConnectionError
from garlicsmtp.network.socks5.exceptions import Socks5HandshakeError


class Socks5Connection:

    def __init__(
        self,
        proxy_host: str = "127.0.0.1",
        proxy_port: int = 9050,
        timeout: float = 30.0,
    ):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.timeout = timeout
        self.socket = None

    def connect(self) -> None:
        try:
            self.socket = socket.create_connection(
                (self.proxy_host, self.proxy_port),
                timeout=self.timeout,
            )
        except OSError as exc:
            raise Socks5ConnectionError(
                f"Unable to connect to SOCKS5 proxy "
                f"{self.proxy_host}:{self.proxy_port}"
            ) from exc

    def send(self, data: bytes) -> None:
        self.socket.sendall(data)

    def receive(self, size: int = 4096) -> bytes:
        return self.socket.recv(size)

    def close(self) -> None:
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def handshake(self) -> None:
        self.send(
            b"\x05\x01\x00"
        )

        response = self.receive(2)

        if response != b"\x05\x00":
            raise Socks5HandshakeError(
                "SOCKS5 proxy rejected no-authentication method"
            )
        
    
    def receive_exactly(self, size: int) -> bytes:
        if self.socket is None:
            raise Socks5ConnectionError(
                "SOCKS5 connection is not open"
            )

        data = bytearray()

        while len(data) < size:
            chunk = self.socket.recv(
                size - len(data)
            )

            if not chunk:
                raise Socks5ConnectionError(
                    "SOCKS5 proxy closed the connection"
                )

            data.extend(chunk)

        return bytes(data)
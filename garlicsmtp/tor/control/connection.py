import ipaddress
import socket
from collections.abc import Callable


SocketFactory = Callable[
    [tuple[str, int], float],
    socket.socket,
]


class TorControlConnection:

    DEFAULT_TIMEOUT = 5.0
    DEFAULT_MAX_LINE_BYTES = 64 * 1024

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 9051,
        timeout: float = DEFAULT_TIMEOUT,
        max_line_bytes: int = (
            DEFAULT_MAX_LINE_BYTES
        ),
        socket_factory: (
            SocketFactory | None
        ) = None,
    ) -> None:
        self._validate_endpoint(
            host,
            port,
        )

        if timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero"
            )

        if max_line_bytes <= 0:
            raise ValueError(
                "max_line_bytes must be "
                "greater than zero"
            )

        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_line_bytes = (
            max_line_bytes
        )

        self.socket_factory = (
            socket_factory
            or socket.create_connection
        )

        self._socket: socket.socket | None = (
            None
        )

        self._receive_buffer = bytearray()

    @property
    def connected(
        self,
    ) -> bool:
        return self._socket is not None

    def connect(
        self,
    ) -> None:
        if self.connected:
            return

        try:
            connected_socket = (
                self.socket_factory(
                    (
                        self.host,
                        self.port,
                    ),
                    self.timeout,
                )
            )

            connected_socket.settimeout(
                self.timeout
            )

            self._socket = connected_socket

        except (
            OSError,
            TimeoutError,
        ) as exc:
            self.close()

            from garlicsmtp.tor.control.exceptions import (
                TorControlConnectionError,
            )

            raise TorControlConnectionError(
                "Unable to connect to the "
                "local Tor Control endpoint"
            ) from exc

    def send_line(
        self,
        line: str,
    ) -> None:
        control_socket = (
            self._require_socket()
        )

        normalized = self._normalize_line(
            line
        )

        try:
            control_socket.sendall(
                normalized.encode(
                    "utf-8"
                )
                + b"\r\n"
            )

        except (
            OSError,
            TimeoutError,
        ) as exc:
            self.close()

            from garlicsmtp.tor.control.exceptions import (
                TorControlConnectionError,
            )

            raise TorControlConnectionError(
                "Unable to send Tor "
                "Control command"
            ) from exc

    def receive_line(
        self,
    ) -> str:
        control_socket = (
            self._require_socket()
        )

        while True:
            separator = (
                self._receive_buffer.find(
                    b"\r\n"
                )
            )

            if separator >= 0:
                raw_line = bytes(
                    self._receive_buffer[
                        :separator
                    ]
                )

                del self._receive_buffer[
                    :separator + 2
                ]

                return self._decode_line(
                    raw_line
                )

            if (
                len(self._receive_buffer)
                > self.max_line_bytes
            ):
                self.close()

                from garlicsmtp.tor.control.exceptions import (
                    TorControlProtocolError,
                )

                raise TorControlProtocolError(
                    "Tor Control reply line "
                    "exceeds the configured limit"
                )

            try:
                chunk = control_socket.recv(
                    4096
                )

            except (
                OSError,
                TimeoutError,
            ) as exc:
                self.close()

                from garlicsmtp.tor.control.exceptions import (
                    TorControlConnectionError,
                )

                raise TorControlConnectionError(
                    "Unable to receive Tor "
                    "Control reply"
                ) from exc

            if not chunk:
                self.close()

                from garlicsmtp.tor.control.exceptions import (
                    TorControlConnectionError,
                )

                raise TorControlConnectionError(
                    "Tor Control connection "
                    "closed unexpectedly"
                )

            self._receive_buffer.extend(
                chunk
            )

    def close(
        self,
    ) -> None:
        control_socket = self._socket
        self._socket = None
        self._receive_buffer.clear()

        if control_socket is None:
            return

        try:
            control_socket.close()
        except OSError:
            pass

    def __enter__(
        self,
    ) -> "TorControlConnection":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        self.close()

    def _require_socket(
        self,
    ) -> socket.socket:
        if self._socket is None:
            from garlicsmtp.tor.control.exceptions import (
                TorControlConnectionError,
            )

            raise TorControlConnectionError(
                "Tor Control connection "
                "is not open"
            )

        return self._socket

    @staticmethod
    def _normalize_line(
        line: str,
    ) -> str:
        if "\r" in line or "\n" in line:
            from garlicsmtp.tor.control.exceptions import (
                TorControlProtocolError,
            )

            raise TorControlProtocolError(
                "Tor Control commands must "
                "contain exactly one line"
            )

        if not line:
            from garlicsmtp.tor.control.exceptions import (
                TorControlProtocolError,
            )

            raise TorControlProtocolError(
                "Tor Control command "
                "cannot be empty"
            )

        return line

    @staticmethod
    def _decode_line(
        raw_line: bytes,
    ) -> str:
        try:
            return raw_line.decode(
                "utf-8"
            )
        except UnicodeDecodeError as exc:
            from garlicsmtp.tor.control.exceptions import (
                TorControlProtocolError,
            )

            raise TorControlProtocolError(
                "Tor Control reply is not "
                "valid UTF-8"
            ) from exc

    @staticmethod
    def _validate_endpoint(
        host: str,
        port: int,
    ) -> None:
        if not isinstance(
            port,
            int,
        ) or isinstance(
            port,
            bool,
        ):
            raise TypeError(
                "port must be an integer"
            )

        if not 1 <= port <= 65535:
            raise ValueError(
                "port must be between "
                "1 and 65535"
            )

        try:
            address = ipaddress.ip_address(
                host
            )
        except ValueError as exc:
            from garlicsmtp.tor.control.exceptions import (
                TorControlSecurityError,
            )

            raise TorControlSecurityError(
                "Tor Control host must be "
                "an explicit loopback IP address"
            ) from exc

        if not address.is_loopback:
            from garlicsmtp.tor.control.exceptions import (
                TorControlSecurityError,
            )

            raise TorControlSecurityError(
                "Tor Control endpoint must "
                "use a loopback address"
            )
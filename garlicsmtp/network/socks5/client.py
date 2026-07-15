from garlicsmtp.network.socks5.connection import Socks5Connection
from garlicsmtp.network.socks5.exceptions import Socks5HandshakeError
from garlicsmtp.network.socks5.reply import Socks5Reply
from garlicsmtp.network.socks5.request import Socks5ConnectRequest


class Socks5Client:

    def __init__(
        self,
        connection: Socks5Connection | None = None,
    ):
        self.connection = connection or Socks5Connection()

    def connect(
        self,
        host: str,
        port: int,
    ) -> Socks5Connection:
        self.connection.connect()

        self.connection.handshake()

        request = Socks5ConnectRequest(
            host=host,
            port=port,
        )

        self.connection.send(
            request.serialize()
        )

        reply_data = self._receive_connect_reply()

        reply = Socks5Reply.parse(reply_data)

        if not reply.success:
            raise Socks5HandshakeError(
                reply.message
            )

        return self.connection
    

    def _receive_connect_reply(self) -> bytes:
        header = self.connection.receive_exactly(4)

        address_type = header[3]

        if address_type == 0x01:
            address = self.connection.receive_exactly(4)

        elif address_type == 0x03:
            length = self.connection.receive_exactly(1)
            address = (
                length
                + self.connection.receive_exactly(
                    length[0]
                )
            )

        elif address_type == 0x04:
            address = self.connection.receive_exactly(16)

        else:
            raise Socks5HandshakeError(
                f"Unsupported SOCKS5 address type: "
                f"{address_type:#x}"
            )

        port = self.connection.receive_exactly(2)

        return header + address + port
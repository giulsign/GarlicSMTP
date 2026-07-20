import threading

from garlicsmtp.imap.protocol import IMAPProtocol
from garlicsmtp.imap.session import IMAPSessionState
from garlicsmtp.network.server import TCPServer
from garlicsmtp.network.text import TextConnection
from garlicsmtp.security.auth import (
    Authenticator,
    RejectingAuthenticator,
)
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.imap.append import (
    IMAPAppendError,
    IMAPAppendParser,
)
from garlicsmtp.imap.reply import (
    IMAPReply,
)

class IMAPServer:

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 1143,
        hostname: str = "garlicsmtp.local",
        authenticator: Authenticator | None = None,
        store: MessageStore | None = None,
    ):
        self.host = host
        self.port = port
        self.hostname = hostname

        self.server = TCPServer(
            host=host,
            port=port,
        )

        self.running = False

        self._connection_threads = set()
        self._threads_lock = threading.Lock()
        self.connection_factory = TextConnection
        self.authenticator = (authenticator or RejectingAuthenticator())
        self.store = store or MessageStore()
        self._clients_lock = threading.Lock()
        self._client_threads = set()
        #self._clients = set()

    def start(self) -> None:
        self.server.start()
        self.running = True

        print(
            f"IMAP Server listening on "
            f"{self.host}:{self.port}"
        )

    def stop(self) -> None:
        self.running = False
        self.server.stop()

        with self._threads_lock:
            threads = list(
                self._connection_threads
            )

        for thread in threads:
            thread.join(timeout=2)

    def tick(self) -> None:
        if not self.running:
            return

        try:
            accepted = self.server.accept_once()

        except OSError:

            if not self.running:
                return

            raise

        if accepted is None:
            return

        client_socket, address = accepted

        thread = threading.Thread(
            target=self._serve_connection,
            args=(
                client_socket,
                address,
            ),
            daemon=True,
            name=(
                f"imap-{address[0]}:"
                f"{address[1]}"
            ),
        )

        with self._threads_lock:
            self._connection_threads.add(
                thread
            )

        thread.start()

    @staticmethod
    def _append_tag(
        line: str,
    ) -> str:
        parts = line.strip().split(
            None,
            1,
        )

        if not parts:
            return "*"

        return parts[0]
    
    @staticmethod
    def _send_continuation(
        connection,
    ) -> None:
        connection.send(
            "+ Ready for literal data\r\n"
        )

    def _handle_append(
        self,
        connection,
        protocol: IMAPProtocol,
        line: str,
    ) -> bool:
        try:
            request = IMAPAppendParser.parse(
                line
            )

        except IMAPAppendError as exc:
            self._send_replies(
                connection,
                [
                    IMAPReply.tagged(
                        self._append_tag(
                            line
                        ),
                        "BAD",
                        str(exc),
                    )
                ],
            )

            return True

        literals = []

        for item in request.items:
            if not item.non_synchronizing:
                self._send_continuation(
                    connection
                )

            literal = connection.receive_bytes(
                item.literal_size
            )

            if literal is None:
                return False

            literals.append(
                literal
            )

        replies = protocol.append_literals(
            request,
            literals,
        )

        self._send_replies(
            connection,
            replies,
        )

        return True

    def _serve_connection(
        self,
        client_socket,
        address,
    ) -> None:
        current = threading.current_thread()

        connection = self._create_connection(
            client_socket
        )

        protocol = IMAPProtocol(
            authenticator=self.authenticator,
            store=self.store,
        )

        try:
            self._send_replies(
                connection,
                protocol.greeting(),
            )

            while self.running:
                line = connection.receive_line()

                if line is None:
                    break

                if (
                    IMAPAppendParser
                    .is_append_command(line)
                ):
                    completed = self._handle_append(
                        connection,
                        protocol,
                        line,
                    )

                    if not completed:
                        break

                    continue

                replies = protocol.execute(
                    line
                )

                self._send_replies(
                    connection,
                    replies,
                )

                if (
                    protocol.session.state
                    is IMAPSessionState.LOGOUT
                ):
                    break

        finally:
            connection.close()

            with self._clients_lock:
                self._client_threads.discard(
                    current
                )

    @staticmethod   
    def _send_replies(
        connection: TextConnection,
        replies,
    ) -> None:
        for response in replies:
            response.send(
                connection
            )

    @property
    def active_connections(self) -> int:
        with self._threads_lock:
            return len(
                self._connection_threads
            )
        
    def _create_connection(
        self,
        client_socket,
    ) -> TextConnection:
        return self.connection_factory(
            connected_socket=client_socket,
        )
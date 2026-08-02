import threading

from garlicsmtp.imap.append import (
    IMAPAppendError,
    IMAPAppendParser,
)
from garlicsmtp.imap.command_result import (
    IMAPCommandAction,
)
from garlicsmtp.imap.protocol import IMAPProtocol
from garlicsmtp.imap.reply import IMAPReply
from garlicsmtp.imap.session import IMAPSessionState
from garlicsmtp.network.server import TCPServer
from garlicsmtp.network.text import TextConnection
from garlicsmtp.security.auth import (  
    Authenticator,
    RejectingAuthenticator,
)
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.imap.idle import (
    IMAPIdleSession,
)
from garlicsmtp.imap.store_event_adapter import (
    IMAPStoreEventAdapter,
)
from garlicsmtp.storage.composite_event_sink import (
    CompositeStoreEventSink,
)
from dataclasses import dataclass



@dataclass
class IMAPConnectionContext:
    connection: TextConnection
    protocol: IMAPProtocol
    idle: IMAPIdleSession
    store_event_adapter: IMAPStoreEventAdapter


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
        self.authenticator = (
            authenticator
            or RejectingAuthenticator()
        )
        self.store = store or MessageStore()
        existing_sink = self.store.event_sink

        if isinstance(
            existing_sink,
            CompositeStoreEventSink,
        ):
            self.store_event_sink = existing_sink
        else:
            self.store_event_sink = (
                CompositeStoreEventSink()
            )

            self.store_event_sink.add(
                existing_sink
            )

            self.store.event_sink = (
                self.store_event_sink
            )


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
    def _send_continuation(
        connection,
        message: str = (
            "Ready for literal data"
        ),
    ) -> None:
        connection.send(
            f"+ {message}\r\n"
        )

    def _serve_connection(
        self,
        client_socket,
        address,
    ) -> None:
        current = threading.current_thread()

        context = self._create_connection_context(
            client_socket,
        )

        handler = IMAPConnectionHandler(
            self,
            context,
        )

        connection = context.connection
        protocol = context.protocol
        idle = context.idle

        try:
            self._send_replies(
                connection,
                protocol.greeting(),
            )

            while self.running:
                if not handler.process_iteration():
                    break

        finally:
            self.store_event_sink.remove(   
                context.store_event_adapter
            )

            connection.close()

            with self._threads_lock:
                self._connection_threads.discard(
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


    def _create_protocol(
        self,
    ) -> IMAPProtocol:
        return IMAPProtocol(
            authenticator=self.authenticator,
            store=self.store,
        )
    
    def _create_idle_session(
            self,
        ) -> IMAPIdleSession:
            return IMAPIdleSession()
        
    def _create_connection_context(
        self,
        client_socket,
    ) -> IMAPConnectionContext:
        connection = self._create_connection(
            client_socket
        )

        protocol = self._create_protocol()

        idle = self._create_idle_session()

        adapter = IMAPStoreEventAdapter(
            notification_sink=idle,
            selected_mailbox=(
                lambda: (
                    protocol.session.selected_mailbox
                    if idle.active
                    else None
                )
            ),
            mailbox_count=(
                lambda mailbox: self.store.count(
                    mailbox
                )
            ),
        )

        self.store_event_sink.add(
            adapter
        )

        return IMAPConnectionContext(
            connection=connection,
            protocol=protocol,
            idle=idle,
            store_event_adapter=adapter,
        )
    

class IMAPConnectionHandler:

    def __init__(
        self,
        server: "IMAPServer",
        context: IMAPConnectionContext,
    ) -> None:
        self._server = server
        self._context = context

    def process_iteration(
        self,
    ) -> bool:
        connection = self._context.connection

        line = connection.receive_line()

        if line is None:
            return False

        self._send_idle_notifications()

        if self._handle_idle_input(
                line,
            ):
                return True

        if (
            IMAPAppendParser
            .is_append_command(line)
        ):
            return self._handle_append(
                line,
            )

        self._execute_command(
            line,
        )

        return not self._should_close_connection()
        
    def _should_close_connection(
        self,
    ) -> bool:
        return (
            self._context.protocol.session.state
            is IMAPSessionState.LOGOUT
        )
    

    def _execute_command(
        self,
        line: str,
    ) -> None:
        connection = self._context.connection
        protocol = self._context.protocol
        idle = self._context.idle

        replies = protocol.execute(
            line,
        )

        self._server._send_replies(
            connection,
            replies,
        )

        self._enter_idle(line)

    def _handle_idle_input(
        self,
        line: str,
    ) -> bool:
        idle = self._context.idle
        connection = self._context.connection

        if not idle.active:
            return False

        replies = idle.handle_input(
            line,
        )

        self._server._send_replies(
            connection,
            replies,
        )

        return True


    def _enter_idle(
        self,
        line: str,
    ) -> None:
        protocol = self._context.protocol
        idle = self._context.idle
        connection = self._context.connection

        if (
            protocol.command_action()
            is not IMAPCommandAction.ENTER_IDLE
        ):
            return

        idle.enter(
            self._append_tag(line),
        )

        connection.send(
            "+ idling\r\n"
        )


    
    def _send_idle_notifications(
        self,
    ) -> None:
        connection = self._context.connection
        idle = self._context.idle

        if not idle.has_notifications():
            return

        for notification in (
            idle.drain_notifications()
        ):
            connection.send(
                f"{notification}\r\n"
            )

    def _handle_append(
        self,
        line: str,
    ) -> bool:
        connection = self._context.connection
        protocol = self._context.protocol

        try:
            request = IMAPAppendParser.parse(
                line
            )

        except IMAPAppendError as exc:
            self._server._send_replies(
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
                self._server._send_continuation(
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

        self._server._send_replies(
            connection,
            replies,
        )

        return True

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
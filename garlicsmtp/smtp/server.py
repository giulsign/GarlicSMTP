from socket import socket

from garlicsmtp.network.server import TCPServer
from garlicsmtp.smtp.connection import SMTPConnection
from garlicsmtp.smtp.protocol import SMTPProtocol
from garlicsmtp.core.service import Service
from garlicsmtp.core.tickable import Tickable
from garlicsmtp.logger import Logger
import threading


class SMTPServer(Service, Tickable):
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 2525,
        hostname: str = "localhost",
        logger=None,
        pipeline=None,
    ):
        self.server = TCPServer(host, port)
        self.hostname = hostname
        self.running = False
        self.host = host
        self.port = port
        self.logger = logger or Logger()
        self.pipeline = pipeline
        self._connection_threads = set()
        self._threads_lock = threading.Lock()

    def start(self) -> None:
        self.server.start()
        self.logger.info(f"SMTP Server listening on {self.host}:{self.port}")
        self.running = True


    def stop(self) -> None:
        self.running = False
        self.server.stop()
        with self._threads_lock:
            threads = list(
                self._connection_threads
            )

        for thread in threads:
            thread.join(timeout=2)



    def handle_connection(
        self,
        client: socket,
        address: tuple[str, int],
    ) -> None:
        connection = SMTPConnection(
            client,
            address,
        )

        protocol = SMTPProtocol(
            connection,
            hostname=self.hostname,
            pipeline=self.pipeline,
        )

        protocol.serve()

    
    def tick(self) -> None:
        if not self.running:
            return

        accepted = self.server.accept_once()

        if accepted is None:
            return

        client, address = accepted

        thread = threading.Thread(
            target=self._serve_connection,
            args=(client, address),
            daemon=True,
            name=f"smtp-{address[0]}:{address[1]}",
        )

        with self._threads_lock:
            self._connection_threads.add(thread)

        thread.start()


    
    def _serve_connection(
        self,
        client,
        address,
    ) -> None:
        current = threading.current_thread()

        try:
            self.handle_connection(
                client,
                address,
            )
        except Exception as exc:
            self.logger.error(
                f"SMTP connection error from "
                f"{address[0]}:{address[1]}: {exc}"
            )
        finally:
            try:
                client.close()
            except Exception:
                pass

            with self._threads_lock:
                self._connection_threads.discard(
                    current
                )

    
    @property
    def active_connections(self) -> int:
        with self._threads_lock:
            return len(
                self._connection_threads
            )
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import threading
from socket import socket

from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.core.service import Service
from garlicsmtp.core.tickable import Tickable
from garlicsmtp.logger import Logger
from garlicsmtp.network.server import TCPServer
from garlicsmtp.smtp.connection import SMTPConnection
from garlicsmtp.smtp.protocol import SMTPProtocol
from garlicsmtp.security.verifier import MessageVerifier


class SMTPServer(Service, Tickable):

    def __init__(
        self,
        *,
        pipeline: Pipeline,
        host: str = "127.0.0.1",
        port: int = 2525,
        hostname: str = "localhost",
        logger=None,
        verifier: MessageVerifier | None = None,
        e2ee_capability: str | None = None,
    ):
        self.server = TCPServer(
            host,
            port,
        )

        self.hostname = hostname
        self.running = False
        self.host = host
        self.port = port
        self.logger = logger or Logger()
        self.pipeline = pipeline
        self.verifier = verifier
        self.e2ee_capability = e2ee_capability
        self._connection_threads = set()
        self._threads_lock = threading.Lock()

    def start(self) -> None:
        self.server.start()

        self.logger.info(
            f"SMTP Server listening on "
            f"{self.host}:{self.port}"
        )

        self.running = True

    def stop(self) -> None:
        self.running = False
        self.server.stop()

        with self._threads_lock:
            threads = list(
                self._connection_threads
            )

        for thread in threads:
            thread.join(
                timeout=2
            )

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
            verifier=self.verifier,
            e2ee_capability=self.e2ee_capability,
        )

        protocol.serve()

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

        client, address = accepted

        thread = threading.Thread(
            target=self._serve_connection,
            args=(
                client,
                address,
            ),
            daemon=True,
            name="smtp-connection",
        )

        with self._threads_lock:
            self._connection_threads.add(
                thread
            )

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
                "SMTP connection error "
                f"[{type(exc).__name__}]"
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
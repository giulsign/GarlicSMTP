# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path

from garlicsmtp.application.builder import (
    ApplicationBuilder,
)
from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
    IMAPSettings,
    SMTPSettings,
    TorSettings,
)
from garlicsmtp.core.engine.app import GarlicSMTP
from garlicsmtp.core.engine.config import (
    GarlicSMTPConfig,
)
from garlicsmtp.logger import Logger
from garlicsmtp.storage.sqlite import (
    SQLiteMessageStoreBackend,
)
from garlicsmtp.transport.onion.transport import (
    OnionTransport,
)


class Bootstrap:

    def __init__(
        self,
        config: GarlicSMTPConfig | None = None,
        default_transport=None,
        queue_backend=None,
    ):
        self.config = (
            config
            or GarlicSMTPConfig()
        )

        self.default_transport = (
            default_transport
        )

        self.queue_backend = (
            queue_backend
        )

        self._context = None
        self._application = None
        self._onion_transport = None
        self._logger = None

    def _build_settings(
        self,
    ) -> ApplicationSettings:
        return ApplicationSettings(
            hostname=self.config.hostname,
            local_domain=self.config.hostname,
            smtp=SMTPSettings(
                host=self.config.listen_host,
                port=self.config.listen_port,
            ),
            imap=IMAPSettings(),
            tor=TorSettings(
                enabled=False,
                socks_host=(
                    self.config.socks_host
                ),
                socks_port=(
                    self.config.socks_port
                ),
            ),
        )

    def _build_paths(
        self,
    ) -> ApplicationPaths:
        mailbox_path = Path(
            self.config.mailbox_db
        )

        if mailbox_path.parent == Path("."):
            root_dir = (
                ApplicationPaths.for_user()
                .root_dir
            )
        else:
            root_dir = (
                mailbox_path.parent
                / ".garlicsmtp-runtime"
            )

        return ApplicationPaths(
            root_dir=root_dir
        )

    def build_context(
        self,
    ):
        if self._context is None:
            message_store_backend = (
                SQLiteMessageStoreBackend(
                    self.config.mailbox_db
                )
            )

            self._context = (
                ApplicationBuilder(
                    paths=self._build_paths(),
                    settings=(
                        self._build_settings()
                    ),
                    default_transport=(
                        self.default_transport
                    ),
                    queue_backend=(
                        self.queue_backend
                    ),
                    message_store_backend=(
                        message_store_backend
                    ),
                    logger=self.build_logger(),
                ).build()
            )

        return self._context

    def build(
        self,
    ) -> GarlicSMTP:
        if self._application is None:
            self._application = GarlicSMTP(
                self.build_context()
            )

        return self._application

    def build_runtime(self):
        return self.build_context().runtime

    def build_server(self):
        return self.build_context().smtp_server

    def build_worker(self):
        return self.build_context().queue_worker

    def build_queue(self):
        return self.build_context().queue

    def build_transport(self):
        return self.build_context().transport

    def build_pipeline(self):
        return self.build_context().pipeline

    def build_message_store(self):
        return self.build_context().store

    def build_logger(self) -> Logger:
        if self._logger is None:
            self._logger = Logger()

        return self._logger

    def build_onion_transport(
        self,
    ) -> OnionTransport:
        if self._onion_transport is None:
            self._onion_transport = (
                OnionTransport(
                    socks_host=(
                        self.config.socks_host
                    ),
                    socks_port=(
                        self.config.socks_port
                    ),
                )
            )

        return self._onion_transport
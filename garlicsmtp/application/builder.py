# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from garlicsmtp.core.engine.runtime import (
        Runtime,
    )


from garlicsmtp.application.context import (
    ApplicationContext,
)
from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
    ConfigurationLoader,
)
from garlicsmtp.core.pipeline import (
    LoggerStage,
    Pipeline,
)
from garlicsmtp.queue.manager import (
    QueueManager,
)
from garlicsmtp.queue.sqlite import (
    SQLiteQueueBackend,
)
from garlicsmtp.queue.stage import (
    QueueStage,
)
from garlicsmtp.storage.delivery_stage import (
    DeliveryStage,
)
from garlicsmtp.storage.sqlite import (
    SQLiteMessageStoreBackend,
)
from garlicsmtp.storage.store import (
    MessageStore,
)
from garlicsmtp.transport.manager import (
    TransportManager,
)
from garlicsmtp.transport.onion.transport import (
    OnionTransport,
)
from garlicsmtp.imap.server import (
    IMAPServer,
)
from garlicsmtp.logger import (
    Logger,
)
from garlicsmtp.queue.worker import (
    QueueWorker,
)
from garlicsmtp.smtp.server import (
    SMTPServer,
)
from garlicsmtp.logger import Logger
from garlicsmtp.storage.backend import (
    MessageStoreBackend,
)
from garlicsmtp.transport.base import Transport
from garlicsmtp.application.tor_monitor_service import (
    TorMonitorService,
)
from garlicsmtp.application.tor_status_provider import (
    TorStatusProvider,
)
from garlicsmtp.application.event_hub import (
    ApplicationEventHub,
)
from garlicsmtp.application.event_log import (
    ApplicationEventLog,
)
from garlicsmtp.application.event_service import (
    ApplicationEventService,
)
from garlicsmtp.tor.control import (
    SafeCookieAuthenticator,
    TorControlClient,
    TorControlConnection,
)
from garlicsmtp.tor.onion_service_manager import (
    OnionServiceManager,    
)
from garlicsmtp.security.signer import (
    MessageSigner,
)
from garlicsmtp.security.signing_identity import (
    SigningIdentity,
)
from garlicsmtp.security.trust_store import (
    FileTrustStore,
)
from garlicsmtp.security.verifier import (
    Ed25519MessageVerifier,
)
from garlicsmtp.security.encryption_identity import (
    EncryptionIdentity,
)
from garlicsmtp.security.encryption_capability import (
    EncryptionCapability,
)
from garlicsmtp.security.encryption_key_store import (
    FileEncryptionKeyStore,
)
from garlicsmtp.security.encryptor import (
    MessageEncryptor,
)


class ApplicationBuilder:

    def __init__(
        self,
        *,
        paths: ApplicationPaths | None = None,
        settings: ApplicationSettings | None = None,
        configuration_loader: ConfigurationLoader | None = None,
        default_transport: Transport | None = None,
        queue_backend=None,
        message_store_backend: MessageStoreBackend | None = None,
        logger: Logger | None = None,
    ) -> None:
        self.paths = (
            paths
            if paths is not None
            else ApplicationPaths.for_development()
        )

        self.configuration_loader = (
            configuration_loader
            or ConfigurationLoader()
        )

        self.settings = settings
        self.default_transport = default_transport
        self.queue_backend = queue_backend
        self.message_store_backend = (
            message_store_backend
        )
        self.logger = logger

    def build(
        self,
    ) -> ApplicationContext:
        self.paths.create_directories()

        settings = (
            self.settings
            or self.configuration_loader.load(
                self.paths.settings_file
            )
        )

        local_domains = {
            settings.local_domain,
            settings.hostname,
        }

        logger = self._build_logger()
        event_hub = self._build_event_hub()

        event_log = self._build_event_log()

        event_service = self._build_event_service(
            event_log=event_log,
            event_hub=event_hub,
        )

        store = self._build_store()
        queue = self._build_queue()

        encryption_key_store = FileEncryptionKeyStore(
            self.paths.root_dir / "encryption_keys.json"
        )

        transport = self._build_transport(
            settings,
            encryption_key_store=encryption_key_store,
        )

        pipeline = self._build_pipeline(
            settings=settings,
            store=store,
            queue=queue,
            local_domains=local_domains,
            encryption_key_store=(
                encryption_key_store
            ),
            transport=transport,    
        )

        signing_identity = SigningIdentity(
            self.paths.root_dir / "signing.key"
        )

        encryption_identity = EncryptionIdentity(
            self.paths.root_dir / "encryption.key"
        )

        e2ee_capability = EncryptionCapability(
            public_key=(
                encryption_identity.private_key
                .public_key()
            )
        ).serialize()

        signer = MessageSigner(
            signing_identity.private_key
        )

        trust_store = FileTrustStore(
            self.paths.root_dir / "trusted_keys.json"
        )

        #encryption_key_store = FileEncryptionKeyStore(
        #    self.paths.root_dir / "encryption_keys.json"
        #)

        verifier = Ed25519MessageVerifier(
            trust_store=trust_store
        )

        signing_public_key = (
            signing_identity.private_key
            .public_key()
            .public_bytes_raw()
        )

        def register_local_hostname(
            hostname: str,
        ) -> None:
            local_domains.add(
                hostname
            )

            trust_store.trust(
                "garlicsmtp@" + hostname,
                signing_public_key,
            )

        smtp_server = self._build_smtp_server(
            settings=settings,
            pipeline=pipeline,
            logger=logger,
            verifier=verifier,
            e2ee_capability=e2ee_capability,
        )

        imap_server = self._build_imap_server(
            settings=settings,
            store=store,
        )

        queue_worker = self._build_queue_worker(
            queue=queue,
            transport=transport,
            logger=logger,
        )

        onion_service = None

        if settings.tor.enabled:
            onion_service = (
                self._build_onion_service(
                    settings,
                    hostname_callback=register_local_hostname,
                )
            )

        tor_status_provider = (
            self._build_tor_status_provider(
                settings,
                onion_service=onion_service,
            )
        )

        tor_monitor = self._build_tor_monitor(
            provider=tor_status_provider,
            event_hub=event_hub,
            event_service=event_service,
        )

        runtime = self._build_runtime(
            smtp_server=smtp_server,
            imap_server=imap_server,
            queue_worker=queue_worker,
            onion_service=onion_service,
            tor_monitor=tor_monitor,
            logger=logger,
        )
        return ApplicationContext(
            paths=self.paths,
            settings=settings,
            logger=logger,
            event_hub=event_hub,
            event_log=event_log,
            event_service=event_service,
            store=store,
            queue=queue,
            transport=transport,
            pipeline=pipeline,
            signer=signer,
            encryption_key_store=encryption_key_store,
            verifier=verifier,
            smtp_server=smtp_server,
            imap_server=imap_server,
            queue_worker=queue_worker,
            onion_service=onion_service,
            tor_monitor=tor_monitor,
            runtime=runtime,
        )

    def _build_store(
        self,
    ) -> MessageStore:
        backend = (
            self.message_store_backend
            or SQLiteMessageStoreBackend(
                self.paths.mailbox_database
            )
        )

        return MessageStore(
            backend=backend
        )
    
    def _build_queue(
        self,
    ) -> QueueManager:
        backend = (
            self.queue_backend
            or SQLiteQueueBackend(
                self.paths.queue_database
            )
        )

        return QueueManager(
            backend=backend
        )

    def _build_transport(
        self,
        settings: ApplicationSettings,
        *,
        encryption_key_store: FileEncryptionKeyStore,
    ) -> TransportManager:

        def remember_e2ee_capability(
            hostname,
            capability,
        ) -> None:
            encryption_key_store.remember(
                hostname,
                capability.public_key.public_bytes_raw(),
            )

        if self.default_transport is not None:
            default_transport = (
                self.default_transport
            )

            if isinstance(
                default_transport,
                OnionTransport,
            ):
                default_transport.e2ee_capability_callback = (
                    remember_e2ee_capability
                )

        else:
            default_transport = OnionTransport(
                socks_host=(
                    settings.tor.socks_host
                ),
                socks_port=(
                    settings.tor.socks_port
                ),
                e2ee_capability_callback=(
                    remember_e2ee_capability
                ),
            )

        return TransportManager(
            default_transport=default_transport
        )

    @staticmethod
    def _build_pipeline(
        *,
        settings: ApplicationSettings,
        store: MessageStore,
        queue: QueueManager,
        local_domains: set[str],
        encryption_key_store,
        transport: TransportManager,
    ) -> Pipeline:
        queue_stage = QueueStage(
            queue
        )

        pipeline = Pipeline()

        pipeline.add(
            LoggerStage()
        )

        default_transport = (
            transport.default_transport
        )

        discover_encryption_key = getattr(
            default_transport,
            "discover_e2ee_capability",
            None,
)

        pipeline.add(
            DeliveryStage(
                store=store,
                queue_stage=queue_stage,
                local_domains=local_domains,
                encryptor=MessageEncryptor(),
                encryption_key_store=(
                    encryption_key_store
                ),
                discover_encryption_key=(
                    discover_encryption_key
                ),
            )
        )

        return pipeline

    def _build_logger(
        self,
    ) -> Logger:
        return self.logger or Logger()

    @staticmethod
    def _build_smtp_server(
        *,
        settings: ApplicationSettings,
        pipeline: Pipeline,
        logger: Logger,
        verifier: Ed25519MessageVerifier,
        e2ee_capability: str,
    ) -> SMTPServer:
        return SMTPServer(
            pipeline=pipeline,
            host=settings.smtp.host,
            port=settings.smtp.port,
            hostname=settings.hostname,
            logger=logger,
            verifier=verifier,
            e2ee_capability=e2ee_capability,
    )

    @staticmethod
    def _build_imap_server(
        *,
        settings: ApplicationSettings,
        store: MessageStore,
    ) -> IMAPServer:
        return IMAPServer(
            host=settings.imap.host,
            port=settings.imap.port,
            hostname=settings.hostname,
            store=store,
        )

    @staticmethod
    def _build_queue_worker(
        *,
        queue: QueueManager,
        transport: TransportManager,
        logger: Logger,
    ) -> QueueWorker:
        return QueueWorker(
            queue=queue,
            transport=transport,
            logger=logger,
        )

    @staticmethod
    def _build_runtime(
        *,
        smtp_server: SMTPServer,
        imap_server: IMAPServer,
        queue_worker: QueueWorker,
        onion_service,
        tor_monitor: TorMonitorService,
        logger: Logger,
    ) -> Runtime:
        from garlicsmtp.core.engine.runtime import (
            Runtime,
        )

        services = [
            smtp_server,
        ]

        if onion_service is not None:
            services.append(
                onion_service
            )

        services.extend(
            [
                imap_server,
                queue_worker,
                tor_monitor,
            ]
        )

        return Runtime(
            services=services,
            tasks=[
                smtp_server,
                imap_server,
                queue_worker,
                tor_monitor,
            ],
            logger=logger,
        )

    def _build_onion_service(
        self,
        settings: ApplicationSettings,
        *,
        hostname_callback=None,
    ) -> OnionServiceManager:
        connection = TorControlConnection(
            host=settings.tor.control_host,
            port=settings.tor.control_port,
        )

        client = TorControlClient(
            connection=connection
        )

        authenticator = SafeCookieAuthenticator(
            client=client,
            configured_cookie_file=(
                settings.tor.cookie_file
            ),
        )

        return OnionServiceManager(
            client=client,
            authenticator=authenticator,
            identity_file=(
                self.paths.onion_identity_file
            ),
            virtual_port=(
                settings.tor.onion_smtp_port
            ),
            target_host=settings.smtp.host,
            target_port=settings.smtp.port,
            hostname_callback=hostname_callback,
        )


    @staticmethod
    def _build_tor_status_provider(
        settings: ApplicationSettings,
        *,
        onion_service=None,
    ) -> TorStatusProvider:
        return TorStatusProvider(
            settings.tor,
            onion_hostname_provider=(
                (
                    lambda: onion_service.hostname
                )
                if onion_service is not None
                else None
            ),
        )


    @staticmethod
    def _build_tor_monitor(
        *,
        provider: TorStatusProvider,
        event_hub: ApplicationEventHub,
        event_service: ApplicationEventService,
    ) -> TorMonitorService:
        return TorMonitorService(
            provider=provider,
            event_hub=event_hub,
            event_service=event_service,
            interval_seconds=10.0,
        )

    @staticmethod
    def _build_event_hub(
    ) -> ApplicationEventHub:
        return ApplicationEventHub()

    @staticmethod
    def _build_event_log(
    ) -> ApplicationEventLog:
        return ApplicationEventLog(
            capacity=500
        )


    @staticmethod
    def _build_event_service(
        *,
        event_log: ApplicationEventLog,
        event_hub: ApplicationEventHub,
    ) -> ApplicationEventService:
        return ApplicationEventService(
            event_log=event_log,
            event_hub=event_hub,
        )

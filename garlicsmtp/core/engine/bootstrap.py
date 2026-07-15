from garlicsmtp.core.engine.app import GarlicSMTP
from garlicsmtp.core.engine.config import GarlicSMTPConfig
from garlicsmtp.core.engine.runtime import Runtime
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.worker import QueueWorker
from garlicsmtp.smtp.server import SMTPServer
from garlicsmtp.transport.manager import TransportManager
from garlicsmtp.transport.onion.transport import OnionTransport
from garlicsmtp.logger import Logger
from garlicsmtp.core.pipeline import LoggerStage
from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.storage.delivery_stage import DeliveryStage
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.storage.sqlite import (SQLiteMessageStoreBackend,)


class Bootstrap:

    def __init__(
        self,
        config: GarlicSMTPConfig | None = None,
        default_transport=None,
        queue_backend=None,
    ):
        self.config = config or GarlicSMTPConfig()
        self.default_transport = default_transport

        self._logger = None
        self._queue = None
        self._transport = None
        self._onion_transport = None
        self._worker = None
        self._server = None
        self._runtime = None
        self._pipeline = None
        self.queue_backend = queue_backend
        self._message_store = None
        


    def build(self) -> GarlicSMTP:
        return GarlicSMTP(
            runtime=self.build_runtime(),
        )
    

    def build_runtime(self) -> Runtime:
        if self._runtime is None:
            server = self.build_server()
            worker = self.build_worker()

            self._runtime = Runtime(
                services=[
                    server,
                    worker,
                ],
                tasks=[
                    server,
                    worker,
                ],
                logger=self.build_logger(),
            )

        return self._runtime

    def build_server(self) -> SMTPServer:
        if self._server is None:
            self._server = SMTPServer(
                host=self.config.listen_host,
                port=self.config.listen_port,
                hostname=self.config.hostname,
                logger=self.build_logger(),
                pipeline=self.build_pipeline(),
            )

        return self._server

    def build_worker(self) -> QueueWorker:
        if self._worker is None:
            self._worker = QueueWorker(
                queue=self.build_queue(),
                transport=self.build_transport(),
                logger=self.build_logger(),
            )

        return self._worker

    def build_queue(self) -> QueueManager:
        if self._queue is None:
            self._queue = QueueManager(backend=self.queue_backend)

        return self._queue

    def build_transport(self) -> TransportManager:
        if self._transport is None:
            self._transport = TransportManager(
                default_transport=(
                    self.default_transport
                    or self.build_onion_transport()
                ),
            )

        return self._transport

    def build_onion_transport(self) -> OnionTransport:
        if self._onion_transport is None:
            self._onion_transport = OnionTransport(
                socks_host=self.config.socks_host,
                socks_port=self.config.socks_port,
                hostname=self.config.hostname,
            )

        return self._onion_transport
    
    def build_logger(self) -> Logger:
        if self._logger is None:
            self._logger = Logger()

        return self._logger
    

    def build_pipeline(self) -> Pipeline:
        if self._pipeline is None:
            queue_stage = QueueStage(
                self.build_queue()
            )

            self._pipeline = Pipeline()

            self._pipeline.add(
                LoggerStage()
            )

            self._pipeline.add(
                DeliveryStage(
                    store=self.build_message_store(),
                    queue_stage=queue_stage,
                    local_domains={
                        self.config.hostname,
                    },
                )
            )

        return self._pipeline
    

    def build_message_store(self) -> MessageStore:
        if self._message_store is None:
            backend = SQLiteMessageStoreBackend(
                self.config.mailbox_db
            )

            self._message_store = MessageStore(
                backend=backend,
            )

        return self._message_store
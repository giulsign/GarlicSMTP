from pathlib import Path

from garlicsmtp.application.controller import (
    ApplicationController,
)
from garlicsmtp.application.context import (
    ApplicationContext,
)
from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
)
from garlicsmtp.core.engine.runtime import Runtime
from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.logger import Logger
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.worker import QueueWorker
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.transport.dummy import (
    DummyTransport,
)
from garlicsmtp.transport.manager import (
    TransportManager,
)
from garlicsmtp.application.event_hub import (
    ApplicationEventHub,
)
from garlicsmtp.application.tor_status import (
    TorStatus,
)


class FakeServer:

    def __init__(self):
        self.running = False
        self.active_connections = 0
        self.pipeline = Pipeline()
        self.store = None

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def tick(self):
        pass

class FakeTorMonitor:

    def __init__(self):
        self.running = False

        self.status = TorStatus(
            enabled=True,
            socks_host="127.0.0.1",
            socks_port=9050,
            socks_available=False,
            control_enabled=False,
            control_host="127.0.0.1",
            control_port=9051,
            control_available=False,
            authenticated=False,
            authentication_method=(
                "DISABLED"
            ),
            version=None,
            bootstrap_progress=None,
            bootstrap_summary=None,
            built_circuits=0,
            active_streams=0,
            new_circuits_allowed=False,
            new_circuits_available=False,
            last_error=(
                "Tor control is disabled"
            ),
            socks_listeners=(),
            control_listeners=(),
            onion_smtp_port=25,
        )

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def tick(self):
        pass

def build_context() -> ApplicationContext:
    paths = ApplicationPaths(
        root_dir=Path(
            "/tmp/garlicsmtp-controller"
        )
    )

    settings = ApplicationSettings()
    logger = Logger()
    event_hub = ApplicationEventHub()
    store = MessageStore()
    queue = QueueManager()

    transport = TransportManager(
        default_transport=DummyTransport(),
    )

    pipeline = Pipeline()

    smtp_server = FakeServer()
    smtp_server.pipeline = pipeline

    imap_server = FakeServer()
    imap_server.store = store

    queue_worker = QueueWorker(
        queue=queue,
        transport=transport,
        logger=logger,
    )
    tor_monitor = FakeTorMonitor()

    runtime = Runtime(
        services=[
            smtp_server,
            imap_server,
            queue_worker,
            tor_monitor,
        ],
        tasks=[
            smtp_server,
            imap_server,
            queue_worker,
            tor_monitor,
        ],
        logger=logger,
    )

    return ApplicationContext(
        paths=paths,
        settings=settings,
        logger=logger,
        event_hub=event_hub,
        store=store,
        queue=queue,
        transport=transport,
        pipeline=pipeline,
        smtp_server=smtp_server,
        imap_server=imap_server,
        queue_worker=queue_worker,
        tor_monitor=tor_monitor,
        runtime=runtime,
    )


def test_application_controller_starts_application():
    context = build_context()

    controller = ApplicationController(
        context
    )

    status = controller.start()

    assert status.running is True
    assert status.smtp_running is True
    assert status.imap_running is True
    assert status.queue_worker_running is True

def test_application_controller_stops_application():
    context = build_context()

    controller = ApplicationController(
        context
    )

    controller.start()

    status = controller.stop()

    assert status.running is False
    assert status.smtp_running is False
    assert status.imap_running is False
    assert status.queue_worker_running is False

def test_application_controller_restarts_application():
    context = build_context()

    controller = ApplicationController(
        context
    )

    controller.start()

    status = controller.restart()

    assert status.running is True
    assert status.smtp_running is True
    assert status.imap_running is True
    assert status.queue_worker_running is True

def test_application_controller_returns_status():
    context = build_context()

    controller = ApplicationController(
        context
    )

    status = controller.status()

    assert status.running is False
    assert status.hostname == (
        "garlicsmtp.local"
    )

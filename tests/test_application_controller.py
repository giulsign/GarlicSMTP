# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

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
from garlicsmtp.application.event_log import (
    ApplicationEventLog,
)
from garlicsmtp.application.event_service import (
    ApplicationEventService,
)
from garlicsmtp.security.encryption_key_store import (
    MemoryEncryptionKeyStore,
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

class FakeOnionService:

    def __init__(self):
        self.hostname = None

    def start(self):
        pass

    def stop(self):
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
    event_log = ApplicationEventLog()

    event_service = ApplicationEventService(
        event_log=event_log,
        event_hub=event_hub,
    )
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
    onion_service = FakeOnionService()

    runtime = Runtime(
        services=[
            smtp_server,
            onion_service,
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

    encryption_key_store = MemoryEncryptionKeyStore()

    return ApplicationContext(
        paths=paths,
        settings=settings,
        logger=logger,
        event_hub=event_hub,
        event_log=event_log,
        event_service=event_service,
        store=store,
        queue=queue,
        transport=transport,
        pipeline=pipeline,
        signer=None,
        encryption_key_store=encryption_key_store,
        smtp_server=smtp_server,
        imap_server=imap_server,
        queue_worker=queue_worker,
        onion_service=onion_service,
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


def test_application_controller_records_start_event():
    context = build_context()

    controller = ApplicationController(
        context
    )

    controller.start()

    events = context.event_log.snapshot()

    assert len(events) == 1
    assert events[0].message == (
        "Application started"
    )


def test_application_controller_records_stop_event():
    context = build_context()

    controller = ApplicationController(
        context
    )

    controller.start()
    controller.stop()

    assert [
        event.message
        for event in (
            context.event_log.snapshot()
        )
    ] == [
        "Application started",
        "Application stopped",
    ]


def test_application_controller_records_restart_event():
    context = build_context()

    controller = ApplicationController(
        context
    )

    controller.restart()

    assert [
        event.message
        for event in (
            context.event_log.snapshot()
        )
    ] == [
        "Application restarted",
    ]

def test_application_controller_runs_runtime_loop():
    context = build_context()

    controller = ApplicationController(
        context
    )

    controller.start()

    assert (
        controller._runtime_thread
        is not None
    )

    assert (
        controller._runtime_thread
        .is_alive()
    )

    controller.stop()

    assert controller._runtime_thread is None

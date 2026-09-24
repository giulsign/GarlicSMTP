# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime, timedelta
import queue

from garlicsmtp.exceptions import (PermanentDeliveryError, TemporaryDeliveryError,)
from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.worker import QueueWorker
from garlicsmtp.transport.dummy import DummyTransport
from garlicsmtp.transport.manager import TransportManager
from garlicsmtp.transport.onion.transport import (
    OnionTransport,
)
from garlicsmtp.security.encryption_key_store import (
    MemoryEncryptionKeyStore,
)


class SpyLogger:

    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)

    def warning(self, message):
        self.messages.append(message)

    def error(self, message):
        self.messages.append(message)


class FixedRetryPolicy:

    def next_retry(self, attempts):
        return datetime(
            2030,
            1,
            1,
            tzinfo=UTC,
        )


class BrokenTransport:

    def deliver(self, item):
        raise RuntimeError("delivery failed")


class FailingTransport:

    def deliver(self, item):
        return False


class TemporaryFailingTransport:

    def deliver(self, item):
        raise TemporaryDeliveryError("temporary failure")


class PermanentFailingTransport:

    def deliver(self, item):
        raise PermanentDeliveryError("permanent failure")


def test_queue_worker_delivers(message):

    queue = QueueManager()

    item = QueueFactory.create(message)

    queue.enqueue(item)

    transport = DummyTransport()

    manager = TransportManager(
        default_transport=transport,
    )

    worker = QueueWorker(
        queue,
        manager,
    )

    assert worker.process() is True

    assert transport.delivered == [item]

    assert queue.size() == 0


def test_worker_start_stop():

    queue = QueueManager()

    transport = TransportManager(
        default_transport=DummyTransport()
    )

    worker = QueueWorker(
        queue,
        transport,
    )

    worker.start()

    assert worker.running is True

    worker.stop()

    assert worker.running is False


def test_worker_tick_processes_queue(message):

    queue = QueueManager()

    item = QueueFactory.create(message)

    queue.enqueue(item)

    transport = TransportManager(
        default_transport=DummyTransport()
    )

    worker = QueueWorker(
        queue,
        transport,
    )

    worker.start()

    worker.tick()

    assert queue.size() == 0

    worker.stop()


def test_worker_uses_logger():

    queue = QueueManager()

    transport = TransportManager(
        default_transport=DummyTransport()
    )

    logger = SpyLogger()

    worker = QueueWorker(
        queue,
        transport,
        logger=logger,
    )

    worker.start()
    worker.stop()

    assert "QueueWorker started" in logger.messages
    assert "QueueWorker stopped" in logger.messages


def test_worker_tick_logs_transport_error(message):

    queue = QueueManager()

    item = QueueFactory.create(message)

    queue.enqueue(item)

    transport = TransportManager(
        default_transport=BrokenTransport()
    )

    logger = SpyLogger()

    worker = QueueWorker(
        queue=queue,
        transport=transport,
        logger=logger,
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert (
        "QueueWorker error [RuntimeError]"
        in logger.messages
    )

    assert all(
        "delivery failed" not in message
        for message in logger.messages
    )


def test_worker_keeps_item_when_transport_fails(message):

    queue = QueueManager()

    item = QueueFactory.create(message)

    queue.enqueue(item)

    transport = TransportManager(
        default_transport=BrokenTransport()
    )

    logger = SpyLogger()

    worker = QueueWorker(
        queue=queue,
        transport=transport,
        logger=logger,
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert queue.size() == 1
    assert queue.peek() is item

    assert (
        "QueueWorker error [RuntimeError]"
        in logger.messages
    )

    assert all(
        "delivery failed" not in message
        for message in logger.messages
    )


def test_worker_keeps_item_when_transport_returns_false(message):

    queue = QueueManager()

    item = QueueFactory.create(message)
    queue.enqueue(item)

    transport = TransportManager(
        default_transport=FailingTransport(),
    )

    worker = QueueWorker(
        queue=queue,
        transport=transport,
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert queue.size() == 1
    assert queue.peek() is item


def test_worker_keeps_item_on_temporary_error(message):

    queue = QueueManager()

    item = QueueFactory.create(message)
    queue.enqueue(item)

    transport = TransportManager(
        default_transport=TemporaryFailingTransport(),
    )

    logger = SpyLogger()

    worker = QueueWorker(
        queue=queue,
        transport=transport,
        logger=logger,
        retry_policy=FixedRetryPolicy(),
    )

    worker.start()
    worker.tick()
    worker.stop()


    assert queue.size() == 1
    assert queue.peek() is None

    assert item.attempts == 1
    assert item.next_retry is not None
    assert (
        item.last_error
        == "TemporaryDeliveryError"
    )


def test_worker_discards_item_on_permanent_error(message):

    queue = QueueManager()

    item = QueueFactory.create(message)
    queue.enqueue(item)

    transport = TransportManager(
        default_transport=PermanentFailingTransport(),
    )

    logger = SpyLogger()

    worker = QueueWorker(
        queue=queue,
        transport=transport,
        logger=logger,
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert queue.size() == 0


def test_worker_skips_item_not_ready(message):

    queue = QueueManager()

    item = QueueFactory.create(message)

    item.next_retry = datetime.now(UTC) + timedelta(minutes=10)

    queue.enqueue(item)

    transport = DummyTransport()

    manager = TransportManager(
        default_transport=transport,
    )

    worker = QueueWorker(
        queue=queue,
        transport=manager,
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert queue.size() == 1
    assert transport.delivered == []


def test_worker_does_not_log_sensitive_exception_message(
    message,
):
    class SensitiveFailingTransport:

        def deliver(
            self,
            item,
        ):
            raise RuntimeError(
                "delivery failed for "
                "alice@secret.onion "
                "subject=Top Secret "
                "private-key-value"
            )

    queue = QueueManager()

    item = QueueFactory.create(
        message
    )

    queue.enqueue(
        item
    )

    transport = TransportManager(
        default_transport=(
            SensitiveFailingTransport()
        ),
    )

    logger = SpyLogger()

    worker = QueueWorker(
        queue=queue,
        transport=transport,
        logger=logger,
    )

    worker.start()
    worker.tick()
    worker.stop()

    output = "\n".join(
        logger.messages
    )

    assert (
        "RuntimeError"
        in output
    )

    assert (
        "alice@secret.onion"
        not in output
    )

    assert (
        "Top Secret"
        not in output
    )

    assert (
        "private-key-value"
        not in output
    )

    assert (
        "delivery failed for"
        not in output
    )


def test_worker_persists_only_temporary_error_category(
    message,
):
    class SensitiveTemporaryTransport:

        def deliver(
            self,
            item,
        ):
            raise TemporaryDeliveryError(
                "delivery failed for "
                "alice@secret.onion "
                "to bob@private.onion "
                "subject=TOP-SECRET"
            )

    queue = QueueManager()

    item = QueueFactory.create(
        message
    )

    queue.enqueue(
        item
    )

    transport = TransportManager(
        default_transport=(
            SensitiveTemporaryTransport()
        ),
    )

    worker = QueueWorker(
        queue=queue,
        transport=transport,
        retry_policy=FixedRetryPolicy(),
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert (
        item.last_error
        == "TemporaryDeliveryError"
    )

    assert (
        "alice@secret.onion"
        not in item.last_error
    )

    assert (
        "bob@private.onion"
        not in item.last_error
    )

    assert (
        "TOP-SECRET"
        not in item.last_error
    )


def test_worker_does_not_persist_permanent_error_metadata(
    message,
):
    class SensitivePermanentTransport:

        def deliver(
            self,
            item,
        ):
            raise PermanentDeliveryError(
                "permanent failure for "
                "alice@secret.onion "
                "private-key-value"
            )

    queue = QueueManager()

    item = QueueFactory.create(
        message
    )

    queue.enqueue(
        item
    )

    transport = TransportManager(
        default_transport=(
            SensitivePermanentTransport()
        ),
    )

    worker = QueueWorker(
        queue=queue,
        transport=transport,
        retry_policy=FixedRetryPolicy(),
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert queue.size() == 0

    assert item.attempts == 0
    assert item.last_error is None
    assert item.next_retry is None


def test_worker_discards_item_on_permanent_error(message):

    queue = QueueManager()

    item = QueueFactory.create(message)
    queue.enqueue(item)

    transport = TransportManager(
        default_transport=PermanentFailingTransport(),
    )

    logger = SpyLogger()

    worker = QueueWorker(
        queue=queue,
        transport=transport,
        logger=logger,
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert queue.size() == 0

    assert item.attempts == 0
    assert item.last_error is None
    assert item.next_retry is None


def test_worker_retries_invalid_onion_e2ee_capability(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    class FakeConnection:

        def __init__(self):
            self.socket = object()
            self.closed = False

        def close(self):
            self.closed = True

    class FakeSocksClient:

        def __init__(self):
            self.connection = FakeConnection()

        def connect(
            self,
            host,
            port,
        ):
            return self.connection

    class InvalidCapabilitySMTPClient:

        e2ee_capability = (
            "v=1; alg=x25519; key=dGVzdA=="
        )

        def discover_e2ee_capability(self):
            return self.e2ee_capability

        def deliver(
            self,
            message,
        ):
            return True

    queue = QueueManager()

    item = QueueFactory.create(
        message
    )

    queue.enqueue(
        item
    )

    socks = FakeSocksClient()

    onion_transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection:
            InvalidCapabilitySMTPClient()
        ),
    )

    transport = TransportManager(
        default_transport=onion_transport,
    )

    worker = QueueWorker(
        queue=queue,
        transport=transport,
        retry_policy=FixedRetryPolicy(),
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert queue.size() == 1
    assert queue.peek() is None

    assert item.attempts == 1
    assert (
        item.last_error
        == "TemporaryDeliveryError"
    )
    assert item.next_retry is not None

    assert (
        socks.connection.closed
        is True
    )


def test_worker_retries_changed_onion_e2ee_key_without_overwriting_pin(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    class FakeConnection:

        def __init__(self):
            self.socket = object()
            self.closed = False

        def close(self):
            self.closed = True

    class FakeSocksClient:

        def __init__(self):
            self.connection = FakeConnection()

        def connect(
            self,
            host,
            port,
        ):
            return self.connection

    class ChangedKeySMTPClient:

        e2ee_capability = (
            "v=1; alg=x25519; "
            "key=AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE="
        )

        def discover_e2ee_capability(self):
            return self.e2ee_capability

        def deliver(
            self,
            message,
        ):
            return True

    encryption_key_store = (
        MemoryEncryptionKeyStore()
    )

    original_key = b"\x00" * 32

    encryption_key_store.remember(
        host,
        original_key,
    )

    def remember_capability(
        hostname,
        capability,
    ):
        encryption_key_store.remember(
            hostname,
            capability.public_key.public_bytes_raw(),
        )

    queue = QueueManager()

    item = QueueFactory.create(
        message
    )

    queue.enqueue(
        item
    )

    socks = FakeSocksClient()

    onion_transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection:
            ChangedKeySMTPClient()
        ),
        e2ee_capability_callback=(
            remember_capability
        ),
    )

    transport = TransportManager(
        default_transport=onion_transport,
    )

    worker = QueueWorker(
        queue=queue,
        transport=transport,
        retry_policy=FixedRetryPolicy(),
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert queue.size() == 1
    assert queue.peek() is None

    assert item.attempts == 1

    assert (
        item.last_error
        == "TemporaryDeliveryError"
    )

    assert item.next_retry is not None

    assert (
        encryption_key_store.get(host)
        == original_key
    )

    assert (
        socks.connection.closed
        is True
    )
    
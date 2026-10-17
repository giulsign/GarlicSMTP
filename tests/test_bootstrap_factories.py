
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.engine import (
    Bootstrap,
    GarlicSMTPConfig,
    Runtime,
)
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.transport.manager import TransportManager
from garlicsmtp.transport.onion.transport import OnionTransport
from garlicsmtp.queue.worker import QueueWorker
from garlicsmtp.smtp.server import SMTPServer
from garlicsmtp.logger import Logger
from garlicsmtp.core.pipeline import Pipeline, PipelineContext
from garlicsmtp.storage.store import MessageStore


def test_bootstrap_factories(
    tmp_path,
    dek,
):
    bootstrap = Bootstrap(
        config=GarlicSMTPConfig(
            mailbox_db=str(tmp_path / "mailboxes.db"),
        ),
        dek=dek,
    )

    assert isinstance(
        bootstrap.build_queue(),
        QueueManager,
    )

    assert isinstance(
        bootstrap.build_onion_transport(),
        OnionTransport,
    )

    assert isinstance(
        bootstrap.build_transport(),
        TransportManager,
    )

    assert isinstance(
        bootstrap.build_worker(),
        QueueWorker,
    )

    assert isinstance(
        bootstrap.build_runtime(),
        Runtime,
    )

    assert isinstance(
        bootstrap.build_server(),
        SMTPServer,
    )

    assert isinstance(
        bootstrap.build_logger(),
        Logger,
    )

    assert isinstance(
        bootstrap.build_pipeline(),
        Pipeline,
    )

    assert isinstance(
        bootstrap.build_message_store(),
        MessageStore,
    )

    bootstrap.build_queue().backend.close()
    bootstrap.build_message_store().backend.close()


def test_bootstrap_reuses_instances(
    tmp_path,
    dek,
):
    bootstrap = Bootstrap(
        config=GarlicSMTPConfig(
            mailbox_db=str(tmp_path / "mailboxes.db"),
        ),
        dek=dek,
    )

    assert bootstrap.build_queue() is bootstrap.build_queue()
    assert bootstrap.build_transport() is bootstrap.build_transport()
    assert bootstrap.build_worker() is bootstrap.build_worker()
    assert bootstrap.build_runtime() is bootstrap.build_runtime()
    assert bootstrap.build_server() is bootstrap.build_server()
    assert bootstrap.build_logger() is bootstrap.build_logger()
    assert bootstrap.build_pipeline() is bootstrap.build_pipeline()
    assert (
        bootstrap.build_message_store()
        is bootstrap.build_message_store()
    )

    bootstrap.build_queue().backend.close()
    bootstrap.build_message_store().backend.close()


def test_bootstrap_runtime_services(
    tmp_path,
    dek,
):
    bootstrap = Bootstrap(
        config=GarlicSMTPConfig(
            mailbox_db=str(tmp_path / "mailboxes.db"),
        ),
        dek=dek,
    )

    runtime = bootstrap.build_runtime()

    assert bootstrap.build_server() in runtime.services
    assert bootstrap.build_worker() in runtime.services

    bootstrap.build_queue().backend.close()
    bootstrap.build_message_store().backend.close()


def test_bootstrap_runtime_tasks(
    tmp_path,
    dek,
):
    bootstrap = Bootstrap(
        config=GarlicSMTPConfig(
            mailbox_db=str(tmp_path / "mailboxes.db"),
        ),
        dek=dek,
    )

    runtime = bootstrap.build_runtime()

    assert bootstrap.build_server() in runtime.tasks
    assert bootstrap.build_worker() in runtime.tasks

    bootstrap.build_queue().backend.close()
    bootstrap.build_message_store().backend.close()


def test_bootstrap_server_uses_shared_pipeline(
    tmp_path,
    dek,
):
    bootstrap = Bootstrap(
        config=GarlicSMTPConfig(
            mailbox_db=str(tmp_path / "mailboxes.db"),
        ),
        dek=dek,
    )

    server = bootstrap.build_server()

    assert server.pipeline is bootstrap.build_pipeline()

    bootstrap.build_queue().backend.close()
    bootstrap.build_message_store().backend.close()


def test_bootstrap_pipeline_stores_local_message(
    tmp_path,
    message,
    dek,
):
    db_path = tmp_path / "mailboxes.db"

    config = GarlicSMTPConfig(
        hostname="garlicsmtp.local",
        mailbox_db=str(db_path),
    )

    bootstrap = Bootstrap(
        config=config,
        dek=dek,
    )

    recipient = f"bob@{bootstrap.config.hostname}"

    message.envelope.recipients = [
        recipient
    ]

    context = PipelineContext(
        message=message,
    )

    bootstrap.build_pipeline().execute(
        context
    )

    store = bootstrap.build_message_store()

    ids = store.list_messages(
        recipient
    )

    assert len(ids) == 1

    stored = store.get(
        recipient,
        ids[0],
    )

    assert stored is not None
    assert stored.envelope.sender == (
        message.envelope.sender
    )

    bootstrap.build_queue().backend.close()
    store.backend.close()


def test_bootstrap_message_store_persists(
    tmp_path,
    message,
    dek,
):
    db_path = tmp_path / "mailboxes.db"

    config = GarlicSMTPConfig(
        hostname="test.onion",
        mailbox_db=str(db_path),
    )

    bootstrap = Bootstrap(
        config=config,
        dek=dek,
    )

    message.envelope.recipients = [
        "bob@test.onion"
    ]

    bootstrap.build_pipeline().execute(
        PipelineContext(
            message=message,
        )
    )

    store = bootstrap.build_message_store()

    ids = store.list_messages(
        "bob@test.onion"
    )

    assert len(ids) == 1

    bootstrap.build_queue().backend.close()
    store.backend.close()

    second_bootstrap = Bootstrap(
        config=config,
        dek=dek,
    )

    restored_store = (
        second_bootstrap.build_message_store()
    )

    restored_ids = restored_store.list_messages(
        "bob@test.onion"
    )

    assert restored_ids == ids

    restored = restored_store.get(
        "bob@test.onion",
        restored_ids[0],
    )

    assert restored is not None
    assert (
        restored.envelope.sender
        == message.envelope.sender
    )

    second_bootstrap.build_queue().backend.close()
    restored_store.backend.close()

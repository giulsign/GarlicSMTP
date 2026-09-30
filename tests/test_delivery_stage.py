# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.storage.delivery_stage import (
    DeliveryStage,
)

from garlicsmtp.storage.store import (
    MessageStore,
)
from garlicsmtp.core.pipeline import PipelineContext
from garlicsmtp.storage.entry import (
    VerificationStatus,
)
from unittest.mock import Mock
from garlicsmtp.smtp.mime import (
    MimeAttachment,
)
from garlicsmtp.storage.attachment_store import (
    AttachmentStore,
)


def test_delivery_stage_stores_local_message(
    message,
):

    message.envelope.recipients = [
        "bob@example.onion"
    ]

    store = MessageStore()

    queue = QueueManager()

    stage = DeliveryStage(
        store=store,
        queue_stage=QueueStage(queue),
        local_domains={
            "example.onion",
        },
    )

    context = PipelineContext(
        message=message,
    )

    stage.process(context)

    ids = store.list_messages(
        "bob@example.onion"
    )

    assert len(ids) == 1

    stored = store.get(
        "bob@example.onion",
        ids[0],
    )

    assert stored is message

    assert queue.size() == 0


def test_delivery_stage_queues_remote_message(
    message,
):

    message.envelope.recipients = [
        "bob@remote.onion"
    ]

    store = MessageStore()

    queue = QueueManager()

    stage = DeliveryStage(
        store=store,
        queue_stage=QueueStage(queue),
        local_domains={
            "example.onion",
        },
    )

    context = PipelineContext(
        message=message,
    )

    stage.process(context)

    assert queue.size() == 1

    assert store.list_messages(
        "bob@remote.onion"
    ) == []


def test_delivery_stage_preserves_verification_status(
    message,
):
    store = MessageStore()

    queue_stage = Mock()

    stage = DeliveryStage(
        store=store,
        queue_stage=queue_stage,
        local_domains={"test.onion"},
    )

    context = PipelineContext(
        message=message,
        verification_status=(
            VerificationStatus.VERIFIED
        ),
    )

    result = stage.process(context)

    entries = store.list_entries(
        "bob@test.onion"
    )

    assert result is context
    assert len(entries) == 1
    assert (
        entries[0].verification_status
        == VerificationStatus.VERIFIED
    )

    queue_stage.process.assert_not_called()


def test_delivery_stage_stores_local_attachments(
    tmp_path,
    message,
):
    message.envelope.recipients = [
        "bob@example.onion"
    ]

    attachment_store = AttachmentStore(
        tmp_path / "attachments"
    )

    store = MessageStore(
        attachment_store=attachment_store,
    )

    queue = QueueManager()

    stage = DeliveryStage(
        store=store,
        queue_stage=QueueStage(queue),
        local_domains={
            "example.onion",
        },
    )

    context = PipelineContext(
        message=message,
        attachments=[
            MimeAttachment(
                filename="document.pdf",
                declared_mime="application/pdf",
                content=b"%PDF-1.4\n",
            ),
        ],
    )

    stage.process(context)

    ids = store.list_messages(
        "bob@example.onion"
    )

    assert len(ids) == 1

    attachments = (
        attachment_store.list_for_message(
            ids[0]
        )
    )

    assert len(attachments) == 1
    assert (
        attachments[0].filename
        == "document.pdf"
    )
    assert (
        attachments[0].declared_mime
        == "application/pdf"
    )
    assert (
        attachments[0].content
        == b"%PDF-1.4\n"
    )


def test_delivery_stage_rolls_back_local_message_when_attachment_save_fails(
    tmp_path,
    message,
):
    message.envelope.recipients = [
        "bob@example.onion"
    ]

    attachment_store = AttachmentStore(
        tmp_path / "attachments"
    )

    attachment_store.save = Mock(
        side_effect=OSError(
            "attachment write failed"
        )
    )

    store = MessageStore(
        attachment_store=attachment_store,
    )

    stage = DeliveryStage(
        store=store,
        queue_stage=QueueStage(
            QueueManager()
        ),
        local_domains={
            "example.onion",
        },
    )

    context = PipelineContext(
        message=message,
        attachments=[
            MimeAttachment(
                filename="document.pdf",
                declared_mime="application/pdf",
                content=b"%PDF-1.4\n",
            ),
        ],
    )

    with pytest.raises(
        OSError,
        match="attachment write failed",
    ):
        stage.process(context)

    assert store.list_messages(
        "bob@example.onion"
    ) == []


def test_delivery_stage_removes_written_attachments_when_later_save_fails(
    tmp_path,
    message,
):
    message.envelope.recipients = [
        "bob@example.onion"
    ]

    attachment_store = AttachmentStore(
        tmp_path / "attachments"
    )

    real_save = attachment_store.save
    calls = 0

    def failing_save(**kwargs):
        nonlocal calls
        calls += 1

        if calls == 2:
            raise OSError(
                "attachment write failed"
            )

        return real_save(**kwargs)

    attachment_store.save = Mock(
        side_effect=failing_save
    )

    store = MessageStore(
        attachment_store=attachment_store,
    )

    stage = DeliveryStage(
        store=store,
        queue_stage=QueueStage(
            QueueManager()
        ),
        local_domains={
            "example.onion",
        },
    )

    context = PipelineContext(
        message=message,
        attachments=[
            MimeAttachment(
                filename="first.pdf",
                declared_mime="application/pdf",
                content=b"%PDF-1.4\nfirst",
            ),
            MimeAttachment(
                filename="second.pdf",
                declared_mime="application/pdf",
                content=b"%PDF-1.4\nsecond",
            ),
        ],
    )

    with pytest.raises(
        OSError,
        match="attachment write failed",
    ):
        stage.process(context)

    assert store.list_messages(
        "bob@example.onion"
    ) == []

    attachments_path = (
        tmp_path / "attachments"
    )

    assert (
        not attachments_path.exists()
        or list(
            attachments_path.iterdir()
        ) == []
    )


def test_delivery_stage_accepts_local_message_without_attachments(
    tmp_path,
    message,
):
    message.envelope.recipients = [
        "bob@example.onion"
    ]

    store = MessageStore(
        attachment_store=AttachmentStore(
            tmp_path / "attachments"
        ),
    )

    stage = DeliveryStage(
        store=store,
        queue_stage=QueueStage(
            QueueManager()
        ),
        local_domains={
            "example.onion",
        },
    )

    context = PipelineContext(
        message=message,
        attachments=None,
    )

    result = stage.process(context)

    assert result is context
    assert len(
        store.list_messages(
            "bob@example.onion"
        )
    ) == 1
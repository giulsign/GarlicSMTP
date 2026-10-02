# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.storage.attachment_store import (
    AttachmentStore,
)


def test_attachment_store_deletes_message_attachments(
    tmp_path,
):
    store = AttachmentStore(
        tmp_path / "attachments"
    )

    message_id = (
        "11111111-2222-3333-4444-555555555555"
    )

    message_directory = (
        tmp_path
        / "attachments"
        / message_id
    )

    message_directory.mkdir(
        parents=True
    )

    attachment = (
        message_directory
        / "attachment"
    )

    attachment.write_bytes(
        b"attachment content"
    )

    assert message_directory.exists()

    store.delete_for_message(
        message_id
    )

    assert not message_directory.exists()


@pytest.mark.parametrize(
    "message_id",
    [
        "",
        "   ",
        "../outside",
        "../../outside",
        "/absolute/path",
        "folder/message",
        "folder\\message",
    ],
)
def test_attachment_store_rejects_unsafe_message_id(
    tmp_path,
    message_id,
):
    store = AttachmentStore(
        tmp_path / "attachments"
    )

    with pytest.raises(ValueError):
        store.delete_for_message(
            message_id
        )


def test_attachment_store_rejects_non_text_message_id(
    tmp_path,
):
    store = AttachmentStore(
        tmp_path / "attachments"
    )

    with pytest.raises(TypeError):
        store.delete_for_message(
            None
        )


def test_attachment_store_saves_attachment_with_opaque_name(
    tmp_path,
):
    store = AttachmentStore(
        tmp_path / "attachments"
    )

    stored = store.save(
        message_id="message-123",
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\n",
    )

    message_path = (
        tmp_path
        / "attachments"
        / "message-123"
    )

    assert stored.filename == "document.pdf"
    assert (
        stored.declared_mime
        == "application/pdf"
    )
    assert stored.content == b"%PDF-1.4\n"

    assert message_path.is_dir()

    names = {
        path.name
        for path in message_path.iterdir()
    }

    assert "document.pdf" not in names


def test_attachment_store_lists_saved_attachments_after_restart(
    tmp_path,
):
    path = tmp_path / "attachments"

    store = AttachmentStore(
        path
    )

    store.save(
        message_id="message-123",
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\n",
    )

    restarted_store = AttachmentStore(
        path
    )

    attachments = (
        restarted_store.list_for_message(
            "message-123"
        )
    )

    assert len(attachments) == 1

    attachment = attachments[0]

    assert attachment.filename == "document.pdf"
    assert (
        attachment.declared_mime
        == "application/pdf"
    )
    assert attachment.content == b"%PDF-1.4\n"


def test_attachment_store_returns_message_directory(
    tmp_path,
):
    store = AttachmentStore(
        tmp_path / "attachments"
    )

    directory = store.directory_for_message(
        "message-123"
    )

    assert directory == (
        tmp_path
        / "attachments"
        / "message-123"
    )

    assert not directory.exists()


def test_attachment_store_materializes_attachment_with_original_filename(
    tmp_path,
):
    store = AttachmentStore(
        tmp_path / "attachments"
    )

    store.save(
        message_id="message-123",
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\n",
    )

    destination = (
        tmp_path
        / "materialized"
    )

    directory = store.materialize_for_message(
        "message-123",
        destination,
    )

    assert directory == destination
    assert (
        destination / "document.pdf"
    ).read_bytes() == b"%PDF-1.4\n"

    persistent_names = {
        path.name
        for path in (
            tmp_path
            / "attachments"
            / "message-123"
        ).iterdir()
    }

    assert "document.pdf" not in persistent_names


def test_attachment_store_rejects_unsafe_filename_when_materializing(
    tmp_path,
):
    store = AttachmentStore(
        tmp_path / "attachments"
    )

    store.save(
        message_id="message-123",
        filename="../secret.txt",
        declared_mime="text/plain",
        content=b"secret",
    )

    destination = (
        tmp_path
        / "materialized"
    )

    with pytest.raises(ValueError):
        store.materialize_for_message(
            "message-123",
            destination,
        )

    assert not (
        destination / "secret.txt"
    ).exists()


def test_attachment_store_rejects_duplicate_filenames_when_materializing(
    tmp_path,
):
    store = AttachmentStore(
        tmp_path / "attachments"
    )

    for content in (
        b"first",
        b"second",
    ):
        store.save(
            message_id="message-123",
            filename="document.txt",
            declared_mime="text/plain",
            content=content,
        )

    destination = (
        tmp_path
        / "materialized"
    )

    with pytest.raises(ValueError):
        store.materialize_for_message(
            "message-123",
            destination,
        )
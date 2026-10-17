# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.storage.attachment_store import (
    AttachmentStore,
)
from cryptography.exceptions import InvalidTag

def test_attachment_store_encrypts_content_and_metadata_at_rest(
    tmp_path,
    dek,
):
    path = tmp_path / "attachments"
    message_id = "message-encrypted-123"
    filename = "private-document.pdf"
    declared_mime = "application/x-private-pdf"
    content = b"PRIVATE-ATTACHMENT-CONTENT-12345"

    store = AttachmentStore(
        path,
        dek=dek,
    )

    stored = store.save(
        message_id=message_id,
        filename=filename,
        declared_mime=declared_mime,
        content=content,
    )

    assert stored.content == content

    message_path = path / message_id
    persisted_files = [
        file
        for file in message_path.iterdir()
        if file.is_file()
    ]

    assert persisted_files

    for file in persisted_files:
        persisted = file.read_bytes()

        assert content not in persisted
        assert filename.encode("utf-8") not in persisted
        assert declared_mime.encode("utf-8") not in persisted

    reopened = AttachmentStore(
        path,
        dek=dek,
    )

    attachments = reopened.list_for_message(
        message_id
    )

    assert len(attachments) == 1
    assert attachments[0].filename == filename
    assert attachments[0].declared_mime == declared_mime
    assert attachments[0].content == content


def test_attachment_store_rejects_wrong_dek(
    tmp_path,
    dek,
):
    path = tmp_path / "attachments"
    dek = bytes(range(32))
    wrong_dek = bytes(range(1, 33))

    AttachmentStore(path, dek=dek).save(
        message_id="message-123",
        filename="private.txt",
        declared_mime="text/plain",
        content=b"PRIVATE-CONTENT",
    )

    with pytest.raises(InvalidTag):
        AttachmentStore(
            path,
            dek=wrong_dek,
        ).list_for_message("message-123")


def test_attachment_store_rejects_ciphertext_moved_to_another_message(
    tmp_path,
    dek,
):
    path = tmp_path / "attachments"
    dek = bytes(range(32))

    store = AttachmentStore(path, dek=dek)

    store.save(
        message_id="message-original",
        filename="private.txt",
        declared_mime="text/plain",
        content=b"PRIVATE-CONTENT",
    )

    original_dir = path / "message-original"
    target_dir = path / "message-target"
    target_dir.mkdir()

    encrypted_file = next(
        original_dir.glob("*.gsat")
    )

    encrypted_file.rename(
        target_dir / encrypted_file.name
    )

    with pytest.raises(InvalidTag):
        store.list_for_message(
            "message-target"
        )


def test_attachment_store_rejects_legacy_plaintext_without_deleting_it(
    tmp_path,
    dek,
):
    path = tmp_path / "attachments"
    message_dir = path / "message-legacy"
    message_dir.mkdir(parents=True)

    content_path = message_dir / "legacy.bin"
    metadata_path = message_dir / "legacy.json"

    content_path.write_bytes(
        b"LEGACY-PRIVATE-CONTENT"
    )
    metadata_path.write_text(
        '{"filename": "old.txt", "declared_mime": "text/plain"}',
        encoding="utf-8",
    )

    original_content = content_path.read_bytes()
    original_metadata = metadata_path.read_bytes()

    store = AttachmentStore(
        path,
        dek=bytes(range(32)),
    )

    with pytest.raises(ValueError, match="legacy"):
        store.list_for_message(
            "message-legacy"
        )

    assert content_path.read_bytes() == original_content
    assert metadata_path.read_bytes() == original_metadata



def test_attachment_store_deletes_message_attachments(
    tmp_path,
    dek,
):
    store = AttachmentStore(
        tmp_path / "attachments",
                dek=dek,
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
    dek,
):
    store = AttachmentStore(
        tmp_path / "attachments",
                dek=dek,
    )

    with pytest.raises(ValueError):
        store.delete_for_message(
            message_id
        )


def test_attachment_store_rejects_non_text_message_id(
    tmp_path,
    dek,
):
    store = AttachmentStore(
        tmp_path / "attachments",
                dek=dek,
    )

    with pytest.raises(TypeError):
        store.delete_for_message(
            None
        )


def test_attachment_store_saves_attachment_with_opaque_name(
    tmp_path,
    dek,
):
    store = AttachmentStore(
        tmp_path / "attachments",
                dek=dek,
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
    dek,
):
    path = tmp_path / "attachments"

    store = AttachmentStore(
        path,
                dek=dek,
    )

    store.save(
        message_id="message-123",
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\n",
    )

    restarted_store = AttachmentStore(
        path,
                          dek=dek,
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
    dek,
):
    store = AttachmentStore(
        tmp_path / "attachments",
                dek=dek,
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
    dek,
):
    store = AttachmentStore(
        tmp_path / "attachments",
                dek=dek,
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
    dek,
):
    store = AttachmentStore(
        tmp_path / "attachments",
                dek=dek,
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
    dek,
):
    store = AttachmentStore(
        tmp_path / "attachments",
                dek=dek,
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
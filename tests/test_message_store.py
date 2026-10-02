# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.storage.store import (
    MessageStore,
)
from garlicsmtp.storage.attachment_store import (
    AttachmentStore,
)


def test_message_store_delegates_to_backend(
    message,
):

    store = MessageStore()

    message_id = store.save(
        "bob",
        message,
    )

    assert message_id in store.list_messages(
        "bob"
    )

    assert (
        store.get(
            "bob",
            message_id,
        )
        is message
    )


def test_message_store_lists_and_counts(
    message,
):

    store = MessageStore()

    store.save(
        "bob@test.onion",
        message,
    )

    assert store.list_mailboxes() == [
        "bob@test.onion"
    ]

    assert store.count(
        "bob@test.onion"
    ) == 1


def test_message_store_updates_flags(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    assert store.set_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Seen",
        },
    ) is True

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert restored.flags == {
        "\\Seen",
    }


def test_message_store_creates_empty_mailbox():
    store = MessageStore()

    assert store.create_mailbox(
        "archive@test.onion"
    ) is True

    assert store.list_mailboxes() == [
        "archive@test.onion",
    ]

    assert store.count(
        "archive@test.onion"
    ) == 0


def test_message_store_does_not_recreate_existing_mailbox():
    store = MessageStore()

    assert store.create_mailbox(
        "archive@test.onion"
    ) is True

    assert store.create_mailbox(
        "archive@test.onion"
    ) is False

    assert store.list_mailboxes() == [
        "archive@test.onion",
    ]


def test_message_store_deletes_mailbox(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    assert store.delete_mailbox(
        "archive@test.onion"
    ) is True

    assert store.list_mailboxes() == []

    assert store.list_entries(
        "archive@test.onion"
    ) == []


def test_message_store_delete_returns_false_for_missing_mailbox():
    store = MessageStore()

    assert store.delete_mailbox(
        "missing@test.onion"
    ) is False


def test_message_store_renames_mailbox(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "Archive",
        message,
    )

    store.add_flags(
        "Archive",
        entry.id,
        {
            "\\Seen",
        },
    )

    assert store.rename_mailbox(
        "Archive",
        "Old",
    ) is True

    assert store.list_mailboxes() == [
        "Old",
    ]

    assert store.list_entries(
        "Archive"
    ) == []

    renamed_entries = store.list_entries(
        "Old"
    )

    assert len(renamed_entries) == 1
    assert renamed_entries[0].id == entry.id
    assert renamed_entries[0].uid == entry.uid
    assert renamed_entries[0].flags == {
        "\\Seen",
    }


def test_message_store_rename_returns_false_for_missing_source():
    store = MessageStore()

    assert store.rename_mailbox(
        "Missing",
        "Archive",
    ) is False


def test_message_store_rename_returns_false_for_existing_destination():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    store.create_mailbox(
        "Old"
    )

    assert store.rename_mailbox(
        "Archive",
        "Old",
    ) is False

    assert store.list_mailboxes() == [
        "Archive",
        "Old",
    ]


def test_message_store_manages_mailbox_subscriptions():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    assert store.subscribe_mailbox(
        "Archive"
    ) is True

    assert store.list_subscribed_mailboxes() == [
        "Archive",
    ]

    assert store.unsubscribe_mailbox(
        "Archive"
    ) is True

    assert store.list_subscribed_mailboxes() == []


def test_message_store_rejects_subscription_to_missing_mailbox():
    store = MessageStore()

    assert store.subscribe_mailbox(
        "Missing"
    ) is False



def test_message_store_deletes_attachments_with_message(
    tmp_path,
    message,
):
    attachment_store = AttachmentStore(
        tmp_path / "attachments"
    )

    store = MessageStore(
        attachment_store=attachment_store,
    )

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    message_directory = (
        tmp_path
        / "attachments"
        / entry.id
    )

    message_directory.mkdir(
        parents=True
    )

    (
        message_directory
        / "attachment"
    ).write_bytes(
        b"attachment content"
    )

    assert store.delete_entry(
        "bob@test.onion",
        entry.id,
    ) is True

    assert not message_directory.exists()


def test_message_store_deletes_mailbox_attachments(
    tmp_path,
    message,
):
    attachment_store = AttachmentStore(
        tmp_path / "attachments"
    )

    store = MessageStore(
        attachment_store=attachment_store,
    )

    first = store.save_entry(
        "archive@test.onion",
        message,
    )

    second = store.save_entry(
        "archive@test.onion",
        message,
    )

    for entry in (
        first,
        second,
    ):
        directory = (
            tmp_path
            / "attachments"
            / entry.id
        )

        directory.mkdir(
            parents=True
        )

        (
            directory
            / "attachment"
        ).write_bytes(
            b"attachment content"
        )

    assert store.delete_mailbox(
        "archive@test.onion"
    ) is True

    assert not (
        tmp_path
        / "attachments"
        / first.id
    ).exists()

    assert not (
        tmp_path
        / "attachments"
        / second.id
    ).exists()


def test_message_store_delete_mailbox_preserves_other_attachments(
    tmp_path,
    message,
):
    attachment_store = AttachmentStore(
        tmp_path / "attachments"
    )

    store = MessageStore(
        attachment_store=attachment_store,
    )

    deleted_entry = store.save_entry(
        "archive@test.onion",
        message,
    )

    preserved_entry = store.save_entry(
        "inbox@test.onion",
        message,
    )

    for entry in (
        deleted_entry,
        preserved_entry,
    ):
        directory = (
            tmp_path
            / "attachments"
            / entry.id
        )

        directory.mkdir(
            parents=True
        )

        (
            directory
            / "attachment"
        ).write_bytes(
            b"attachment content"
        )

    assert store.delete_mailbox(
        "archive@test.onion"
    ) is True

    assert not (
        tmp_path
        / "attachments"
        / deleted_entry.id
    ).exists()

    assert (
        tmp_path
        / "attachments"
        / preserved_entry.id
    ).exists()


def test_message_store_copies_attachments_with_message(
    tmp_path,
    message,
):
    attachment_store = AttachmentStore(
        tmp_path / "attachments"
    )

    store = MessageStore(
        attachment_store=attachment_store,
    )

    source = store.save_entry(
        "source@test.onion",
        message,
    )

    store.create_mailbox(
        "destination@test.onion"
    )

    attachment_store.save(
        message_id=source.id,
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\nattachment",
    )

    copied = store.copy_entry(
        "source@test.onion",
        source.id,
        "destination@test.onion",
    )

    assert copied is not None
    assert copied.id != source.id

    source_attachments = (
        attachment_store.list_for_message(
            source.id
        )
    )

    copied_attachments = (
        attachment_store.list_for_message(
            copied.id
        )
    )

    assert len(source_attachments) == 1
    assert len(copied_attachments) == 1

    assert copied_attachments[0].filename == (
        "document.pdf"
    )
    assert (
        copied_attachments[0].declared_mime
        == "application/pdf"
    )
    assert copied_attachments[0].content == (
        b"%PDF-1.4\nattachment"
    )


def test_message_store_copy_rolls_back_when_attachment_copy_fails(
    tmp_path,
    message,
    monkeypatch,
):
    attachment_store = AttachmentStore(
        tmp_path / "attachments"
    )

    store = MessageStore(
        attachment_store=attachment_store,
    )

    source = store.save_entry(
        "source@test.onion",
        message,
    )

    store.create_mailbox(
        "destination@test.onion"
    )

    attachment_store.save(
        message_id=source.id,
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\nattachment",
    )

    original_save = attachment_store.save

    def failing_save(**kwargs):
        if kwargs["message_id"] != source.id:
            raise OSError("attachment copy failed")

        return original_save(**kwargs)

    monkeypatch.setattr(
        attachment_store,
        "save",
        failing_save,
    )

    try:
        store.copy_entry(
            "source@test.onion",
            source.id,
            "destination@test.onion",
        )
    except OSError as exc:
        assert str(exc) == (
            "attachment copy failed"
        )
    else:
        raise AssertionError(
            "Expected attachment copy failure"
        )

    assert store.list_entries(
        "destination@test.onion"
    ) == []

    source_attachments = (
        attachment_store.list_for_message(
            source.id
        )
    )

    assert len(source_attachments) == 1
    assert source_attachments[0].filename == (
        "document.pdf"
    )
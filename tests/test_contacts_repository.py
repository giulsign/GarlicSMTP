
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest
import json

from garlicsmtp.gui.contacts_repository import (
    ContactsRepository,
)


def test_missing_contacts_file_returns_empty_list(
    tmp_path,
):
    contacts_file = (
        tmp_path
        / "contacts.json"
    )

    repository = ContactsRepository(
        contacts_file
    )

    assert repository.list_contacts() == []
    assert not contacts_file.exists()



def test_existing_contacts_file_returns_saved_contacts(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        '{"version": 1, "next_id": 2, '
        '"contacts": [{"id": 1, "name": "Mario", '
        '"onion_address": "garlicsmtp@example.onion"}]}',
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    assert repository.list_contacts() == [
        {
            "id": 1,
            "name": "Mario",
            "onion_address": "garlicsmtp@example.onion",
        }
    ]



def test_malformed_contacts_file_raises_value_error(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    invalid_content = (
        '{"version": 1, "contacts": ['
    )

    contacts_file.write_text(
        invalid_content,
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts JSON",
    ):
        repository.list_contacts()

    assert contacts_file.read_text(
        encoding="utf-8",
    ) == invalid_content



def test_contacts_file_without_contacts_key_raises_value_error(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        '{"version": 1}',
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()



@pytest.mark.parametrize(
    "invalid_contacts",
    [
        None,
        {},
        "not-a-list",
        123,
    ],
)
def test_contacts_must_be_a_list(
    tmp_path,
    invalid_contacts,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        json.dumps({
            "version": 1,
            "contacts": invalid_contacts,
        }),
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()


def test_contact_must_be_an_object(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        json.dumps({
            "version": 1,
            "contacts": ["not-an-object"],
        }),
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()


@pytest.mark.parametrize(
    "missing_field",
    [
        "id",
        "name",
        "onion_address",
    ],
)
def test_contact_requires_mandatory_fields(
    tmp_path,
    missing_field,
):
    contacts_file = tmp_path / "contacts.json"

    contact = {
        "id": 1,
        "name": "Mario",
        "onion_address": "garlicsmtp@example.onion",
    }

    del contact[missing_field]

    contacts_file.write_text(
        json.dumps({
            "version": 1,
            "contacts": [contact],
        }),
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()


def test_duplicate_contact_ids_are_rejected(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        json.dumps({
            "version": 1,
            "contacts": [
                {
                    "id": 1,
                    "name": "Mario",
                    "onion_address": "mario@example.onion",
                },
                {
                    "id": 1,
                    "name": "Luigi",
                    "onion_address": "luigi@example.onion",
                },
            ],
        }),
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()



@pytest.mark.parametrize(
    "invalid_id",
    [
        0,
        -1,
        "1",
        None,
        True,
    ],
)
def test_contact_id_must_be_positive_integer(
    tmp_path,
    invalid_id,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        json.dumps({
            "version": 1,
            "contacts": [{
                "id": invalid_id,
                "name": "Mario",
                "onion_address": "mario@example.onion",
            }],
        }),
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()


@pytest.mark.parametrize(
    "invalid_name",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_contact_name_must_be_nonempty_string(
    tmp_path,
    invalid_name,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        json.dumps({
            "version": 1,
            "contacts": [{
                "id": 1,
                "name": invalid_name,
                "onion_address": "mario@example.onion",
            }],
        }),
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()


@pytest.mark.parametrize(
    "invalid_address",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_contact_address_must_be_nonempty_string(
    tmp_path,
    invalid_address,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        json.dumps({
            "version": 1,
            "contacts": [{
                "id": 1,
                "name": "Mario",
                "onion_address": invalid_address,
            }],
        }),
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()


@pytest.mark.parametrize(
    "invalid_version",
    [
        0,
        2,
        "1",
        None,
        True,
    ],
)
def test_contacts_version_must_be_one(
    tmp_path,
    invalid_version,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        json.dumps({
            "version": invalid_version,
            "contacts": [],
        }),
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()



@pytest.mark.parametrize(
    "invalid_next_id",
    [
        0,
        -1,
        "2",
        None,
        True,
        1.5,
    ],
)
def test_next_id_must_be_positive_integer(
    tmp_path,
    invalid_next_id,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        json.dumps({
            "version": 1,
            "next_id": invalid_next_id,
            "contacts": [],
        }),
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()


@pytest.mark.parametrize(
    "invalid_next_id",
    [
        1,
        2,
    ],
)
def test_next_id_must_exceed_existing_ids(
    tmp_path,
    invalid_next_id,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        json.dumps({
            "version": 1,
            "next_id": invalid_next_id,
            "contacts": [{
                "id": 2,
                "name": "Mario",
                "onion_address": "mario@example.onion",
            }],
        }),
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.list_contacts()


def test_next_id_greater_than_existing_ids_is_accepted(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    contacts_file.write_text(
        json.dumps({
            "version": 1,
            "next_id": 3,
            "contacts": [{
                "id": 2,
                "name": "Mario",
                "onion_address": "mario@example.onion",
            }],
        }),
        encoding="utf-8",
    )

    original_content = contacts_file.read_text(
        encoding="utf-8",
    )

    repository = ContactsRepository(
        contacts_file
    )

    assert len(repository.list_contacts()) == 1

    assert contacts_file.read_text(
        encoding="utf-8",
    ) == original_content



def test_add_first_contact_creates_json_file(
    tmp_path,
):
    contacts_file = (
        tmp_path
        / "contacts.json"
    )

    repository = ContactsRepository(
        contacts_file
    )

    contact = repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    assert contact == {
        "id": 1,
        "name": "Mario",
        "onion_address": "mario@example.onion",
    }

    assert contacts_file.is_file()

    data = json.loads(
        contacts_file.read_text(
            encoding="utf-8",
        )
    )

    assert data == {
        "version": 1,
        "next_id": 2,
        "contacts": [contact],
    }


def test_added_contact_survives_repository_reload(
    tmp_path,
):
    contacts_file = (
        tmp_path
        / "contacts.json"
    )

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    reloaded_repository = ContactsRepository(
        contacts_file
    )

    assert reloaded_repository.list_contacts() == [
        {
            "id": 1,
            "name": "Mario",
            "onion_address": "mario@example.onion",
        }
    ]


def test_adding_second_contact_increments_id(
    tmp_path,
):
    contacts_file = (
        tmp_path
        / "contacts.json"
    )

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    second_contact = repository.add_contact(
        name="Luigi",
        onion_address="luigi@example.onion",
    )

    assert second_contact["id"] == 2

    data = json.loads(
        contacts_file.read_text(
            encoding="utf-8",
        )
    )

    assert data["next_id"] == 3
    assert len(data["contacts"]) == 2



@pytest.mark.parametrize(
    "invalid_name",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_add_invalid_name_does_not_create_file(
    tmp_path,
    invalid_name,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.add_contact(
            name=invalid_name,
            onion_address="mario@example.onion",
        )

    assert not contacts_file.exists()


@pytest.mark.parametrize(
    "invalid_address",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_add_invalid_address_preserves_existing_file(
    tmp_path,
    invalid_address,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    original_content = contacts_file.read_bytes()

    with pytest.raises(
        ValueError,
        match="Invalid contacts structure",
    ):
        repository.add_contact(
            name="Luigi",
            onion_address=invalid_address,
        )

    assert contacts_file.read_bytes() == original_content


def test_failed_write_preserves_existing_contacts(
    tmp_path,
    monkeypatch,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    original_content = contacts_file.read_bytes()

    original_dump = json.dump

    def failing_dump(*args, **kwargs):
        raise OSError("Simulated write failure")

    monkeypatch.setattr(
        json,
        "dump",
        failing_dump,
    )

    with pytest.raises(
        OSError,
        match="Simulated write failure",
    ):
        repository.add_contact(
            name="Luigi",
            onion_address="luigi@example.onion",
        )

    assert contacts_file.read_bytes() == original_content



def test_update_contact_changes_name_and_address(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    updated_contact = repository.update_contact(
        contact_id=1,
        name="Mario Rossi",
        onion_address="mario.rossi@example.onion",
    )

    assert updated_contact == {
        "id": 1,
        "name": "Mario Rossi",
        "onion_address": "mario.rossi@example.onion",
    }

    data = json.loads(
        contacts_file.read_text(
            encoding="utf-8",
        )
    )

    assert data["contacts"] == [
        updated_contact
    ]

    assert data["next_id"] == 2


def test_update_contact_preserves_other_contacts(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    repository.add_contact(
        name="Luigi",
        onion_address="luigi@example.onion",
    )

    repository.update_contact(
        contact_id=1,
        name="Mario Rossi",
        onion_address="mario.rossi@example.onion",
    )

    contacts = repository.list_contacts()

    assert len(contacts) == 2

    assert contacts[1] == {
        "id": 2,
        "name": "Luigi",
        "onion_address": "luigi@example.onion",
    }


def test_update_missing_contact_preserves_file(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    original_content = contacts_file.read_bytes()

    with pytest.raises(
        ValueError,
        match="Contact not found",
    ):
        repository.update_contact(
            contact_id=999,
            name="Sconosciuto",
            onion_address="unknown@example.onion",
        )

    assert contacts_file.read_bytes() == original_content


def test_update_contact_persists_after_reload(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    repository.update_contact(
        contact_id=1,
        name="Mario Rossi",
        onion_address="mario.rossi@example.onion",
    )

    reloaded_repository = ContactsRepository(
        contacts_file
    )

    assert reloaded_repository.list_contacts() == [
        {
            "id": 1,
            "name": "Mario Rossi",
            "onion_address": "mario.rossi@example.onion",
        }
    ]



def test_delete_contact_removes_existing_contact(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    repository.delete_contact(
        contact_id=1
    )

    assert repository.list_contacts() == []

    data = json.loads(
        contacts_file.read_text(
            encoding="utf-8",
        )
    )

    assert data["next_id"] == 2


def test_delete_contact_preserves_other_contacts(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    repository.add_contact(
        name="Luigi",
        onion_address="luigi@example.onion",
    )

    repository.delete_contact(
        contact_id=1
    )

    assert repository.list_contacts() == [
        {
            "id": 2,
            "name": "Luigi",
            "onion_address": "luigi@example.onion",
        }
    ]


def test_deleted_contact_id_is_not_reused(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    repository.delete_contact(
        contact_id=1
    )

    new_contact = repository.add_contact(
        name="Luigi",
        onion_address="luigi@example.onion",
    )

    assert new_contact["id"] == 2


def test_delete_missing_contact_preserves_file(
    tmp_path,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    original_content = contacts_file.read_bytes()

    with pytest.raises(
        ValueError,
        match="Contact not found",
    ):
        repository.delete_contact(
            contact_id=999
        )

    assert contacts_file.read_bytes() == original_content



def test_add_contact_preserves_file_when_replace_fails(
    tmp_path,
    monkeypatch,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    original_content = contacts_file.read_bytes()

    def failing_replace(source, destination):
        raise OSError("Simulated replace failure")

    monkeypatch.setattr(
        "garlicsmtp.gui.contacts_repository.os.replace",
        failing_replace,
    )

    with pytest.raises(
        OSError,
        match="Simulated replace failure",
    ):
        repository.add_contact(
            name="Luigi",
            onion_address="luigi@example.onion",
        )

    assert contacts_file.read_bytes() == original_content


def test_replace_failure_removes_temporary_file(
    tmp_path,
    monkeypatch,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    def failing_replace(source, destination):
        raise OSError("Simulated replace failure")

    monkeypatch.setattr(
        "garlicsmtp.gui.contacts_repository.os.replace",
        failing_replace,
    )

    with pytest.raises(
        OSError,
        match="Simulated replace failure",
    ):
        repository.add_contact(
            name="Mario",
            onion_address="mario@example.onion",
        )

    assert not contacts_file.exists()

    assert list(
        tmp_path.glob(".contacts-*.tmp")
    ) == []


def test_update_contact_preserves_file_when_replace_fails(
    tmp_path,
    monkeypatch,
):
    contacts_file = tmp_path / "contacts.json"

    repository = ContactsRepository(
        contacts_file
    )

    repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    original_content = contacts_file.read_bytes()

    def failing_replace(source, destination):
        raise OSError("Simulated replace failure")

    monkeypatch.setattr(
        "garlicsmtp.gui.contacts_repository.os.replace",
        failing_replace,
    )

    with pytest.raises(
        OSError,
        match="Simulated replace failure",
    ):
        repository.update_contact(
            contact_id=1,
            name="Mario Rossi",
            onion_address="mario.rossi@example.onion",
        )

    assert contacts_file.read_bytes() == original_content



def test_concurrent_add_contact_preserves_both_contacts(
    tmp_path,
    monkeypatch,
):
    import threading

    contacts_file = tmp_path / "contacts.json"

    first_repository = ContactsRepository(
        contacts_file
    )

    second_repository = ContactsRepository(
        contacts_file
    )

    first_repository.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    original_read_data = (
        ContactsRepository._read_data
    )

    second_started = threading.Event()
    second_finished = threading.Event()

    second_errors = []
    second_thread = None

    def add_second_contact():
        second_started.set()

        try:
            second_repository.add_contact(
                name="Luigi",
                onion_address="luigi@example.onion",
            )
        except Exception as exc:
            second_errors.append(exc)
        finally:
            second_finished.set()

    def interleaved_read_data(self):
        nonlocal second_thread

        data = original_read_data(self)

        if (
            self is first_repository
            and second_thread is None
        ):
            second_thread = threading.Thread(
                target=add_second_contact,
                daemon=True,
            )

            second_thread.start()

            assert second_started.wait(
                timeout=5
            )

        return data

    monkeypatch.setattr(
        ContactsRepository,
        "_read_data",
        interleaved_read_data,
    )

    first_repository.add_contact(
        name="Anna",
        onion_address="anna@example.onion",
    )

    assert second_thread is not None

    assert second_finished.wait(
        timeout=5
    ), "Second writer did not finish"

    second_thread.join(
        timeout=5
    )

    assert second_errors == []

    contacts = ContactsRepository(
        contacts_file
    ).list_contacts()

    assert len(contacts) == 3

    assert {
        contact["name"]
        for contact in contacts
    } == {
        "Mario",
        "Luigi",
        "Anna",
    }

    assert len({
        contact["id"]
        for contact in contacts
    }) == 3


# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.gui.contacts_view_model import (
    ContactsViewModel,
)

from garlicsmtp.gui.contacts_repository import (
    ContactsRepository,
)


@pytest.fixture
def view_model(tmp_path):
    repository = ContactsRepository(
        tmp_path / "contacts.json"
    )

    return ContactsViewModel(
        repository
    )


def test_initial_contacts_are_empty(
    view_model,
):
    assert view_model.contacts == []


def test_add_contact_refreshes_contacts(
    view_model,
):
    contact = view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    assert contact["id"] == 1

    assert view_model.contacts == [
        {
            "id": 1,
            "name": "Mario",
            "onion_address": "mario@example.onion",
        }
    ]


def test_update_contact_refreshes_contacts(
    view_model,
):
    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    updated = view_model.update_contact(
        contact_id=1,
        name="Mario Rossi",
        onion_address="mario.rossi@example.onion",
    )

    assert updated["name"] == "Mario Rossi"

    assert view_model.contacts[0]["name"] == (
        "Mario Rossi"
    )


def test_delete_contact_refreshes_contacts(
    view_model,
):
    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    view_model.delete_contact(
        contact_id=1
    )

    assert view_model.contacts == []


def test_refresh_contacts_reads_external_changes(
    view_model,
):
    repository = view_model.repository

    repository.add_contact(
        name="Luigi",
        onion_address="luigi@example.onion",
    )

    view_model.refresh()

    assert view_model.contacts[0]["name"] == (
        "Luigi"
    )


def test_failed_update_preserves_contacts(
    view_model,
):
    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    with pytest.raises(
        ValueError,
        match="Contact not found",
    ):
        view_model.update_contact(
            contact_id=999,
            name="Sconosciuto",
            onion_address="unknown@example.onion",
        )

    assert view_model.contacts[0]["name"] == (
        "Mario"
    )


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


def test_get_contact_name_by_onion_address(
    view_model,
):
    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@example.onion",
    )

    name = view_model.get_contact_name(
        "mario@example.onion"
    )

    assert name == "Mario Rossi"


def test_get_contact_name_returns_none_for_unknown_address(
    view_model,
):
    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@example.onion",
    )

    name = view_model.get_contact_name(
        "unknown@example.onion"
    )

    assert name is None


def test_format_contact_address_includes_saved_name(
    view_model,
):
    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@example.onion",
    )

    formatted = view_model.format_contact_address(
        "mario@example.onion"
    )

    assert formatted == (
        "Mario Rossi — mario@example.onion"
    )


def test_format_contact_address_preserves_unknown_address(
    view_model,
):
    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@example.onion",
    )

    formatted = view_model.format_contact_address(
        "unknown@example.onion"
    )

    assert formatted == "unknown@example.onion"


def test_filter_contacts_by_name_case_insensitive(
    view_model,
):
    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@example.onion",
    )

    view_model.add_contact(
        name="Luigi Verdi",
        onion_address="luigi@example.onion",
    )

    results = view_model.filter_contacts(
        "MARIO"
    )

    assert len(results) == 1
    assert results[0]["name"] == "Mario Rossi"

    assert len(view_model.contacts) == 2


def test_filter_contacts_by_onion_address(
    view_model,
):
    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@alpha.onion",
    )

    view_model.add_contact(
        name="Luigi Verdi",
        onion_address="luigi@beta.onion",
    )

    results = view_model.filter_contacts(
        "BETA.ONION"
    )

    assert len(results) == 1
    assert results[0]["name"] == "Luigi Verdi"
    assert results[0]["onion_address"] == (
        "luigi@beta.onion"
    )

    assert len(view_model.contacts) == 2


def test_filter_contacts_empty_query_returns_all_contacts(
    view_model,
):
    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@example.onion",
    )

    view_model.add_contact(
        name="Luigi Verdi",
        onion_address="luigi@example.onion",
    )

    results = view_model.filter_contacts("")

    assert results == view_model.contacts
    assert len(results) == 2


def test_filter_contacts_unknown_query_returns_empty_list(
    view_model,
):
    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@example.onion",
    )

    results = view_model.filter_contacts(
        "inesistente"
    )

    assert results == []
    assert len(view_model.contacts) == 1

# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.gui.contacts_repository import (
    ContactsRepository,
)


class ContactsViewModel:

    def __init__(
        self,
        repository: ContactsRepository,
    ) -> None:
        self.repository = repository
        self.contacts = []

        self.refresh()

    def refresh(
        self,
    ) -> None:
        self.contacts = (
            self.repository.list_contacts()
        )

    def filter_contacts(
        self,
        query: str,
    ) -> list[dict]:
        normalized_query = query.casefold()

        return [
            contact
            for contact in self.contacts
            if (
                normalized_query in contact["name"].casefold()
                or normalized_query
                in contact["onion_address"].casefold()
            )
        ]

    def get_contact_name(
        self,
        onion_address: str,
    ) -> str | None:
        for contact in self.contacts:
            if contact["onion_address"] == onion_address:
                return contact["name"]

        return None

    def format_contact_address(
        self,
        onion_address: str,
    ) -> str:
        name = self.get_contact_name(
            onion_address
        )

        if name is None:
            return onion_address

        return f"{name} — {onion_address}"

    def add_contact(
        self,
        name: str,
        onion_address: str,
    ) -> dict:
        contact = self.repository.add_contact(
            name=name,
            onion_address=onion_address,
        )

        self.refresh()

        return contact

    def update_contact(
        self,
        contact_id: int,
        name: str,
        onion_address: str,
    ) -> dict:
        contact = self.repository.update_contact(
            contact_id=contact_id,
            name=name,
            onion_address=onion_address,
        )

        self.refresh()

        return contact

    def delete_contact(
        self,
        contact_id: int,
    ) -> None:
        self.repository.delete_contact(
            contact_id=contact_id
        )

        self.refresh()

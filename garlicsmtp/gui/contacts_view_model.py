
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

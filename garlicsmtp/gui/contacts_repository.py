
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import fcntl
import json
import os
import tempfile

from contextlib import contextmanager
from pathlib import Path


class ContactsRepository:

    def __init__(
        self,
        path: Path,
    ) -> None:
        self.path = Path(path)

    def list_contacts(
        self,
    ) -> list:
        if not self.path.exists():
            return []

        data = self._read_data()

        return data["contacts"]

    def add_contact(
        self,
        name: str,
        onion_address: str,
    ) -> dict:
        with self._write_lock():
            if self.path.exists():
                data = self._read_data()
            else:
                data = {
                    "version": 1,
                    "next_id": 1,
                    "contacts": [],
                }

            contacts = data["contacts"]

            next_id = data.get("next_id")

            if next_id is None:
                next_id = (
                    max(
                        (
                            contact["id"]
                            for contact in contacts
                        ),
                        default=0,
                    )
                    + 1
                )

            contact = {
                "id": next_id,
                "name": name,
                "onion_address": onion_address,
            }

            contacts.append(contact)

            data["next_id"] = next_id + 1

            self._validate_structure(data)
            self._write_data(data)

            return contact

    def update_contact(
        self,
        contact_id: int,
        name: str,
        onion_address: str,
    ) -> dict:
        with self._write_lock():
            if not self.path.exists():
                raise ValueError(
                    "Contact not found"
                )

            data = self._read_data()

            for contact in data["contacts"]:
                if contact["id"] == contact_id:
                    updated_contact = {
                        "id": contact_id,
                        "name": name,
                        "onion_address": onion_address,
                    }

                    original_contact = (
                        contact.copy()
                    )

                    contact.update(
                        updated_contact
                    )

                    try:
                        self._validate_structure(
                            data
                        )
                    except ValueError:
                        contact.clear()
                        contact.update(
                            original_contact
                        )
                        raise

                    self._write_data(data)

                    return updated_contact

            raise ValueError(
                "Contact not found"
            )

    def delete_contact(
        self,
        contact_id: int,
    ) -> None:
        with self._write_lock():
            if not self.path.exists():
                raise ValueError(
                    "Contact not found"
                )

            data = self._read_data()

            contacts = data["contacts"]

            for index, contact in enumerate(
                contacts
            ):
                if contact["id"] == contact_id:
                    del contacts[index]

                    self._validate_structure(
                        data
                    )

                    self._write_data(data)

                    return

            raise ValueError(
                "Contact not found"
            )

    @contextmanager
    def _write_lock(
        self,
    ):
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        lock_path = self.path.with_name(
            self.path.name + ".lock"
        )

        with lock_path.open("a+b") as lock_file:
            fcntl.flock(
                lock_file.fileno(),
                fcntl.LOCK_EX,
            )

            try:
                yield
            finally:
                fcntl.flock(
                    lock_file.fileno(),
                    fcntl.LOCK_UN,
                )

    def _read_data(
        self,
    ) -> dict:
        try:
            with self.path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid contacts JSON"
            ) from exc

        self._validate_structure(data)

        return data

    def _write_data(
        self,
        data: dict,
    ) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=".contacts-",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(
                    temporary_file.name
                )

                json.dump(
                    data,
                    temporary_file,
                    indent=2,
                    ensure_ascii=False,
                )

                temporary_file.flush()
                os.fsync(
                    temporary_file.fileno()
                )

            os.replace(
                temporary_path,
                self.path,
            )

        finally:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink()

    @staticmethod
    def _validate_structure(
        data,
    ) -> None:
        error_message = (
            "Invalid contacts structure"
        )

        if not isinstance(data, dict):
            raise ValueError(error_message)

        version = data.get("version")

        if (
            type(version) is not int
            or version != 1
        ):
            raise ValueError(error_message)

        contacts = data.get("contacts")

        if not isinstance(contacts, list):
            raise ValueError(error_message)

        required_fields = {
            "id",
            "name",
            "onion_address",
        }

        seen_ids = set()

        for contact in contacts:
            if not isinstance(contact, dict):
                raise ValueError(error_message)

            if not required_fields.issubset(
                contact
            ):
                raise ValueError(error_message)

            contact_id = contact["id"]

            if (
                type(contact_id) is not int
                or contact_id <= 0
            ):
                raise ValueError(error_message)

            if contact_id in seen_ids:
                raise ValueError(error_message)

            seen_ids.add(contact_id)

            name_value = contact["name"]

            if (
                not isinstance(name_value, str)
                or not name_value.strip()
            ):
                raise ValueError(error_message)

            address_value = (
                contact["onion_address"]
            )

            if (
                not isinstance(
                    address_value,
                    str,
                )
                or not address_value.strip()
            ):
                raise ValueError(error_message)

        if "next_id" in data:
            next_id = data["next_id"]

            if (
                type(next_id) is not int
                or next_id <= 0
            ):
                raise ValueError(error_message)

            if (
                seen_ids
                and next_id <= max(seen_ids)
            ):
                raise ValueError(error_message)

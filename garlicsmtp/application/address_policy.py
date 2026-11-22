# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from threading import Lock
import re


class AddressPolicy:
    """Session-scoped policy for personalized Onion email addresses."""

    CANONICAL_LOCALPART = "garlicsmtp"

    def __init__(self) -> None:
        self._lock = Lock()
        self._custom_addresses_enabled = False
        self._local_hostname: str | None = None

    @property
    def custom_addresses_enabled(self) -> bool:
        with self._lock:
            return self._custom_addresses_enabled

    def set_custom_addresses_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._custom_addresses_enabled = bool(enabled)

    def set_local_hostname(self, hostname: str) -> None:
        hostname = hostname.strip().casefold()
        if not hostname.endswith(".onion"):
            raise ValueError("Local hostname must be an Onion hostname")
        if hostname == ".onion":
            raise ValueError("Local Onion hostname is empty")
        with self._lock:
            self._local_hostname = hostname

    @property
    def canonical_sender(self) -> str | None:
        with self._lock:
            if self._local_hostname is None:
                return None
            return f"{self.CANONICAL_LOCALPART}@{self._local_hostname}"

    @staticmethod
    def _parse_address(address: str) -> tuple[str, str] | None:
        if not isinstance(address, str) or address.count("@") != 1:
            return None

        localpart, hostname = address.split("@", 1)

        if not localpart or not hostname:
            return None

        if any(char.isspace() for char in address):
            return None

        hostname = hostname.casefold()

        if not re.fullmatch(r"[a-z2-7]{56}\.onion", hostname):
            return None

        return localpart, hostname

    def allows_sender(self, address: str) -> bool:
        parsed = self._parse_address(address)
        if parsed is None:
            return False

        localpart, hostname = parsed

        with self._lock:
            if self._local_hostname is None:
                return False

            if hostname != self._local_hostname:
                return False

            return (
                self._custom_addresses_enabled
                or localpart == self.CANONICAL_LOCALPART
            )

    def allows_outgoing_recipient(self, address: str) -> bool:
        parsed = self._parse_address(address)
        if parsed is None:
            return False

        localpart, _ = parsed

        with self._lock:
            return (
                self._custom_addresses_enabled
                or localpart == self.CANONICAL_LOCALPART
            )

    def allows_incoming_recipient(self, address: str) -> bool:
        parsed = self._parse_address(address)
        if parsed is None:
            return False

        localpart, hostname = parsed

        with self._lock:
            if self._local_hostname is None:
                return False

            if hostname != self._local_hostname:
                return False

            return (
                self._custom_addresses_enabled
                or localpart == self.CANONICAL_LOCALPART
            )

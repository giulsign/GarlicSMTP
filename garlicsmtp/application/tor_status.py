# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TorStatus:

    enabled: bool

    socks_host: str
    socks_port: int
    socks_available: bool

    control_enabled: bool
    control_host: str
    control_port: int
    control_available: bool
    authenticated: bool
    authentication_method: str

    version: str | None
    bootstrap_progress: int | None
    bootstrap_summary: str | None

    built_circuits: int
    active_streams: int

    new_circuits_allowed: bool
    new_circuits_available: bool

    last_error: str | None

    socks_listeners: tuple[str, ...] = ()
    control_listeners: tuple[str, ...] = ()

    onion_smtp_port: int = 25
    onion_hostname: str | None = None

    @property
    def socks_endpoint(
        self,
    ) -> str:
        return (
            f"{self.socks_host}:"
            f"{self.socks_port}"
        )

    @property
    def control_endpoint(
        self,
    ) -> str:
        return (
            f"{self.control_host}:"
            f"{self.control_port}"
        )

    @property
    def ready(
        self,
    ) -> bool:
        return (
            self.enabled
            and self.socks_available
            and (
                not self.control_enabled
                or (
                    self.control_available
                    and self.authenticated
                    and (
                        self.authentication_method
                        == "SAFECOOKIE"
                    )
                )
            )
        )


    @property
    def bootstrap_complete(
        self,
    ) -> bool:
        return (
            self.bootstrap_progress == 100
        )


    @property
    def socks_listeners_text(
        self,
    ) -> str:
        if not self.socks_listeners:
            return self.socks_endpoint

        return ", ".join(
            self.socks_listeners
        )


    @property
    def control_listeners_text(
        self,
    ) -> str:
        if not self.control_listeners:
            return self.control_endpoint

        return ", ".join(
            self.control_listeners
        )

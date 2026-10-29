# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass, field
from pathlib import Path
from ipaddress import IPv4Address


@dataclass(slots=True)
class SMTPSettings:
    host: str = "127.0.0.1"
    port: int = 2525

    def __post_init__(self) -> None:
        try:
            address = IPv4Address(self.host)
        except ValueError as exc:
            raise ValueError(
                "SMTP host must be an IPv4 loopback address"
            ) from exc

        if not address.is_loopback:
            raise ValueError(
                "SMTP host must be an IPv4 loopback address"
            )


@dataclass(slots=True)
class IMAPSettings:
    host: str = "127.0.0.1"
    port: int = 1143

    def __post_init__(self) -> None:
        try:
            address = IPv4Address(self.host)
        except ValueError as exc:
            raise ValueError(
                "IMAP host must be an IPv4 loopback address"
            ) from exc

        if not address.is_loopback:
            raise ValueError(
                "IMAP host must be an IPv4 loopback address"
            )

@dataclass(slots=True)
class LoggingSettings:
    level: str = "INFO"


@dataclass(slots=True)
class TorSettings:
    enabled: bool = True

    socks_host: str = "127.0.0.1"
    socks_port: int = 9050

    onion_smtp_port: int = 25

    onion_http_port: int = 80
    onion_http_target_port: int = 8080

    control_enabled: bool = False
    control_host: str = "127.0.0.1"
    control_port: int = 9051

    cookie_file: Path | None = None

    require_safecookie: bool = True
    allow_new_circuits: bool = False

    onion_custom_page_enabled: bool = False
    onion_custom_page_path: str | None = None


@dataclass(slots=True)
class ApplicationSettings:
    hostname: str = "garlicsmtp.local"
    local_domain: str = "test.onion"

    smtp: SMTPSettings = field(
        default_factory=SMTPSettings,
    )

    imap: IMAPSettings = field(
        default_factory=IMAPSettings,
    )

    logging: LoggingSettings = field(
        default_factory=LoggingSettings,
    )

    tor: TorSettings = field(
        default_factory=TorSettings,
    )
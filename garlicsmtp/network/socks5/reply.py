# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass

from garlicsmtp.network.socks5.exceptions import Socks5HandshakeError


REPLY_CODES = {
    0x00: "succeeded",
    0x01: "general SOCKS server failure",
    0x02: "connection not allowed by ruleset",
    0x03: "network unreachable",
    0x04: "host unreachable",
    0x05: "connection refused",
    0x06: "TTL expired",
    0x07: "command not supported",
    0x08: "address type not supported",
}


@dataclass(slots=True)
class Socks5Reply:
    version: int
    status: int
    address_type: int

    @property
    def success(self) -> bool:
        return self.status == 0x00

    @property
    def message(self) -> str:
        return REPLY_CODES.get(
            self.status,
            "unknown SOCKS5 error",
        )

    @classmethod
    def parse(cls, data: bytes):
        if len(data) < 4:
            raise Socks5HandshakeError(
                "Invalid SOCKS5 reply"
            )

        return cls(
            version=data[0],
            status=data[1],
            address_type=data[3],
        )
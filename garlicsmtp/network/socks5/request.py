# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
import socket


@dataclass(slots=True)
class Socks5ConnectRequest:
    host: str
    port: int

    def serialize(self) -> bytes:
        host = self.host.encode("idna")

        return (
            b"\x05"                    # SOCKS5
            + b"\x01"                  # CONNECT
            + b"\x00"                  # Reserved
            + b"\x03"                  # Domain name
            + bytes([len(host)])       # Host length
            + host
            + self.port.to_bytes(2, "big")
        )
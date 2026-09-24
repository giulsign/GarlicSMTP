# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

class Socks5Error(Exception):
    pass


class Socks5ConnectionError(Socks5Error):
    pass


class Socks5HandshakeError(Socks5Error):
    pass
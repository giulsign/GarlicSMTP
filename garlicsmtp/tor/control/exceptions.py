# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

class TorControlError(Exception):
    """Base error for Tor Control operations."""


class TorControlSecurityError(
    TorControlError
):
    """Raised when an unsafe endpoint is requested."""


class TorControlConnectionError(
    TorControlError
):
    """Raised when the control connection fails."""


class TorControlProtocolError(
    TorControlError
):
    """Raised when malformed control data is received."""
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.transport.dns.records import MXRecord
from garlicsmtp.transport.dns.resolver import DNSResolver
from garlicsmtp.transport.dns.exceptions import DNSLookupError

__all__ = [
    "DNSResolver",
    "MXRecord",
    "DNSLookupError",
]
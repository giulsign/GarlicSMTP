# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from .message import MailMessage
from .envelope import Envelope
from .header import MailHeaders
from .metadata import Metadata
from .smtp import SMTPCommand, SMTPReply
from .onion import OnionAddress

__all__ = [
    "MailMessage",
    "Envelope",
    "MailHeaders",
    "Metadata",
    "SMTPCommand",
    "SMTPReply",
    "OnionAddress",
]

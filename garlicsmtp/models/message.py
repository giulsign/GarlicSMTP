# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass

from .envelope import Envelope
from .header import MailHeaders
from .metadata import Metadata


@dataclass

class MailMessage:

    envelope: Envelope

    headers: MailHeaders

    metadata: Metadata

    body: str = ""

# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass 

from garlicsmtp.models import MailMessage 
from garlicsmtp.storage.entry import (
    VerificationStatus,
)

@dataclass
class PipelineContext:
    message: MailMessage
    accepted: bool = True
    reject_reason: str = ""
    transport: str = "onion"
    verification_status: VerificationStatus = (
        VerificationStatus.UNSIGNED
    )

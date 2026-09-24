# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.models.envelope import Envelope
from garlicsmtp.models.header import MailHeaders
from garlicsmtp.models.message import MailMessage


@pytest.fixture
def message():

    return MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion"
            ],
        ),
        headers=MailHeaders(),
    )

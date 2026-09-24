# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.transport.dns.records import MXRecord


def test_mx_record():
    record = MXRecord(
        priority=10,
        exchange="mail.example.com",
    )

    assert record.priority == 10
    assert record.exchange == "mail.example.com"
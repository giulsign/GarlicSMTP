# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime

from garlicsmtp.queue.retry import RetryPolicy


def test_retry_policy_returns_future_datetime():

    policy = RetryPolicy()

    now = datetime.now(UTC)

    retry = policy.next_retry(1)

    assert retry > now


def test_retry_policy_backoff_grows():

    policy = RetryPolicy()

    first = policy.next_retry(1)
    second = policy.next_retry(2)
    third = policy.next_retry(3)

    now = datetime.now(UTC)

    first_delay = (first - now).total_seconds()
    second_delay = (second - now).total_seconds()
    third_delay = (third - now).total_seconds()

    assert first_delay < second_delay < third_delay
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.application.attachment_limit import (
    ATTACHMENT_LIMIT_BYTES,
    AttachmentLimitExceeded,
    validate_attachment_sizes,
)


def test_attachment_limit_is_one_mib():
    assert ATTACHMENT_LIMIT_BYTES == 1_048_576


def test_attachment_limit_accepts_total_exactly_one_mib():
    validate_attachment_sizes(
        [
            524_288,
            524_288,
        ]
    )


def test_attachment_limit_rejects_total_above_one_mib():
    with pytest.raises(
        AttachmentLimitExceeded
    ):
        validate_attachment_sizes(
            [
                524_288,
                524_289,
            ]
        )


@pytest.mark.parametrize(
    "sizes",
    [
        [-1],
        [100, -1],
        [1.5],
        ["1024"],
        [None],
    ],
)
def test_attachment_limit_rejects_invalid_sizes(
    sizes,
):
    with pytest.raises(
        (TypeError, ValueError)
    ):
        validate_attachment_sizes(
            sizes
        )


def test_attachment_limit_uses_explicit_limit():
    with pytest.raises(
        AttachmentLimitExceeded
    ):
        validate_attachment_sizes(
            [
                600_000,
            ],
            limit_bytes=500_000,
        )
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

ATTACHMENT_LIMIT_BYTES = 1_048_576


class AttachmentLimitExceeded(
    ValueError
):
    pass


def validate_attachment_sizes(
    sizes,
) -> None:
    total = 0

    for size in sizes:
        if not isinstance(
            size,
            int,
        ):
            raise TypeError(
                "attachment size must be an integer"
            )

        if size < 0:
            raise ValueError(
                "attachment size cannot be negative"
            )

        total += size

    if total > ATTACHMENT_LIMIT_BYTES:
        raise AttachmentLimitExceeded(
            "attachment total exceeds 1 MiB"
        )

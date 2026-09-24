# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.security.signature_header import (
    SignatureHeader,
)


def test_signature_header_round_trip():
    header = SignatureHeader(
        version=1,
        algorithm="ed25519",
        public_key="abc",
        signature="def",
    )

    restored = SignatureHeader.parse(
        header.serialize()
    )

    assert restored == header


def test_signature_header_rejects_missing_fields():
    with pytest.raises(ValueError):
        SignatureHeader.parse(
            "v=1; alg=ed25519"
        )


def test_signature_header_rejects_unknown_version():
    with pytest.raises(ValueError):
        SignatureHeader.parse(
            "v=99; alg=ed25519; key=abc; sig=def"
        )


def test_signature_header_rejects_unknown_algorithm():
    with pytest.raises(ValueError):
        SignatureHeader.parse(
            "v=1; alg=rsa; key=abc; sig=def"
        )

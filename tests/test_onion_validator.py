# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.transport.onion.validator import OnionValidator


def test_onion_resolver_valid():

    host = "a" * 56 + ".onion"

    validator = OnionValidator()

    address = validator.resolve(
        f"alice@{host}"
    )

    assert address.localpart == "alice"
    assert address.hostname == host


def test_onion_resolver_invalid():

    validator = OnionValidator()

    with pytest.raises(ValueError):
        validator.resolve("alice@test.onion")
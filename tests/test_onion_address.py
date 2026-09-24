# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.models import OnionAddress


def test_onion_address_parse():

    address = OnionAddress.parse(
        "alice@TestAddress.onion"
    )

    assert address.localpart == "alice"
    assert address.hostname == "testaddress.onion"
    assert address.is_onion is True
    assert str(address) == "alice@testaddress.onion"


def test_onion_address_non_onion():

    address = OnionAddress.parse(
        "bob@example.com"
    )

    assert address.is_onion is False

    
def test_valid_onion():

        host = "a" * 56 + ".onion"

        address = OnionAddress.parse(
            f"alice@{host}"
        )

        assert address.is_valid


def test_invalid_onion():

        address = OnionAddress.parse(
            "alice@test.onion"
        )

        assert not address.is_valid
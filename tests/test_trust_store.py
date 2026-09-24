# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.security.trust_store import (
    MemoryTrustStore,
)


def test_memory_trust_store_unknown_sender():
    store = MemoryTrustStore()

    assert (
        store.is_trusted(
            "alice@test.onion",
            b"\x01" * 32,
        )
        is False
    )


def test_memory_trust_store_trusts_exact_sender_key_pair():
    store = MemoryTrustStore()

    key = b"\x01" * 32

    store.trust(
        "alice@test.onion",
        key,
    )

    assert (
        store.is_trusted(
            "alice@test.onion",
            key,
        )
        is True
    )


def test_memory_trust_store_rejects_different_key():
    store = MemoryTrustStore()

    store.trust(
        "alice@test.onion",
        b"\x01" * 32,
    )

    assert (
        store.is_trusted(
            "alice@test.onion",
            b"\x02" * 32,
        )
        is False
    )

# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application.address_policy import AddressPolicy


def test_rejects_invalid_onion_recipient_by_default():
    policy = AddressPolicy()

    assert not policy.allows_outgoing_recipient(
        "garlicsmtp@test.onion"
    )


def test_accepts_canonical_onion_recipient_by_default():
    policy = AddressPolicy()
    hostname = "a" * 56 + ".onion"

    assert policy.allows_outgoing_recipient(
        f"garlicsmtp@{hostname}"
    )


def test_rejects_custom_recipient_by_default():
    policy = AddressPolicy()
    hostname = "a" * 56 + ".onion"

    assert policy.custom_addresses_enabled is False

    assert not policy.allows_outgoing_recipient(
        f"mario@{hostname}"
    )


def test_custom_addresses_can_be_enabled_and_disabled():
    policy = AddressPolicy()
    hostname = "a" * 56 + ".onion"
    recipient = f"mario@{hostname}"

    assert policy.custom_addresses_enabled is False
    assert not policy.allows_outgoing_recipient(recipient)

    policy.set_custom_addresses_enabled(True)

    assert policy.custom_addresses_enabled is True
    assert policy.allows_outgoing_recipient(recipient)

    policy.set_custom_addresses_enabled(False)

    assert policy.custom_addresses_enabled is False
    assert not policy.allows_outgoing_recipient(recipient)


def test_custom_addresses_do_not_persist_across_instances():
    previous_session = AddressPolicy()
    previous_session.set_custom_addresses_enabled(True)

    assert previous_session.custom_addresses_enabled is True

    new_session = AddressPolicy()

    assert new_session.custom_addresses_enabled is False

    hostname = "a" * 56 + ".onion"

    assert not new_session.allows_outgoing_recipient(
        f"mario@{hostname}"
    )


def test_custom_sender_must_belong_to_local_onion():
    policy = AddressPolicy()

    local_hostname = "a" * 56 + ".onion"
    foreign_hostname = "b" * 56 + ".onion"

    policy.set_local_hostname(local_hostname)
    policy.set_custom_addresses_enabled(True)

    assert policy.allows_sender(
        f"mario@{local_hostname}"
    )

    assert not policy.allows_sender(
        f"mario@{foreign_hostname}"
    )


def test_only_canonical_sender_allowed_by_default():
    policy = AddressPolicy()
    hostname = "a" * 56 + ".onion"

    policy.set_local_hostname(hostname)

    assert policy.canonical_sender == f"garlicsmtp@{hostname}"

    assert policy.allows_sender(
        f"garlicsmtp@{hostname}"
    )

    assert not policy.allows_sender(
        f"mario@{hostname}"
    )
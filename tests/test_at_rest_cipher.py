# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from cryptography.exceptions import InvalidTag
from garlicsmtp.security.at_rest_cipher import AtRestCipher



def test_at_rest_cipher_encrypts_and_decrypts_without_exposing_plaintext():
    key = bytes(range(32))
    plaintext = (
        b"GarlicSMTP confidential message body "
        b"with private attachment metadata"
    )

    cipher = AtRestCipher(key)

    encrypted = cipher.encrypt(plaintext)

    assert encrypted != plaintext
    assert plaintext not in encrypted
    assert cipher.decrypt(encrypted) == plaintext


def test_at_rest_cipher_rejects_wrong_key():
    plaintext = b"Confidential GarlicSMTP message"

    encrypted = AtRestCipher(bytes(range(32))).encrypt(plaintext)

    with pytest.raises(InvalidTag):
        AtRestCipher(bytes(range(1, 33))).decrypt(encrypted)


def test_at_rest_cipher_rejects_tampered_ciphertext():
    cipher = AtRestCipher(bytes(range(32)))
    encrypted = bytearray(cipher.encrypt(b"Private message"))

    encrypted[-1] ^= 0x01

    with pytest.raises(InvalidTag):
        cipher.decrypt(bytes(encrypted))


def test_at_rest_cipher_uses_distinct_nonce_for_each_encryption():
    cipher = AtRestCipher(bytes(range(32)))
    plaintext = b"Same confidential message"

    first = cipher.encrypt(plaintext)
    second = cipher.encrypt(plaintext)

    assert first != second
    assert first[1:13] != second[1:13]
    assert cipher.decrypt(first) == plaintext
    assert cipher.decrypt(second) == plaintext
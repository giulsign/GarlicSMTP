# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)


def test_password_hasher_verifies_password():
    hasher = PasswordHasher()

    encoded = hasher.hash_password(
        "correct horse battery staple"
    )

    assert hasher.verify_password(
        "correct horse battery staple",
        encoded,
    ) is True


def test_password_hasher_rejects_wrong_password():
    hasher = PasswordHasher()

    encoded = hasher.hash_password(
        "correct horse battery staple"
    )

    assert hasher.verify_password(
        "wrong password",
        encoded,
    ) is False


def test_password_hasher_rejects_malformed_hash():
    hasher = PasswordHasher()

    assert hasher.verify_password(
        "secret",
        "not-a-valid-password-hash",
    ) is False


def test_password_hasher_encodes_algorithm_parameters_salt_and_hash():
    hasher = PasswordHasher()

    encoded = hasher.hash_password(
        "secret"
    )

    (
        algorithm,
        n,
        r,
        p,
        length,
        salt,
        derived,
    ) = encoded.split("$")

    assert algorithm == "scrypt"
    assert int(n) > 0
    assert int(r) > 0
    assert int(p) > 0
    assert int(length) > 0
    assert salt
    assert derived

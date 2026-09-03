# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import base64
import pytest

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
)

from garlicsmtp.security.encryption_capability import (
    EncryptionCapability,
)


def test_encryption_capability_parses_public_key():
    private_key = X25519PrivateKey.generate()

    public_key_bytes = (
        private_key.public_key().public_bytes_raw()
    )

    encoded_key = base64.b64encode(
        public_key_bytes
    ).decode("ascii")

    capability = EncryptionCapability.parse(
        "v=1; "
        "alg=x25519; "
        f"key={encoded_key}"
    )

    assert (
        capability.public_key.public_bytes_raw()
        == public_key_bytes
    )


def test_encryption_capability_rejects_unsupported_version():
    private_key = X25519PrivateKey.generate()

    encoded_key = base64.b64encode(
        private_key.public_key().public_bytes_raw()
    ).decode("ascii")

    with pytest.raises(
        ValueError,
        match="unsupported encryption version",
    ):
        EncryptionCapability.parse(
            "v=2; "
            "alg=x25519; "
            f"key={encoded_key}"
        )


def test_encryption_capability_rejects_unsupported_algorithm():
    private_key = X25519PrivateKey.generate()

    encoded_key = base64.b64encode(
        private_key.public_key().public_bytes_raw()
    ).decode("ascii")

    with pytest.raises(
        ValueError,
        match="unsupported encryption algorithm",
    ):
        EncryptionCapability.parse(
            "v=1; "
            "alg=rsa; "
            f"key={encoded_key}"
        )


def test_encryption_capability_rejects_malformed_key_base64():
    with pytest.raises(
        ValueError,
        match="invalid encryption key",
    ):
        EncryptionCapability.parse(
            "v=1; "
            "alg=x25519; "
            "key=not-base64!"
        )


def test_encryption_capability_rejects_invalid_key_length():
    encoded_key = base64.b64encode(
        b"too-short"
    ).decode("ascii")

    with pytest.raises(
        ValueError,
        match="invalid encryption key length",
    ):
        EncryptionCapability.parse(
            "v=1; "
            "alg=x25519; "
            f"key={encoded_key}"
        )


def test_encryption_capability_rejects_duplicate_field():
    private_key = X25519PrivateKey.generate()

    encoded_key = base64.b64encode(
        private_key.public_key().public_bytes_raw()
    ).decode("ascii")

    with pytest.raises(
        ValueError,
        match="duplicate encryption field",
    ):
        EncryptionCapability.parse(
            "v=1; "
            "alg=x25519; "
            "alg=x25519; "
            f"key={encoded_key}"
        )


def test_encryption_capability_rejects_unknown_field():
    private_key = X25519PrivateKey.generate()

    encoded_key = base64.b64encode(
        private_key.public_key().public_bytes_raw()
    ).decode("ascii")

    with pytest.raises(
        ValueError,
        match="unknown encryption field",
    ):
        EncryptionCapability.parse(
            "v=1; "
            "alg=x25519; "
            f"key={encoded_key}; "
            "foo=bar"
        )


def test_encryption_capability_rejects_missing_field():
    private_key = X25519PrivateKey.generate()

    encoded_key = base64.b64encode(
        private_key.public_key().public_bytes_raw()
    ).decode("ascii")

    with pytest.raises(
        ValueError,
        match="missing encryption field",
    ):
        EncryptionCapability.parse(
            "v=1; "
            f"key={encoded_key}"
        )


def test_encryption_capability_rejects_malformed_field():
    with pytest.raises(
        ValueError,
        match="malformed encryption field",
    ):
        EncryptionCapability.parse(
            "v=1; "
            "alg=x25519; "
            "key"
        )


def test_encryption_capability_serializes_public_key():
    private_key = X25519PrivateKey.generate()

    public_key = private_key.public_key()

    encoded_key = base64.b64encode(
        public_key.public_bytes_raw()
    ).decode("ascii")

    capability = EncryptionCapability(
        public_key=public_key
    )

    assert capability.serialize() == (
        "v=1; "
        "alg=x25519; "
        f"key={encoded_key}"
    )
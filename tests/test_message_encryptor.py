# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest
import base64

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
)

from garlicsmtp.security.encryptor import (
    MessageEncryptor,
)
from garlicsmtp.security.decryptor import (
    MessageDecryptor,
    _parse_payload,
)
from cryptography.exceptions import InvalidTag
from garlicsmtp.security.encryptor import (
    MessageEncryptor,
)
from garlicsmtp.security.encryptor import (
    ENCRYPTION_HEADER,
    MessageEncryptor,
)



def test_message_encryptor_hides_plaintext(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    assert encrypted is not message

    assert (
        message.body
        not in encrypted.body
    )


def test_message_encryptor_round_trip(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    decrypted = decryptor.decrypt(
        encrypted,
        recipient_private_key,
    )

    assert decrypted.body == (
        "secret plaintext"
    )


def test_message_encryptor_hides_headers_and_body(
    message,
):
    message.headers.add(
        "Subject",
        "Secret subject",
    )
    message.headers.add(
        "X-GarlicSMTP-Signature",
        "test-signature",
    )
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    assert (
        encrypted.headers.get(
            "Subject"
        )
        is None
    )

    assert (
        encrypted.headers.get(
            "X-GarlicSMTP-Signature"
        )
        is None
    )

    assert (
        "Secret subject"
        not in encrypted.body
    )

    assert (
        "test-signature"
        not in encrypted.body
    )

    assert (
        "secret plaintext"
        not in encrypted.body
    )


def test_message_decryptor_rejects_wrong_private_key(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    wrong_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    with pytest.raises(InvalidTag):
        decryptor.decrypt(
            encrypted,
            wrong_private_key,
        )


def test_message_decryptor_rejects_tampered_ciphertext(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    import base64

    ciphertext = bytearray(
        base64.b64decode(
            encrypted.body
        )
    )

    ciphertext[0] ^= 1

    encrypted.body = base64.b64encode(
        bytes(ciphertext)
    ).decode("ascii")

    with pytest.raises(InvalidTag):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_tampered_envelope(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    encrypted.envelope.sender = (
        "mallory@test.onion"
    )

    with pytest.raises(InvalidTag):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_tampered_recipient_order(
    message,
):
    message.envelope.recipients = [
        "bob@test.onion",
        "carol@test.onion",
    ]
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    encrypted.envelope.recipients = [
        "carol@test.onion",
        "bob@test.onion",
    ]

    with pytest.raises(InvalidTag):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_missing_encryption_header(
    message,
):
    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    decryptor = MessageDecryptor()

    with pytest.raises(ValueError):
        decryptor.decrypt(
            message,
            recipient_private_key,
        )


def test_message_decryptor_rejects_unsupported_version(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    value = encrypted.headers.get(
        "X-GarlicSMTP-Encryption"
    )

    encrypted.headers.add(
        "X-GarlicSMTP-Encryption",
        value.replace(
            "v=1",
            "v=2",
            1,
        ),
    )

    with pytest.raises(ValueError):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_unsupported_algorithm(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    value = encrypted.headers.get(
        "X-GarlicSMTP-Encryption"
    )

    encrypted.headers.add(
        "X-GarlicSMTP-Encryption",
        value.replace(
            "alg=x25519-chacha20poly1305",
            "alg=unsupported",
            1,
        ),
    )

    with pytest.raises(ValueError):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_malformed_key_base64(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    value = encrypted.headers.get(
        "X-GarlicSMTP-Encryption"
    )

    parts = []

    for part in value.split(";"):
        stripped = part.strip()

        if stripped.startswith("key="):
            parts.append(
                stripped + "!!"
            )
        else:
            parts.append(stripped)

    encrypted.headers.add(
        "X-GarlicSMTP-Encryption",
        "; ".join(parts),
    )

    with pytest.raises(ValueError):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_malformed_nonce_base64(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    value = encrypted.headers.get(
        "X-GarlicSMTP-Encryption"
    )

    parts = []

    for part in value.split(";"):
        stripped = part.strip()

        if stripped.startswith("nonce="):
            parts.append(
                stripped + "!!"
            )
        else:
            parts.append(stripped)

    encrypted.headers.add(
        "X-GarlicSMTP-Encryption",
        "; ".join(parts),
    )

    with pytest.raises(ValueError):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_malformed_ciphertext_base64(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    encrypted.body += "!!"

    with pytest.raises(ValueError):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_invalid_nonce_length(
    message,
):
    import base64

    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    value = encrypted.headers.get(
        "X-GarlicSMTP-Encryption"
    )

    parts = []

    for part in value.split(";"):
        stripped = part.strip()

        if stripped.startswith("nonce="):
            parts.append(
                "nonce="
                + base64.b64encode(
                    b"x" * 11
                ).decode("ascii")
            )
        else:
            parts.append(stripped)

    encrypted.headers.add(
        "X-GarlicSMTP-Encryption",
        "; ".join(parts),
    )

    with pytest.raises(
        ValueError,
        match="invalid nonce length",
    ):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_duplicate_encryption_fields(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    value = encrypted.headers.get(
        "X-GarlicSMTP-Encryption"
    )

    encrypted.headers.add(
        "X-GarlicSMTP-Encryption",
        value + "; v=1",
    )

    with pytest.raises(
        ValueError,
        match="duplicate encryption field",
    ):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_unknown_encryption_field(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    value = encrypted.headers.get(
        "X-GarlicSMTP-Encryption"
    )

    encrypted.headers.add(
        "X-GarlicSMTP-Encryption",
        value + "; extra=value",
    )

    with pytest.raises(
        ValueError,
        match="unknown encryption field",
    ):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_missing_encryption_field(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    value = encrypted.headers.get(
        "X-GarlicSMTP-Encryption"
    )

    parts = [
        part.strip()
        for part in value.split(";")
        if not part.strip().startswith(
            "nonce="
        )
    ]

    encrypted.headers.add(
        "X-GarlicSMTP-Encryption",
        "; ".join(parts),
    )

    with pytest.raises(
        ValueError,
        match="missing encryption field",
    ):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_message_decryptor_rejects_malformed_encryption_field(
    message,
):
    message.body = "secret plaintext"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    encryptor = MessageEncryptor()
    decryptor = MessageDecryptor()

    encrypted = encryptor.encrypt(
        message,
        recipient_private_key.public_key(),
    )

    value = encrypted.headers.get(
        "X-GarlicSMTP-Encryption"
    )

    encrypted.headers.add(
        "X-GarlicSMTP-Encryption",
        value + "; malformed",
    )

    with pytest.raises(
        ValueError,
        match="malformed encryption field",
    ):
        decryptor.decrypt(
            encrypted,
            recipient_private_key,
        )


def test_decrypted_payload_rejects_missing_headers():
    payload = b'{"body":"secret plaintext"}'

    with pytest.raises(
        ValueError,
        match="invalid encrypted payload",
    ):
        _parse_payload(
            payload
        )


def test_decrypted_payload_rejects_non_object_headers():
    payload = (
        b'{"headers":[],"body":"secret plaintext"}'
    )

    with pytest.raises(
        ValueError,
        match="invalid encrypted payload",
    ):
        _parse_payload(
            payload
        )


def test_decrypted_payload_rejects_non_string_body():
    payload = (
        b'{"headers":{},"body":123}'
    )

    with pytest.raises(
        ValueError,
        match="invalid encrypted payload",
    ):
        _parse_payload(
            payload
        )


def test_decrypted_payload_rejects_unknown_field():
    payload = (
        b'{"headers":{},"body":"secret","extra":1}'
    )

    with pytest.raises(
        ValueError,
        match="invalid encrypted payload",
    ):
        _parse_payload(
            payload
        )


def test_decrypted_payload_rejects_malformed_json():
    payload = b'{"headers":{},"body":"secret"'

    with pytest.raises(
        ValueError,
        match="invalid encrypted payload",
    ):
        _parse_payload(
            payload
        )


def test_decrypted_payload_rejects_invalid_utf8():
    payload = b"\xff\xfe"

    with pytest.raises(
        ValueError,
        match="invalid encrypted payload",
    ):
        _parse_payload(
            payload
        )


def test_message_decryptor_rejects_invalid_ephemeral_key_length(
    message,
):
    recipient_private_key = X25519PrivateKey.generate()
    recipient_public_key = recipient_private_key.public_key()

    encrypted = MessageEncryptor().encrypt(
        message,
        recipient_public_key,
    )

    encryption_value = encrypted.headers.get(
        ENCRYPTION_HEADER
    )

    parts = encryption_value.split(";")

    malformed_parts = []

    for part in parts:
        stripped = part.strip()

        if stripped.startswith("key="):
            malformed_parts.append(
                "key="
                + base64.b64encode(
                    b"\x00" * 31
                ).decode("ascii")
            )
        else:
            malformed_parts.append(
                stripped
            )

    encrypted.headers.add(
        ENCRYPTION_HEADER,
        "; ".join(
            malformed_parts
        ),
    )

    with pytest.raises(
        ValueError,
        match="invalid ephemeral key length",
    ):
        MessageDecryptor().decrypt(
            encrypted,
            recipient_private_key,
        )
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import base64
import json

from cryptography.hazmat.primitives import (
    hashes,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import (
    ChaCha20Poly1305,
)
from cryptography.hazmat.primitives.kdf.hkdf import (
    HKDF,
)

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)

from garlicsmtp.security.encryptor import (
    ENCRYPTION_HEADER,
    HKDF_INFO,
)
from garlicsmtp.security.encryptor import (
    _envelope_aad,
)

def _parse_payload(
    plaintext: bytes,
) -> dict:
    try:
        payload = json.loads(
            plaintext.decode("utf-8")
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise ValueError(
            "invalid encrypted payload"
        ) from exc

    if (
        not isinstance(payload, dict)
        or set(payload) != {
            "headers",
            "body",
        }
        or not isinstance(
            payload["headers"],
            dict,
        )
        or not isinstance(
            payload["body"],
            str,
        )
    ):
        raise ValueError(
            "invalid encrypted payload"
        )

    return payload

class MessageDecryptor:

    def decrypt(
        self,
        message: MailMessage,
        recipient_private_key,
    ) -> MailMessage:
        encryption_value = (
            message.headers.get(
                ENCRYPTION_HEADER
            )
        )

        if encryption_value is None:
            raise ValueError(
                "missing encryption header"
            )

        fields = {}

        for part in encryption_value.split(";"):
            stripped = part.strip()

            if "=" not in stripped:
                raise ValueError(
                    "malformed encryption field"
                )

            name, value = stripped.split(
                "=",
                1,
            )

            if name not in {
                "v",
                "alg",
                "key",
                "nonce",
            }:
                raise ValueError(
                    "unknown encryption field"
                )

            if name in fields:
                raise ValueError(
                    "duplicate encryption field"
                )

            fields[name] = value

        required_fields = {
            "v",
            "alg",
            "key",
            "nonce",
        }

        if set(fields) != required_fields:
            raise ValueError(   
                "missing encryption field"
            )

        if fields.get("v") != "1":
            raise ValueError(
                "unsupported encryption version"
            )
        if (
            fields.get("alg")
            != "x25519-chacha20poly1305"
        ):
            raise ValueError(
                "unsupported encryption algorithm"
            )

        ephemeral_public_key_bytes = base64.b64decode(
            fields["key"],
            validate=True,
        )

        if len(ephemeral_public_key_bytes) != 32:
            raise ValueError(
                "invalid ephemeral key length"
            )

        ephemeral_public_key = X25519PublicKey.from_public_bytes(
            ephemeral_public_key_bytes
        )

        nonce = base64.b64decode(
            fields["nonce"],
            validate=True,
        )

        if len(nonce) != 12:
            raise ValueError(
                "invalid nonce length"
            )

        ciphertext = base64.b64decode(
            message.body,
            validate=True,
        )

        shared_secret = (
            recipient_private_key.exchange(
                ephemeral_public_key
            )
        )

        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=HKDF_INFO,
        ).derive(shared_secret)

        plaintext = ChaCha20Poly1305(
            key
        ).decrypt(
            nonce,
            ciphertext,
            _envelope_aad(
                message
            ),
        )

        payload = _parse_payload(
            plaintext
        )

        return MailMessage(
            envelope=Envelope(
                sender=message.envelope.sender,
                recipients=list(
                    message.envelope.recipients
                ),
            ),
            headers=MailHeaders(
                fields=payload["headers"]
            ),
            body=payload["body"],
        )
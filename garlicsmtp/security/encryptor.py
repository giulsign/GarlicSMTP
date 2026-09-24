# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import base64
import json
import os

from cryptography.hazmat.primitives import (
    hashes,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
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


ENCRYPTION_HEADER = "X-GarlicSMTP-Encryption"
HKDF_INFO = b"GarlicSMTP E2EE v1"



def _envelope_aad(
        message: MailMessage,
    ) -> bytes:
        data = {
            "sender": (
                message.envelope.sender
            ),
            "recipients": list(
                message.envelope.recipients
            ),
        }

        return json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")


class MessageEncryptor:

    def encrypt(
        self,
        message: MailMessage,
        recipient_public_key,
    ) -> MailMessage:
        ephemeral_private_key = (
            X25519PrivateKey.generate()
        )

        shared_secret = (
            ephemeral_private_key.exchange(
                recipient_public_key
            )
        )

        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=HKDF_INFO,
        ).derive(shared_secret)

        payload = json.dumps(
            {
                "headers": (
                    message.headers.fields
                ),
                "body": message.body,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        nonce = os.urandom(12)

        ciphertext = ChaCha20Poly1305(
            key
        ).encrypt(
            nonce,
            payload,
            _envelope_aad(
                message
            ),
        )

        ephemeral_public_key = (
            ephemeral_private_key
            .public_key()
            .public_bytes_raw()
        )

        encryption_value = (
            "v=1; "
            "alg=x25519-chacha20poly1305; "
            "key="
            + base64.b64encode(
                ephemeral_public_key
            ).decode("ascii")
            + "; nonce="
            + base64.b64encode(
                nonce
            ).decode("ascii")
        )

        headers = MailHeaders()
        headers.add(
            ENCRYPTION_HEADER,
            encryption_value,
        )

        return MailMessage(
            envelope=Envelope(
                sender=message.envelope.sender,
                recipients=list(
                    message.envelope.recipients
                ),
            ),
            headers=headers,
            body=base64.b64encode(
                ciphertext
            ).decode("ascii"),
        )
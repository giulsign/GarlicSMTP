# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from garlicsmtp.models import MailMessage
from garlicsmtp.security.canonicalizer import (
    MessageCanonicalizer,
)
from garlicsmtp.security.signature_header import (
    SIGNATURE_HEADER,
    SignatureHeader,
)


class MessageSigner:

    def __init__(
        self,
        private_key: Ed25519PrivateKey,
    ):
        self.private_key = private_key

    def sign(
        self,
        message: MailMessage,
    ) -> MailMessage:
        canonical = (
            MessageCanonicalizer.canonicalize(
                message
            )
        )

        signature = self.private_key.sign(
            canonical
        )

        public_key = (
            self.private_key
            .public_key()
            .public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        )

        header = SignatureHeader(
            version=1,
            algorithm="ed25519",
            public_key=base64.b64encode(
                public_key
            ).decode("ascii"),
            signature=base64.b64encode(
                signature
            ).decode("ascii"),
        )

        message.headers.add(
            SIGNATURE_HEADER,
            header.serialize(),
        )

        return message

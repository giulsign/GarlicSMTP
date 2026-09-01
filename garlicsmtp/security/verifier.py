# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC, abstractmethod
import base64
import binascii

from garlicsmtp.models.message import MailMessage
from garlicsmtp.storage.entry import VerificationStatus
from garlicsmtp.security.signature_header import (
    SIGNATURE_HEADER,
    SignatureHeader,
)
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)

from garlicsmtp.security.canonicalizer import (
    MessageCanonicalizer,
)
from garlicsmtp.security.trust_store import (
    TrustStore,
)


class MessageVerifier(ABC):

    @abstractmethod
    def verify(
        self,
        message: MailMessage,
    ) -> VerificationStatus:
        """
        Verify the authenticity and integrity of a message.

        The verification result is local trust metadata and
        must not modify the message being verified.
        """
        raise NotImplementedError


class Ed25519MessageVerifier(MessageVerifier):

    def __init__(
        self,
        trust_store: TrustStore | None = None,
    ):
        self.trust_store = trust_store

    def verify(
        self,
        message: MailMessage,
    ) -> VerificationStatus:
        signature_value = message.headers.get(
            SIGNATURE_HEADER
        )

        if signature_value is None:
            return VerificationStatus.UNSIGNED

        try:
            header = SignatureHeader.parse(
                signature_value
            )
        except ValueError:
            return VerificationStatus.INVALID

        try:
            public_key = base64.b64decode(
                header.public_key,
                validate=True,
            )

            signature = base64.b64decode(
                header.signature,
                validate=True,
            )
        except (binascii.Error, ValueError):
            return VerificationStatus.INVALID

        if len(public_key) != 32:
            return VerificationStatus.INVALID

        if len(signature) != 64:
            return VerificationStatus.INVALID

        try:
            verifier_key = Ed25519PublicKey.from_public_bytes(
                public_key
            )

            verifier_key.verify(
                signature,
                MessageCanonicalizer.canonicalize(
                    message
                ),
            )
        except (ValueError, InvalidSignature):
            return VerificationStatus.INVALID

        if (
            self.trust_store is not None
            and self.trust_store.is_trusted(
                message.envelope.sender,
                public_key,
            )
        ):
            return VerificationStatus.VERIFIED

        return VerificationStatus.UNKNOWN_KEY
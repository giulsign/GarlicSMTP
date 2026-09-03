# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
import base64
import binascii

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PublicKey,
)


@dataclass(frozen=True)
class EncryptionCapability:

    public_key: X25519PublicKey

    def serialize(
        self,
    ) -> str:
        encoded_key = base64.b64encode(
            self.public_key.public_bytes_raw()
        ).decode("ascii")

        return (
            "v=1; "
            "alg=x25519; "
            f"key={encoded_key}"
        )

    @classmethod
    def parse(
        cls,
        value: str,
    ) -> "EncryptionCapability":
        fields = {}

        for part in value.split(";"):
            stripped = part.strip()

            if "=" not in stripped:
                raise ValueError(
                    "malformed encryption field"
                )

            name, field_value = stripped.split(
                "=",
                1,
            )

            if name not in {
                "v",
                "alg",
                "key",
            }:
                raise ValueError(
                    "unknown encryption field"
                )

            if name in fields:
                raise ValueError(
                    "duplicate encryption field"
                )

            fields[name] = field_value

        required_fields = {
            "v",
            "alg",
            "key",
        }

        if set(fields) != required_fields:
            raise ValueError(
                "missing encryption field"
            )

        if fields.get("v") != "1":
            raise ValueError(
                "unsupported encryption version"
            )

        if fields.get("alg") != "x25519":
            raise ValueError(
                "unsupported encryption algorithm"
            )

        try:
            public_key_bytes = base64.b64decode(
                fields["key"],
                validate=True,
            )
        except binascii.Error as exc:
            raise ValueError(
                "invalid encryption key"
            ) from exc

        if len(public_key_bytes) != 32:
            raise ValueError(
                "invalid encryption key length"
            )

        public_key = X25519PublicKey.from_public_bytes(
            public_key_bytes
        )

        return cls(
            public_key=public_key
        )

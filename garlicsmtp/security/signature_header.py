# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass


SIGNATURE_HEADER = "X-GarlicSMTP-Signature"


@dataclass(frozen=True)
class SignatureHeader:
    version: int
    algorithm: str
    public_key: str
    signature: str

    def serialize(self) -> str:
        return (
            f"v={self.version}; "
            f"alg={self.algorithm}; "
            f"key={self.public_key}; "
            f"sig={self.signature}"
        )

    @classmethod
    def parse(
        cls,
        value: str,
    ) -> "SignatureHeader":
        parts = {}

        for item in value.split(";"):
            item = item.strip()

            if "=" not in item:
                raise ValueError(
                    "Invalid signature header"
                )

            key, field_value = item.split(
                "=",
                1,
            )

            key = key.strip()
            field_value = field_value.strip()

            if not key or not field_value:
                raise ValueError(
                    "Invalid signature header"
                )

            if key in parts:
                raise ValueError(
                    "Invalid signature header"
                )

            parts[key] = field_value

        required = {
            "v",
            "alg",
            "key",
            "sig",
        }

        if set(parts) != required:
            raise ValueError(
                "Invalid signature header"
            )

        try:
            version = int(parts["v"])
        except ValueError as exc:
            raise ValueError(
                "Invalid signature header"
            ) from exc

        if version != 1:
            raise ValueError(
                "Unsupported signature version"
            )

        if parts["alg"] != "ed25519":
            raise ValueError(
                "Unsupported signature algorithm"
            )

        return cls(
            version=version,
            algorithm=parts["alg"],
            public_key=parts["key"],
            signature=parts["sig"],
        )

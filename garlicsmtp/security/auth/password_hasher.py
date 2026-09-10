# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


import base64
import os

from cryptography.hazmat.primitives.kdf.scrypt import (
    Scrypt,
)


class PasswordHasher:

    _N = 2**14
    _R = 8
    _P = 1
    _LENGTH = 32

    def hash_password(
        self,
        password: str,
    ) -> str:
        salt = os.urandom(16)

        derived = self._derive(
            password,
            salt,
            n=self._N,
            r=self._R,
            p=self._P,
            length=self._LENGTH,
        )

        return "$".join(
            (
                "scrypt",
                str(self._N),
                str(self._R),
                str(self._P),
                str(self._LENGTH),
                base64.b64encode(salt).decode("ascii"),
                base64.b64encode(derived).decode("ascii"),
            )
        )

    def verify_password(
        self,
        password: str,
        encoded: str,
    ) -> bool:
        try:
            (
                algorithm,
                n,
                r,
                p,
                length,
                salt,
                expected,
            ) = encoded.split("$")

            if algorithm != "scrypt":
                return False

            derived = self._derive(
                password,
                base64.b64decode(salt),
                n=int(n),
                r=int(r),
                p=int(p),
                length=int(length),
            )

            return derived == base64.b64decode(
                expected
            )

        except (
            ValueError,
            TypeError,
        ):
            return False

    @staticmethod
    def _derive(
        password: str,
        salt: bytes,
        *,
        n: int,
        r: int,
        p: int,
        length: int,
    ) -> bytes:
        return Scrypt(
            salt=salt,
            length=length,
            n=n,
            r=r,
            p=p,
        ).derive(
            password.encode("utf-8")
        )

import os
import secrets

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from garlicsmtp.security.at_rest_cipher import AtRestCipher


class AtRestKeyManager:
    _VERSION = b"\x02"
    _SALT_SIZE = 16
    _DEK_SIZE = 32

    _SCRYPT_N = 2**14
    _SCRYPT_R = 8
    _SCRYPT_P = 1

    _PURPOSES = {
        "password": b"\x01",
        "recovery": b"\x02",
    }

    def generate_dek(self) -> bytes:
        return os.urandom(self._DEK_SIZE)

    def generate_recovery_key(self) -> str:
        return secrets.token_hex(32)

    def wrap_dek(
        self,
        *,
        dek: bytes,
        secret: str,
        purpose: str = "password",
    ) -> bytes:
        if not isinstance(dek, bytes) or len(dek) != self._DEK_SIZE:
            raise ValueError("DEK must be 32 bytes")

        if not isinstance(secret, str) or not secret:
            raise ValueError("Wrapping secret must not be empty")

        purpose_id = self._purpose_id(purpose)
        salt = os.urandom(self._SALT_SIZE)

        kek = self._derive_kek(
            secret,
            salt,
            purpose_id,
        )

        encrypted_dek = AtRestCipher(kek).encrypt(dek)

        return (
            self._VERSION
            + purpose_id
            + salt
            + encrypted_dek
        )

    def unwrap_dek(
        self,
        *,
        wrapped: bytes,
        secret: str,
        purpose: str = "password",
    ) -> bytes:
        minimum_size = (
            1  # wrapping version
            + 1  # purpose
            + self._SALT_SIZE
            + 1  # cipher version
            + 12  # nonce
            + self._DEK_SIZE
            + 16  # authentication tag
        )

        if not isinstance(wrapped, bytes) or len(wrapped) < minimum_size:
            raise ValueError("Invalid wrapped DEK")

        if not isinstance(secret, str) or not secret:
            raise ValueError("Wrapping secret must not be empty")

        if wrapped[:1] != self._VERSION:
            raise ValueError("Unsupported wrapped DEK version")

        expected_purpose = self._purpose_id(purpose)
        stored_purpose = wrapped[1:2]

        if stored_purpose != expected_purpose:
            raise ValueError("Incorrect wrapped DEK purpose")

        salt = wrapped[2 : 2 + self._SALT_SIZE]
        encrypted_dek = wrapped[2 + self._SALT_SIZE :]

        kek = self._derive_kek(
            secret,
            salt,
            expected_purpose,
        )

        dek = AtRestCipher(kek).decrypt(encrypted_dek)

        if len(dek) != self._DEK_SIZE:
            raise ValueError("Invalid decrypted DEK")

        return dek

    @classmethod
    def _purpose_id(cls, purpose: str) -> bytes:
        try:
            return cls._PURPOSES[purpose]
        except (KeyError, TypeError) as exc:
            raise ValueError(
                "Unsupported DEK wrapping purpose"
            ) from exc

    def _derive_kek(
        self,
        secret: str,
        salt: bytes,
        purpose_id: bytes,
    ) -> bytes:
        return Scrypt(
            salt=salt,
            length=self._DEK_SIZE,
            n=self._SCRYPT_N,
            r=self._SCRYPT_R,
            p=self._SCRYPT_P,
        ).derive(
            b"GarlicSMTP at-rest KEK v2\x00"
            + purpose_id
            + b"\x00"
            + secret.encode("utf-8")
        )
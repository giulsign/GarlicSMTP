import os

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


class AtRestCipher:
    _NONCE_SIZE = 12
    _VERSION = b"\x01"

    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) != 32:
            raise ValueError("At-rest encryption key must be 32 bytes")

        self._cipher = ChaCha20Poly1305(key)

    def encrypt(self, plaintext: bytes) -> bytes:
        nonce = os.urandom(self._NONCE_SIZE)
        ciphertext = self._cipher.encrypt(
            nonce,
            plaintext,
            self._VERSION,
        )

        return self._VERSION + nonce + ciphertext

    def decrypt(self, encrypted: bytes) -> bytes:
        minimum_size = 1 + self._NONCE_SIZE + 16

        if len(encrypted) < minimum_size:
            raise ValueError("Invalid encrypted payload")

        version = encrypted[:1]

        if version != self._VERSION:
            raise ValueError("Unsupported encrypted payload version")

        nonce = encrypted[1 : 1 + self._NONCE_SIZE]
        ciphertext = encrypted[1 + self._NONCE_SIZE :]

        return self._cipher.decrypt(
            nonce,
            ciphertext,
            version,
        )

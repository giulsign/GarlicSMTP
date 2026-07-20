import secrets

from garlicsmtp.security.auth.authenticator import (
    Authenticator,
)


class MemoryAuthenticator(Authenticator):

    def __init__(
        self,
        credentials: dict[str, str] | None = None,
    ):
        self._credentials = dict(
            credentials or {}
        )

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> bool:
        expected_password = self._credentials.get(
            username
        )

        if expected_password is None:
            return False

        return secrets.compare_digest(
            expected_password,
            password,
        )

    def add_user(
        self,
        username: str,
        password: str,
    ) -> None:
        self._credentials[username] = password
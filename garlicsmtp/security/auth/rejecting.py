from garlicsmtp.security.auth.authenticator import (
    Authenticator,
)


class RejectingAuthenticator(Authenticator):

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> bool:
        return False
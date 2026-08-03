class TorControlError(Exception):
    """Base error for Tor Control operations."""


class TorControlSecurityError(
    TorControlError
):
    """Raised when an unsafe endpoint is requested."""


class TorControlConnectionError(
    TorControlError
):
    """Raised when the control connection fails."""


class TorControlProtocolError(
    TorControlError
):
    """Raised when malformed control data is received."""
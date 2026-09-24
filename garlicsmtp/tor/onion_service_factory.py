from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
)
from garlicsmtp.tor.control import (
    SafeCookieAuthenticator,
    TorControlClient,
    TorControlConnection,
)
from garlicsmtp.tor.onion_service_manager import (
    OnionServiceManager,
)


def build_onion_service_manager(
    *,
    paths: ApplicationPaths,
    settings: ApplicationSettings,
    hostname_callback=None,
) -> OnionServiceManager:
    connection = TorControlConnection(
        host=settings.tor.control_host,
        port=settings.tor.control_port,
    )

    client = TorControlClient(
        connection=connection,
    )

    authenticator = SafeCookieAuthenticator(
        client=client,
        configured_cookie_file=(
            settings.tor.cookie_file
        ),
    )

    return OnionServiceManager(
        client=client,
        authenticator=authenticator,
        identity_file=paths.onion_identity_file,
        virtual_port=settings.tor.onion_smtp_port,
        target_host=settings.smtp.host,
        target_port=settings.smtp.port,
        hostname_callback=hostname_callback,
    )

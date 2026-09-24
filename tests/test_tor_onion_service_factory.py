from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
)
from garlicsmtp.tor.onion_service_factory import (
    build_onion_service_manager,
)
from garlicsmtp.tor.onion_service_manager import (
    OnionServiceManager,
)


def test_build_onion_service_manager_uses_application_configuration(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    settings = ApplicationSettings()
    settings.tor.control_host = "127.0.0.2"
    settings.tor.control_port = 19051
    settings.tor.onion_smtp_port = 2526
    settings.smtp.host = "127.0.0.3"
    settings.smtp.port = 2527

    callback = object()

    onion_service = build_onion_service_manager(
        paths=paths,
        settings=settings,
        hostname_callback=callback,
    )

    assert isinstance(
        onion_service,
        OnionServiceManager,
    )

    assert (
        onion_service.identity_file
        == paths.onion_identity_file
    )

    assert (
        onion_service.virtual_port
        == settings.tor.onion_smtp_port
    )

    assert (
        onion_service.target_host
        == settings.smtp.host
    )

    assert (
        onion_service.target_port
        == settings.smtp.port
    )

    assert (
        onion_service.hostname_callback
        is callback
    )

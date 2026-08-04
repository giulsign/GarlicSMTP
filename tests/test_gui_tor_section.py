from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.sections import (
    TorSection,
)
from tests.support import (
    make_application_status,
    make_tor_status,
)

from tests.test_gui_main_window import (
    FakeController,
    get_application,
)


def test_tor_section_displays_status():
    get_application()

    controller = FakeController()

    controller.current_status = (
        make_application_status(
            tor=make_tor_status(
                control_enabled=True,
                control_available=True,
                authenticated=True,
                authentication_method=(
                    "SAFECOOKIE"
                ),
                socks_available=True,
                version="0.4.8.12",
                bootstrap_progress=100,
                bootstrap_summary="Done",
                built_circuits=3,
                active_streams=1,
                last_error=None,
                socks_listeners=(
                    "127.0.0.1:9050",
                ),
                control_listeners=(
                    "127.0.0.1:9051",
                ),
            )
        )
    )

    view_model = ApplicationViewModel(
        controller
    )

    section = TorSection(
        view_model=view_model
    )

    section.refresh_view()

    assert (
        section.status_value.text()
        == "Ready"
    )

    assert (
        section.socks_value.text()
        == "127.0.0.1:9050"
    )

    assert (
        section.control_value.text()
        == "127.0.0.1:9051"
    )

    assert (
        section.authentication_value.text()
        == "SAFECOOKIE"
    )

    assert (
        section.version_value.text()
        == "0.4.8.12"
    )

    assert (
        section.bootstrap_value.text()
        == "100% — Done"
    )

    assert (
        section.circuits_value.text()
        == "3 built circuits"
    )

    assert (
        section.streams_value.text()
        == "1 active stream"
    )

    assert (
        section.onion_smtp_value.text()
        == "25"
    )

    assert (
        section.error_value.text()
        == "None"
    )

    section.close()

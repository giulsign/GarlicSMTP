from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.sections import (
    ApplicationSection,
)
from tests.support import (
    make_application_status,
)

from tests.test_gui_main_window import (
    FakeController,
    get_application,
)


def test_application_section_displays_status():
    get_application()

    controller = FakeController()

    controller.current_status = (
        make_application_status()
    )

    view_model = ApplicationViewModel(
        controller
    )

    section = ApplicationSection(
        view_model=view_model
    )

    section.refresh_view()

    assert (
        section.runtime_value.text()
        == "Stopped"
    )

    assert (
        section.hostname_value.text()
        == "garlicsmtp.local"
    )

    assert (
        section.domain_value.text()
        == "test.onion"
    )

    section.close()

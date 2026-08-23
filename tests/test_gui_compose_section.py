from garlicsmtp.application.compose_view_model import (
    ComposeViewModel,
)
from garlicsmtp.gui.sections.compose_section import (
    ComposeSection,
)
from tests.test_gui_main_window import (
    get_application,
)


class FakeComposer:

    def send(
        self,
        *,
        sender,
        recipient,
        subject,
        body,
    ):
        del sender
        del recipient
        del subject
        del body

        return True


def test_compose_section_has_required_fields():
    get_application()

    view_model = ComposeViewModel(
        FakeComposer()
    )

    section = ComposeSection(
        view_model=view_model
    )

    assert hasattr(
        section,
        "sender_input",
    )

    assert hasattr(
        section,
        "recipient_input",
    )

    assert hasattr(
        section,
        "subject_input",
    )

    assert hasattr(
        section,
        "body_input",
    )

    assert hasattr(
        section,
        "send_button",
    )

    assert hasattr(
        section,
        "clear_button",
    )

    assert (
        section.send_button.text()
        == "Send"
    )

    assert (
        section.clear_button.text()
        == "Clear"
    )

    section.close()


def test_compose_section_send_uses_view_model():
    get_application()

    class FakeComposer:

        def __init__(self):
            self.calls = []

        def send(
            self,
            *,
            sender,
            recipient,
            subject,
            body,
        ):
            self.calls.append(
                {
                    "sender": sender,
                    "recipient": recipient,
                    "subject": subject,
                    "body": body,
                }
            )

            return True

    composer = FakeComposer()

    view_model = ComposeViewModel(
        composer
    )

    section = ComposeSection(
        view_model=view_model
    )

    section.sender_input.setText(
        "alice@sender.onion"
    )

    section.recipient_input.setText(
        "bob@receiver.onion"
    )

    section.subject_input.setText(
        "Hello"
    )

    section.body_input.setPlainText(
        "Hello from GarlicSMTP"
    )

    section.send_button.click()

    assert composer.calls == [
        {
            "sender": (
                "alice@sender.onion"
            ),
            "recipient": (
                "bob@receiver.onion"
            ),
            "subject": "Hello",
            "body": (
                "Hello from GarlicSMTP"
            ),
        }
    ]

    section.close()
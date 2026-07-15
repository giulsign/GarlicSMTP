import pytest

from garlicsmtp.models.envelope import Envelope
from garlicsmtp.models.header import MailHeaders
from garlicsmtp.models.metadata import Metadata
from garlicsmtp.models.message import MailMessage


@pytest.fixture
def message():

    return MailMessage(

        envelope=Envelope(

            sender="alice@test.onion",

            recipients=[

                "bob@test.onion"

            ]

        ),

        headers=MailHeaders(),

        metadata=Metadata()

    )

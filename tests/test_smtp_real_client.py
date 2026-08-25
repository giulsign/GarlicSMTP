import smtplib
import threading
import time

from garlicsmtp.core.engine import Bootstrap
from garlicsmtp.core.engine import GarlicSMTPConfig
from garlicsmtp.transport.base import Transport

class SpyTransport(Transport):

    def __init__(self):
        self.delivered = []

    def deliver(self, item):
        self.delivered.append(item)
        return True

def run_app(app):
    app.start()
    app.run()

def test_smtp_real_client_delivers_to_queue(tmp_path):

    config = GarlicSMTPConfig(
        listen_host="127.0.0.1",
        listen_port=2529,
        hostname="garlicsmtp.local",
        mailbox_db=str(
            tmp_path
            / "mailboxes.db"
        ),
    )

    spy = SpyTransport()

    bootstrap = Bootstrap(
        config,
        default_transport=spy,
    )

    app = bootstrap.build()

    thread = threading.Thread(
        target=run_app,
        args=(app,),
    )

    thread.start()

    try:
        time.sleep(0.2)

        with smtplib.SMTP(
            "127.0.0.1",
            2529,
            timeout=5,
        ) as client:
            client.ehlo("client.local")
            client.mail("alice@test.onion")
            client.rcpt("bob@test.onion")
            client.data("Subject: Real Client\r\n\r\nHello")

        deadline = time.monotonic() + 2.0

        while (
            len(spy.delivered) == 0
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        assert len(spy.delivered) == 1

        item = spy.delivered[0]

        assert item.message.envelope.sender == "alice@test.onion"
        assert item.message.envelope.recipients == ["bob@test.onion"]
        assert item.message.headers.get("Subject") == "Real Client"
        assert item.message.body == "Hello"

    finally:
        app.stop()
        thread.join(timeout=2)



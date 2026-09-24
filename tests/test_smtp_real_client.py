# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import smtplib
import threading
import time

from garlicsmtp.core.engine import Bootstrap
from garlicsmtp.core.engine import GarlicSMTPConfig
from garlicsmtp.transport.base import Transport
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
)

class SpyTransport(Transport):

    def __init__(self):
        self.delivered = []
        self.discovered = []
        self.encryption_key_store = None

        self.private_key = (
            X25519PrivateKey.generate()
        )

    def discover_e2ee_capability(
        self,
        hostname,
    ):
        self.discovered.append(
            hostname
        )

        self.encryption_key_store.remember(
            hostname,
            self.private_key
            .public_key()
            .public_bytes_raw(),
        )

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

    spy.encryption_key_store = (
        bootstrap.build_context()
        .encryption_key_store
    )

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
        assert (
            item.message.headers.get(
                "X-GarlicSMTP-Encryption"
            )
            is not None
        )

        assert "Real Client" not in (
            str(item.message.headers.fields)
        )

        assert "Hello" not in item.message.body
        assert spy.discovered == [
            "test.onion"
        ]

    finally:
        app.stop()
        thread.join(timeout=2)



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

def test_smtp_real_client_delivers_to_local_mailbox(tmp_path, dek):

    config = GarlicSMTPConfig(
        listen_host="127.0.0.1",
        listen_port=2529,
        hostname="a" * 56 + ".onion",
        mailbox_db=str(tmp_path / "mailboxes.db"),
    )

    spy = SpyTransport()

    bootstrap = Bootstrap(
        config,
        default_transport=spy,
        dek=dek,
    )

    app = bootstrap.build()

    context = bootstrap.build_context()
    local_host = config.hostname
    sender = f"garlicsmtp@{local_host}"
    recipient = f"garlicsmtp@{local_host}"

    context.address_policy.set_local_hostname(local_host)

    spy.encryption_key_store = context.encryption_key_store

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
            client.set_debuglevel(1)
            client.ehlo("client.local")

            mail_code, mail_reply = client.mail(sender)
            print("MAIL FROM:", mail_code, mail_reply, flush=True)
            assert mail_code == 250, (mail_code, mail_reply)

            rcpt_code, rcpt_reply = client.rcpt(recipient)
            print("RCPT TO:", rcpt_code, rcpt_reply, flush=True)
            assert rcpt_code == 250, (rcpt_code, rcpt_reply)

            client.data("Subject: Real Client\r\n\r\nHello")

        entries = context.store.list_entries(recipient)

        assert len(entries) == 1

        stored = entries[0].message

        assert stored.envelope.sender == sender
        assert stored.envelope.recipients == [recipient]
        assert stored.headers.get("Subject") == "Real Client"
        assert "Hello" in stored.body

        assert spy.delivered == []
        assert spy.discovered == []

    finally:
        app.stop()
        thread.join(timeout=2)



# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import socket
import threading
import time
import pytest

from garlicsmtp.exceptions import (
    TemporaryDeliveryError,
)

from garlicsmtp.core.pipeline import (
    LoggerStage,
    Pipeline,
)
from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.sqlite import SQLiteQueueBackend
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.smtp.server import SMTPServer
from garlicsmtp.transport.onion.transport import OnionTransport
from garlicsmtp.application import (
    ApplicationBuilder,
)
from garlicsmtp.application.mail_composer import (
    MailComposerService,
)
from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
)
from garlicsmtp.security.signing_identity import (
    SigningIdentity,
)
from garlicsmtp.storage.entry import (
    VerificationStatus,
)

class LocalSocksConnection:

    def __init__(
        self,
        host: str,
        port: int,
    ):
        self.socket = socket.create_connection(
            (host, port),
            timeout=5,
        )

    def close(self):
        self.socket.close()


class LocalSocksClient:

    def __init__(
        self,
        host: str,
        port: int,
    ):
        self.host = host
        self.port = port
        self.calls = []

    def connect(
        self,
        onion_host: str,
        onion_port: int,
    ):
        self.calls.append(
            (onion_host, onion_port)
        )

        return LocalSocksConnection(
            self.host,
            self.port,
        )


def test_onion_transport_delivers_to_real_smtp_server(
    tmp_path,
):

    host = "a" * 56 + ".onion"
    port = 2532

    backend = SQLiteQueueBackend(
        tmp_path / "receiver.db"
    )

    queue = QueueManager(
        backend=backend,
    )

    pipeline = Pipeline()
    pipeline.add(LoggerStage())
    pipeline.add(QueueStage(queue))

    server = SMTPServer(
        host="127.0.0.1",
        port=port,
        hostname=host,
        pipeline=pipeline,
    )

    server.start()

    stop_event = threading.Event()

    def run_server():
        while not stop_event.is_set():
            server.tick()
            time.sleep(0.01)

    server_thread = threading.Thread(
        target=run_server,
        daemon=True,
    )

    server_thread.start()

    try:
        socks = LocalSocksClient(
            "127.0.0.1",
            port,
        )

        transport = OnionTransport(
            socks_client=socks,
        )

        message = MailMessage(
            envelope=Envelope(
                sender="alice@sender.onion",
                recipients=[
                    f"bob@{host}"
                ],
            ),
            headers=MailHeaders(
                fields={
                    "Subject": "Local E2E",
                }
            ),
            body="Hello local onion flow",
        )

        item = QueueFactory.create(
            message
        )

        assert transport.deliver(item) is True

        deadline = time.monotonic() + 2.0

        while (
            queue.size() == 0
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        assert queue.size() == 1

        received = queue.peek()

        assert received is not None
        assert received.message is not None

        assert (
            received.message.envelope.sender
            == "alice@sender.onion"
        )

        assert (
            received.message.envelope.recipients
            == [f"bob@{host}"]
        )

        assert (
            received.message.headers.fields.get(
                "Subject"
            )
            == "Local E2E"
        )

        assert (
            received.message.body
            == "Hello local onion flow"
        )

        assert socks.calls == [
            (host, 25)
        ]

    finally:
        stop_event.set()
        server.stop()
        server_thread.join(timeout=2)
        backend.close()


def test_two_application_nodes_exchange_e2ee_message(
    tmp_path,
):
    bob_host = "b" * 56 + ".onion"
    bob_port = 2533

    bob_paths = ApplicationPaths(
        root_dir=tmp_path / "bob"
    )

    bob_settings = ApplicationSettings()
    bob_settings.hostname = bob_host
    bob_settings.local_domain = bob_host
    bob_settings.smtp.host = "127.0.0.1"
    bob_settings.smtp.port = bob_port
    bob_settings.tor.enabled = False

    bob = ApplicationBuilder(
        paths=bob_paths,
        settings=bob_settings,
    ).build()

    bob.smtp_server.start()

    stop_event = threading.Event()

    def run_bob_server():
        while not stop_event.is_set():
            bob.smtp_server.tick()
            time.sleep(0.01)

    server_thread = threading.Thread(
        target=run_bob_server,
        daemon=True,
    )
    server_thread.start()

    try:
        socks = LocalSocksClient(
            "127.0.0.1",
            bob_port,
        )

        alice_transport = OnionTransport(
            socks_client=socks,
        )

        alice_paths = ApplicationPaths(
            root_dir=tmp_path / "alice"
        )

        alice_settings = ApplicationSettings()
        alice_settings.tor.enabled = False

        alice = ApplicationBuilder(
            paths=alice_paths,
            settings=alice_settings,
            default_transport=alice_transport,
        ).build()

        composer = MailComposerService(
            pipeline=alice.pipeline,
            signer=alice.signer,
        )

        sender = (
            f"alice@{alice_settings.local_domain}"
        )
        recipient = f"bob@{bob_host}"

        assert composer.send(
            sender=sender,
            recipient=recipient,
            subject="Node to node E2EE",
            body="Hello from Alice",
        ) is True

        assert alice.queue.size() == 1

        queued = alice.queue.peek()

        assert queued is not None
        assert queued.message is not None

        assert (
            queued.message.headers.get(
                "X-GarlicSMTP-Encryption"
            )
            is not None
        )

        assert (
            "Hello from Alice"
            not in queued.message.body
        )

        assert alice.queue_worker.process() is True

        deadline = time.monotonic() + 2.0

        while (
            bob.store.count(recipient) == 0
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        assert bob.store.count(recipient) == 1

        entries = bob.store.list_entries(
            recipient
        )

        assert len(entries) == 1

        received = bob.store.get(
            recipient,
            entries[0].id,
        )

        assert received is not None

        assert (
            received.envelope.sender
            == sender
        )
        assert (
            received.envelope.recipients
            == [recipient]
        )
        assert (
            received.headers.get("Subject")
            == "Node to node E2EE"
        )
        assert (
            received.body
            == "Hello from Alice"
        )

        assert alice.queue.size() == 0

        assert socks.calls == [
            (bob_host, 25),
            (bob_host, 25),
        ]

    finally:
        stop_event.set()
        bob.smtp_server.stop()
        server_thread.join(timeout=2)

        bob.queue.backend.close()
        bob.store.backend.close()

        if "alice" in locals():
            alice.queue.backend.close()
            alice.store.backend.close()


def test_two_application_nodes_verify_trusted_e2ee_message(
    tmp_path,
):
    bob_host = "b" * 56 + ".onion"
    bob_port = 2533

    bob_paths = ApplicationPaths(
        root_dir=tmp_path / "bob"
    )

    bob_settings = ApplicationSettings()
    bob_settings.hostname = bob_host
    bob_settings.local_domain = bob_host
    bob_settings.smtp.host = "127.0.0.1"
    bob_settings.smtp.port = bob_port
    bob_settings.tor.enabled = False

    bob = ApplicationBuilder(
        paths=bob_paths,
        settings=bob_settings,
    ).build()

    bob.smtp_server.start()

    stop_event = threading.Event()

    def run_bob_server():
        while not stop_event.is_set():
            bob.smtp_server.tick()
            time.sleep(0.01)

    server_thread = threading.Thread(
        target=run_bob_server,
        daemon=True,
    )
    server_thread.start()

    try:
        socks = LocalSocksClient(
            "127.0.0.1",
            bob_port,
        )

        alice_transport = OnionTransport(
            socks_client=socks,
        )

        alice_paths = ApplicationPaths(
            root_dir=tmp_path / "alice"
        )

        alice_settings = ApplicationSettings()
        alice_settings.tor.enabled = False

        alice = ApplicationBuilder(
            paths=alice_paths,
            settings=alice_settings,
            default_transport=alice_transport,
        ).build()

        sender = (
            f"alice@{alice_settings.local_domain}"
        )
        recipient = f"bob@{bob_host}"

        # Bob trusts the actual persistent Ed25519
        # signing identity used by Alice's builder.
        alice_signing_identity = SigningIdentity(
            alice_paths.root_dir / "signing.key"
        )

        bob.smtp_server.verifier.trust_store.trust(
            sender,
            alice_signing_identity.private_key
            .public_key()
            .public_bytes_raw(),
        )

        composer = MailComposerService(
            pipeline=alice.pipeline,
            signer=alice.signer,
        )

        assert composer.send(
            sender=sender,
            recipient=recipient,
            subject="Node to node trusted E2EE",
            body="Hello securely from Alice",
        ) is True

        # Alice must queue ciphertext, not plaintext.
        assert alice.queue.size() == 1

        queued = alice.queue.peek()

        assert queued is not None
        assert queued.message is not None

        assert (
            queued.message.headers.get(
                "X-GarlicSMTP-Encryption"
            )
            is not None
        )

        assert (
            "Hello securely from Alice"
            not in queued.message.body
        )

        # Real QueueWorker -> OnionTransport ->
        # SMTPClient -> Bob SMTPServer.
        assert alice.queue_worker.process() is True

        deadline = time.monotonic() + 2.0

        while (
            bob.store.count(recipient) == 0
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        assert bob.store.count(recipient) == 1

        entries = bob.store.list_entries(
            recipient
        )

        assert len(entries) == 1

        # Bob decrypted first and then verified
        # Alice's Ed25519 signature using his trust store.
        assert (
            entries[0].verification_status
            == VerificationStatus.VERIFIED
        )

        received = bob.store.get(
            recipient,
            entries[0].id,
        )

        assert received is not None

        assert (
            received.envelope.sender
            == sender
        )

        assert (
            received.envelope.recipients
            == [recipient]
        )

        assert (
            received.headers.get("Subject")
            == "Node to node trusted E2EE"
        )

        assert (
            received.body
            == "Hello securely from Alice"
        )

        assert alice.queue.size() == 0

        # First connection: E2EE discovery/pinning.
        # Second connection: actual SMTP delivery.
        assert socks.calls == [
            (bob_host, 25),
            (bob_host, 25),
        ]

    finally:
        stop_event.set()
        bob.smtp_server.stop()
        server_thread.join(timeout=2)

        bob.queue.backend.close()
        bob.store.backend.close()

        if "alice" in locals():
            alice.queue.backend.close()
            alice.store.backend.close()


def test_two_application_nodes_reject_changed_e2ee_key(
    tmp_path,
):
    bob_host = "b" * 56 + ".onion"
    first_bob_port = 2533
    second_bob_port = 2534

    bob_paths = ApplicationPaths(
        root_dir=tmp_path / "bob"
    )

    bob_settings = ApplicationSettings()
    bob_settings.hostname = bob_host
    bob_settings.local_domain = bob_host
    bob_settings.smtp.host = "127.0.0.1"
    bob_settings.smtp.port = first_bob_port
    bob_settings.tor.enabled = False

    bob = ApplicationBuilder(
        paths=bob_paths,
        settings=bob_settings,
    ).build()

    bob.smtp_server.start()

    first_stop_event = threading.Event()

    def run_first_bob_server():
        while not first_stop_event.is_set():
            bob.smtp_server.tick()
            time.sleep(0.01)

    first_server_thread = threading.Thread(
        target=run_first_bob_server,
        daemon=True,
    )
    first_server_thread.start()

    alice = None
    second_bob = None
    second_stop_event = None
    second_server_thread = None

    try:
        socks = LocalSocksClient(
            "127.0.0.1",
            first_bob_port,
        )

        alice_transport = OnionTransport(
            socks_client=socks,
        )

        alice_paths = ApplicationPaths(
            root_dir=tmp_path / "alice"
        )

        alice_settings = ApplicationSettings()
        alice_settings.tor.enabled = False

        alice = ApplicationBuilder(
            paths=alice_paths,
            settings=alice_settings,
            default_transport=alice_transport,
        ).build()

        composer = MailComposerService(
            pipeline=alice.pipeline,
            signer=alice.signer,
        )

        sender = (
            f"alice@{alice_settings.local_domain}"
        )
        recipient = f"bob@{bob_host}"

        #
        # First contact.
        #
        # Alice discovers Bob's original X25519 key,
        # pins it, encrypts the message and delivers it.
        #
        assert composer.send(
            sender=sender,
            recipient=recipient,
            subject="Before key change",
            body="FIRST MESSAGE",
        ) is True

        assert alice.queue.size() == 1

        assert alice.queue_worker.process() is True

        deadline = time.monotonic() + 2.0

        while (
            bob.store.count(recipient) == 0
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        assert bob.store.count(recipient) == 1
        assert alice.queue.size() == 0

        pinned_key = (
            alice.encryption_key_store.get(
                bob_host
            )
        )

        assert pinned_key is not None

        #
        # Shut down the original Bob node.
        #
        first_stop_event.set()
        bob.smtp_server.stop()
        first_server_thread.join(timeout=2)

        bob.queue.backend.close()
        bob.store.backend.close()

        #
        # Simulate loss/rotation/replacement of Bob's
        # persistent E2EE identity.
        #
        # The same onion hostname will now advertise
        # a different X25519 public key.
        #
        encryption_key_path = (
            bob_paths.root_dir / "encryption.key"
        )

        encryption_key_path.unlink()

        bob_settings.smtp.port = second_bob_port

        second_bob = ApplicationBuilder(
            paths=bob_paths,
            settings=bob_settings,
        ).build()

        new_bob_key = (
            second_bob.smtp_server
            .encryption_private_key
            .public_key()
            .public_bytes_raw()
        )

        assert new_bob_key != pinned_key

        second_bob.smtp_server.start()

        second_stop_event = threading.Event()

        def run_second_bob_server():
            while not second_stop_event.is_set():
                second_bob.smtp_server.tick()
                time.sleep(0.01)

        second_server_thread = threading.Thread(
            target=run_second_bob_server,
            daemon=True,
        )
        second_server_thread.start()

        #
        # Local test harness now routes the same onion
        # hostname to Bob's replacement SMTP server.
        #
        socks.port = second_bob_port

        #
        # Alice still has Bob's original key pinned.
        #
        # Because the key is already known, this message
        # is encrypted and queued with the old pinned key.
        #
        assert composer.send(
            sender=sender,
            recipient=recipient,
            subject="After key change",
            body="SECOND MESSAGE MUST NOT ARRIVE",
        ) is True

        assert alice.queue.size() == 1

        queued = alice.queue.peek()

        assert queued is not None
        assert queued.message is not None

        assert (
            queued.message.headers.get(
                "X-GarlicSMTP-Encryption"
            )
            is not None
        )

        assert (
            "SECOND MESSAGE MUST NOT ARRIVE"
            not in queued.message.body
        )

        #
        # During actual SMTP delivery Bob advertises
        # the new key. Alice must reject the key change
        # as a temporary delivery failure.
        #
        with pytest.raises(
            TemporaryDeliveryError
        ):
            alice.queue_worker.process()

        #
        # Temporary failure: message remains queued.
        #
        assert alice.queue.size() == 1

        #
        # Bob must not have received the second message.
        # The existing mailbox still contains only the
        # first successfully delivered message.
        #
        assert (
            second_bob.store.count(recipient)
            == 1
        )

        entries = second_bob.store.list_entries(
            recipient
        )

        assert len(entries) == 1

        received = second_bob.store.get(
            recipient,
            entries[0].id,
        )

        assert received is not None
        assert received.body == "FIRST MESSAGE"

        #
        # The pinned key must not be silently replaced.
        #
        assert (
            alice.encryption_key_store.get(
                bob_host
            )
            == pinned_key
        )

    finally:
        if (
            second_stop_event is not None
            and second_bob is not None
        ):
            second_stop_event.set()
            second_bob.smtp_server.stop()

        if second_server_thread is not None:
            second_server_thread.join(timeout=2)

        if second_bob is not None:
            second_bob.queue.backend.close()
            second_bob.store.backend.close()

        if first_server_thread.is_alive():
            first_stop_event.set()
            bob.smtp_server.stop()
            first_server_thread.join(timeout=2)

            bob.queue.backend.close()
            bob.store.backend.close()

        if alice is not None:
            alice.queue.backend.close()
            alice.store.backend.close()
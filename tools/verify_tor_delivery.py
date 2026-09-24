import argparse
import sys
import time

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
    Metadata,
)
from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.queue.sqlite import SQLiteQueueBackend
from garlicsmtp.transport.onion.transport import OnionTransport
from garlicsmtp.storage.sqlite import SQLiteMessageStoreBackend


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Send one GarlicSMTP message over Tor "
            "and verify it in the receiver SQLite queue."
        )
    )

    parser.add_argument(
        "--sender-onion",
        required=True,
    )

    parser.add_argument(
        "--receiver-onion",
        required=True,
    )

    parser.add_argument(
        "--receiver-db",
        default="receiver-mailboxes.db",
    )

    parser.add_argument(
        "--subject",
        default="GarlicSMTP Tor verification",
    )

    parser.add_argument(
        "--body",
        default="GarlicSMTP end-to-end verification.",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    sender = f"alice@{args.sender_onion}"
    recipient = f"bob@{args.receiver_onion}"

    backend = SQLiteQueueBackend(
        args.receiver_db
    )

    try:
        before = backend.size()
    finally:
        backend.close()

    message = MailMessage(
        envelope=Envelope(
            sender=sender,
            recipients=[recipient],
        ),
        headers=MailHeaders(
            fields={
                "Subject": args.subject,
            }
        ),
        metadata=Metadata(),
        body=args.body,
    )

    item = QueueFactory.create(
        message
    )

    transport = OnionTransport(
        hostname=args.sender_onion,
    )

    if not transport.deliver(item):
        print(
            "Delivery was not accepted.",
            file=sys.stderr,
        )
        return 1

    deadline = time.monotonic() + args.timeout

    while time.monotonic() < deadline:
        backend = SQLiteQueueBackend(
            args.receiver_db
        )

        try:
            if backend.size() > before:
                received = backend.peek()

                if (
                    received is not None
                    and received.message is not None
                    and received.message.envelope.sender == sender
                    and received.message.envelope.recipients == [recipient]
                    and received.message.headers.fields.get("Subject")
                    == args.subject
                    and received.message.body == args.body
                ):
                    print(
                        "Tor delivery verified"
                    )
                    return 0
        finally:
            backend.close()

        time.sleep(0.1)

    print(
        "Message was accepted but not verified "
        "in the receiver queue.",
        file=sys.stderr,
    )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
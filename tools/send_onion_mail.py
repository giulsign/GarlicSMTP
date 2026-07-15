import argparse

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
    Metadata,
)
from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.transport.onion.transport import OnionTransport


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Send one message through "
            "GarlicSMTP OnionTransport."
        )
    )

    parser.add_argument(
        "--from-address",
        required=True,
    )

    parser.add_argument(
        "--to-address",
        required=True,
    )

    parser.add_argument(
        "--subject",
        default="GarlicSMTP Tor test",
    )

    parser.add_argument(
        "--body",
        default="First GarlicSMTP mail over Tor.",
    )

    parser.add_argument(
        "--hostname",
        required=True,
        help="EHLO hostname of the sender.",
    )

    parser.add_argument(
        "--socks-host",
        default="127.0.0.1",
    )

    parser.add_argument(
        "--socks-port",
        type=int,
        default=9050,
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    message = MailMessage(
        envelope=Envelope(
            sender=args.from_address,
            recipients=[
                args.to_address
            ],
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
        socks_host=args.socks_host,
        socks_port=args.socks_port,
        hostname=args.hostname,
    )

    delivered = transport.deliver(
        item
    )

    print(
        "Delivery accepted"
        if delivered
        else "Delivery failed"
    )

    return 0 if delivered else 1


if __name__ == "__main__":
    raise SystemExit(main())
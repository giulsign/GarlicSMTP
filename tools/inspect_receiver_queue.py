import argparse
import sys

from garlicsmtp.queue.sqlite import SQLiteQueueBackend


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the first message stored "
            "in a GarlicSMTP SQLite queue."
        )
    )

    parser.add_argument(
        "--queue-db",
        default="receiver-queue.db",
        help="Path to a legacy receiver queue database. "
            "Default: receiver-queue.db",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    backend = SQLiteQueueBackend(
        args.queue_db
    )

    try:
        count = backend.size()

        print(f"Messages: {count}")

        if count == 0:
            print(
                "No messages found.",
                file=sys.stderr,
            )
            return 1

        item = backend.peek()

        if item is None or item.message is None:
            print(
                "Invalid queue item.",
                file=sys.stderr,
            )
            return 1

        message = item.message

        print(f"Queue ID: {item.id}")
        print(
            f"Created: {item.created.isoformat()}"
        )
        print(
            f"From: {message.envelope.sender}"
        )
        print(
            "To: "
            + ", ".join(
                message.envelope.recipients
            )
        )

        print("Headers:")

        for name, value in message.headers.fields.items():
            print(f"  {name}: {value}")

        print("Body:")
        print(message.body)

        return 0

    finally:
        backend.close()


if __name__ == "__main__":
    raise SystemExit(main())

import argparse

from garlicsmtp.cli.mailbox import (
    list_mailboxes,
    list_messages,
    show_message,
)
from garlicsmtp.core.engine import Bootstrap
from garlicsmtp.version import print_version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="garlicsmtp",
        description="SMTP transport over Onion Services.",
    )

    parser.add_argument(
        "--mailbox-db",
        default="mailboxes.db",
        help=(
            "Path to the mailbox SQLite database. "
            "Default: mailboxes.db"
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
    )

    mailbox_parser = subparsers.add_parser(
        "mailbox",
        help="Inspect stored mailboxes.",
    )

    mailbox_subparsers = mailbox_parser.add_subparsers(
        dest="mailbox_command",
        required=True,
    )

    mailbox_subparsers.add_parser(
        "list",
        help="List all mailboxes.",
    )

    messages_parser = mailbox_subparsers.add_parser(
        "messages",
        help="List messages in a mailbox.",
    )

    messages_parser.add_argument(
        "mailbox",
        help="Full mailbox address.",
    )

    show_parser = mailbox_subparsers.add_parser(
        "show",
        help="Show one message.",
    )

    show_parser.add_argument(
        "mailbox",
        help="Full mailbox address.",
    )

    show_parser.add_argument(
        "message",
        help="Message position or full message ID.",
    )

    return parser


def run_server() -> int:
    print_version()

    print()
    print("GarlicSMTP starting...")

    app = Bootstrap().build()

    app.start()
    app.run()

    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        return run_server()

    if args.command == "mailbox":
        if args.mailbox_command == "list":
            return list_mailboxes(
                args.mailbox_db
            )

        if args.mailbox_command == "messages":
            return list_messages(
                args.mailbox_db,
                args.mailbox,
            )

        if args.mailbox_command == "show":
            return show_message(
                args.mailbox_db,
                args.mailbox,
                args.message,
            )

    parser.error("Unsupported command")
    return 2
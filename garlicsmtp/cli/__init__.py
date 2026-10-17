# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.


import argparse
import getpass

from garlicsmtp.cli.mailbox import (
    list_mailboxes,
    list_messages,
    show_message,
    update_flags,
)
from garlicsmtp.core.engine import Bootstrap
from garlicsmtp.version import print_version
from garlicsmtp.configuration.paths import ApplicationPaths
from garlicsmtp.security.auth.account_credentials import (
    AccountCredentialStore,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="garlicsmtp",
        description="SMTP transport over Onion Services.",
    )

    parser.add_argument(
        "--mailbox-db",
        default=None,
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

    flags_parser = mailbox_subparsers.add_parser(
        "flags",
        help="Add or remove flags from a message.",
    )

    flags_parser.add_argument(
        "mailbox",
        help="Full mailbox address.",
    )

    flags_parser.add_argument(
        "message",
        help="Message UID or full message ID.",
    )

    flags_parser.add_argument(
        "operation",
        choices=[
            "add",
            "remove",
            "set",
        ],
    )

    flags_parser.add_argument(
        "flags",
        nargs="+",
        help=r"Flags such as \Seen or \Flagged.",
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

def unlock_cli_dek(paths: ApplicationPaths) -> bytes | None:
    credentials_file = paths.account_credentials_file

    if not credentials_file.exists():
        print("Account credentials not found.")
        return None

    store = AccountCredentialStore(path=credentials_file)

    try:
        username = input("Username: ")
        password = getpass.getpass("Password: ")

        return store.unlock_dek_with_password(
            username=username,
            password=password,
        )
    except (ValueError, PermissionError, OSError, EOFError):
        print("Unable to unlock account.")
        return None

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        return run_server()

    if args.command == "mailbox":
        paths = ApplicationPaths.for_user()

        database_path = (
            args.mailbox_db
            if args.mailbox_db is not None
            else str(paths.mailbox_database)
        )

        if database_path != str(paths.mailbox_database):
            print("Custom mailbox database paths are not yet supported.")
            return 2

        dek = unlock_cli_dek(paths)
        if dek is None:
            return 1
        if args.mailbox_command == "list":
            return list_mailboxes(
                database_path,
                dek=dek,
            )

        if args.mailbox_command == "messages":
            return list_messages(
                database_path,
                args.mailbox,
                dek=dek,
            )

        if args.mailbox_command == "show":
            return show_message(
                database_path,
                args.mailbox,
                args.message,
                dek=dek,
            )
        
        if args.mailbox_command == "flags":
            return update_flags(
                database_path=database_path,
                mailbox=args.mailbox,
                message_reference=args.message,
                operation=args.operation,
                flags=set(args.flags),
                dek=dek,
            )

    parser.error("Unsupported command")
    return 2
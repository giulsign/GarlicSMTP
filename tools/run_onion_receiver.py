import argparse

from garlicsmtp.core.engine import (
    Bootstrap,
    GarlicSMTPConfig,
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Run a GarlicSMTP receiving node "
            "without an outbound worker."
        )
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=2526,
    )

    parser.add_argument(
        "--hostname",
        required=True,
    )

    parser.add_argument(
        "--mailbox-db",
        default="receiver-mailboxes.db",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    config = GarlicSMTPConfig(
        listen_host=args.host,
        listen_port=args.port,
        hostname=args.hostname,
        mailbox_db=args.mailbox_db,
    )

    bootstrap = Bootstrap(
        config=config,
    )

    server = bootstrap.build_server()
    runtime = bootstrap.build_runtime()

    # Il receiver deve solo ricevere e salvare
    # messaggi locali. Non avviamo il QueueWorker.
    runtime.services = [
        server,
    ]

    runtime.tasks = [
        server,
    ]

    try:
        runtime.start()
        runtime.run()
    finally:
        runtime.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
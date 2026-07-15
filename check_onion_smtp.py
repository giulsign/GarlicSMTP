import argparse
import sys

from garlicsmtp.network.socks5 import (
    Socks5Client,
    Socks5Connection,
)
from garlicsmtp.network.socks5.exceptions import (
    Socks5ConnectionError,
    Socks5HandshakeError,
)
from garlicsmtp.transport.smtp.connection import SMTPConnection
from garlicsmtp.transport.smtp.exceptions import SMTPClientError
from garlicsmtp.transport.smtp.protocol import SMTPClientProtocol


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Check whether an SMTP server is reachable "
            "through a Tor SOCKS5 proxy."
        )
    )

    parser.add_argument(
        "host",
        help="Destination v3 onion hostname.",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=25,
        help="Destination SMTP port. Default: 25.",
    )

    parser.add_argument(
        "--socks-host",
        default="127.0.0.1",
        help="Tor SOCKS5 host. Default: 127.0.0.1.",
    )

    parser.add_argument(
        "--socks-port",
        type=int,
        default=9050,
        help="Tor SOCKS5 port. Default: 9050.",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Connection timeout in seconds. Default: 30.",
    )

    return parser.parse_args()


def check_onion_smtp(
    host: str,
    port: int,
    socks_host: str,
    socks_port: int,
    timeout: float,
) -> int:
    socks_connection = Socks5Connection(
        proxy_host=socks_host,
        proxy_port=socks_port,
        timeout=timeout,
    )

    socks_client = Socks5Client(
        connection=socks_connection,
    )

    try:
        print(
            f"Connecting to Tor SOCKS5 proxy "
            f"{socks_host}:{socks_port}..."
        )

        connection = socks_client.connect(
            host,
            port,
        )

        print(
            f"SOCKS5 tunnel established to "
            f"{host}:{port}"
        )

        smtp_connection = SMTPConnection(
            timeout=timeout,
            connected_socket=connection.socket,
        )

        protocol = SMTPClientProtocol(
            smtp_connection,
        )

        greeting = protocol.greeting()

        print(
            f"SMTP banner: "
            f"{greeting.code} {greeting.message}"
        )

        return 0

    except (
        Socks5ConnectionError,
        Socks5HandshakeError,
        SMTPClientError,
        OSError,
        TimeoutError,
    ) as exc:
        print(
            f"Connection failed: {exc}",
            file=sys.stderr,
        )

        return 1

    finally:
        socks_connection.close()


def main() -> int:
    args = parse_arguments()

    return check_onion_smtp(
        host=args.host,
        port=args.port,
        socks_host=args.socks_host,
        socks_port=args.socks_port,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    raise SystemExit(main())
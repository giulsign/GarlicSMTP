from dataclasses import dataclass


@dataclass(slots=True)
class GarlicSMTPConfig:
    hostname: str = "garlicsmtp.local"
    listen_host: str = "127.0.0.1"
    listen_port: int = 2525
    socks_host: str = "127.0.0.1"
    socks_port: int = 9050
    queue_directory: str = "./queue"
    mailbox_db: str = "mailboxes.db"
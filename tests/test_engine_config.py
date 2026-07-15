from garlicsmtp.core.engine import GarlicSMTPConfig


def test_engine_config_defaults():

    config = GarlicSMTPConfig()

    assert config.hostname == "garlicsmtp.local"
    assert config.listen_host == "127.0.0.1"
    assert config.listen_port == 2525
    assert config.socks_host == "127.0.0.1"
    assert config.socks_port == 9050
    assert config.mailbox_db == "mailboxes.db"


def test_engine_config_custom_values():

    config = GarlicSMTPConfig(
        hostname="mail.test.onion",
        listen_host="0.0.0.0",
        listen_port=2526,
        socks_host="127.0.0.1",
        socks_port=9150,
    )

    assert config.hostname == "mail.test.onion"
    assert config.listen_host == "0.0.0.0"
    assert config.listen_port == 2526
    assert config.socks_port == 9150


def test_config_accepts_custom_mailbox_db():

    config = GarlicSMTPConfig(
        mailbox_db="custom-mailboxes.db",
    )

    assert (
        config.mailbox_db
        == "custom-mailboxes.db"
    )
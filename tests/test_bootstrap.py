from garlicsmtp.core.engine import Bootstrap, GarlicSMTP
from garlicsmtp.core.engine import GarlicSMTPConfig



def test_bootstrap_builds_application():

    app = Bootstrap().build()

    assert isinstance(app, GarlicSMTP)
    assert app.runtime is not None

def test_bootstrap_uses_configuration():

    config = GarlicSMTPConfig(
        hostname="mail.example.onion",
        listen_host="0.0.0.0",
        listen_port=10025,
    )

    bootstrap = Bootstrap(config)

    server = bootstrap.build_server()


def test_bootstrap_uses_socks_configuration():

    config = GarlicSMTPConfig(
        socks_host="127.0.0.2",
        socks_port=9150,
    )

    bootstrap = Bootstrap(config)

    onion = bootstrap.build_onion_transport()

    assert onion.socks_client.connection.proxy_host == "127.0.0.2"
    assert onion.socks_client.connection.proxy_port == 9150
from garlicsmtp.network.socks5.request import (
    Socks5ConnectRequest,
)


def test_connect_request():

    req = Socks5ConnectRequest(
        host="example.onion",
        port=25,
    )

    data = req.serialize()

    assert data.startswith(
        b"\x05\x01\x00\x03"
    )

    assert data.endswith(
        b"\x00\x19"
    )  # porta 25
import pytest

from garlicsmtp.network.socks5.exceptions import Socks5HandshakeError
from garlicsmtp.network.socks5.reply import Socks5Reply


def test_socks5_reply_success():

    reply = Socks5Reply.parse(
        b"\x05\x00\x00\x03"
    )

    assert reply.version == 5
    assert reply.status == 0
    assert reply.address_type == 3
    assert reply.success is True
    assert reply.message == "succeeded"


def test_socks5_reply_failure():

    reply = Socks5Reply.parse(
        b"\x05\x05\x00\x03"
    )

    assert reply.success is False
    assert reply.message == "connection refused"


def test_socks5_reply_invalid():

    with pytest.raises(Socks5HandshakeError):
        Socks5Reply.parse(b"\x05")
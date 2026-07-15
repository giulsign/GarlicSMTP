from garlicsmtp.network.server import TCPServer


def test_tcp_server_start_stop():
    server = TCPServer(host="127.0.0.1", port=0)

    server.start()

    assert server.socket is not None

    server.stop()

    assert server.socket is None


def test_tcp_server_accept_once_without_connection():

    server = TCPServer(host="127.0.0.1", port=0)

    server.start()

    try:
        assert server.accept_once() is None
    finally:
        server.stop()
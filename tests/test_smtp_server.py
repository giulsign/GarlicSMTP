from garlicsmtp.smtp.server import SMTPServer
import threading


def test_smtp_server_start_stop():

    server = SMTPServer(host="127.0.0.1", port=0)

    server.start()

    assert server.running is True
    assert server.server.socket is not None

    server.stop()

    assert server.running is False
    assert server.server.socket is None


def test_smtp_server_tick_without_connection():

    server = SMTPServer(host="127.0.0.1", port=0)

    server.start()

    try:
        server.tick()
        assert server.running is True
    finally:
        server.stop()


class SpyLogger:

    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)

    def warning(self, message):
        self.messages.append(message)

    def error(self, message):
        self.messages.append(message)


def test_smtp_server_uses_logger():

    logger = SpyLogger()

    server = SMTPServer(
        host="127.0.0.1",
        port=2530,
        logger=logger,
    )

    server.start()

    try:
        assert "SMTP Server listening on 127.0.0.1:2530" in logger.messages
    finally:
        server.stop()


def test_smtp_server_handles_connection_in_thread():

    entered = threading.Event()
    release = threading.Event()

    class FakeClient:

        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class FakeTCPServer:

        def __init__(self):
            self.client = FakeClient()
            self.accepted = False

        def accept_once(self):
            if self.accepted:
                return None

            self.accepted = True

            return (
                self.client,
                ("127.0.0.1", 10000),
            )

        def stop(self):
            pass

    server = SMTPServer(
        host="127.0.0.1",
        port=2531,
    )

    server.server = FakeTCPServer()
    server.running = True

    def fake_handle_connection(
        client,
        address,
    ):
        entered.set()
        release.wait(timeout=2)

    server.handle_connection = (
        fake_handle_connection
    )

    server.tick()

    assert entered.wait(timeout=1)
    assert server.active_connections == 1

    # Il tick deve essere già terminato,
    # mentre la connessione continua nel thread.
    assert server.running is True

    release.set()

    for _ in range(100):
        if server.active_connections == 0:
            break

        threading.Event().wait(0.01)

    assert server.active_connections == 0
    assert server.server.client.closed is True
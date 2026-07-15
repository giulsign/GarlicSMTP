from garlicsmtp.core.engine import GarlicSMTP
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.transport.dummy import DummyTransport
from garlicsmtp.transport.manager import TransportManager
from garlicsmtp.core.engine import GarlicSMTP


class FakeRuntime:

    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


def test_engine_start_stop():

    runtime = FakeRuntime()

    app = GarlicSMTP(runtime)

    app.start()
    assert runtime.started is True

    app.stop()
    assert runtime.stopped is True
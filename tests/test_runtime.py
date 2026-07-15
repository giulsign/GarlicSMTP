from garlicsmtp.core.engine import Runtime
from garlicsmtp.core.engine import RuntimeState


class FakeService:

    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


def test_runtime_start_stop():

    server = FakeService()
    worker = FakeService()

    runtime = Runtime(
        services=[
            server,
            worker,
        ]
    )

    runtime.start()

    assert server.started is True
    assert worker.started is True
    assert runtime.state is RuntimeState.RUNNING

    runtime.stop()

    assert worker.stopped is True
    assert server.stopped is True
    assert runtime.state is RuntimeState.STOPPED

class BrokenService:

    def start(self):
        raise RuntimeError()

    def stop(self):
        pass


def test_runtime_rolls_back_on_failure():

    started = []

    class GoodService:

        def start(self):
            started.append(True)

        def stop(self):
            started.clear()

    runtime = Runtime(
        services=[
            GoodService(),
            BrokenService(),
        ]
    )

    import pytest

    with pytest.raises(RuntimeError):
        runtime.start()

    assert started == []


def test_runtime_runs_tasks_once(monkeypatch):

    class FakeTask:

        def __init__(self):
            self.count = 0

        def tick(self):
            self.count += 1

    task = FakeTask()

    runtime = Runtime(
        tasks=[task],
    )

    runtime.state = RuntimeState.RUNNING

    def fake_sleep(seconds):
        runtime.state = RuntimeState.STOPPED

    monkeypatch.setattr(
        "time.sleep",
        fake_sleep,
    )

    runtime.run()

    assert task.count == 1


class SpyLogger:

    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(message)

    def warning(self, message):
        self.messages.append(message)

    def error(self, message):
        self.messages.append(message)


def test_runtime_uses_logger():

    logger = SpyLogger()

    runtime = Runtime(
        logger=logger,
    )

    runtime.start()
    runtime.stop()

    assert "Runtime starting..." in logger.messages
    assert "Runtime ready" in logger.messages
    assert "Runtime stopping..." in logger.messages
    assert "Runtime stopped" in logger.messages


def test_runtime_runs_multiple_tasks_once(monkeypatch):

    class FakeTask:

        def __init__(self):
            self.count = 0

        def tick(self):
            self.count += 1

    first = FakeTask()
    second = FakeTask()

    runtime = Runtime(
        tasks=[
            first,
            second,
        ],
    )

    runtime.state = RuntimeState.RUNNING

    def fake_sleep(seconds):
        runtime.state = RuntimeState.STOPPED

    monkeypatch.setattr(
        "time.sleep",
        fake_sleep,
    )

    runtime.run()

    assert first.count == 1
    assert second.count == 1
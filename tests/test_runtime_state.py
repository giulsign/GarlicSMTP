from garlicsmtp.core.engine import RuntimeState


def test_runtime_state_values():

    assert RuntimeState.STOPPED.name == "STOPPED"
    assert RuntimeState.STARTING.name == "STARTING"
    assert RuntimeState.RUNNING.name == "RUNNING"
    assert RuntimeState.STOPPING.name == "STOPPING"
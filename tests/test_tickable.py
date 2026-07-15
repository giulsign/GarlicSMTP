from garlicsmtp.core.tickable import Tickable


def test_tickable_interface():

    assert hasattr(Tickable, "tick")
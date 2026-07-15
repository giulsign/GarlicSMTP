from garlicsmtp.core.service import Service


def test_service_interface():

    assert hasattr(Service, "start")
    assert hasattr(Service, "stop")
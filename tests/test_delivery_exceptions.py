from garlicsmtp.exceptions import (
    DeliveryError,
    GarlicSMTPError,
    PermanentDeliveryError,
    TemporaryDeliveryError,
)


def test_delivery_exception_hierarchy():

    assert issubclass(DeliveryError, GarlicSMTPError)
    assert issubclass(TemporaryDeliveryError, DeliveryError)
    assert issubclass(PermanentDeliveryError, DeliveryError)
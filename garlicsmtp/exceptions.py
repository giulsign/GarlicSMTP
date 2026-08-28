# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

"""
GarlicSMTP Exceptions
"""
class GarlicSMTPError(Exception):
    """Base exception for GarlicSMTP."""

class ConfigurationError(GarlicSMTPError):
    pass


class SMTPError(GarlicSMTPError):
    pass


class SMTPProtocolError(SMTPError):
    pass


class SMTPAuthenticationError(SMTPError):
    pass


class TransportError(GarlicSMTPError):
    pass


class OnionTransportError(TransportError):
    pass


class QueueError(GarlicSMTPError):
    pass


class RetryError(GarlicSMTPError):
    pass





class DeliveryError(GarlicSMTPError):
    """Base delivery exception."""


class TemporaryDeliveryError(DeliveryError):
    """Temporary delivery failure. Message can be retried."""


class PermanentDeliveryError(DeliveryError):
    """Permanent delivery failure. Message should not be retried."""
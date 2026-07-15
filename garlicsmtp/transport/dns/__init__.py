from garlicsmtp.transport.dns.records import MXRecord
from garlicsmtp.transport.dns.resolver import DNSResolver
from garlicsmtp.transport.dns.exceptions import DNSLookupError

__all__ = [
    "DNSResolver",
    "MXRecord",
    "DNSLookupError",
]
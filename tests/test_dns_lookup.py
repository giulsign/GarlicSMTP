from garlicsmtp.transport.dns import DNSResolver


class FakeAnswer:

    def __init__(self, preference, exchange):
        self.preference = preference
        self.exchange = exchange


def test_lookup_mx(monkeypatch):

    def fake_resolve(domain, record_type):

        assert domain == "example.com"
        assert record_type == "MX"

        return [
            FakeAnswer(20, "mx2.example.com."),
            FakeAnswer(10, "mx1.example.com."),
        ]

    import dns.resolver

    monkeypatch.setattr(
        dns.resolver,
        "resolve",
        fake_resolve,
    )

    resolver = DNSResolver()

    records = resolver.lookup_mx("example.com")

    assert len(records) == 2

    assert records[0].priority == 10
    assert records[0].exchange == "mx1.example.com"

    assert records[1].priority == 20
    assert records[1].exchange == "mx2.example.com"

import pytest
import dns.resolver

from garlicsmtp.transport.dns import (
    DNSLookupError,
    DNSResolver,
)


def test_lookup_mx_failure(monkeypatch):

    def fake_resolve(domain, record_type):
        raise dns.resolver.NXDOMAIN

    monkeypatch.setattr(
        dns.resolver,
        "resolve",
        fake_resolve,
    )

    resolver = DNSResolver()

    with pytest.raises(DNSLookupError):
        resolver.lookup_mx("missing.example")
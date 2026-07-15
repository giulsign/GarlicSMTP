from garlicsmtp.transport.dns.records import MXRecord


def test_mx_record():
    record = MXRecord(
        priority=10,
        exchange="mail.example.com",
    )

    assert record.priority == 10
    assert record.exchange == "mail.example.com"
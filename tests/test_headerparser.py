from garlicsmtp.smtp.headerparser import HeaderParser


def test_header_parser():
    headers = HeaderParser.parse([
        "Subject: GarlicSMTP",
        "From: alice@test.onion",
        "To: bob@test.onion",
    ])

    assert headers["Subject"] == "GarlicSMTP"
    assert headers["From"] == "alice@test.onion"
    assert headers["To"] == "bob@test.onion"
import pytest

from garlicsmtp.tor.control import (
    TorControlProtocolError,
    TorReplyParser,
    TorReplySeparator,
)


def line_reader(
    *lines: str,
):
    remaining = list(
        lines
    )

    def receive_line():
        if not remaining:
            return None

        return remaining.pop(0)

    return receive_line



def test_parser_reads_simple_reply():
    reply = TorReplyParser().parse(
        line_reader(
            "250 OK"
        )
    )

    assert reply.status == 250
    assert reply.successful is True
    assert reply.asynchronous is False
    assert reply.message == "OK"

    assert len(reply.lines) == 1
    assert reply.final_line.is_final is True

    assert (
        reply.final_line.separator
        is TorReplySeparator.FINAL
    )


def test_parser_reads_multiline_reply():
    reply = TorReplyParser().parse(
        line_reader(
            "250-PROTOCOLINFO 1",
            (
                '250-AUTH METHODS=SAFECOOKIE '
                'COOKIEFILE="/run/tor/'
                'control.authcookie"'
            ),
            '250-VERSION Tor="0.4.8.12"',
            "250 OK",
        )
    )

    assert reply.status == 250
    assert len(reply.lines) == 4

    assert reply.lines[0].text == (
        "PROTOCOLINFO 1"
    )

    assert (
        reply.lines[0].is_continuation
        is True
    )

    assert reply.final_line.text == "OK"


def test_reply_finds_keyword():
    reply = TorReplyParser().parse(
        line_reader(
            "250-PROTOCOLINFO 1",
            '250-VERSION Tor="0.4.8.12"',
            "250 OK",
        )
    )

    version = reply.find(
        "VERSION"
    )

    assert version is not None

    assert version.text == (
        'VERSION Tor="0.4.8.12"'
    )

    assert version.value == (
        'Tor="0.4.8.12"'
    )

    assert reply.find(
        "MISSING"
    ) is None


def test_parser_reads_data_block():
    reply = TorReplyParser().parse(
        line_reader(
            "250+config=",
            "SocksPort 9050",
            "ControlPort 9051",
            ".",
            "250 OK",
        )
    )

    assert len(reply.lines) == 2

    data_line = reply.lines[0]

    assert data_line.has_data is True
    assert data_line.keyword == "config"
    assert data_line.value == ""

    assert data_line.data == (
        "SocksPort 9050",
        "ControlPort 9051",
    )

    assert data_line.data_text == (
        "SocksPort 9050\n"
        "ControlPort 9051"
    )


def test_parser_unescapes_data_lines():
    reply = TorReplyParser().parse(
        line_reader(
            "250+data=",
            "..leading-period",
            "...two-periods",
            ".",
            "250 OK",
        )
    )

    assert reply.lines[0].data == (
        ".leading-period",
        "..two-periods",
    )


def test_parser_preserves_empty_data_lines():
    reply = TorReplyParser().parse(
        line_reader(
            "250+data=",
            "first",
            "",
            "third",
            ".",
            "250 OK",
        )
    )

    assert reply.lines[0].data == (
        "first",
        "",
        "third",
    )


def test_parser_reads_error_reply():
    reply = TorReplyParser().parse(
        line_reader(
            "551 Internal error"
        )
    )

    assert reply.status == 551
    assert reply.successful is False
    assert reply.message == (
        "Internal error"
    )


def test_parser_reads_asynchronous_reply():
    reply = TorReplyParser().parse(
        line_reader(
            "650 CIRC 18 BUILT"
        )
    )

    assert reply.status == 650
    assert reply.asynchronous is True
    assert reply.successful is False


@pytest.mark.parametrize(
    "line",
    [
        "",
        "2",
        "25",
        "250",
        "ABC OK",
        "25A OK",
    ],
)
def test_parser_rejects_invalid_status_line(
    line,
):
    with pytest.raises(
        TorControlProtocolError
    ):
        TorReplyParser().parse(
            line_reader(
                line
            )
        )


@pytest.mark.parametrize(
    "line",
    [
        "250:OK",
        "250_OK",
        "250/OK",
    ],
)
def test_parser_rejects_invalid_separator(
    line,
):
    with pytest.raises(
        TorControlProtocolError
    ):
        TorReplyParser().parse(
            line_reader(
                line
            )
        )


def test_parser_rejects_mismatched_status_codes():
    with pytest.raises(
        TorControlProtocolError
    ):
        TorReplyParser().parse(
            line_reader(
                "250-VERSION Tor=1",
                "551 OK",
            )
        )


def test_parser_rejects_missing_final_line():
    with pytest.raises(
        TorControlProtocolError
    ):
        TorReplyParser().parse(
            line_reader(
                "250-VERSION Tor=1",
            )
        )


def test_parser_rejects_unterminated_data_block():
    with pytest.raises(
        TorControlProtocolError
    ):
        TorReplyParser().parse(
            line_reader(
                "250+data=",
                "unfinished",
            )
        )


def test_parser_limits_reply_lines():
    parser = TorReplyParser(
        max_reply_lines=2
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        parser.parse(
            line_reader(
                "250-one",
                "250-two",
                "250 OK",
            )
        )


def test_parser_limits_data_lines():
    parser = TorReplyParser(
        max_data_lines=2
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        parser.parse(
            line_reader(
                "250+data=",
                "one",
                "two",
                "three",
                ".",
                "250 OK",
            )
        )

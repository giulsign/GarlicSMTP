from garlicsmtp.smtp.replies import ReplyFactory


def test_reply_greeting():
    reply = ReplyFactory.greeting("garlicsmtp.onion")
    assert reply.code == 220
    assert reply.serialize() == b"220 garlicsmtp.onion GarlicSMTP ready\r\n"
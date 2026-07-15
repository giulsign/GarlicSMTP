from garlicsmtp.transport.smtp.connection import SMTPConnection
from garlicsmtp.transport.smtp.protocol import SMTPClientProtocol

class FakeSocketMultiReply:

    def __init__(self):
        self.sent = b""
        self.replies = [
            b"354 End data\r\n",
            b"250 Message accepted\r\n",
        ]

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        return self.replies.pop(0)

    def close(self):
        pass

class FakeSocketQuit:

    def __init__(self):
        self.sent = b""

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        return b"221 Bye\r\n"

    def close(self):
        pass

class FakeSocket:

    def __init__(self):

        self.sent = b""

    def sendall(self, data):

        self.sent += data

    def recv(self, size):

        return b"250 OK\r\n"

    def close(self):

        pass


def test_protocol_send():

    connection = SMTPConnection()
    
    connection.socket = FakeSocket()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    protocol.send_command("EHLO garlic")

    assert connection.socket.sent == b"EHLO garlic\r\n"


def test_protocol_receive():

    connection = SMTPConnection()
    
    connection.socket = FakeSocket()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.read_reply()

    assert reply.code == 250
    assert reply.message == "OK"

def test_protocol_ehlo():

    connection = SMTPConnection()
    
    connection.socket = FakeSocket()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.ehlo("garlic.onion")

    assert connection.socket.sent == (
        b"EHLO garlic.onion\r\n"
    )

    assert reply.code == 250

def test_protocol_mail_from():

    connection = SMTPConnection()
    
    connection.socket = FakeSocket()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.mail_from("alice@example.com")

    assert connection.socket.sent == (
        b"MAIL FROM:<alice@example.com>\r\n"
    )

    assert reply.code == 250


def test_protocol_rcpt_to():

    connection = SMTPConnection()
    
    connection.socket = FakeSocket()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.rcpt_to("bob@example.com")

    assert connection.socket.sent == (
        b"RCPT TO:<bob@example.com>\r\n"
    )

    assert reply.code == 250


def test_protocol_data():

    connection = SMTPConnection()
    
    connection.socket = FakeSocketMultiReply()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.data("Subject: Test\r\n\r\nHello")

    assert connection.socket.sent == (
        b"DATA\r\n"
        b"Subject: Test\r\n\r\nHello\r\n.\r\n"
    )

    assert reply.code == 250


def test_protocol_quit():

    connection = SMTPConnection()
    
    connection.socket = FakeSocketQuit()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.quit()

    assert connection.socket.sent == b"QUIT\r\n"
    assert reply.code == 221
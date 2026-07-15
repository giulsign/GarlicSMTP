class Socks5Error(Exception):
    pass


class Socks5ConnectionError(Socks5Error):
    pass


class Socks5HandshakeError(Socks5Error):
    pass
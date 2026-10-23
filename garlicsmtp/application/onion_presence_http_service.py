# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import threading
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from html.parser import HTMLParser

from garlicsmtp.core.service import Service

_ALLOWED_HTML_TAGS = frozenset({
    "html",
    "head",
    "body",
    "title",
    "meta",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
})

_VOID_HTML_TAGS = frozenset({
    "br",
    "meta",
})

_INLINE_TAGS = frozenset({"strong", "em", "br"})

_ALLOWED_CHILDREN = {
    "html": frozenset({"head", "body"}),
    "head": frozenset({"title", "meta"}),
    "body": frozenset({
        "h1", "h2", "h3", "h4", "h5", "h6",
        "p", "ul", "ol", "strong", "em", "br",
    }),
    "ul": frozenset({"li"}),
    "ol": frozenset({"li"}),
    "li": frozenset({
        "p", "ul", "ol", "strong", "em", "br",
    }),
    "p": _INLINE_TAGS,
    "h1": _INLINE_TAGS,
    "h2": _INLINE_TAGS,
    "h3": _INLINE_TAGS,
    "h4": _INLINE_TAGS,
    "h5": _INLINE_TAGS,
    "h6": _INLINE_TAGS,
    "strong": _INLINE_TAGS,
    "em": _INLINE_TAGS,
    "title": frozenset(),
    "meta": frozenset(),
    "br": frozenset(),
}

_TEXT_ALLOWED_TAGS = frozenset({
    "body",
    "title",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "li",
    "strong",
    "em",
})

_MAX_CUSTOM_HTML_BYTES = 256 * 1024

class _SafeHtmlValidator(HTMLParser):

    def __init__(self) -> None:
        super().__init__()
        self.has_invalid_markup = False
        self._open_tags: list[str] = []
        self._root_seen = False
        self._root_closed = False
        self._head_seen = False
        self._body_seen = False

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()

        parent = self._open_tags[-1] if self._open_tags else None

        if tag not in _ALLOWED_HTML_TAGS:
            self.has_invalid_markup = True
            return

        if tag != "html":
            if parent is None or tag not in _ALLOWED_CHILDREN.get(parent, frozenset()):
                self.has_invalid_markup = True

        for name, value in attrs:
            attribute = name.lower()

            if attribute.startswith("on"):
                self.has_invalid_markup = True
                continue

            if (
                attribute in {"href", "src", "action", "formaction"}
                and value is not None
                and value.strip().lower().startswith("javascript:")
            ):
                self.has_invalid_markup = True
                continue

            if tag == "meta":
                if (
                    attribute != "charset"
                    or value is None
                    or value.lower() != "utf-8"
                ):
                    self.has_invalid_markup = True
            else:
                self.has_invalid_markup = True

        parent = self._open_tags[-1] if self._open_tags else None

        if tag == "head":
            if parent != "html" or self._head_seen or self._body_seen:
                self.has_invalid_markup = True
            self._head_seen = True

        elif tag == "body":
            if parent != "html" or self._body_seen:
                self.has_invalid_markup = True
            self._body_seen = True

        if tag == "html":
            if self._root_seen or self._open_tags:
                self.has_invalid_markup = True
            self._root_seen = True

        elif not self._open_tags or self._root_closed:
            self.has_invalid_markup = True

        # Importante: FUORI dal ciclo degli attributi.
        if tag not in _VOID_HTML_TAGS:
            self._open_tags.append(tag)

    def handle_startendtag(self, tag: str, attrs) -> None:
        tag = tag.lower()

        if tag not in _VOID_HTML_TAGS:
            self.has_invalid_markup = True
            return

        self.handle_starttag(tag, attrs)

    def handle_comment(self, data: str) -> None:
        self.has_invalid_markup = True

    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower() != "doctype html":
            self.has_invalid_markup = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if not self._open_tags or self._open_tags[-1] != tag:
            self.has_invalid_markup = True
            return

        self._open_tags.pop()

        if tag == "html":
            self._root_closed = True


    def handle_pi(self, data: str) -> None:
        self.has_invalid_markup = True


    def validate_complete(self) -> None:
        # Conserva gli eventuali frammenti non analizzati.
        pending_data = self.rawdata

        self.close()

        if not self._root_seen or not self._root_closed:
            self.has_invalid_markup = True

        if self._open_tags:
            self.has_invalid_markup = True

        if pending_data or self.rawdata:
            self.has_invalid_markup = True

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return

        if not self._open_tags:
            self.has_invalid_markup = True
            return

        parent = self._open_tags[-1]

        if parent not in _TEXT_ALLOWED_TAGS:
            self.has_invalid_markup = True
            return

        if parent == "title" and ("<" in data or ">" in data):
            self.has_invalid_markup = True

class _PresenceRequestHandler(
    BaseHTTPRequestHandler
):
    def do_GET(self) -> None:
        if self.path == "/health":
            body = b"OK"
            content_type = "text/plain; charset=utf-8"

        elif self.path == "/":
            service = self.server

            if (
                service.custom_page_enabled
                and service.custom_html is not None
            ):
                body = service.custom_html.encode("utf-8")
            else:
                body = (
                    b"<!DOCTYPE html>\n"
                    b'<html lang="en">\n'
                    b"<head>\n"
                    b'  <meta charset="utf-8">\n'
                    b"  <title>GarlicSMTP</title>\n"
                    b"</head>\n"
                    b"<body>\n"
                    b"  <h1>GarlicSMTP</h1>\n"
                    b"  <p>Onion Service Online</p>\n"
                    b"</body>\n"
                    b"</html>\n"
                )

            content_type = "text/html; charset=utf-8"

        else:
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header(
            "Content-Type",
            content_type,
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; "
            "script-src 'none'; "
            "style-src 'none'; "
            "img-src 'none'; "
            "connect-src 'none'; "
            "font-src 'none'; "
            "object-src 'none'; "
            "frame-src 'none'; "
            "form-action 'none'; "
            "base-uri 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def log_message(
        self,
        format: str,
        *args,
    ) -> None:
        # Evita log di richieste e indirizzi.
        pass


class OnionPresenceHttpService(Service):

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8080,
        custom_html: str | None = None,
        custom_page_enabled: bool = False,
    ) -> None:
        if host != "127.0.0.1":
            raise ValueError(
                "Onion Presence HTTP must bind "
                "to 127.0.0.1"
            )

        self.host = host
        self.port = port
        self.running = False
        if custom_page_enabled and custom_html is not None:
            if len(custom_html.encode("utf-8")) > _MAX_CUSTOM_HTML_BYTES:
                raise ValueError(
                    "Custom Onion HTML exceeds the maximum size of 256 KiB"
                )

            validator = _SafeHtmlValidator()
            validator.feed(custom_html)
            validator.validate_complete()

            if validator.has_invalid_markup:
                raise ValueError(
                    "Custom Onion HTML contains disallowed or malformed markup"
                )
        self.custom_html = custom_html
        self.custom_page_enabled = custom_page_enabled

        self._server: (
            ThreadingHTTPServer | None
        ) = None

        self._thread: (
            threading.Thread | None
        ) = None

    def start(self) -> None:
        if self.running:
            return

        server = ThreadingHTTPServer(
            (self.host, self.port),
            _PresenceRequestHandler,
        )
        server.custom_html = self.custom_html
        server.custom_page_enabled = self.custom_page_enabled

        server.daemon_threads = True

        thread = threading.Thread(
            target=server.serve_forever,
            daemon=True,
            name="garlicsmtp-onion-presence-http",
        )

        self.port = server.server_address[1]
        self._server = server
        self._thread = thread

        try:
            thread.start()
        except Exception:
            server.server_close()
            self._server = None
            self._thread = None
            raise

        self.running = True

    def stop(self) -> None:
        if not self.running:
            return

        server = self._server
        thread = self._thread

        if server is not None:
            server.shutdown()
            server.server_close()

        if thread is not None:
            thread.join(timeout=3)

        self._server = None
        self._thread = None
        self.running = False

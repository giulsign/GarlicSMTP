import http.client
import pytest

from garlicsmtp.application.onion_presence_http_service import (
    OnionPresenceHttpService,
)


def test_onion_presence_http_service_health_and_shutdown():
    service = OnionPresenceHttpService(
        host="127.0.0.1",
        port=0,
    )

    assert service.host == "127.0.0.1"

    service.start()

    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            service.port,
            timeout=2,
        )

        try:
            connection.request(
                "GET",
                "/health",
            )

            response = connection.getresponse()

            assert response.status == 200
            assert response.read() == b"OK"
        finally:
            connection.close()

    finally:
        service.stop()

    assert service.running is False


def test_onion_presence_http_service_serves_default_page():
    service = OnionPresenceHttpService(
        host="127.0.0.1",
        port=0,
    )

    service.start()

    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            service.port,
            timeout=2,
        )

        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            body = response.read()

            assert response.status == 200
            assert (
                response.getheader("Content-Type")
                == "text/html; charset=utf-8"
            )
            assert b"GarlicSMTP" in body
            assert b"Onion Service Online" in body
        finally:
            connection.close()

    finally:
        service.stop()


def test_onion_presence_http_service_releases_port_on_stop():
    service = OnionPresenceHttpService(
        host="127.0.0.1",
        port=0,
    )

    service.start()
    assigned_port = service.port

    service.stop()

    assert service.running is False

    replacement = OnionPresenceHttpService(
        host="127.0.0.1",
        port=assigned_port,
    )

    replacement.start()

    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            assigned_port,
            timeout=2,
        )

        try:
            connection.request("GET", "/health")
            response = connection.getresponse()

            assert response.status == 200
            assert response.read() == b"OK"
        finally:
            connection.close()

    finally:
        replacement.stop()


def test_onion_presence_http_service_can_restart():
    service = OnionPresenceHttpService(
        host="127.0.0.1",
        port=0,
    )

    try:
        service.start()

        assert service.running is True

        first_port = service.port

        service.stop()

        assert service.running is False

        service.start()

        assert service.running is True
        assert service.port == first_port

        connection = http.client.HTTPConnection(
            "127.0.0.1",
            service.port,
            timeout=2,
        )

        try:
            connection.request("GET", "/health")
            response = connection.getresponse()

            assert response.status == 200
            assert response.read() == b"OK"
        finally:
            connection.close()

    finally:
        service.stop()

    assert service.running is False


def test_onion_presence_http_service_requires_opt_in_for_custom_page():
    custom_html = (
        "<!DOCTYPE html>"
        "<html><head><title>Personal Page</title></head>"
        "<body><h1>My Onion Page</h1></body></html>"
    )

    service = OnionPresenceHttpService(
        host="127.0.0.1",
        port=0,
        custom_html=custom_html,
        custom_page_enabled=False,
    )

    service.start()

    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            service.port,
            timeout=2,
        )

        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            body = response.read()

            assert response.status == 200
            assert b"GarlicSMTP" in body
            assert b"My Onion Page" not in body
        finally:
            connection.close()

    finally:
        service.stop()


def test_onion_presence_http_service_serves_custom_page_when_enabled():
    custom_html = (
        "<!DOCTYPE html>"
        "<html><head><title>Personal Page</title></head>"
        "<body><h1>My Onion Page</h1></body></html>"
    )

    service = OnionPresenceHttpService(
        host="127.0.0.1",
        port=0,
        custom_html=custom_html,
        custom_page_enabled=True,
    )

    service.start()

    try:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            service.port,
            timeout=2,
        )

        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            body = response.read()

            assert response.status == 200
            assert (
                response.getheader("Content-Type")
                == "text/html; charset=utf-8"
            )
            assert body == custom_html.encode("utf-8")
        finally:
            connection.close()

    finally:
        service.stop()



def test_onion_presence_http_service_rejects_script_in_custom_page():
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=(
                "<html><body>"
                "<script>alert('hello')</script>"
                "</body></html>"
            ),
            custom_page_enabled=True,
        )


def test_onion_presence_http_service_rejects_event_handlers():
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=(
                "<html><body>"
                '<img src="invalid" onerror="alert(1)">'
                "</body></html>"
            ),
            custom_page_enabled=True,
        )


def test_onion_presence_http_service_rejects_javascript_urls():
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=(
                "<html><body>"
                '<a href="javascript:alert(1)">Apri</a>'
                "</body></html>"
            ),
            custom_page_enabled=True,
        )


def test_onion_presence_http_service_rejects_iframe():
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=(
                "<html><body>"
                '<iframe src="https://example.com"></iframe>'
                "</body></html>"
            ),
            custom_page_enabled=True,
        )


def test_onion_presence_http_service_rejects_meta_refresh():
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=(
                "<html><head>"
                '<meta http-equiv="refresh" '
                'content="0;url=https://example.com">'
                "</head><body><h1>Hello</h1></body></html>"
            ),
            custom_page_enabled=True,
        )


def test_onion_presence_http_service_accepts_meta_charset():
    custom_html = (
        "<html>"
        "<head>"
        '<meta charset="utf-8">'
        "<title>La mia pagina Onion</title>"
        "</head>"
        "<body>"
        "<h1>Benvenuti</h1>"
        "<p>Questa è una pagina statica.</p>"
        "</body>"
        "</html>"
    )

    service = OnionPresenceHttpService(
        host="127.0.0.1",
        port=0,
        custom_html=custom_html,
        custom_page_enabled=True,
    )

    try:
        service.start()

        connection = http.client.HTTPConnection(
            "127.0.0.1",
            service.port,
            timeout=2,
        )
        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            body = response.read()
        finally:
            connection.close()

        assert response.status == 200
        assert body == custom_html.encode("utf-8")
    finally:
        service.stop()


def test_onion_presence_http_service_sets_restrictive_csp():
    service = OnionPresenceHttpService(
        host="127.0.0.1",
        port=0,
    )

    try:
        service.start()

        connection = http.client.HTTPConnection(
            "127.0.0.1",
            service.port,
            timeout=2,
        )
        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            response.read()

            assert response.status == 200
            assert response.getheader("Content-Security-Policy") == (
                "default-src 'none'; "
                "script-src 'none'; "
                "style-src 'none'; "
                "img-src 'none'; "
                "connect-src 'none'; "
                "font-src 'none'; "
                "object-src 'none'; "
                "frame-src 'none'; "
                "form-action 'none'; "
                "base-uri 'none'"
            )
        finally:
            connection.close()
    finally:
        service.stop()


def test_onion_presence_http_service_sets_csp_on_custom_page():
    custom_html = "<html><body><h1>Pagina personale</h1></body></html>"

    service = OnionPresenceHttpService(
        host="127.0.0.1",
        port=0,
        custom_html=custom_html,
        custom_page_enabled=True,
    )

    try:
        service.start()

        connection = http.client.HTTPConnection(
            "127.0.0.1",
            service.port,
            timeout=2,
        )
        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            body = response.read()

            assert response.status == 200
            assert body == custom_html.encode("utf-8")
            assert response.getheader("Content-Security-Policy") == (
                "default-src 'none'; "
                "script-src 'none'; "
                "style-src 'none'; "
                "img-src 'none'; "
                "connect-src 'none'; "
                "font-src 'none'; "
                "object-src 'none'; "
                "frame-src 'none'; "
                "form-action 'none'; "
                "base-uri 'none'"
            )
        finally:
            connection.close()
    finally:
        service.stop()


def test_onion_presence_http_service_rejects_html_comments():
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=(
                "<html><body>"
                "<!-- <script>alert(1)</script> -->"
                "<h1>Benvenuti</h1>"
                "</body></html>"
            ),
            custom_page_enabled=True,
        )


def test_onion_presence_http_service_rejects_non_html5_doctype():
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=(
                '<!DOCTYPE html SYSTEM "https://example.com/external.dtd">'
                "<html><body>"
                "<h1>Benvenuti</h1>"
                "</body></html>"
            ),
            custom_page_enabled=True,
        )


@pytest.mark.parametrize(
    "custom_html",
    [
        "<html><body><h1>Pagina incompleta",
        "<html><body><p>Test</p></body></html><script",
        "<html><body><?processing instruction?></body></html>",
    ],
    ids=[
        "unclosed-tags",
        "incomplete-script-tag",
        "processing-instruction",
    ],
)
def test_onion_presence_http_service_rejects_malformed_html(custom_html):
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=custom_html,
            custom_page_enabled=True,
        )


@pytest.mark.parametrize(
    "custom_html",
    [
        "<html><body><h1>Uno</h1></body></html>"
        "<html><body><h1>Due</h1></body></html>",
        "<html><body/><h1>Fuori dal body</h1></html>",
        "<html><body><h1>Test</h1></body></html>"
        "<p>Fuori dal documento</p>",
    ],
    ids=[
        "duplicate-html-root",
        "self-closing-body",
        "content-after-html",
    ],
)
def test_onion_presence_http_service_rejects_invalid_document_structure(
    custom_html,
):
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=custom_html,
            custom_page_enabled=True,
        )


@pytest.mark.parametrize(
    "custom_html",
    [
        "<html><body><h1>Pagina</h1></body></html>TESTO",
        "<html><h1>Fuori dal body</h1><body></body></html>",
        "<html><body><p>Uno</p></body>"
        "<body><p>Due</p></body></html>",
    ],
    ids=[
        "text-after-html",
        "heading-outside-body",
        "duplicate-body",
    ],
)
def test_onion_presence_http_service_rejects_invalid_body_structure(
    custom_html,
):
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=custom_html,
            custom_page_enabled=True,
        )


@pytest.mark.parametrize(
    "custom_html",
    [
        "<html><body><li>Elemento isolato</li></body></html>",
        "<html><head><title><strong>Titolo</strong></title></head>"
        "<body><h1>Pagina</h1></body></html>",
        "<html><head><p>Testo nel head</p></head>"
        "<body><h1>Pagina</h1></body></html>",
    ],
    ids=[
        "li-outside-list",
        "element-inside-title",
        "paragraph-inside-head",
    ],
)
def test_onion_presence_http_service_rejects_invalid_tag_nesting(
    custom_html,
):
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=custom_html,
            custom_page_enabled=True,
        )


@pytest.mark.parametrize(
    "custom_html",
    [
        (
            "<!DOCTYPE html>"
            "<html><body>"
            "<ul><li><strong>Primo</strong></li>"
            "<li><em>Secondo</em></li></ul>"
            "</body></html>"
        ),
        (
            "<html><body>"
            "<h1>Titolo</h1>"
            "<p>Testo con <strong>grassetto</strong> "
            "ed <em>enfasi</em>.</p>"
            "</body></html>"
        ),
        (
            "<html><head>"
            '<meta charset="utf-8">'
            "<title>Pagina personale</title>"
            "</head><body>"
            "<h1>Benvenuti</h1>"
            "<p>Prima riga<br>Seconda riga</p>"
            "</body></html>"
        ),
    ],
    ids=[
        "valid-list",
        "valid-inline-formatting",
        "valid-head-and-void-elements",
    ],
)
def test_onion_presence_http_service_accepts_valid_html_nesting(
    custom_html,
):
    service = OnionPresenceHttpService(
        host="127.0.0.1",
        port=0,
        custom_html=custom_html,
        custom_page_enabled=True,
    )

    try:
        service.start()

        connection = http.client.HTTPConnection(
            "127.0.0.1",
            service.port,
            timeout=2,
        )
        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            body = response.read()

            assert response.status == 200
            assert body == custom_html.encode("utf-8")
        finally:
            connection.close()
    finally:
        service.stop()


@pytest.mark.parametrize(
    "custom_html",
    [
        (
            "<html><body>"
            "<ul><p>Elemento senza li</p></ul>"
            "</body></html>"
        ),
        (
            "<html><body>"
            "<ul><li>Primo<li>Secondo</li></li></ul>"
            "</body></html>"
        ),
        (
            "<html><body>"
            "<p>Testo <h1>Titolo annidato</h1></p>"
            "</body></html>"
        ),
    ],
    ids=[
        "paragraph-directly-in-list",
        "li-directly-in-li",
        "heading-inside-paragraph",
    ],
)
def test_onion_presence_http_service_rejects_invalid_parent_child(
    custom_html,
):
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=custom_html,
            custom_page_enabled=True,
        )


@pytest.mark.parametrize(
    "custom_html",
    [
        "<html><body><ul>Testo diretto</ul></body></html>",
        "<html><body><ol>Testo diretto</ol></body></html>",
        (
            "<html><head>Testo fuori dal titolo"
            "<title>Pagina</title></head>"
            "<body><h1>Benvenuti</h1></body></html>"
        ),
    ],
    ids=[
        "text-directly-in-ul",
        "text-directly-in-ol",
        "text-directly-in-head",
    ],
)
def test_onion_presence_http_service_rejects_text_in_containers(
    custom_html,
):
    with pytest.raises(ValueError):
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=custom_html,
            custom_page_enabled=True,
        )


@pytest.mark.parametrize(
    "custom_html",
    [
        (
            "<html><head>"
            "<title>Pagina &lt;privata&gt;</title>"
            "</head><body><h1>Benvenuti</h1></body></html>"
        ),
        (
            "<html><head>"
            "<title>Pagina &#60;privata&#62;</title>"
            "</head><body><h1>Benvenuti</h1></body></html>"
        ),
        (
            "<html><head><title>Pagina</title></head>"
            "<body><p>Tom &amp; Jerry</p></body></html>"
        ),
    ],
    ids=[
        "named-entities-in-title",
        "numeric-entities-in-title",
        "safe-entity-in-body",
    ],
)
def test_onion_presence_http_service_handles_html_entities(
    custom_html,
):
    should_reject = "privata" in custom_html

    if should_reject:
        with pytest.raises(ValueError):
            OnionPresenceHttpService(
                host="127.0.0.1",
                port=0,
                custom_html=custom_html,
                custom_page_enabled=True,
            )
    else:
        service = OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=custom_html,
            custom_page_enabled=True,
        )
        assert service.custom_html == custom_html


@pytest.mark.parametrize(
    ("custom_html", "enabled", "should_reject"),
    [
        (
            "<html><body><p>"
            + "A" * 262_144
            + "</p></body></html>",
            True,
            True,
        ),
        (
            "<html><body><p>"
            + "A" * 262_144
            + "</p></body></html>",
            False,
            False,
        ),
        (
            "<html><body><p>"
            + "é" * 140_000
            + "</p></body></html>",
            True,
            True,
        ),
    ],
    ids=[
        "oversized-enabled-page",
        "oversized-disabled-page",
        "utf8-byte-size",
    ],
)
def test_onion_presence_http_service_limits_custom_html_size(
    custom_html,
    enabled,
    should_reject,
):
    if should_reject:
        with pytest.raises(ValueError):
            OnionPresenceHttpService(
                host="127.0.0.1",
                port=0,
                custom_html=custom_html,
                custom_page_enabled=enabled,
            )
    else:
        service = OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=custom_html,
            custom_page_enabled=enabled,
        )
        assert service.custom_html == custom_html


@pytest.mark.parametrize(
    ("offset", "character", "should_reject"),
    [
        (-1, "A", False),
        (0, "A", False),
        (1, "A", True),
        (0, "é", False),
    ],
    ids=[
        "one-byte-below-limit",
        "exactly-at-limit",
        "one-byte-above-limit",
        "multibyte-at-limit",
    ],
)

def test_onion_presence_http_service_custom_html_size_boundaries(
    offset,
    character,
    should_reject,
):
    prefix = "<html><body><p>"
    suffix = "</p></body></html>"
    wrapper_bytes = len((prefix + suffix).encode("utf-8"))
    target_bytes = 262_144 + offset
    content_bytes = target_bytes - wrapper_bytes

    character_bytes = len(character.encode("utf-8"))
    count, remainder = divmod(content_bytes, character_bytes)

    content = character * count + "A" * remainder

    custom_html = prefix + content + suffix

    assert len(custom_html.encode("utf-8")) == target_bytes

    if should_reject:
        with pytest.raises(ValueError):
            OnionPresenceHttpService(
                host="127.0.0.1",
                port=0,
                custom_html=custom_html,
                custom_page_enabled=True,
            )
    else:
        OnionPresenceHttpService(
            host="127.0.0.1",
            port=0,
            custom_html=custom_html,
            custom_page_enabled=True,
        )
import http.client
import ipaddress
import socket
import ssl
from urllib.parse import urljoin, urlsplit


MAX_DOWNLOAD = 50 * 1024 * 1024


def public_address(url: str) -> tuple[str, int, str, str]:
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError(
            "Nur öffentliche HTTP(S)-Adressen ohne Zugangsdaten sind erlaubt."
        )
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    if not addresses or any(
        not ipaddress.ip_address(item[4][0]).is_global for item in addresses
    ):
        raise ValueError("Private und lokale Netzwerkziele sind nicht erlaubt.")
    return parsed.hostname, port, str(addresses[0][4][0]), parsed.scheme


def fetch_public(url: str, limit: int = MAX_DOWNLOAD) -> bytes:
    for _ in range(6):
        host, port, address, scheme = public_address(url)
        connection: http.client.HTTPConnection
        if scheme == "https":
            connection = http.client.HTTPSConnection(
                host, port, timeout=20, context=ssl.create_default_context()
            )
        else:
            connection = http.client.HTTPConnection(host, port, timeout=20)
        # Pin the validated address, retaining the original hostname for TLS verification.
        setattr(
            connection,
            "_create_connection",
            lambda target, timeout, source_address=None: socket.create_connection(
                (address, port), timeout, source_address
            ),
        )
        parsed = urlsplit(url)
        try:
            connection.request(
                "GET",
                (parsed.path or "/") + ("?" + parsed.query if parsed.query else ""),
                headers={
                    "User-Agent": "Kinderbuch-Bildlabor/1",
                    "Accept-Encoding": "identity",
                },
            )
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                if not location:
                    raise ValueError("Weiterleitung ohne Zieladresse.")
                url = urljoin(url, location)
                continue
            if response.status != 200:
                raise ValueError(
                    f"Abruf fehlgeschlagen (HTTP {response.status}); nur frei zugängliche Quellen sind unterstützt."
                )
            content = response.read(limit + 1)
            if len(content) > limit:
                raise ValueError("Download überschreitet die Größenbegrenzung.")
            return content
        finally:
            connection.close()
    raise ValueError("Zu viele Weiterleitungen.")

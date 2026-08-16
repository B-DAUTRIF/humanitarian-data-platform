from __future__ import annotations

import hashlib
import http.client
import ipaddress
import os
import socket
import ssl
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse


REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


@dataclass(frozen=True)
class DownloadResult:
    temporary_path: Path
    final_url: str
    headers: dict[str, str]
    sha256: str
    size_bytes: int


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, hostname: str, address: str, port: int, timeout: float) -> None:
        super().__init__(hostname, port=port, timeout=timeout)
        self._pinned_address = address

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self._pinned_address, self.port), self.timeout, self.source_address
        )
        peer = ipaddress.ip_address(self.sock.getpeername()[0])
        if not peer.is_global or str(peer) != str(ipaddress.ip_address(self._pinned_address)):
            self.sock.close()
            raise OSError("Le pair HTTP ne correspond pas à l'adresse publique validée")


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, hostname: str, address: str, port: int, timeout: float) -> None:
        super().__init__(hostname, port=port, timeout=timeout, context=ssl.create_default_context())
        self._pinned_address = address

    def connect(self) -> None:
        raw = socket.create_connection(
            (self._pinned_address, self.port), self.timeout, self.source_address
        )
        peer = ipaddress.ip_address(raw.getpeername()[0])
        if not peer.is_global or str(peer) != str(ipaddress.ip_address(self._pinned_address)):
            raw.close()
            raise OSError("Le pair HTTPS ne correspond pas à l'adresse publique validée")
        self.sock = self._context.wrap_socket(raw, server_hostname=self.host)


def resolve_public_addresses(url: str) -> tuple[str, int, tuple[str, ...]]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Seules les URL HTTP(S) avec un hôte sont autorisées")
    if parsed.username or parsed.password:
        raise ValueError("Les URL contenant des identifiants sont interdites")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        resolved = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Le nom d'hôte de la ressource est introuvable") from exc
    addresses = tuple(sorted({item[4][0] for item in resolved}))
    if not addresses:
        raise ValueError("Aucune adresse n'a été trouvée pour la ressource")
    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise ValueError("La ressource pointe vers une adresse réseau non publique")
    return parsed.hostname, port, addresses


def _request_once(url: str, *, timeout_seconds: float, user_agent: str) -> tuple[http.client.HTTPResponse, http.client.HTTPConnection]:
    parsed = urlparse(url)
    hostname, port, addresses = resolve_public_addresses(url)
    target = parsed.path or "/"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    host_header = hostname
    if parsed.port and parsed.port not in {80, 443}:
        host_header = f"{hostname}:{parsed.port}"
    last_error: Exception | None = None
    for address in addresses:
        connection: http.client.HTTPConnection | None = None
        try:
            if parsed.scheme == "https":
                connection = _PinnedHTTPSConnection(hostname, address, port, timeout_seconds)
            else:
                connection = _PinnedHTTPConnection(hostname, address, port, timeout_seconds)
            connection.request(
                "GET",
                target,
                headers={"Host": host_header, "User-Agent": user_agent, "Accept-Encoding": "identity"},
            )
            return connection.getresponse(), connection
        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            last_error = exc
            try:
                if connection is not None:
                    connection.close()
            except Exception:
                pass
    raise ValueError("Connexion impossible vers les adresses publiques validées") from last_error


def download_public_file(
    url: str,
    destination_directory: Path,
    *,
    max_bytes: int,
    user_agent: str,
    max_redirects: int = 5,
) -> DownloadResult:
    destination_directory.mkdir(parents=True, exist_ok=True)
    current_url = url
    for _ in range(max_redirects + 1):
        response, connection = _request_once(
            current_url, timeout_seconds=120.0, user_agent=user_agent
        )
        try:
            headers = {key.casefold(): value for key, value in response.getheaders()}
            if response.status in REDIRECT_STATUSES:
                location = headers.get("location")
                if not location:
                    raise ValueError("Redirection sans destination")
                current_url = urljoin(current_url, location)
                resolve_public_addresses(current_url)
                continue
            if response.status < 200 or response.status >= 300:
                raise ValueError(f"Réponse HTTP distante inattendue : {response.status}")
            declared = headers.get("content-length")
            if declared and int(declared) > max_bytes:
                raise ValueError(f"Ressource supérieure à la limite de {max_bytes} octets")

            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".hdp-download-", suffix=".part", dir=destination_directory
            )
            temporary_path = Path(temporary_name)
            digest = hashlib.sha256()
            total = 0
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    while True:
                        chunk = response.read(65_536)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > max_bytes:
                            raise ValueError(f"Ressource supérieure à la limite de {max_bytes} octets")
                        digest.update(chunk)
                        stream.write(chunk)
                    stream.flush()
                    os.fsync(stream.fileno())
                return DownloadResult(
                    temporary_path=temporary_path,
                    final_url=current_url,
                    headers=headers,
                    sha256=digest.hexdigest(),
                    size_bytes=total,
                )
            except Exception:
                temporary_path.unlink(missing_ok=True)
                raise
        finally:
            response.close()
            connection.close()
    raise ValueError("Trop de redirections HTTP")

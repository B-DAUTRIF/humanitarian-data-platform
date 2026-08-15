from __future__ import annotations

import hashlib
import ipaddress
import re
import socket
from pathlib import Path
from urllib.parse import urlparse


def safe_filename(value: str, fallback: str = "ressource.bin") -> str:
    """Return a Windows-safe filename without path components."""
    name = Path(value.replace("\\", "/")).name.strip().strip(".")
    name = re.sub(r"[<>:\"/\\|?*\x00-\x1f]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        name = fallback
    stem, suffix = Path(name).stem[:120], Path(name).suffix[:20]
    return f"{stem or 'ressource'}{suffix}"[:145]


def safe_query_fragment(query: str) -> str:
    fragment = re.sub(r"[^a-zA-Z0-9_-]+", "-", query.strip()).strip("-")
    return fragment[:50] or "query"


def resource_key(resource_id: str | None, url: str) -> str:
    if resource_id:
        return safe_filename(str(resource_id), "resource")[:100]
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_public_url(url: str) -> str:
    """Reject non-HTTP and non-public destinations to reduce SSRF exposure."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Seules les URL HTTP(S) avec un hôte sont autorisées")
    if parsed.username or parsed.password:
        raise ValueError("Les URL contenant des identifiants sont interdites")

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise ValueError("Le nom d'hôte de la ressource est introuvable") from exc

    if not addresses:
        raise ValueError("Aucune adresse n'a été trouvée pour la ressource")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError("La ressource pointe vers une adresse réseau non publique")
    return url


def confined_path(root: Path, relative: str) -> Path:
    root_resolved = root.resolve()
    candidate = (root_resolved / relative).resolve()
    if not candidate.is_relative_to(root_resolved):
        raise ValueError("Chemin de données non autorisé")
    return candidate

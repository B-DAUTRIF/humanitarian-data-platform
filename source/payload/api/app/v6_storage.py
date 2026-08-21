from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class StorageValidationError(ValueError):
    pass


def serialize_public_content(content: Any, output_format: str) -> tuple[bytes, str, str]:
    normalized_format = output_format.strip().casefold()
    if normalized_format in {"json", "geojson"}:
        data = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        media_type = "application/geo+json" if normalized_format == "geojson" else "application/json"
        suffix = ".geojson" if normalized_format == "geojson" else ".json"
    elif normalized_format in {"text", "txt", "csv"}:
        if not isinstance(content, str):
            raise StorageValidationError("ce format de sortie attend une chaîne de caractères")
        data = content.encode("utf-8")
        media_type = "text/csv; charset=utf-8" if normalized_format == "csv" else "text/plain; charset=utf-8"
        suffix = ".csv" if normalized_format == "csv" else ".txt"
    else:
        raise StorageValidationError("format matérialisable non pris en charge")
    return data, media_type, suffix


def validation_delay_seconds(
    *,
    source_frequency_seconds: int | None,
    source_duration_seconds: int | None,
) -> int:
    candidates = [
        value
        for value in (source_frequency_seconds, source_duration_seconds)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0
    ]
    if not candidates:
        raise StorageValidationError(
            "une fréquence déclarée ou une durée de validité par source est obligatoire"
        )
    return min(candidates)


def content_addressed_path(root: Path, cache_key: str, content_sha256: str, suffix: str) -> Path:
    if len(cache_key) != 64 or any(character not in "0123456789abcdef" for character in cache_key.casefold()):
        raise StorageValidationError("clé de cache invalide")
    if len(content_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in content_sha256.casefold()
    ):
        raise StorageValidationError("empreinte de contenu invalide")
    if suffix not in {".json", ".geojson", ".txt", ".csv"}:
        raise StorageValidationError("extension de cache invalide")
    resolved_root = root.resolve()
    # Le chemin dépend uniquement du contenu : deux clés canoniques pointant vers
    # le même artefact public partagent donc réellement un seul fichier.
    path = resolved_root / "objects" / content_sha256[:2].casefold() / f"{content_sha256.casefold()}.blob"
    if resolved_root not in path.parents:
        raise StorageValidationError("chemin de cache hors racine")
    return path


def publish_atomically(root: Path, cache_key: str, data: bytes, suffix: str) -> tuple[Path, str, bool]:
    content_sha256 = hashlib.sha256(data).hexdigest()
    destination = content_addressed_path(root, cache_key, content_sha256, suffix)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if destination.exists():
        if destination.is_symlink() or hashlib.sha256(destination.read_bytes()).hexdigest() != content_sha256:
            raise StorageValidationError("collision ou fichier de cache altéré")
        return destination, content_sha256, False
    descriptor, temporary_name = tempfile.mkstemp(prefix=".hdp-cache-", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != content_sha256:
            raise StorageValidationError("l'empreinte du fichier temporaire est incohérente")
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
        directory_descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination, content_sha256, True

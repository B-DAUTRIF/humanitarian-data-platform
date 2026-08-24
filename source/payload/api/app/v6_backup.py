from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import unquote, urlparse


class BackupError(ValueError):
    pass


MAX_BACKUP_ENTRIES = 10_000
MAX_BACKUP_UNCOMPRESSED_BYTES = 50 * 1024 * 1024 * 1024
MAX_BACKUP_MANIFEST_BYTES = 4 * 1024 * 1024
BACKUP_SCOPES = {"global", "project", "signals"}


def backup_root(data_directory: Path) -> Path:
    root = (data_directory.resolve() / "backups").resolve()
    if data_directory.resolve() not in root.parents:
        raise BackupError("racine de sauvegarde invalide")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pg_dump_command(database_url: str, destination: Path) -> tuple[list[str], dict[str, str]]:
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname or not parsed.path.strip("/"):
        raise BackupError("DATABASE_URL PostgreSQL invalide")
    command = [
        "pg_dump",
        "--host", parsed.hostname,
        "--port", str(parsed.port or 5432),
        "--username", unquote(parsed.username or ""),
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file", str(destination),
        unquote(parsed.path.strip("/")),
    ]
    environment = {
        **os.environ,
        "PGPASSWORD": unquote(parsed.password or ""),
        "PGCONNECT_TIMEOUT": "15",
    }
    return command, environment


def create_global_dump(database_url: str, destination: Path, *, timeout_seconds: int = 1800) -> None:
    command, environment = pg_dump_command(database_url, destination)
    result = subprocess.run(
        command,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        destination.unlink(missing_ok=True)
        raise BackupError(f"pg_dump a échoué: {result.stderr[-2000:]}")
    if not destination.is_file() or destination.stat().st_size == 0:
        raise BackupError("pg_dump n'a produit aucune archive")
    os.chmod(destination, 0o600)


def export_query_as_jsonl(
    connection: Any,
    destination: Path,
    query: str,
    parameters: tuple[Any, ...],
) -> int:
    count = 0
    descriptor, temporary_name = tempfile.mkstemp(prefix=".hdp-export-", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            cursor = connection.execute(query, parameters)
            columns = [column.name for column in cursor.description]
            for row in cursor:
                document = {
                    column: value
                    for column, value in zip(columns, row, strict=True)
                }
                stream.write(
                    json.dumps(
                        document,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                    )
                    + "\n"
                )
                count += 1
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return count


def build_manifest(
    *,
    backup_id: str,
    application_version: str,
    schema_versions: list[str],
    scope: str,
    selector: dict[str, Any],
    files: Iterable[Path],
    row_counts: dict[str, int],
    created_at: datetime | None = None,
) -> dict[str, Any]:
    moment = created_at or datetime.now(UTC)
    inventory = []
    for path in sorted(files, key=lambda item: item.name):
        inventory.append(
            {
                "name": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    return {
        "manifest_version": "1.0",
        "backup_id": backup_id,
        "application_version": application_version,
        "schema_versions": schema_versions,
        "scope": scope,
        "selector": selector,
        "created_at": moment.isoformat(),
        "files": inventory,
        "row_counts": row_counts,
        "restore_automatically_authorized": False,
    }


def publish_bundle(root: Path, backup_id: str, files: list[Path], manifest: dict[str, Any]) -> Path:
    destination = root / f"hdp-{backup_id}.zip"
    descriptor, temporary_name = tempfile.mkstemp(prefix=".hdp-backup-", suffix=".zip", dir=root)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2, default=str),
            )
            for path in files:
                archive.write(path, f"data/{path.name}")
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def _validate_archive_member(info: zipfile.ZipInfo) -> None:
    name = info.filename
    path = PurePosixPath(name)
    if (
        not name
        or "\\" in name
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or info.is_dir()
    ):
        raise BackupError(f"entrée de sauvegarde invalide: {name!r}")
    unix_mode = (info.external_attr >> 16) & 0o170000
    if unix_mode == 0o120000:
        raise BackupError(f"lien symbolique interdit dans la sauvegarde: {name}")
    if info.flag_bits & 0x1:
        raise BackupError(f"entrée chiffrée non prise en charge: {name}")


def _manifest_inventory(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if manifest.get("manifest_version") != "1.0":
        raise BackupError("version de manifeste de sauvegarde incompatible")
    if manifest.get("scope") not in BACKUP_SCOPES:
        raise BackupError("périmètre de sauvegarde invalide")
    if not isinstance(manifest.get("schema_versions"), list) or not all(
        isinstance(version, str) and version for version in manifest["schema_versions"]
    ):
        raise BackupError("versions de schéma absentes ou invalides")
    if manifest.get("restore_automatically_authorized") is not False:
        raise BackupError("le manifeste ne doit jamais autoriser automatiquement une restauration")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise BackupError("inventaire de sauvegarde absent")
    inventory: dict[str, dict[str, Any]] = {}
    for item in files:
        if not isinstance(item, dict):
            raise BackupError("entrée d'inventaire invalide")
        name = item.get("name")
        size = item.get("size_bytes")
        digest = item.get("sha256")
        if (
            not isinstance(name, str)
            or not name
            or PurePosixPath(name).name != name
            or "\\" in name
        ):
            raise BackupError("nom de fichier invalide dans le manifeste")
        if name in inventory:
            raise BackupError(f"fichier dupliqué dans le manifeste: {name}")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise BackupError(f"taille invalide dans le manifeste: {name}")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise BackupError(f"empreinte invalide dans le manifeste: {name}")
        inventory[name] = item
    return inventory


def prevalidate_backup_bundle(
    bundle: Path,
    *,
    max_entries: int = MAX_BACKUP_ENTRIES,
    max_uncompressed_bytes: int = MAX_BACKUP_UNCOMPRESSED_BYTES,
) -> dict[str, Any]:
    if max_entries < 2 or max_uncompressed_bytes < 1:
        raise BackupError("limites de prévalidation invalides")
    if bundle.is_symlink() or not bundle.is_file():
        raise BackupError("archive de sauvegarde introuvable ou non régulière")
    try:
        with zipfile.ZipFile(bundle, "r") as archive:
            entries = archive.infolist()
            if len(entries) > max_entries:
                raise BackupError("la sauvegarde contient trop d'entrées")
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)):
                raise BackupError("la sauvegarde contient des entrées dupliquées")
            total_size = 0
            for entry in entries:
                _validate_archive_member(entry)
                total_size += entry.file_size
                if total_size > max_uncompressed_bytes:
                    raise BackupError("la sauvegarde dépasse la taille décompressée autorisée")
            by_name = {entry.filename: entry for entry in entries}
            manifest_info = by_name.get("manifest.json")
            if manifest_info is None or manifest_info.file_size > MAX_BACKUP_MANIFEST_BYTES:
                raise BackupError("manifeste absent ou trop volumineux")
            try:
                manifest = json.loads(archive.read(manifest_info).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise BackupError("manifeste JSON invalide") from exc
            if not isinstance(manifest, dict):
                raise BackupError("le manifeste doit être un objet JSON")
            inventory = _manifest_inventory(manifest)
            expected_entries = {f"data/{name}" for name in inventory}
            actual_entries = set(by_name) - {"manifest.json"}
            if actual_entries != expected_entries:
                missing = sorted(expected_entries - actual_entries)
                unexpected = sorted(actual_entries - expected_entries)
                raise BackupError(
                    f"inventaire incohérent: absentes={missing[:10]}, inattendues={unexpected[:10]}"
                )
            validated_bytes = 0
            for name, item in inventory.items():
                info = by_name[f"data/{name}"]
                if info.file_size != item["size_bytes"]:
                    raise BackupError(f"taille incohérente pour {name}")
                digest = hashlib.sha256()
                observed_size = 0
                with archive.open(info, "r") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        observed_size += len(chunk)
                        validated_bytes += len(chunk)
                        if observed_size > item["size_bytes"] or validated_bytes > max_uncompressed_bytes:
                            raise BackupError("flux décompressé supérieur aux limites déclarées")
                        digest.update(chunk)
                if observed_size != item["size_bytes"] or digest.hexdigest() != item["sha256"]:
                    raise BackupError(f"empreinte incohérente pour {name}")
    except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError) as exc:
        raise BackupError("archive ZIP de sauvegarde invalide") from exc
    return {
        "status": "prevalidated",
        "bundle_sha256": file_sha256(bundle),
        "manifest": manifest,
        "file_count": len(inventory),
        "uncompressed_size_bytes": total_size,
        "restore_automatically_authorized": False,
        "restore_executed": False,
    }

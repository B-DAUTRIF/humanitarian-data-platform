from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse


class BackupError(ValueError):
    pass


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

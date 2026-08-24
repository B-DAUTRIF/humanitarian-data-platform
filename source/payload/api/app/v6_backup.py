from __future__ import annotations

import hashlib
import json
import os
import secrets
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
GLOBAL_DUMP_NAME = "postgresql-global.dump"
TEMPORARY_RESTORE_DATABASE_PREFIX = "hdp_restore_"


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


def _postgres_client_options(database_url: str) -> tuple[Any, list[str], dict[str, str]]:
    parsed = urlparse(database_url)
    if (
        parsed.scheme not in {"postgres", "postgresql"}
        or not parsed.hostname
        or not parsed.path.strip("/")
        or not parsed.username
    ):
        raise BackupError("DATABASE_URL PostgreSQL invalide")
    options = [
        "--host", parsed.hostname,
        "--port", str(parsed.port or 5432),
        "--username", unquote(parsed.username),
    ]
    environment = {
        **os.environ,
        "PGPASSWORD": unquote(parsed.password or ""),
        "PGCONNECT_TIMEOUT": "15",
    }
    return parsed, options, environment


def _run_postgres_client(
    command: list[str],
    environment: dict[str, str],
    *,
    operation: str,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BackupError(f"{operation} impossible") from exc
    if result.returncode != 0:
        detail = result.stderr.strip()[-2000:] or f"code {result.returncode}"
        raise BackupError(f"{operation} a échoué: {detail}")
    return result


def _copy_verified_global_dump(
    bundle: Path,
    destination: Path,
    *,
    expected_size: int,
    expected_sha256: str,
) -> None:
    digest = hashlib.sha256()
    observed_size = 0
    try:
        with zipfile.ZipFile(bundle, "r") as archive:
            info = archive.getinfo(f"data/{GLOBAL_DUMP_NAME}")
            with archive.open(info, "r") as source, destination.open("xb") as target:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    observed_size += len(chunk)
                    if observed_size > expected_size:
                        raise BackupError("le dump PostgreSQL dépasse sa taille déclarée")
                    digest.update(chunk)
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
    except (KeyError, OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        destination.unlink(missing_ok=True)
        raise BackupError("extraction confinée du dump PostgreSQL impossible") from exc
    if observed_size != expected_size or digest.hexdigest() != expected_sha256:
        destination.unlink(missing_ok=True)
        raise BackupError("le dump PostgreSQL a changé après prévalidation")
    os.chmod(destination, 0o600)


def restore_global_backup_to_temporary_database(
    bundle: Path,
    database_url: str,
    *,
    expected_application_version: str,
    expected_schema_versions: list[str],
    timeout_seconds: int = 1800,
) -> dict[str, Any]:
    if timeout_seconds < 30 or timeout_seconds > 7200:
        raise BackupError("délai de restauration temporaire invalide")
    validation = prevalidate_backup_bundle(bundle)
    manifest = validation["manifest"]
    if manifest.get("scope") != "global":
        raise BackupError("seule une sauvegarde globale peut être restaurée dans une base temporaire")
    if manifest.get("application_version") != expected_application_version:
        raise BackupError("version applicative de la sauvegarde incompatible")
    if manifest.get("schema_versions") != expected_schema_versions:
        raise BackupError("versions de schéma de la sauvegarde incompatibles")
    inventory = _manifest_inventory(manifest)
    if set(inventory) != {GLOBAL_DUMP_NAME}:
        raise BackupError("inventaire global inattendu")

    parsed, options, environment = _postgres_client_options(database_url)
    source_database = unquote(parsed.path.strip("/"))
    temporary_database = f"{TEMPORARY_RESTORE_DATABASE_PREFIX}{secrets.token_hex(8)}"
    created = False
    operation_error: BackupError | None = None
    drop_error: BackupError | None = None
    restored_versions: list[str] = []
    table_count = 0

    with tempfile.TemporaryDirectory(prefix=".hdp-restore-", dir=bundle.parent) as temporary_name:
        dump = Path(temporary_name) / GLOBAL_DUMP_NAME
        item = inventory[GLOBAL_DUMP_NAME]
        _copy_verified_global_dump(
            bundle,
            dump,
            expected_size=item["size_bytes"],
            expected_sha256=item["sha256"],
        )
        if file_sha256(bundle) != validation["bundle_sha256"]:
            raise BackupError("le bundle a changé après prévalidation")
        try:
            _run_postgres_client(
                [
                    "createdb",
                    *options,
                    "--maintenance-db", source_database,
                    temporary_database,
                ],
                environment,
                operation="création de la base temporaire (collision ou droits insuffisants)",
                timeout_seconds=60,
            )
            created = True
            _run_postgres_client(
                [
                    "pg_restore",
                    *options,
                    "--dbname", temporary_database,
                    "--exit-on-error",
                    "--single-transaction",
                    "--no-owner",
                    "--no-privileges",
                    str(dump),
                ],
                environment,
                operation="restauration transactionnelle temporaire",
                timeout_seconds=timeout_seconds,
            )
            versions_result = _run_postgres_client(
                [
                    "psql",
                    *options,
                    "--dbname", temporary_database,
                    "--no-psqlrc",
                    "--tuples-only",
                    "--no-align",
                    "--command", "SELECT version FROM schema_migrations ORDER BY version",
                ],
                environment,
                operation="vérification des migrations restaurées",
                timeout_seconds=60,
            )
            restored_versions = [line for line in versions_result.stdout.splitlines() if line]
            if restored_versions != expected_schema_versions:
                raise BackupError("les migrations restaurées ne correspondent pas au manifeste")
            tables_result = _run_postgres_client(
                [
                    "psql",
                    *options,
                    "--dbname", temporary_database,
                    "--no-psqlrc",
                    "--tuples-only",
                    "--no-align",
                    "--command",
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'",
                ],
                environment,
                operation="vérification des tables restaurées",
                timeout_seconds=60,
            )
            try:
                table_count = int(tables_result.stdout.strip())
            except ValueError as exc:
                raise BackupError("comptage des tables restaurées invalide") from exc
            if table_count < 1:
                raise BackupError("aucune table restaurée")
        except BackupError as exc:
            operation_error = exc
        finally:
            if created:
                try:
                    _run_postgres_client(
                        [
                            "dropdb",
                            *options,
                            "--maintenance-db", source_database,
                            "--if-exists",
                            "--force",
                            temporary_database,
                        ],
                        environment,
                        operation="suppression de la base temporaire",
                        timeout_seconds=60,
                    )
                except BackupError as exc:
                    drop_error = exc

    if operation_error is not None:
        if drop_error is not None:
            raise BackupError(f"{operation_error}; {drop_error}") from operation_error
        raise operation_error
    if drop_error is not None:
        raise drop_error
    return {
        "status": "temporary_restore_verified",
        "bundle_sha256": validation["bundle_sha256"],
        "scope": "global",
        "application_version": expected_application_version,
        "schema_version_count": len(restored_versions),
        "restored_table_count": table_count,
        "restore_executed": True,
        "temporary_database_dropped": True,
        "collision_policy": "reject_without_overwrite",
        "restore_automatically_authorized": False,
    }

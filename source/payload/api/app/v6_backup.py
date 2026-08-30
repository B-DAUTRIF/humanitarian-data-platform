from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import unquote, urlparse, urlunparse

import psycopg
from psycopg import sql


class BackupError(ValueError):
    pass


MAX_BACKUP_ENTRIES = 10_000
MAX_BACKUP_UNCOMPRESSED_BYTES = 50 * 1024 * 1024 * 1024
MAX_BACKUP_MANIFEST_BYTES = 4 * 1024 * 1024
BACKUP_SCOPES = {"global", "project", "signals"}
GLOBAL_DUMP_NAME = "postgresql-global.dump"
TEMPORARY_RESTORE_DATABASE_PREFIX = "hdp_restore_"
MAX_BACKUP_JSONL_LINE_BYTES = 16 * 1024 * 1024
SIGNALS_RESTORE_CORE_TABLES = {
    "projects",
    "signal_events",
    "signal_rules",
    "signal_actions",
    "rule_definitions",
    "rule_versions",
    "rule_evaluations",
    "action_requests",
    "action_executions",
}
SIGNALS_RESTORE_ACTION_WORKER_TABLES = {
    "internal_notifications",
    "project_tasks",
    "signal_classifications",
    "action_drafts",
    "automated_data_jobs",
}
SIGNALS_RESTORE_TABLES = SIGNALS_RESTORE_CORE_TABLES | SIGNALS_RESTORE_ACTION_WORKER_TABLES
ACTION_WORKER_SCHEMA_VERSION = "6.0.0-011-action-workers"
SENSITIVE_FIELD_MARKERS = (
    "authorization",
    "cookie",
    "credential",
    "password",
    "secret",
    "token",
)
PROJECT_BACKUP_EXCLUDED_TABLES = {
    "database_backups",
    "operator_auth_challenges",
    "operator_sessions",
    "operator_webauthn_credentials",
    "schema_migrations",
}
PROJECT_FILE_COLUMNS = {
    "acquisitions": "raw_path",
    "cache_entries": "storage_path",
    "data_artifacts": "path",
    "local_resources": "local_path",
    "mail_attachments": "storage_path",
    "script_executions": "report_path",
}


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


def select_signal_backup_events(
    connection: psycopg.Connection[Any],
    *,
    project_id: Any | None,
    signal_ids: list[Any],
    signal_from: datetime | None,
    signal_to: datetime | None,
) -> tuple[list[Any], list[Any]]:
    """Resolve a signal backup selector in one repeatable-read transaction.

    The time window is half-open: ``signal_from`` is included and ``signal_to``
    is excluded.  Query fragments are fixed constants; selector values remain
    PostgreSQL parameters.
    """
    rows = connection.execute(
        """SELECT id,project_id FROM signal_events
           WHERE (%s::uuid IS NULL OR project_id=%s::uuid)
             AND (NOT %s OR id=ANY(%s::uuid[]))
             AND (%s::timestamptz IS NULL OR occurred_at>=%s::timestamptz)
             AND (%s::timestamptz IS NULL OR occurred_at<%s::timestamptz)
           ORDER BY occurred_at,id""",
        (
            project_id,
            project_id,
            bool(signal_ids),
            signal_ids,
            signal_from,
            signal_from,
            signal_to,
            signal_to,
        ),
    ).fetchall()
    selected_signal_ids = [row[0] for row in rows]
    selected_project_ids = sorted({row[1] for row in rows}, key=str)
    return selected_signal_ids, selected_project_ids


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


def _foreign_key_graph(
    connection: Any,
) -> list[tuple[str, str, list[str], list[str]]]:
    rows = connection.execute(
        """SELECT child.relname,parent.relname,
                  array_agg(child_attribute.attname ORDER BY keys.ordinality),
                  array_agg(parent_attribute.attname ORDER BY keys.ordinality)
           FROM pg_constraint constraint_definition
           JOIN pg_class child ON child.oid=constraint_definition.conrelid
           JOIN pg_namespace child_namespace ON child_namespace.oid=child.relnamespace
           JOIN pg_class parent ON parent.oid=constraint_definition.confrelid
           JOIN pg_namespace parent_namespace ON parent_namespace.oid=parent.relnamespace
           JOIN LATERAL unnest(constraint_definition.conkey,constraint_definition.confkey)
                WITH ORDINALITY AS keys(child_number,parent_number,ordinality) ON TRUE
           JOIN pg_attribute child_attribute
                ON child_attribute.attrelid=child.oid AND child_attribute.attnum=keys.child_number
           JOIN pg_attribute parent_attribute
                ON parent_attribute.attrelid=parent.oid AND parent_attribute.attnum=keys.parent_number
           WHERE constraint_definition.contype='f'
             AND child_namespace.nspname='public' AND parent_namespace.nspname='public'
           GROUP BY constraint_definition.oid,child.relname,parent.relname
           ORDER BY child.relname,parent.relname"""
    ).fetchall()
    return [
        (str(child), str(parent), [str(item) for item in child_columns], [str(item) for item in parent_columns])
        for child, parent, child_columns, parent_columns in rows
    ]


def _selection_insert(
    connection: Any,
    query: Any,
    parameters: tuple[Any, ...],
) -> int:
    cursor = connection.execute(query, parameters)
    return max(cursor.rowcount, 0)


def _confined_project_asset(data_directory: Path, reference: str) -> Path:
    root = data_directory.resolve()
    raw = Path(reference)
    current = raw if raw.is_absolute() else root / raw
    parts = current.parts
    probe = Path(parts[0]) if current.is_absolute() else root
    for part in parts[1:] if current.is_absolute() else parts:
        probe = probe / part
        if probe.is_symlink():
            raise BackupError(f"lien symbolique interdit pour le fichier projet: {reference}")
    candidate = current.resolve()
    if candidate != root and root not in candidate.parents:
        raise BackupError(f"fichier projet hors du répertoire de données: {reference}")
    if not candidate.is_file():
        raise BackupError(f"fichier projet absent ou non régulier: {reference}")
    return candidate


def export_project_graph(
    connection: Any,
    directory: Path,
    project_id: Any,
    data_directory: Path,
) -> tuple[list[Path], dict[str, int], list[dict[str, Any]]]:
    connection.execute(
        """CREATE TEMP TABLE hdp_project_backup_selection (
               table_name TEXT NOT NULL,
               row_ctid TID NOT NULL,
               owned BOOLEAN NOT NULL,
               PRIMARY KEY (table_name,row_ctid)
           ) ON COMMIT DROP"""
    )
    project_tables = {
        str(row[0])
        for row in connection.execute(
            """SELECT columns.table_name
               FROM information_schema.columns columns
               JOIN information_schema.tables tables
                 ON tables.table_schema=columns.table_schema AND tables.table_name=columns.table_name
               WHERE columns.table_schema='public' AND columns.column_name='project_id'
                 AND tables.table_type='BASE TABLE'"""
        ).fetchall()
    }
    project_tables.difference_update(PROJECT_BACKUP_EXCLUDED_TABLES)
    _selection_insert(
        connection,
        """INSERT INTO hdp_project_backup_selection(table_name,row_ctid,owned)
           SELECT 'projects',ctid,TRUE FROM projects WHERE id=%s ON CONFLICT DO NOTHING""",
        (project_id,),
    )
    for table in sorted(project_tables):
        _selection_insert(
            connection,
            sql.SQL(
                "INSERT INTO hdp_project_backup_selection(table_name,row_ctid,owned) "
                "SELECT %s,ctid,TRUE FROM {} WHERE project_id=%s ON CONFLICT DO NOTHING"
            ).format(sql.Identifier("public", table)),
            (table, project_id),
        )

    graph = [
        edge
        for edge in _foreign_key_graph(connection)
        if edge[0] not in PROJECT_BACKUP_EXCLUDED_TABLES
        and edge[1] not in PROJECT_BACKUP_EXCLUDED_TABLES
    ]
    for _ in range(100):
        changed = 0
        for child, parent, child_columns, parent_columns in graph:
            join = sql.SQL(" AND ").join(
                sql.SQL("child.{}=parent.{}").format(
                    sql.Identifier(child_column), sql.Identifier(parent_column)
                )
                for child_column, parent_column in zip(child_columns, parent_columns, strict=True)
            )
            changed += _selection_insert(
                connection,
                sql.SQL(
                    "INSERT INTO hdp_project_backup_selection(table_name,row_ctid,owned) "
                    "SELECT %s,parent.ctid,FALSE FROM {} parent JOIN {} child ON {} "
                    "JOIN hdp_project_backup_selection selected "
                    "ON selected.table_name=%s AND selected.row_ctid=child.ctid "
                    "ON CONFLICT DO NOTHING"
                ).format(
                    sql.Identifier("public", parent),
                    sql.Identifier("public", child),
                    join,
                ),
                (parent, child),
            )
            if child not in project_tables:
                changed += _selection_insert(
                    connection,
                    sql.SQL(
                        "INSERT INTO hdp_project_backup_selection(table_name,row_ctid,owned) "
                        "SELECT %s,child.ctid,TRUE FROM {} child JOIN {} parent ON {} "
                        "JOIN hdp_project_backup_selection selected "
                        "ON selected.table_name=%s AND selected.row_ctid=parent.ctid AND selected.owned "
                        "ON CONFLICT (table_name,row_ctid) DO UPDATE SET owned=TRUE "
                        "WHERE NOT hdp_project_backup_selection.owned"
                    ).format(
                        sql.Identifier("public", child),
                        sql.Identifier("public", parent),
                        join,
                    ),
                    (child, parent),
                )
        if changed == 0:
            break
    else:
        raise BackupError("fermeture des dépendances projet non convergente")

    for table in sorted(project_tables):
        foreign_row = connection.execute(
            sql.SQL(
                "SELECT 1 FROM {} value JOIN hdp_project_backup_selection selected "
                "ON selected.table_name=%s AND selected.row_ctid=value.ctid "
                "WHERE value.project_id<>%s LIMIT 1"
            ).format(sql.Identifier("public", table)),
            (table, project_id),
        ).fetchone()
        if foreign_row:
            raise BackupError(f"dépendance d'un autre projet détectée: {table}")

    selected_tables = [
        str(row[0])
        for row in connection.execute(
            """SELECT table_name FROM hdp_project_backup_selection
               GROUP BY table_name ORDER BY table_name"""
        ).fetchall()
    ]
    files: list[Path] = []
    row_counts: dict[str, int] = {}
    for table in selected_tables:
        destination = directory / f"{table}.jsonl"
        count = export_query_as_jsonl(
            connection,
            destination,
            sql.SQL(
                "SELECT value.* FROM {} value JOIN hdp_project_backup_selection selected "
                "ON selected.table_name=%s AND selected.row_ctid=value.ctid"
            ).format(sql.Identifier("public", table)),
            (table,),
        )
        files.append(destination)
        row_counts[table] = count

    assets_by_digest: dict[str, dict[str, Any]] = {}
    for table, column in PROJECT_FILE_COLUMNS.items():
        if table not in selected_tables:
            continue
        references = connection.execute(
            sql.SQL(
                "SELECT DISTINCT value.{} FROM {} value "
                "JOIN hdp_project_backup_selection selected "
                "ON selected.table_name=%s AND selected.row_ctid=value.ctid "
                "WHERE value.{} IS NOT NULL AND value.{}<>''"
            ).format(
                sql.Identifier(column),
                sql.Identifier("public", table),
                sql.Identifier(column),
                sql.Identifier(column),
            ),
            (table,),
        ).fetchall()
        for (reference_value,) in references:
            reference = str(reference_value)
            source = _confined_project_asset(data_directory, reference)
            digest = file_sha256(source)
            asset = assets_by_digest.setdefault(
                digest,
                {
                    "archive_name": f"asset-{digest}",
                    "sha256": digest,
                    "size_bytes": source.stat().st_size,
                    "source": source,
                    "references": [],
                },
            )
            asset["references"].append(
                {"table": table, "column": column, "stored_path": reference}
            )
    project_assets: list[dict[str, Any]] = []
    for digest, asset in sorted(assets_by_digest.items()):
        destination = directory / asset["archive_name"]
        with asset["source"].open("rb") as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        os.chmod(destination, 0o600)
        if file_sha256(destination) != digest:
            raise BackupError("copie d'un fichier projet incohérente")
        files.append(destination)
        project_assets.append(
            {key: value for key, value in asset.items() if key != "source"}
        )
    return files, row_counts, project_assets


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


def _contains_sensitive_field(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            (
                any(marker in str(key).casefold() for marker in SENSITIVE_FIELD_MARKERS)
                and not str(key).casefold().endswith("_sha256")
            )
            or _contains_sensitive_field(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_sensitive_field(item) for item in value)
    return False


def _jsonl_restore_inventory(
    manifest: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    inventory = _manifest_inventory(manifest)
    row_counts = manifest.get("row_counts")
    if not isinstance(row_counts, dict):
        raise BackupError("comptages de lignes absents du manifeste")
    tables: dict[str, dict[str, Any]] = {}
    other_files: dict[str, dict[str, Any]] = {}
    for name, item in inventory.items():
        if not name.endswith(".jsonl"):
            other_files[name] = item
            continue
        stem = name.removesuffix(".jsonl")
        table = stem.removeprefix("related-")
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", table):
            raise BackupError(f"nom de table de restauration invalide: {table}")
        if table in tables:
            raise BackupError(f"table de restauration dupliquée: {table}")
        declared_rows = row_counts.get(stem)
        if not isinstance(declared_rows, int) or isinstance(declared_rows, bool) or declared_rows < 0:
            raise BackupError(f"comptage de lignes invalide: {stem}")
        tables[table] = {
            "member": f"data/{name}",
            "declared_rows": declared_rows,
            "inventory": item,
        }
    return tables, other_files


def _scoped_restore_inventory(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tables, other_files = _jsonl_restore_inventory(manifest)
    if other_files:
        raise BackupError(f"fichiers inattendus dans le bundle signaux: {sorted(other_files)}")
    required = set(SIGNALS_RESTORE_CORE_TABLES)
    if ACTION_WORKER_SCHEMA_VERSION in manifest["schema_versions"]:
        required.update(SIGNALS_RESTORE_ACTION_WORKER_TABLES)
    missing = sorted(required - set(tables))
    unexpected = sorted(set(tables) - SIGNALS_RESTORE_TABLES)
    if missing or unexpected:
        raise BackupError(
            f"inventaire signaux incomplet: absentes={missing}, inattendues={unexpected}"
        )
    return tables


def _project_restore_inventory(
    manifest: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    tables, other_files = _jsonl_restore_inventory(manifest)
    if "projects" not in tables or tables["projects"]["declared_rows"] != 1:
        raise BackupError("le bundle projet doit contenir exactement un projet")
    assets = manifest.get("project_assets")
    if not isinstance(assets, list):
        raise BackupError("inventaire des fichiers projet absent")
    validated_assets: list[dict[str, Any]] = []
    expected_asset_names: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            raise BackupError("entrée de fichier projet invalide")
        archive_name = asset.get("archive_name")
        digest = asset.get("sha256")
        size = asset.get("size_bytes")
        references = asset.get("references")
        if (
            not isinstance(archive_name, str)
            or not re.fullmatch(r"asset-[0-9a-f]{64}", archive_name)
            or not isinstance(digest, str)
            or archive_name != f"asset-{digest}"
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or not isinstance(references, list)
            or not references
        ):
            raise BackupError("métadonnées de fichier projet invalides")
        inventory_item = other_files.get(archive_name)
        if (
            inventory_item is None
            or inventory_item["sha256"] != digest
            or inventory_item["size_bytes"] != size
            or archive_name in expected_asset_names
        ):
            raise BackupError("inventaire de fichier projet incohérent")
        for reference in references:
            if (
                not isinstance(reference, dict)
                or set(reference) != {"table", "column", "stored_path"}
                or reference.get("table") not in tables
                or PROJECT_FILE_COLUMNS.get(str(reference.get("table"))) != reference.get("column")
                or not isinstance(reference.get("stored_path"), str)
                or not reference["stored_path"]
            ):
                raise BackupError("référence de fichier projet invalide")
        expected_asset_names.add(archive_name)
        validated_assets.append(asset)
    if set(other_files) != expected_asset_names:
        raise BackupError("fichiers projet inattendus ou absents")
    return tables, validated_assets


def _validate_project_asset_references(
    bundle: Path,
    tables: dict[str, dict[str, Any]],
    assets: list[dict[str, Any]],
) -> None:
    declared = {
        (str(reference["table"]), str(reference["column"]), str(reference["stored_path"]))
        for asset in assets
        for reference in asset["references"]
    }
    observed: set[tuple[str, str, str]] = set()
    try:
        with zipfile.ZipFile(bundle, "r") as archive:
            for table, column in PROJECT_FILE_COLUMNS.items():
                if table not in tables:
                    continue
                with archive.open(tables[table]["member"], "r") as stream:
                    while True:
                        raw_line = stream.readline(MAX_BACKUP_JSONL_LINE_BYTES + 1)
                        if not raw_line:
                            break
                        if len(raw_line) > MAX_BACKUP_JSONL_LINE_BYTES:
                            raise BackupError(f"ligne JSONL trop volumineuse: {table}")
                        try:
                            document = json.loads(raw_line.decode("utf-8"))
                        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                            raise BackupError(f"ligne JSONL invalide: {table}") from exc
                        reference = document.get(column) if isinstance(document, dict) else None
                        if reference is not None and str(reference):
                            observed.add((table, column, str(reference)))
    except (KeyError, OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise BackupError("vérification des références de fichiers projet impossible") from exc
    if observed != declared:
        missing = sorted(observed - declared)
        unexpected = sorted(declared - observed)
        raise BackupError(
            f"références de fichiers projet incohérentes: absentes={missing[:10]}, inattendues={unexpected[:10]}"
        )


def _temporary_database_url(parsed: Any, database: str) -> str:
    return urlunparse(parsed._replace(path=f"/{database}"))


def _schema_dump(
    database_url: str,
    destination: Path,
    *,
    timeout_seconds: int,
) -> None:
    parsed, options, environment = _postgres_client_options(database_url)
    source_database = unquote(parsed.path.strip("/"))
    _run_postgres_client(
        [
            "pg_dump",
            *options,
            "--dbname", source_database,
            "--format=custom",
            "--schema-only",
            "--no-owner",
            "--no-privileges",
            "--file", str(destination),
        ],
        environment,
        operation="export du schéma PostgreSQL courant",
        timeout_seconds=timeout_seconds,
    )
    if not destination.is_file() or destination.stat().st_size == 0:
        raise BackupError("l'export du schéma PostgreSQL est vide")
    os.chmod(destination, 0o600)


def _dependency_order(
    connection: psycopg.Connection[Any],
    tables: set[str],
) -> list[str]:
    rows = connection.execute(
        """SELECT child.relname,parent.relname
           FROM pg_constraint constraint_definition
           JOIN pg_class child ON child.oid=constraint_definition.conrelid
           JOIN pg_namespace child_namespace ON child_namespace.oid=child.relnamespace
           JOIN pg_class parent ON parent.oid=constraint_definition.confrelid
           JOIN pg_namespace parent_namespace ON parent_namespace.oid=parent.relnamespace
           WHERE constraint_definition.contype='f'
             AND child_namespace.nspname='public' AND parent_namespace.nspname='public'"""
    ).fetchall()
    parents: dict[str, set[str]] = {table: set() for table in tables}
    for child, parent in rows:
        if str(child) in tables and str(parent) in tables:
            parents[str(child)].add(str(parent))
    pending = set(tables)
    ordered: list[str] = []
    while pending:
        ready = sorted(table for table in pending if not (parents[table] & pending))
        if not ready:
            raise BackupError("cycle de dépendances entre tables du bundle")
        ordered.extend(ready)
        pending.difference_update(ready)
    return ordered


def _import_jsonl_tables(
    bundle: Path,
    database_url: str,
    tables: dict[str, dict[str, Any]],
) -> tuple[int, dict[str, int]]:
    restored_counts: dict[str, int] = {}
    try:
        with zipfile.ZipFile(bundle, "r") as archive, psycopg.connect(
            database_url, autocommit=False
        ) as connection:
            ordered = _dependency_order(connection, set(tables))
            for table in ordered:
                columns = [
                    str(row[0])
                    for row in connection.execute(
                        """SELECT column_name FROM information_schema.columns
                           WHERE table_schema='public' AND table_name=%s
                           ORDER BY ordinal_position""",
                        (table,),
                    ).fetchall()
                ]
                if not columns:
                    raise BackupError(f"table absente du schéma courant: {table}")
                expected_columns = set(columns)
                restored = 0
                with archive.open(tables[table]["member"], "r") as stream:
                    while True:
                        raw_line = stream.readline(MAX_BACKUP_JSONL_LINE_BYTES + 1)
                        if not raw_line:
                            break
                        if len(raw_line) > MAX_BACKUP_JSONL_LINE_BYTES:
                            raise BackupError(f"ligne JSONL trop volumineuse: {table}")
                        try:
                            document = json.loads(raw_line.decode("utf-8"))
                        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                            raise BackupError(f"ligne JSONL invalide: {table}") from exc
                        if not isinstance(document, dict) or set(document) != expected_columns:
                            raise BackupError(f"colonnes JSONL incompatibles: {table}")
                        if _contains_sensitive_field(document):
                            raise BackupError(f"champ sensible interdit dans le bundle: {table}")
                        connection.execute(
                            sql.SQL(
                                "INSERT INTO {} SELECT * FROM json_populate_record(NULL::{}, %s::json)"
                            ).format(
                                sql.Identifier("public", table),
                                sql.Identifier("public", table),
                            ),
                            (json.dumps(document, ensure_ascii=False, separators=(",", ":")),),
                        )
                        restored += 1
                if restored != tables[table]["declared_rows"]:
                    raise BackupError(f"comptage restauré incohérent: {table}")
                observed = connection.execute(
                    sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier("public", table))
                ).fetchone()
                if observed is None or int(observed[0]) != restored:
                    raise BackupError(f"collision ou lignes inattendues dans la table: {table}")
                restored_counts[table] = restored
            connection.commit()
    except BackupError:
        raise
    except psycopg.errors.UniqueViolation as exc:
        raise BackupError("collision d'identifiant refusée sans écrasement") from exc
    except (KeyError, OSError, zipfile.BadZipFile, zipfile.LargeZipFile, psycopg.Error) as exc:
        raise BackupError("import transactionnel du bundle signaux impossible") from exc
    return sum(restored_counts.values()), restored_counts


def restore_signals_backup_to_temporary_database(
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
    if manifest.get("scope") != "signals":
        raise BackupError("ce chemin exige une sauvegarde de signaux")
    if manifest.get("application_version") != expected_application_version:
        raise BackupError("version applicative de la sauvegarde incompatible")
    if manifest.get("schema_versions") != expected_schema_versions:
        raise BackupError("versions de schéma de la sauvegarde incompatibles")
    tables = _scoped_restore_inventory(manifest)
    parsed, options, environment = _postgres_client_options(database_url)
    source_database = unquote(parsed.path.strip("/"))
    temporary_database = f"{TEMPORARY_RESTORE_DATABASE_PREFIX}{secrets.token_hex(8)}"
    created = False
    operation_error: BackupError | None = None
    drop_error: BackupError | None = None
    restored_rows = 0
    restored_counts: dict[str, int] = {}

    with tempfile.TemporaryDirectory(prefix=".hdp-signals-restore-", dir=bundle.parent) as temporary_name:
        schema_dump = Path(temporary_name) / "postgresql-schema.dump"
        _schema_dump(database_url, schema_dump, timeout_seconds=min(timeout_seconds, 600))
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
                    str(schema_dump),
                ],
                environment,
                operation="restauration transactionnelle du schéma temporaire",
                timeout_seconds=timeout_seconds,
            )
            restored_rows, restored_counts = _import_jsonl_tables(
                bundle,
                _temporary_database_url(parsed, temporary_database),
                tables,
            )
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
        "scope": "signals",
        "application_version": expected_application_version,
        "schema_version_count": len(expected_schema_versions),
        "restored_table_count": len(restored_counts),
        "restored_row_count": restored_rows,
        "restore_executed": True,
        "temporary_database_dropped": True,
        "collision_policy": "reject_without_overwrite",
        "restore_automatically_authorized": False,
    }


def restore_project_backup_to_temporary_database(
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
    if manifest.get("scope") != "project":
        raise BackupError("ce chemin exige une sauvegarde de projet")
    if manifest.get("application_version") != expected_application_version:
        raise BackupError("version applicative de la sauvegarde incompatible")
    if manifest.get("schema_versions") != expected_schema_versions:
        raise BackupError("versions de schéma de la sauvegarde incompatibles")
    tables, assets = _project_restore_inventory(manifest)
    _validate_project_asset_references(bundle, tables, assets)
    parsed, options, environment = _postgres_client_options(database_url)
    source_database = unquote(parsed.path.strip("/"))
    temporary_database = f"{TEMPORARY_RESTORE_DATABASE_PREFIX}{secrets.token_hex(8)}"
    created = False
    operation_error: BackupError | None = None
    drop_error: BackupError | None = None
    restored_rows = 0
    restored_counts: dict[str, int] = {}

    with tempfile.TemporaryDirectory(prefix=".hdp-project-restore-", dir=bundle.parent) as temporary_name:
        schema_dump = Path(temporary_name) / "postgresql-schema.dump"
        _schema_dump(database_url, schema_dump, timeout_seconds=min(timeout_seconds, 600))
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
                    str(schema_dump),
                ],
                environment,
                operation="restauration transactionnelle du schéma temporaire",
                timeout_seconds=timeout_seconds,
            )
            restored_rows, restored_counts = _import_jsonl_tables(
                bundle,
                _temporary_database_url(parsed, temporary_database),
                tables,
            )
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
        "scope": "project",
        "application_version": expected_application_version,
        "schema_version_count": len(expected_schema_versions),
        "restored_table_count": len(restored_counts),
        "restored_row_count": restored_rows,
        "verified_asset_count": len(assets),
        "verified_asset_size_bytes": sum(int(asset["size_bytes"]) for asset in assets),
        "restore_executed": True,
        "temporary_database_dropped": True,
        "collision_policy": "reject_without_overwrite",
        "restore_automatically_authorized": False,
    }

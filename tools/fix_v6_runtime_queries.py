#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "source" / "payload" / "api" / "app" / "v6_features.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: bloc attendu exactement une fois, trouvé {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")

    rss_old = '''    with db() as connection:\n        rows = connection.execute(\n            """SELECT id,source_key,version_number,name,organization,region,themes,languages,\n                      feed_url,portal_url,evidence_url,protocol,license,declared_frequency,\n                      allowed_hosts,state,created_at,created_by,decided_at,decided_by\n               FROM rss_feed_sources WHERE (%s IS NULL OR state=%s)\n               ORDER BY created_at DESC""",\n            (state, state),\n        ).fetchall()\n'''
    rss_new = '''    statement = """SELECT id,source_key,version_number,name,organization,region,themes,languages,\n                      feed_url,portal_url,evidence_url,protocol,license,declared_frequency,\n                      allowed_hosts,state,created_at,created_by,decided_at,decided_by\n               FROM rss_feed_sources"""\n    parameters: tuple[Any, ...] = ()\n    if state is not None:\n        statement += " WHERE state=%s"\n        parameters = (state,)\n    statement += " ORDER BY created_at DESC"\n    with db() as connection:\n        rows = connection.execute(statement, parameters).fetchall()\n'''
    text = replace_once(text, rss_old, rss_new, "RSS optional-state query")

    backup_old = '''    with db() as connection:\n        rows = connection.execute(\n            """SELECT id,scope,project_id,selector,status,bundle_sha256,size_bytes,manifest,\n                      error,created_at,finished_at,created_by\n               FROM database_backups\n               WHERE (%s IS NULL OR project_id=%s)\n               ORDER BY created_at DESC LIMIT %s""",\n            (project_id, project_id, limit),\n        ).fetchall()\n'''
    backup_new = '''    statement = """SELECT id,scope,project_id,selector,status,bundle_sha256,size_bytes,manifest,\n                      error,created_at,finished_at,created_by\n               FROM database_backups"""\n    parameters: list[Any] = []\n    if project_id is not None:\n        statement += " WHERE project_id=%s"\n        parameters.append(project_id)\n    statement += " ORDER BY created_at DESC LIMIT %s"\n    parameters.append(limit)\n    with db() as connection:\n        rows = connection.execute(statement, tuple(parameters)).fetchall()\n'''
    text = replace_once(text, backup_old, backup_new, "backup optional-project query")

    catalog_old = '''    with db() as connection:\n        rows = connection.execute(\n            """SELECT id,source_id,api_version,endpoint_id,external_id,record_type,title,\n                      normalized_metadata,unmapped_fields,raw_snapshot_id,connector_version,\n                      transformation_version,confidence,observed_at,valid_until\n               FROM catalog_records\n               WHERE (%s IS NULL OR source_id=%s)\n                 AND (%s IS NULL OR record_type=%s)\n                 AND (%s='' OR title ILIKE %s OR normalized_metadata::text ILIKE %s)\n               ORDER BY observed_at DESC LIMIT %s""",\n            (source_id, source_id, record_type, record_type, query, f"%{query}%", f"%{query}%", limit),\n        ).fetchall()\n'''
    catalog_new = '''    statement = """SELECT id,source_id,api_version,endpoint_id,external_id,record_type,title,\n                      normalized_metadata,unmapped_fields,raw_snapshot_id,connector_version,\n                      transformation_version,confidence,observed_at,valid_until\n               FROM catalog_records"""\n    conditions: list[str] = []\n    parameters: list[Any] = []\n    if source_id is not None:\n        conditions.append("source_id=%s")\n        parameters.append(source_id)\n    if record_type is not None:\n        conditions.append("record_type=%s")\n        parameters.append(record_type)\n    if query:\n        pattern = f"%{query}%"\n        conditions.append("(title ILIKE %s OR normalized_metadata::text ILIKE %s)")\n        parameters.extend((pattern, pattern))\n    if conditions:\n        statement += " WHERE " + " AND ".join(conditions)\n    statement += " ORDER BY observed_at DESC LIMIT %s"\n    parameters.append(limit)\n    with db() as connection:\n        rows = connection.execute(statement, tuple(parameters)).fetchall()\n'''
    text = replace_once(text, catalog_old, catalog_new, "catalog optional filters query")

    dev_count = text.count("6.0.0-dev")
    if dev_count != 5:
        raise SystemExit(f"release identity: attendu 5 marqueurs 6.0.0-dev, trouvé {dev_count}")
    text = text.replace("6.0.0-dev", "6.0.0")

    TARGET.write_text(text, encoding="utf-8")
    print("v6_features.py: 3 requêtes optionnelles corrigées; 5 identités dev supprimées")


if __name__ == "__main__":
    main()

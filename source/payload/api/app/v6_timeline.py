from __future__ import annotations

import uuid
from typing import Any


TIMELINE_KEYS = (
    "id",
    "project_id",
    "scope",
    "event_type",
    "object_type",
    "object_id",
    "status",
    "summary",
    "details",
    "actor",
    "occurred_at",
)


GLOBAL_TIMELINE_QUERY = """
WITH combined AS (
    SELECT id,project_id,scope,event_type,object_type,object_id,status,
           summary,details,actor,occurred_at
    FROM application_timeline
    WHERE scope='global' AND project_id IS NULL
    UNION ALL
    SELECT md5('migration:' || m.version)::uuid,NULL::uuid,'global',
           'migration.applied','schema_migration',m.version,'completed',
           'Migration ' || m.version || ' appliquée',
           jsonb_build_object('description',m.description),'system',m.applied_at
    FROM schema_migrations m
    WHERE NOT EXISTS (
        SELECT 1 FROM application_timeline t
        WHERE t.scope='global' AND t.event_type='migration.applied'
          AND t.object_id=m.version
    )
    UNION ALL
    SELECT v.id,NULL::uuid,'global','connector.contract_imported',
           'source_api_version',v.id::text,'completed',
           'Contrat ' || v.source_id || ' ' || v.api_version || ' importé',
           jsonb_build_object(
               'source_id',v.source_id,'api_version',v.api_version,
               'documentation_sha256',v.documentation_sha256,
               'valid_from',v.valid_from,'valid_until',v.valid_until
           ),'system',v.verified_at
    FROM source_api_versions v
    WHERE NOT EXISTS (
        SELECT 1 FROM application_timeline t
        WHERE t.scope='global' AND t.event_type='connector.contract_imported'
          AND t.object_id=v.id::text
    )
    UNION ALL
    SELECT h.id,NULL::uuid,'global','connector.endpoint_state','source_endpoint',
           h.endpoint_id::text,'completed',
           'Endpoint ' || e.endpoint_id || ' : ' || h.previous_state || ' → ' || h.new_state,
           jsonb_build_object(
               'source_id',v.source_id,'previous_state',h.previous_state,
               'new_state',h.new_state,'evidence',h.evidence
           ),h.actor,h.occurred_at
    FROM endpoint_activation_history h
    JOIN source_endpoints e ON e.id=h.endpoint_id
    JOIN source_api_versions v ON v.id=e.api_version_id
    WHERE NOT EXISTS (
        SELECT 1 FROM application_timeline t
        WHERE t.scope='global' AND t.event_type='connector.endpoint_state'
          AND t.object_id=h.endpoint_id::text AND t.occurred_at=h.occurred_at
    )
)
SELECT id,project_id,scope,event_type,object_type,object_id,status,
       summary,details,actor,occurred_at
FROM combined
WHERE (%s::text IS NULL OR event_type=%s::text)
ORDER BY occurred_at DESC,id DESC LIMIT %s
"""


PROJECT_TIMELINE_QUERY = """
WITH combined AS (
    SELECT id,project_id,scope,event_type,object_type,object_id,status,
           summary,details,actor,occurred_at
    FROM application_timeline
    WHERE scope='project' AND project_id=%s
    UNION ALL
    SELECT s.id,s.project_id,'project','search.federated','federated_search',
           s.id::text,s.status,'Recherche fédérée : ' || s.query,
           jsonb_build_object('sources',s.sources,'criteria',s.criteria),
           'local-operator',s.started_at
    FROM federated_searches s
    WHERE s.project_id=%s AND NOT EXISTS (
        SELECT 1 FROM application_timeline t
        WHERE t.scope='project' AND t.project_id=s.project_id
          AND t.object_type='federated_search' AND t.object_id=s.id::text
    )
    UNION ALL
    SELECT a.id,a.project_id,'project','acquisition.completed','acquisition',
           a.id::text,'completed','Acquisition ' || a.source || ' : ' || a.query,
           jsonb_build_object('source',a.source,'item_count',a.item_count,'sha256',a.sha256),
           'system',a.retrieved_at
    FROM acquisitions a
    WHERE a.project_id=%s AND NOT EXISTS (
        SELECT 1 FROM application_timeline t
        WHERE t.scope='project' AND t.project_id=a.project_id
          AND t.object_type='acquisition' AND t.object_id=a.id::text
    )
    UNION ALL
    SELECT e.id,e.project_id,'project','script.execution','script_execution',
           e.id::text,e.status,'Script ' || s.name || ' : ' || e.status,
           jsonb_build_object('script_id',e.script_id,'language',e.language,'error',e.error),
           'local-operator',e.requested_at
    FROM script_executions e JOIN project_scripts s ON s.id=e.script_id
    WHERE e.project_id=%s AND NOT EXISTS (
        SELECT 1 FROM application_timeline t
        WHERE t.scope='project' AND t.project_id=e.project_id
          AND t.object_type='script_execution' AND t.object_id=e.id::text
    )
    UNION ALL
    SELECT r.id,s.project_id,'project','resource.refresh','resource_refresh_run',
           r.id::text,r.status,'Mise à jour de la ressource ' || s.resource_id::text,
           jsonb_build_object('resource_id',s.resource_id,'acquisition_id',r.acquisition_id,'error',r.error),
           'system',r.started_at
    FROM resource_refresh_runs r
    JOIN resource_refresh_schedules s ON s.id=r.refresh_schedule_id
    WHERE s.project_id=%s AND NOT EXISTS (
        SELECT 1 FROM application_timeline t
        WHERE t.scope='project' AND t.project_id=s.project_id
          AND t.object_type='resource_refresh_run' AND t.object_id=r.id::text
    )
    UNION ALL
    SELECT e.id,e.project_id,'project','signal.ingested','signal_event',
           e.id::text,'observed',e.title,
           jsonb_build_object(
               'source',e.source,'severity',e.severity,'confidence',e.confidence,
               'themes',e.themes,'locations',e.locations
           ),'system',e.received_at
    FROM signal_events e
    WHERE e.project_id=%s AND NOT EXISTS (
        SELECT 1 FROM application_timeline t
        WHERE t.scope='project' AND t.project_id=e.project_id
          AND t.object_type='signal_event' AND t.object_id=e.id::text
    )
)
SELECT id,project_id,scope,event_type,object_type,object_id,status,
       summary,details,actor,occurred_at
FROM combined
WHERE (%s::text IS NULL OR event_type=%s::text)
ORDER BY occurred_at DESC,id DESC LIMIT %s
"""


def list_timeline(
    connection: Any,
    scope: str,
    project_id: uuid.UUID | None,
    event_type: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    if scope == "global":
        rows = connection.execute(
            GLOBAL_TIMELINE_QUERY,
            (event_type, event_type, limit),
        ).fetchall()
    elif scope == "project" and project_id is not None:
        rows = connection.execute(
            PROJECT_TIMELINE_QUERY,
            (project_id, project_id, project_id, project_id, project_id, project_id, event_type, event_type, limit),
        ).fetchall()
    else:
        raise ValueError("Portée de chronologie invalide")
    return [dict(zip(TIMELINE_KEYS, row, strict=True)) for row in rows]

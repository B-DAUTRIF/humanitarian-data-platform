from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urlparse

import psycopg
from fastapi import APIRouter, HTTPException, Query, Request
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field

from .request_security import bearer_token
from .v6_catalog import canonical_json


DATABASE_URL = os.environ["DATABASE_URL"]
CONTRACT_VERSION = "hdp-spip/1.0"
BRIDGE_TOKEN_PREFIX = "hdps_"
MAX_DOCUMENT_BYTES = 2_000_000
ALLOWED_SCOPES = frozenset({"publication:pull", "publication:ack"})
PUBLICATION_KINDS = frozenset(
    {"documentation", "news", "feed_curation", "alert_curation", "project_share"}
)

router = APIRouter(tags=["spip"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SpipConnectionCreate(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    base_url: str = Field(min_length=12, max_length=500)


class PublicationDraftCreate(StrictModel):
    project_id: uuid.UUID
    kind: Literal[
        "documentation", "news", "feed_curation", "alert_curation", "project_share"
    ]
    title: str = Field(min_length=2, max_length=240)
    summary: str = Field(default="", max_length=2_000)
    body_text: str = Field(default="", max_length=500_000)
    source_snapshot: dict[str, Any] = Field(default_factory=dict)
    supersedes_id: uuid.UUID | None = None
    data_classification: Literal["public"] = "public"


class PublicationDraftPatch(StrictModel):
    title: str | None = Field(default=None, min_length=2, max_length=240)
    summary: str | None = Field(default=None, max_length=2_000)
    body_text: str | None = Field(default=None, max_length=500_000)
    source_snapshot: dict[str, Any] | None = None


class PublicationDecision(StrictModel):
    decision: Literal["approve", "reject", "withdraw"]
    reason: str = Field(default="", max_length=2_000)


class SpipAcknowledgement(StrictModel):
    status: Literal["imported", "published", "withdrawn", "rejected"]
    external_id: str = Field(default="", max_length=200)
    external_url: str = Field(default="", max_length=1_000)
    content_sha256: str = Field(default="", max_length=64)


def database_connection(*, autocommit: bool = True) -> psycopg.Connection[Any]:
    return psycopg.connect(DATABASE_URL, autocommit=autocommit)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validated_spip_base_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("L'URL du site SPIP doit être une origine HTTPS sans identifiants")
    if parsed.query or parsed.fragment:
        raise ValueError("L'URL du site SPIP ne doit contenir ni requête ni fragment")
    return value.strip().rstrip("/")


def publication_document(
    publication_id: uuid.UUID,
    series_id: uuid.UUID,
    revision: int,
    project_id: uuid.UUID,
    kind: str,
    title: str,
    summary: str,
    body_text: str,
    source_snapshot: dict[str, Any],
    created_at: datetime,
) -> dict[str, Any]:
    if kind not in PUBLICATION_KINDS:
        raise ValueError("Type de publication SPIP invalide")
    document = {
        "schema": CONTRACT_VERSION,
        "publication_id": str(publication_id),
        "series_id": str(series_id),
        "revision": revision,
        "project_id": str(project_id),
        "kind": kind,
        "title": title,
        "summary": summary,
        "body_format": "plain_text",
        "body_text": body_text,
        "source_snapshot": source_snapshot,
        "data_classification": "public",
        "created_at": created_at.isoformat(),
    }
    if len(canonical_json(document).encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise ValueError("Le document SPIP dépasse la limite de 2 Mo")
    return document


def timeline(
    connection: psycopg.Connection[Any],
    event_type: str,
    publication_id: uuid.UUID,
    summary: str,
    details: dict[str, Any],
    now: datetime,
    project_id: uuid.UUID | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO application_timeline
            (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
        VALUES (%s,%s,%s,%s,'spip_publication',%s,'completed',%s,%s,'operator',%s)
        """,
        (
            uuid.uuid4(),
            project_id,
            "project" if project_id else "global",
            event_type,
            str(publication_id),
            summary,
            Jsonb(details),
            now,
        ),
    )


def row_to_publication(row: tuple[Any, ...], include_document: bool = True) -> dict[str, Any]:
    item = {
        "id": str(row[0]),
        "series_id": str(row[1]),
        "project_id": str(row[2]),
        "kind": row[3],
        "title": row[4],
        "summary": row[5],
        "revision": row[6],
        "status": row[7],
        "content_sha256": row[9],
        "supersedes_id": str(row[10]) if row[10] else None,
        "created_at": row[11],
        "updated_at": row[12],
        "approved_at": row[13],
        "withdrawn_at": row[14],
        "decision_reason": row[15],
    }
    if include_document:
        item["document"] = row[8]
        item["document_canonical"] = canonical_json(row[8])
    return item


def publication_select() -> str:
    return """
        SELECT id,series_id,project_id,kind,title,summary,revision,status,document,
               content_sha256,supersedes_id,created_at,updated_at,approved_at,
               withdrawn_at,decision_reason
        FROM spip_publication_drafts
    """


@router.post("/api/v6/spip/connections", status_code=201)
def create_spip_connection(body: SpipConnectionCreate) -> dict[str, Any]:
    try:
        base_url = validated_spip_base_url(body.base_url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    token = BRIDGE_TOKEN_PREFIX + secrets.token_urlsafe(48)
    connection_id, now = uuid.uuid4(), datetime.now(UTC)
    scopes = sorted(ALLOWED_SCOPES)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO spip_connections
                (id,name,base_url,token_sha256,scopes,enabled,created_at,last_used_at,revoked_at)
            VALUES (%s,%s,%s,%s,%s,TRUE,%s,NULL,NULL)
            """,
            (connection_id, body.name, base_url, sha256_text(token), Jsonb(scopes), now),
        )
        timeline(
            connection,
            "spip.connection_created",
            connection_id,
            "Connexion SPIP à droits minimaux créée",
            {"base_url": base_url, "scopes": scopes},
            now,
        )
    return {
        "id": str(connection_id),
        "name": body.name,
        "base_url": base_url,
        "scopes": scopes,
        "token": token,
        "token_displayed_once": True,
    }


@router.get("/api/v6/spip/connections")
def list_spip_connections() -> dict[str, Any]:
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id,name,base_url,scopes,enabled,created_at,last_used_at,revoked_at
            FROM spip_connections ORDER BY created_at DESC
            """
        ).fetchall()
    return {
        "items": [
            {
                "id": str(row[0]),
                "name": row[1],
                "base_url": row[2],
                "scopes": row[3],
                "enabled": row[4],
                "created_at": row[5],
                "last_used_at": row[6],
                "revoked_at": row[7],
            }
            for row in rows
        ]
    }


@router.post("/api/v6/spip/connections/{connection_id}/revoke")
def revoke_spip_connection(connection_id: uuid.UUID) -> dict[str, Any]:
    now = datetime.now(UTC)
    with database_connection() as connection:
        row = connection.execute(
            """
            UPDATE spip_connections SET enabled=FALSE,revoked_at=%s
            WHERE id=%s AND revoked_at IS NULL RETURNING id
            """,
            (now, connection_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Connexion SPIP introuvable ou révoquée")
        timeline(
            connection,
            "spip.connection_revoked",
            connection_id,
            "Connexion SPIP révoquée",
            {},
            now,
        )
    return {"id": str(connection_id), "revoked": True}


@router.post("/api/v6/spip/publications", status_code=201)
def create_publication_draft(body: PublicationDraftCreate) -> dict[str, Any]:
    publication_id, now = uuid.uuid4(), datetime.now(UTC)
    series_id, revision = uuid.uuid4(), 1
    with database_connection(autocommit=False) as connection:
        project = connection.execute(
            "SELECT 1 FROM projects WHERE id=%s AND archived_at IS NULL", (body.project_id,)
        ).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Projet introuvable ou archivé")
        if body.supersedes_id:
            previous = connection.execute(
                """
                SELECT series_id,revision,project_id,kind FROM spip_publication_drafts
                WHERE id=%s AND status IN ('approved','exported','withdrawn')
                FOR UPDATE
                """,
                (body.supersedes_id,),
            ).fetchone()
            if not previous:
                raise HTTPException(status_code=409, detail="Publication précédente non versionnable")
            if previous[2] != body.project_id or previous[3] != body.kind:
                raise HTTPException(status_code=409, detail="Projet ou type incompatible avec la série")
            series_id, revision = previous[0], int(previous[1]) + 1
        try:
            document = publication_document(
                publication_id,
                series_id,
                revision,
                body.project_id,
                body.kind,
                body.title,
                body.summary,
                body.body_text,
                body.source_snapshot,
                now,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        digest = sha256_text(canonical_json(document))
        connection.execute(
            """
            INSERT INTO spip_publication_drafts
                (id,series_id,project_id,kind,title,summary,revision,status,document,
                 content_sha256,supersedes_id,created_at,updated_at,approved_at,
                 withdrawn_at,decision_reason)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'draft',%s,%s,%s,%s,%s,NULL,NULL,'')
            """,
            (
                publication_id,
                series_id,
                body.project_id,
                body.kind,
                body.title,
                body.summary,
                revision,
                Jsonb(document),
                digest,
                body.supersedes_id,
                now,
                now,
            ),
        )
        timeline(
            connection,
            "spip.draft_created",
            publication_id,
            "Brouillon SPIP créé",
            {"kind": body.kind, "revision": revision, "content_sha256": digest},
            now,
            body.project_id,
        )
    return {
        "id": str(publication_id),
        "series_id": str(series_id),
        "revision": revision,
        "status": "draft",
        "content_sha256": digest,
        "manual_approval_required": True,
    }


@router.patch("/api/v6/spip/publications/{publication_id}")
def update_publication_draft(
    publication_id: uuid.UUID, body: PublicationDraftPatch
) -> dict[str, Any]:
    now = datetime.now(UTC)
    with database_connection(autocommit=False) as connection:
        row = connection.execute(
            publication_select() + " WHERE id=%s FOR UPDATE", (publication_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Brouillon SPIP introuvable")
        if row[7] != "draft":
            raise HTTPException(status_code=409, detail="Seul un brouillon peut être modifié")
        old_document = dict(row[8])
        title = body.title if body.title is not None else row[4]
        summary = body.summary if body.summary is not None else row[5]
        body_text = body.body_text if body.body_text is not None else old_document["body_text"]
        snapshot = (
            body.source_snapshot if body.source_snapshot is not None else old_document["source_snapshot"]
        )
        try:
            document = publication_document(
                row[0], row[1], row[6], row[2], row[3], title, summary, body_text, snapshot, row[11]
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        digest = sha256_text(canonical_json(document))
        connection.execute(
            """
            UPDATE spip_publication_drafts
            SET title=%s,summary=%s,document=%s,content_sha256=%s,updated_at=%s
            WHERE id=%s
            """,
            (title, summary, Jsonb(document), digest, now, publication_id),
        )
        timeline(
            connection,
            "spip.draft_updated",
            publication_id,
            "Brouillon SPIP modifié",
            {"content_sha256": digest},
            now,
            row[2],
        )
    return {"id": str(publication_id), "status": "draft", "content_sha256": digest}


@router.get("/api/v6/spip/publications")
def list_publication_drafts(
    project_id: uuid.UUID | None = None,
    status: str | None = Query(default=None, pattern="^(draft|approved|exported|rejected|withdrawn)$"),
) -> dict[str, Any]:
    clauses, parameters = [], []
    if project_id:
        clauses.append("project_id=%s")
        parameters.append(project_id)
    if status:
        clauses.append("status=%s")
        parameters.append(status)
    query = publication_select()
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY updated_at DESC LIMIT 500"
    with database_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return {"items": [row_to_publication(row, include_document=False) for row in rows]}


@router.get("/api/v6/spip/publications/{publication_id}")
def get_publication_draft(publication_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(publication_select() + " WHERE id=%s", (publication_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Publication SPIP introuvable")
    return row_to_publication(row)


@router.post("/api/v6/spip/publications/{publication_id}/decision")
def decide_publication(publication_id: uuid.UUID, body: PublicationDecision) -> dict[str, Any]:
    now = datetime.now(UTC)
    with database_connection(autocommit=False) as connection:
        row = connection.execute(
            "SELECT project_id,status FROM spip_publication_drafts WHERE id=%s FOR UPDATE",
            (publication_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Publication SPIP introuvable")
        transitions = {
            "approve": ({"draft"}, "approved", "approved_at"),
            "reject": ({"draft"}, "rejected", None),
            "withdraw": ({"approved", "exported"}, "withdrawn", "withdrawn_at"),
        }
        allowed, target, timestamp_column = transitions[body.decision]
        if row[1] not in allowed:
            raise HTTPException(
                status_code=409,
                detail=f"Transition {row[1]} vers {target} interdite",
            )
        query = "UPDATE spip_publication_drafts SET status=%s,decision_reason=%s,updated_at=%s"
        parameters: list[Any] = [target, body.reason, now]
        if timestamp_column:
            query += f",{timestamp_column}=%s"
            parameters.append(now)
        query += " WHERE id=%s"
        parameters.append(publication_id)
        connection.execute(query, parameters)
        timeline(
            connection,
            f"spip.publication_{target}",
            publication_id,
            f"Publication SPIP : décision {target}",
            {"decision": body.decision, "reason": body.reason},
            now,
            row[0],
        )
    return {
        "id": str(publication_id),
        "status": target,
        "manual_decision_recorded": True,
    }


def bridge_connection(request: Request, required_scope: str) -> tuple[uuid.UUID, str]:
    token = bearer_token(request)
    if not token.startswith(BRIDGE_TOKEN_PREFIX) or len(token) < 64:
        raise HTTPException(status_code=401, detail="Jeton de passerelle SPIP invalide")
    digest, now = sha256_text(token), datetime.now(UTC)
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT id,scopes FROM spip_connections
            WHERE token_sha256=%s AND enabled=TRUE AND revoked_at IS NULL
            """,
            (digest,),
        ).fetchone()
        if not row or required_scope not in set(row[1]):
            raise HTTPException(status_code=403, detail="Droit de passerelle SPIP insuffisant")
        connection.execute("UPDATE spip_connections SET last_used_at=%s WHERE id=%s", (now, row[0]))
    return row[0], token


def encode_cursor(updated_at: datetime, publication_id: uuid.UUID) -> str:
    raw = json.dumps(
        [updated_at.isoformat(), str(publication_id)], separators=(",", ":")
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(value: str) -> tuple[datetime, uuid.UUID]:
    try:
        padded = value + "=" * (-len(value) % 4)
        timestamp, identifier = json.loads(base64.urlsafe_b64decode(padded))
        moment = datetime.fromisoformat(timestamp)
        if moment.tzinfo is None:
            raise ValueError
        return moment, uuid.UUID(identifier)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="Curseur SPIP invalide") from exc


@router.get("/api/spip-bridge/v1/publications")
def pull_spip_publications(
    request: Request,
    cursor: str = Query(default="", max_length=500),
    limit: int = Query(default=50, ge=1, le=100),
) -> dict[str, Any]:
    bridge_connection(request, "publication:pull")
    parameters: list[Any] = []
    query = publication_select() + " WHERE status IN ('approved','exported','withdrawn')"
    if cursor:
        moment, identifier = decode_cursor(cursor)
        query += " AND (updated_at>%s OR (updated_at=%s AND id>%s))"
        parameters.extend([moment, moment, identifier])
    query += " ORDER BY updated_at,id LIMIT %s"
    parameters.append(limit)
    with database_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()
    items = []
    for row in rows:
        item = row_to_publication(row, include_document=row[7] != "withdrawn")
        if row[7] == "withdrawn":
            item["tombstone"] = True
        items.append(item)
    next_cursor = encode_cursor(rows[-1][12], rows[-1][0]) if rows else cursor
    return {
        "contract": CONTRACT_VERSION,
        "items": items,
        "next_cursor": next_cursor,
        "has_more": len(rows) == limit,
    }


@router.post("/api/spip-bridge/v1/publications/{publication_id}/acknowledge")
def acknowledge_spip_publication(
    publication_id: uuid.UUID,
    body: SpipAcknowledgement,
    request: Request,
) -> dict[str, Any]:
    connection_id, _ = bridge_connection(request, "publication:ack")
    idempotency_key = request.headers.get("idempotency-key", "").strip()
    if not 16 <= len(idempotency_key) <= 200:
        raise HTTPException(status_code=422, detail="Idempotency-Key requis (16 à 200 caractères)")
    now = datetime.now(UTC)
    with database_connection(autocommit=False) as connection:
        existing = connection.execute(
            """
            SELECT response FROM spip_delivery_events
            WHERE connection_id=%s AND idempotency_key=%s
            """,
            (connection_id, idempotency_key),
        ).fetchone()
        if existing:
            return dict(existing[0])
        row = connection.execute(
            """
            SELECT project_id,status,series_id,content_sha256
            FROM spip_publication_drafts WHERE id=%s FOR UPDATE
            """,
            (publication_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Publication SPIP introuvable")
        if body.status in {"imported", "published"}:
            if row[1] not in {"approved", "exported"}:
                raise HTTPException(status_code=409, detail="Publication non approuvée")
            if body.content_sha256 != row[3]:
                raise HTTPException(status_code=409, detail="Empreinte de publication incohérente")
            connection.execute(
                "UPDATE spip_publication_drafts SET status='exported',updated_at=%s WHERE id=%s",
                (now, publication_id),
            )
        elif body.status == "withdrawn" and row[1] != "withdrawn":
            raise HTTPException(status_code=409, detail="Retrait HDP non approuvé")
        response = {
            "id": str(publication_id),
            "acknowledged": True,
            "status": body.status,
            "contract": CONTRACT_VERSION,
        }
        connection.execute(
            """
            INSERT INTO spip_external_mappings
                (connection_id,series_id,external_id,external_url,last_publication_id,
                 last_status,updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (connection_id,series_id) DO UPDATE
            SET external_id=EXCLUDED.external_id,external_url=EXCLUDED.external_url,
                last_publication_id=EXCLUDED.last_publication_id,
                last_status=EXCLUDED.last_status,updated_at=EXCLUDED.updated_at
            """,
            (
                connection_id,
                row[2],
                body.external_id,
                body.external_url,
                publication_id,
                body.status,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO spip_delivery_events
                (id,connection_id,publication_id,event_type,idempotency_key,request,response,created_at)
            VALUES (%s,%s,%s,'acknowledge',%s,%s,%s,%s)
            """,
            (
                uuid.uuid4(),
                connection_id,
                publication_id,
                idempotency_key,
                Jsonb(body.model_dump(mode="json")),
                Jsonb(response),
                now,
            ),
        )
        timeline(
            connection,
            "spip.delivery_acknowledged",
            publication_id,
            "Réception SPIP confirmée",
            {"status": body.status, "connection_id": str(connection_id)},
            now,
            row[0],
        )
    return response

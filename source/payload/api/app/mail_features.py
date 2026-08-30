from __future__ import annotations

import hashlib
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import psycopg
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from psycopg.types.json import Jsonb

from .mail_ingestion import (
    MAX_EML_BYTES,
    MailValidationError,
    parse_public_eml,
    publish_mail_attachment,
)
from .v6_features import dispatch_event_to_v6_rules


DATABASE_URL = os.environ["DATABASE_URL"]
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
router = APIRouter(prefix="/api/v6/mail", tags=["mail"])


def db(*, autocommit: bool = True) -> psycopg.Connection[Any]:
    return psycopg.connect(DATABASE_URL, autocommit=autocommit)


def public_evidence_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Une URL HTTPS publique sans identifiants est obligatoire")
    return value.strip()


def timeline(
    connection: psycopg.Connection[Any],
    event_type: str,
    message_id: uuid.UUID,
    summary: str,
    now: datetime,
    project_id: uuid.UUID | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO application_timeline
            (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
        VALUES (%s,%s,%s,%s,'mail_message',%s,'completed',%s,'{}'::jsonb,'operator',%s)
        """,
        (
            uuid.uuid4(),
            project_id,
            "project" if project_id else "global",
            event_type,
            str(message_id),
            summary,
            now,
        ),
    )


@router.post("/import-eml", status_code=201)
async def import_public_eml(
    file: UploadFile = File(...),
    public_source_url: str = Form(..., min_length=12, max_length=2000),
    public_source_confirmed: bool = Form(...),
) -> dict[str, Any]:
    if not public_source_confirmed:
        raise HTTPException(
            status_code=422,
            detail="Confirmez que le message et ses pièces jointes sont intégralement publics",
        )
    try:
        evidence_url = public_evidence_url(public_source_url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    content = await file.read(MAX_EML_BYTES + 1)
    await file.close()
    try:
        parsed = parse_public_eml(content)
    except MailValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    now, message_id = datetime.now(UTC), uuid.uuid4()
    mail_root = DATA_DIR / "mail"
    stored = []
    try:
        for attachment in parsed.attachments:
            path, created = publish_mail_attachment(mail_root, attachment)
            stored.append((uuid.uuid4(), attachment, path, created))
    except (OSError, MailValidationError) as exc:
        raise HTTPException(status_code=500, detail=f"Stockage de pièce jointe impossible: {exc}") from exc
    try:
        with db(autocommit=False) as connection:
            duplicate = connection.execute(
                "SELECT id FROM mail_messages WHERE message_key=%s", (parsed.message_key,)
            ).fetchone()
            if duplicate:
                raise HTTPException(
                    status_code=409,
                    detail=f"Message déjà importé: {duplicate[0]}",
                )
            connection.execute(
                """
                INSERT INTO mail_messages
                    (id,message_key,subject,sent_at,received_at,sender_domain,sender_sha256,
                     body_text,body_sha256,public_source_url,data_classification,
                     attachment_count,malware_scan_status,created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'public',%s,'not_available',%s)
                """,
                (
                    message_id,
                    parsed.message_key,
                    parsed.subject,
                    parsed.sent_at,
                    now,
                    parsed.sender_domain,
                    parsed.sender_sha256,
                    parsed.body_text,
                    parsed.body_sha256,
                    evidence_url,
                    len(stored),
                    now,
                ),
            )
            for attachment_id, attachment, path, _ in stored:
                connection.execute(
                    """
                    INSERT INTO mail_attachments
                        (id,message_id,filename,content_type,size_bytes,sha256,storage_path,
                         malware_scan_status,created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,'not_available',%s)
                    """,
                    (
                        attachment_id,
                        message_id,
                        attachment.filename,
                        attachment.content_type,
                        len(attachment.content),
                        attachment.sha256,
                        str(path),
                        now,
                    ),
                )
            timeline(
                connection,
                "mail.public_eml_imported",
                message_id,
                "Message EML public importé",
                now,
            )
    except HTTPException:
        raise
    return {
        "id": str(message_id),
        "subject": parsed.subject,
        "attachment_count": len(stored),
        "data_classification": "public",
        "personal_addresses_stored": False,
        "malware_scan_status": "not_available",
        "next_step": "manual_project_link",
    }


@router.get("/messages")
def list_mail_messages(
    project_id: uuid.UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    with db() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT m.id,m.subject,m.sent_at,m.received_at,m.sender_domain,
                   m.body_sha256,m.public_source_url,m.attachment_count,m.malware_scan_status,
                   (l.project_id IS NOT NULL) AS linked
            FROM mail_messages m
            LEFT JOIN mail_project_links l ON l.message_id=m.id AND (%s IS NULL OR l.project_id=%s)
            ORDER BY m.received_at DESC LIMIT %s
            """,
            (project_id, project_id, limit),
        ).fetchall()
    keys = (
        "id",
        "subject",
        "sent_at",
        "received_at",
        "sender_domain",
        "body_sha256",
        "public_source_url",
        "attachment_count",
        "malware_scan_status",
        "linked_to_selected_project",
    )
    return [dict(zip(keys, row, strict=True)) for row in rows]


@router.get("/messages/{message_id}")
def get_mail_message(message_id: uuid.UUID) -> dict[str, Any]:
    with db() as connection:
        row = connection.execute(
            """
            SELECT id,subject,sent_at,received_at,sender_domain,body_text,body_sha256,
                   public_source_url,data_classification,malware_scan_status
            FROM mail_messages WHERE id=%s
            """,
            (message_id,),
        ).fetchone()
        attachments = connection.execute(
            """
            SELECT id,filename,content_type,size_bytes,sha256,malware_scan_status
            FROM mail_attachments WHERE message_id=%s ORDER BY filename,id
            """,
            (message_id,),
        ).fetchall()
    if not row:
        raise HTTPException(status_code=404, detail="Message introuvable")
    return {
        "id": str(row[0]),
        "subject": row[1],
        "sent_at": row[2],
        "received_at": row[3],
        "sender_domain": row[4],
        "body_text": row[5],
        "body_sha256": row[6],
        "public_source_url": row[7],
        "data_classification": row[8],
        "malware_scan_status": row[9],
        "attachments": [
            {
                "id": str(item[0]),
                "filename": item[1],
                "content_type": item[2],
                "size_bytes": item[3],
                "sha256": item[4],
                "malware_scan_status": item[5],
            }
            for item in attachments
        ],
    }


@router.post("/messages/{message_id}/projects/{project_id}", status_code=201)
def link_mail_to_project(message_id: uuid.UUID, project_id: uuid.UUID) -> dict[str, Any]:
    now, signal_id = datetime.now(UTC), uuid.uuid4()
    with db(autocommit=False) as connection:
        project = connection.execute(
            "SELECT 1 FROM projects WHERE id=%s AND archived_at IS NULL", (project_id,)
        ).fetchone()
        message = connection.execute(
            """
            SELECT subject,body_text,sent_at,received_at,public_source_url,message_key
            FROM mail_messages WHERE id=%s
            """,
            (message_id,),
        ).fetchone()
        if not project or not message:
            raise HTTPException(status_code=404, detail="Projet ou message introuvable")
        existing = connection.execute(
            "SELECT signal_event_id FROM mail_project_links WHERE message_id=%s AND project_id=%s",
            (message_id, project_id),
        ).fetchone()
        if existing:
            return {
                "message_id": str(message_id),
                "project_id": str(project_id),
                "signal_event_id": str(existing[0]),
                "created": False,
            }
        connection.execute(
            """
            INSERT INTO signal_events
                (id,project_id,source,external_id,title,summary,occurred_at,received_at,
                 locations,themes,severity,confidence,evidence,raw)
            VALUES (%s,%s,'public-email',%s,%s,%s,%s,%s,'[]'::jsonb,
                    '["veille documentaire"]'::jsonb,0.1,0.6,%s,%s)
            """,
            (
                signal_id,
                project_id,
                message[5],
                message[0],
                message[1][:5_000],
                message[2] or message[3],
                now,
                Jsonb([{"type": "public_source", "url": message[4]}]),
                Jsonb({"mail_message_id": str(message_id), "classification": "public"}),
            ),
        )
        connection.execute(
            """
            INSERT INTO mail_project_links
                (message_id,project_id,signal_event_id,linked_at,linked_by)
            VALUES (%s,%s,%s,%s,'operator')
            """,
            (message_id, project_id, signal_id, now),
        )
        timeline(
            connection,
            "mail.linked_to_project",
            message_id,
            "Message public rattaché au projet et exposé aux règles",
            now,
            project_id,
        )
    evaluations = dispatch_event_to_v6_rules(project_id, signal_id)
    return {
        "message_id": str(message_id),
        "project_id": str(project_id),
        "signal_event_id": str(signal_id),
        "created": True,
        "rule_evaluations": evaluations["evaluations"],
    }


@router.get("/attachments/{attachment_id}/download", response_class=FileResponse)
def download_mail_attachment(
    attachment_id: uuid.UUID,
    acknowledge_unscanned: bool = Query(default=False),
) -> FileResponse:
    with db() as connection:
        row = connection.execute(
            "SELECT filename,content_type,sha256,storage_path,malware_scan_status FROM mail_attachments WHERE id=%s",
            (attachment_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Pièce jointe introuvable")
    if row[4] != "passed" and not acknowledge_unscanned:
        raise HTTPException(
            status_code=409,
            detail="Analyse antimalware indisponible: confirmation explicite requise",
        )
    root = (DATA_DIR / "mail").resolve()
    path = Path(row[3]).resolve()
    if root not in path.parents or path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=409, detail="Chemin de pièce jointe invalide")
    if hashlib.sha256(path.read_bytes()).hexdigest() != row[2]:
        raise HTTPException(status_code=409, detail="Empreinte de pièce jointe incohérente")
    return FileResponse(path, media_type=row[1], filename=row[0])

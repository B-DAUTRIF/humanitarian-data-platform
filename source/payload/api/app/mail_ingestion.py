from __future__ import annotations

import hashlib
import html
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parsedate_to_datetime, parseaddr
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .security import safe_filename


MAX_EML_BYTES = 30 * 1024 * 1024
MAX_BODY_CHARS = 500_000
MAX_ATTACHMENTS = 50
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024
MAX_TOTAL_ATTACHMENT_BYTES = 30 * 1024 * 1024
BLOCKED_SUFFIXES = frozenset(
    {".exe", ".dll", ".com", ".scr", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".jar"}
)
EMAIL_PATTERN = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
URL_PATTERN = re.compile(r"https?://[^\s<>\"]+", re.IGNORECASE)


class MailValidationError(ValueError):
    pass


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return " ".join(self.parts)


@dataclass(frozen=True)
class ParsedAttachment:
    filename: str
    content_type: str
    content: bytes
    sha256: str


@dataclass(frozen=True)
class ParsedPublicMail:
    message_key: str
    subject: str
    sent_at: datetime | None
    sender_domain: str
    sender_sha256: str
    body_text: str
    body_sha256: str
    attachments: tuple[ParsedAttachment, ...]


def _redact_url(value: str) -> str:
    parsed = urlsplit(value.rstrip(".,;:)"))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def redact_public_text(value: str) -> str:
    redacted = EMAIL_PATTERN.sub("[adresse masquée]", value)
    redacted = URL_PATTERN.sub(lambda match: _redact_url(match.group(0)), redacted)
    redacted = "\n".join(line.rstrip() for line in redacted.replace("\x00", "").splitlines())
    return redacted[:MAX_BODY_CHARS]


def _message_text(message: Message) -> str:
    plain: list[str] = []
    html_parts: list[str] = []
    for part in message.walk():
        if part.is_multipart() or part.get_filename() or part.get_content_disposition() == "attachment":
            continue
        content_type = part.get_content_type().casefold()
        if content_type not in {"text/plain", "text/html"}:
            continue
        try:
            content = part.get_content()
        except (LookupError, UnicodeError):
            payload = part.get_payload(decode=True) or b""
            content = payload.decode("utf-8", "replace")
        if not isinstance(content, str):
            continue
        if content_type == "text/plain":
            plain.append(content)
        else:
            html_parts.append(content)
    if plain:
        return "\n\n".join(plain)
    extractor = _TextExtractor()
    for content in html_parts:
        extractor.feed(content)
    return html.unescape(extractor.text())


def _sent_at(message: Message) -> datetime | None:
    raw = str(message.get("Date", "")).strip()
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except (TypeError, ValueError, OverflowError):
        return None


def parse_public_eml(content: bytes) -> ParsedPublicMail:
    if not content or len(content) > MAX_EML_BYTES:
        raise MailValidationError("Le fichier EML est vide ou dépasse 30 Mio")
    if b"\x00" in content[:100_000]:
        raise MailValidationError("Le fichier ne ressemble pas à un message EML")
    message = BytesParser(policy=policy.default).parsebytes(content)
    content_types = {part.get_content_type().casefold() for part in message.walk()}
    if content_types & {"multipart/encrypted", "application/pkcs7-mime", "application/x-pkcs7-mime"}:
        raise MailValidationError("Les messages chiffrés ne sont pas importables automatiquement")
    subject = redact_public_text(str(message.get("Subject", "(sans objet)")))[:500]
    _, sender = parseaddr(str(message.get("From", "")))
    sender_normalized = sender.strip().casefold()
    sender_domain = sender_normalized.rpartition("@")[2][:255] if "@" in sender_normalized else ""
    sender_sha256 = hashlib.sha256(sender_normalized.encode("utf-8")).hexdigest() if sender_normalized else ""
    body = redact_public_text(_message_text(message))
    attachments: list[ParsedAttachment] = []
    total = 0
    for part in message.walk():
        filename = part.get_filename()
        if not filename and part.get_content_disposition() != "attachment":
            continue
        if len(attachments) >= MAX_ATTACHMENTS:
            raise MailValidationError("Le message contient plus de 50 pièces jointes")
        payload = part.get_payload(decode=True) or b""
        if len(payload) > MAX_ATTACHMENT_BYTES:
            raise MailValidationError("Une pièce jointe dépasse 25 Mio")
        total += len(payload)
        if total > MAX_TOTAL_ATTACHMENT_BYTES:
            raise MailValidationError("Les pièces jointes dépassent 30 Mio au total")
        name = safe_filename(str(filename or f"piece-{len(attachments) + 1}"))
        if Path(name).suffix.casefold() in BLOCKED_SUFFIXES:
            raise MailValidationError(f"Type de pièce jointe exécutable refusé: {name}")
        attachments.append(
            ParsedAttachment(
                filename=name,
                content_type=part.get_content_type()[:255],
                content=payload,
                sha256=hashlib.sha256(payload).hexdigest(),
            )
        )
    message_id = str(message.get("Message-ID", "")).strip()
    stable_input = message_id if message_id else hashlib.sha256(content).hexdigest()
    return ParsedPublicMail(
        message_key=hashlib.sha256(stable_input.encode("utf-8")).hexdigest(),
        subject=subject,
        sent_at=_sent_at(message),
        sender_domain=sender_domain,
        sender_sha256=sender_sha256,
        body_text=body,
        body_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
        attachments=tuple(attachments),
    )


def publish_mail_attachment(root: Path, attachment: ParsedAttachment) -> tuple[Path, bool]:
    resolved_root = root.resolve()
    destination = resolved_root / "objects" / attachment.sha256[:2] / attachment.sha256
    if resolved_root not in destination.parents:
        raise MailValidationError("Chemin de pièce jointe hors racine")
    destination.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if destination.exists():
        if destination.is_symlink() or hashlib.sha256(destination.read_bytes()).hexdigest() != attachment.sha256:
            raise MailValidationError("Pièce jointe existante altérée")
        return destination, False
    descriptor, temporary_name = tempfile.mkstemp(prefix=".hdp-mail-", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(attachment.content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
        directory_descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)
    return destination, True

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = SOURCE_ROOT / "payload" / "api"
sys.path.insert(0, str(API_ROOT))
os.environ.setdefault("DATABASE_URL", "postgresql://hdp:hdp@127.0.0.1:5432/hdp")

from app.mail_ingestion import (  # noqa: E402
    MailValidationError,
    parse_public_eml,
    publish_mail_attachment,
)


class V6MailIngestionTest(unittest.TestCase):
    def test_public_eml_redacts_addresses_and_url_parameters(self) -> None:
        content = (
            b"From: Alice <alice@example.org>\r\n"
            b"To: veille@example.net\r\n"
            b"Subject: Public health alert\r\n"
            b"Message-ID: <public-1@example.org>\r\n"
            b"Date: Fri, 21 Aug 2026 12:00:00 +0000\r\n"
            b"MIME-Version: 1.0\r\n"
            b"Content-Type: multipart/mixed; boundary=hdp\r\n\r\n"
            b"--hdp\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n"
            b"Contact alice@example.org and read https://example.org/bulletin?token=secret\r\n"
            b"--hdp\r\nContent-Type: text/csv\r\nContent-Disposition: attachment; filename=data.csv\r\n\r\n"
            b"area,cases\nA,4\n\r\n--hdp--\r\n"
        )
        parsed = parse_public_eml(content)
        self.assertEqual(parsed.sender_domain, "example.org")
        self.assertNotIn("alice@example.org", parsed.body_text)
        self.assertNotIn("token=secret", parsed.body_text)
        self.assertIn("https://example.org/bulletin", parsed.body_text)
        self.assertEqual(len(parsed.attachments), 1)
        self.assertEqual(parsed.attachments[0].filename, "data.csv")

    def test_executable_attachment_is_rejected(self) -> None:
        content = (
            b"From: public@example.org\r\nSubject: Alert\r\nMIME-Version: 1.0\r\n"
            b"Content-Type: application/octet-stream\r\n"
            b"Content-Disposition: attachment; filename=payload.exe\r\n\r\nMZ"
        )
        with self.assertRaises(MailValidationError):
            parse_public_eml(content)

    def test_attachment_storage_is_content_addressed_and_idempotent(self) -> None:
        content = (
            b"From: public@example.org\r\nSubject: Data\r\nMIME-Version: 1.0\r\n"
            b"Content-Type: text/csv\r\nContent-Disposition: attachment; filename=data.csv\r\n\r\na,b\n1,2\n"
        )
        attachment = parse_public_eml(content).attachments[0]
        with tempfile.TemporaryDirectory() as directory:
            first, created = publish_mail_attachment(Path(directory), attachment)
            second, created_again = publish_mail_attachment(Path(directory), attachment)
            self.assertTrue(created)
            self.assertFalse(created_again)
            self.assertEqual(first, second)
            self.assertEqual(first.read_bytes(), attachment.content)

    def test_mail_routes_and_public_only_migration_are_explicit(self) -> None:
        routes = (API_ROOT / "app" / "mail_features.py").read_text(encoding="utf-8")
        migrations = (API_ROOT / "app" / "migrations.py").read_text(encoding="utf-8")
        html = (API_ROOT / "static" / "index.html").read_text(encoding="utf-8")
        for route in (
            '/import-eml',
            '/messages',
            '/messages/{message_id}',
            '/messages/{message_id}/projects/{project_id}',
            '/attachments/{attachment_id}/download',
        ):
            self.assertIn(route, routes)
        self.assertIn("public_source_confirmed", routes)
        self.assertIn("acknowledge_unscanned", routes)
        self.assertIn('version="6.0.0-010-public-mail-ingestion"', migrations)
        self.assertIn("CHECK (data_classification='public')", migrations)
        self.assertIn('id="view-mail"', html)


if __name__ == "__main__":
    unittest.main()

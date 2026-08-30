from __future__ import annotations

import hashlib
import os
import sys
import unittest
import uuid
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = SOURCE_ROOT / "payload" / "api"
PLUGIN_ROOT = SOURCE_ROOT / "spip-plugin" / "hdp"
sys.path.insert(0, str(API_ROOT))
os.environ.setdefault("DATABASE_URL", "postgresql://hdp:hdp@127.0.0.1:5432/hdp")

from app.spip_bridge import (  # noqa: E402
    CONTRACT_VERSION,
    decode_cursor,
    encode_cursor,
    publication_document,
    sha256_text,
    validated_spip_base_url,
)
from app.v6_catalog import canonical_json  # noqa: E402


class V6SpipBridgeTest(unittest.TestCase):
    def test_publication_contract_is_canonical_public_and_versioned(self) -> None:
        publication_id, series_id, project_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        document = publication_document(
            publication_id,
            series_id,
            2,
            project_id,
            "project_share",
            "Situation humanitaire",
            "Résumé public",
            "Corps public",
            {"signals": 3},
            datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
        )
        serialized = canonical_json(document)
        self.assertEqual(document["schema"], CONTRACT_VERSION)
        self.assertEqual(document["data_classification"], "public")
        self.assertEqual(document["body_format"], "plain_text")
        self.assertEqual(sha256_text(serialized), hashlib.sha256(serialized.encode()).hexdigest())

    def test_spip_connection_requires_https_origin_without_credentials(self) -> None:
        self.assertEqual(validated_spip_base_url("https://spip.example.org/"), "https://spip.example.org")
        for invalid in (
            "http://spip.example.org",
            "https://user:secret@spip.example.org",
            "https://spip.example.org/?token=secret",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validated_spip_base_url(invalid)

    def test_bridge_cursor_round_trip_is_stable(self) -> None:
        moment = datetime(2026, 8, 21, 12, 34, 56, tzinfo=UTC)
        identifier = uuid.uuid4()
        self.assertEqual(decode_cursor(encode_cursor(moment, identifier)), (moment, identifier))

    def test_operator_and_minimal_service_routes_are_separated(self) -> None:
        source = (API_ROOT / "app" / "spip_bridge.py").read_text(encoding="utf-8")
        main = (API_ROOT / "app" / "main.py").read_text(encoding="utf-8")
        for route in (
            '/api/v6/spip/connections',
            '/api/v6/spip/publications',
            '/api/v6/spip/publications/{publication_id}/decision',
            '/api/spip-bridge/v1/publications',
            '/api/spip-bridge/v1/publications/{publication_id}/acknowledge',
        ):
            self.assertIn(route, source)
        self.assertIn('path.startswith("/api/spip-bridge/v1/")', main)
        self.assertIn('bridge_connection(request, "publication:pull")', source)
        self.assertIn('bridge_connection(request, "publication:ack")', source)
        self.assertNotIn("runner", source.casefold())

    def test_plugin_manifest_templates_and_secret_boundary_are_present(self) -> None:
        manifest = ET.parse(PLUGIN_ROOT / "paquet.xml").getroot()
        self.assertEqual(manifest.attrib["compatibilite"], "[4.2.0;4.4.*]")
        client = (PLUGIN_ROOT / "inc" / "hdp_client.php").read_text(encoding="utf-8")
        listing = (PLUGIN_ROOT / "hdp.html").read_text(encoding="utf-8")
        detail = (PLUGIN_ROOT / "hdp_publication.html").read_text(encoding="utf-8")
        readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("_HDP_BRIDGE_TOKEN", client)
        self.assertIn("hash_equals", client)
        self.assertIn("data_classification", client)
        self.assertIn("#CACHE{0}", listing)
        self.assertIn("#SESSION{id_auteur}", listing)
        self.assertIn("#CACHE{0}", detail)
        self.assertIn("getenv('HDP_BRIDGE_TOKEN')", readme)
        self.assertNotIn("GITHUB_TOKEN", client)

    def test_spip_migration_is_audited_and_idempotent(self) -> None:
        migrations = (API_ROOT / "app" / "migrations.py").read_text(encoding="utf-8")
        self.assertIn('version="6.0.0-009-spip-publication-bridge"', migrations)
        for table in (
            "spip_connections",
            "spip_publication_drafts",
            "spip_external_mappings",
            "spip_delivery_events",
        ):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", migrations)
        self.assertIn("UNIQUE (connection_id, idempotency_key)", migrations)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = SOURCE_ROOT / "payload" / "api"


class V6PasskeyAuthTest(unittest.TestCase):
    def test_webauthn_options_require_discoverable_credential_and_user_verification(self) -> None:
        import sys

        sys.path.insert(0, str(API_ROOT))
        from app.passkey_auth import authentication_options, registration_options

        registration_challenge, registration = registration_options("localhost", [])
        authentication_challenge, authentication = authentication_options("localhost", [])
        self.assertGreaterEqual(len(registration_challenge), 32)
        self.assertGreaterEqual(len(authentication_challenge), 32)
        self.assertEqual(
            registration["authenticatorSelection"]["residentKey"], "required"
        )
        self.assertEqual(
            registration["authenticatorSelection"]["userVerification"], "required"
        )
        self.assertEqual(authentication["userVerification"], "required")
        self.assertEqual(authentication["rpId"], "localhost")

    def test_session_tokens_are_opaque_and_only_hash_is_stable(self) -> None:
        import sys

        sys.path.insert(0, str(API_ROOT))
        from app.passkey_auth import opaque_token, token_sha256

        first, second = opaque_token(), opaque_token()
        self.assertNotEqual(first, second)
        self.assertGreaterEqual(len(first), 64)
        self.assertEqual(len(token_sha256(first)), 64)
        self.assertEqual(token_sha256(first), token_sha256(first))

    def test_http_contract_removes_installation_secret_from_urls(self) -> None:
        main = (API_ROOT / "app" / "main.py").read_text(encoding="utf-8")
        login = (API_ROOT / "static" / "login.html").read_text(encoding="utf-8")
        compose = (SOURCE_ROOT / "payload" / "compose.yaml").read_text(encoding="utf-8")
        installer = (SOURCE_ROOT / "src" / "installer.c").read_text(encoding="utf-8")
        starter = (SOURCE_ROOT / "payload" / "start-hdp.cmd").read_text(encoding="utf-8")
        for marker in (
            '/api/auth/register/options',
            '/api/auth/register/verify',
            '/api/auth/authenticate/options',
            '/api/auth/authenticate/verify',
            '/api/auth/logout',
            'secure=HDP_COOKIE_SECURE',
            'token_sha256(token)',
        ):
            self.assertIn(marker, main)
        self.assertIn("navigator.credentials.create", login)
        self.assertIn("navigator.credentials.get", login)
        self.assertIn("HDP_AUTH_MODE: ${HDP_AUTH_MODE:-passkey}", compose)
        self.assertNotIn("?token=%ls", installer)
        self.assertNotIn("?token=%HDP_LOCAL_TOKEN%", starter)

    def test_migration_persists_credentials_challenges_and_hashed_sessions(self) -> None:
        migrations = (API_ROOT / "app" / "migrations.py").read_text(encoding="utf-8")
        self.assertIn('version="6.0.0-008-passkey-operator-auth"', migrations)
        self.assertIn("CREATE TABLE IF NOT EXISTS operator_webauthn_credentials", migrations)
        self.assertIn("CREATE TABLE IF NOT EXISTS operator_auth_challenges", migrations)
        self.assertIn("CREATE TABLE IF NOT EXISTS operator_sessions", migrations)
        self.assertIn("token_sha256 CHAR(64) NOT NULL UNIQUE", migrations)


if __name__ == "__main__":
    unittest.main()

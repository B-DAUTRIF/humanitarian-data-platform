#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import psycopg
from psycopg.types.json import Jsonb
from playwright.sync_api import sync_playwright


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def navigation_counter(page):
    events: list[str] = []

    def record(frame):
        if frame == page.main_frame:
            events.append(frame.url)

    page.on("framenavigated", record)
    return events


def insert_test_session(database_url: str, token: str) -> uuid.UUID:
    credential_uuid = uuid.uuid4()
    now = datetime.now(UTC)
    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute(
            """
            INSERT INTO operator_webauthn_credentials
                (id,credential_id,public_key,sign_count,transports,aaguid,device_type,
                 backed_up,label,created_at,last_used_at,revoked_at)
            VALUES (%s,%s,%s,0,%s,%s,%s,FALSE,%s,%s,%s,NULL)
            """,
            (
                credential_uuid,
                b"hdp-browser-bootstrap-credential",
                b"synthetic-public-key-not-used-for-bootstrap-test",
                Jsonb([]),
                "00000000-0000-0000-0000-000000000000",
                "single_device",
                "Bootstrap E2E synthetic credential",
                now,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO operator_sessions
                (id,token_sha256,credential_id,created_at,expires_at,last_seen_at,revoked_at)
            VALUES (%s,%s,%s,%s,%s,%s,NULL)
            """,
            (
                uuid.uuid4(),
                hashlib.sha256(token.encode("utf-8")).hexdigest(),
                credential_uuid,
                now,
                now + timedelta(minutes=10),
                now,
            ),
        )
    return credential_uuid


def expire_test_session(database_url: str, token: str) -> None:
    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute(
            """
            UPDATE operator_sessions
            SET expires_at=%s
            WHERE token_sha256=%s
            """,
            (
                datetime.now(UTC) - timedelta(minutes=1),
                hashlib.sha256(token.encode("utf-8")).hexdigest(),
            ),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="HDP V6 passkey bootstrap browser regression test")
    parser.add_argument("--base-url", default="http://127.0.0.1:18081")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    database_url = os.environ["DATABASE_URL"]
    parsed = urlparse(base)
    host = parsed.hostname or "127.0.0.1"

    report: dict[str, object] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)

        # UC-AUTH-BOOT-01: no session. Root must remain on the stable login page.
        anonymous = browser.new_context()
        page = anonymous.new_page()
        navigations = navigation_counter(page)
        response = page.goto(base + "/", wait_until="networkidle", timeout=30_000)
        require(response is not None and response.status == 200, "Anonymous root did not return HTTP 200")
        page.wait_for_selector("#authenticate, #register", timeout=10_000)
        time.sleep(2)
        require(page.title().startswith("Connexion"), f"Unexpected anonymous title: {page.title()}")
        require(len(navigations) == 1, f"Reload loop detected without session: {navigations}")
        status = anonymous.request.get(base + "/api/auth/status")
        require(status.status == 200 and status.json()["mode"] == "passkey", "Passkey auth status unavailable")
        protected = anonymous.request.get(base + "/api/projects")
        require(protected.status == 401, f"Protected API should be 401 anonymously, got {protected.status}")
        time.sleep(1)
        require(len(navigations) == 1, "Protected API 401 triggered browser navigation")
        report["anonymous_navigation_count"] = len(navigations)
        anonymous.close()

        # UC-AUTH-BOOT-02: valid synthetic server-side session. The real V6 UI must load once.
        token = "hdp-passkey-bootstrap-e2e-session-token"
        insert_test_session(database_url, token)
        authenticated = browser.new_context()
        authenticated.add_cookies(
            [
                {
                    "name": "hdp_session",
                    "value": token,
                    "domain": host,
                    "path": "/",
                    "httpOnly": True,
                    "secure": False,
                    "sameSite": "Strict",
                }
            ]
        )
        page = authenticated.new_page()
        auth_navigations = navigation_counter(page)
        response = page.goto(base + "/", wait_until="domcontentloaded", timeout=30_000)
        require(response is not None and response.status == 200, "Authenticated root did not return HTTP 200")
        page.wait_for_selector("[data-view]", timeout=20_000)
        page.wait_for_timeout(2500)
        require(page.title() == "Humanitarian Data Platform 6.0.0", f"Authenticated UI title incorrect: {page.title()}")
        require(len(auth_navigations) == 1, f"Unexpected navigation while authenticated: {auth_navigations}")
        page.locator('[data-view="source-settings"]').click()
        page.locator("#native-api-inventory-panel").wait_for(state="visible", timeout=20_000)
        require(page.locator("#inv-source option").count() == 10, "Authenticated inventory bootstrap failed")
        report["authenticated_navigation_count"] = len(auth_navigations)

        # UC-AUTH-BOOT-03: expire the same server-side session. A fresh root request must
        # transition to login exactly once and remain stable, never reload recursively.
        expire_test_session(database_url, token)
        expired = browser.new_context()
        expired.add_cookies(
            [
                {
                    "name": "hdp_session",
                    "value": token,
                    "domain": host,
                    "path": "/",
                    "httpOnly": True,
                    "secure": False,
                    "sameSite": "Strict",
                }
            ]
        )
        page = expired.new_page()
        expired_navigations = navigation_counter(page)
        response = page.goto(base + "/", wait_until="networkidle", timeout=30_000)
        require(response is not None and response.status == 200, "Expired-session root did not return HTTP 200")
        page.wait_for_selector("#authenticate", timeout=10_000)
        page.wait_for_timeout(2500)
        require(page.title().startswith("Connexion"), "Expired session did not return to login")
        require(len(expired_navigations) == 1, f"Reload loop detected after session expiry: {expired_navigations}")
        report["expired_navigation_count"] = len(expired_navigations)
        expired.close()
        authenticated.close()
        browser.close()

    report["result"] = "passed"
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(json.dumps({"result": "failed", "error": str(exc)}, ensure_ascii=False), file=os.sys.stderr)
        raise SystemExit(1)

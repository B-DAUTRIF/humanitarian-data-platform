#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


REQUIRED_VIEWS = (
    "search",
    "intelligence",
    "actions",
    "sources",
    "source-settings",
    "inventory",
    "projects",
    "data",
    "rss",
    "spip",
    "mail",
    "timeline",
    "map",
    "scripts",
    "notebooks",
    "schedules",
    "sql",
    "backups",
    "technologies",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Recette navigateur HDP V6")
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    failures: list[str] = []
    api_errors: list[str] = []
    console_errors: list[str] = []
    visited: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            extra_http_headers={
                "Authorization": f"Bearer {args.token}",
                "x-hdp-csrf": "1",
            }
        )
        page = context.new_page()
        page.on("pageerror", lambda error: failures.append(f"pageerror: {error}"))
        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )
        page.on(
            "response",
            lambda response: api_errors.append(f"{response.status} {response.url}")
            if "/api/" in response.url and response.status >= 400
            else None,
        )

        response = page.goto(base + "/", wait_until="domcontentloaded", timeout=30_000)
        require(response is not None and response.status == 200, "La page racine ne répond pas HTTP 200")
        page.wait_for_selector("[data-view]", timeout=20_000)

        nav_views = set(page.locator("[data-view]").evaluate_all("els => els.map(e => e.dataset.view)"))
        section_views = set(
            page.locator('section[id^="view-"]').evaluate_all(
                "els => els.map(e => e.id.substring('view-'.length))"
            )
        )
        require(set(REQUIRED_VIEWS) <= nav_views, f"Onglets absents: {sorted(set(REQUIRED_VIEWS)-nav_views)}")
        require(set(REQUIRED_VIEWS) <= section_views, f"Vues absentes: {sorted(set(REQUIRED_VIEWS)-section_views)}")

        for view in REQUIRED_VIEWS:
            trigger = page.locator(f'[data-view="{view}"]').first
            require(trigger.count() == 1, f"Déclencheur de vue absent: {view}")
            trigger.click(timeout=10_000)
            section = page.locator(f"#view-{view}")
            section.wait_for(state="visible", timeout=10_000)
            require(section.is_visible(), f"Vue non visible après clic: {view}")
            visited.append(view)

        # The exhaustive API inventory must be injected into the actual source-settings view,
        # not merely exist on a separate audit page.
        page.locator('[data-view="source-settings"]').first.click()
        panel = page.locator("#native-api-inventory-panel")
        panel.wait_for(state="visible", timeout=20_000)
        require(page.locator("#inv-source option").count() == 10, "L'inventaire natif n'expose pas dix sources")
        require(page.locator("#inv-operation option").count() > 0, "Aucune opération dans l'inventaire natif")
        page.locator("#inv-params [data-inventory-param]").first.wait_for(state="visible", timeout=10_000)
        require(page.locator("#inv-params [data-inventory-param]").count() > 0, "Aucun paramètre natif rendu")

        # Check authenticated API access from the same browser context. RSS, backups and
        # catalog are deliberately invoked without optional filters: these calls previously
        # exposed PostgreSQL NULL-parameter typing failures and are now permanent regressions.
        endpoints = (
            "/api/health",
            "/api-inventory/sources",
            "/api/projects",
            "/api/v6/timeline",
            "/api/v6/rss/candidates",
            "/api/v6/backups",
            "/api/v6/catalog",
        )
        api_status: dict[str, int] = {}
        for endpoint in endpoints:
            result = context.request.get(base + endpoint)
            api_status[endpoint] = result.status
            require(result.ok, f"API navigateur en échec: {endpoint} -> {result.status}")

        browser.close()

    require(not failures, "; ".join(failures))
    local_api_errors = [item for item in api_errors if item.startswith(("4", "5")) and base in item]
    require(not local_api_errors, f"Réponses API HDP en erreur: {local_api_errors[:20]}")

    report: dict[str, Any] = {
        "result": "passed",
        "visited_views": visited,
        "view_count": len(visited),
        "api_status": api_status,
        "console_errors": console_errors,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, PlaywrightError) as exc:
        print(json.dumps({"result": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)

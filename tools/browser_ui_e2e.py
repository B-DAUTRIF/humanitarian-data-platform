#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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


def expect_status(response: Any, expected: int, label: str) -> Any:
    require(response.status == expected, f"{label}: HTTP {response.status}, attendu {expected}: {response.text()[:500]}")
    return response


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
    workflow: dict[str, Any] = {}

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
        body_text = page.locator("body").inner_text()
        for mode in ("Simple", "Avancé", "Expert"):
            require(mode in body_text, f"Mode utilisateur absent de l'interface: {mode}")

        for view in REQUIRED_VIEWS:
            trigger = page.locator(f'[data-view="{view}"]').first
            require(trigger.count() == 1, f"Déclencheur de vue absent: {view}")
            trigger.click(timeout=10_000)
            section = page.locator(f"#view-{view}")
            section.wait_for(state="visible", timeout=10_000)
            require(section.is_visible(), f"Vue non visible après clic: {view}")
            visited.append(view)

        # The exhaustive API inventory must be injected into the actual source-settings view.
        page.locator('[data-view="source-settings"]').first.click()
        panel = page.locator("#native-api-inventory-panel")
        panel.wait_for(state="visible", timeout=20_000)
        require(page.locator("#inv-source option").count() == 10, "L'inventaire natif n'expose pas dix sources")
        require(page.locator("#inv-operation option").count() > 0, "Aucune opération dans l'inventaire natif")
        page.locator("#inv-params [data-inventory-param]").first.wait_for(state="visible", timeout=10_000)
        require(page.locator("#inv-params [data-inventory-param]").count() > 0, "Aucun paramètre natif rendu")

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

        # Real API workflow against the same PostgreSQL instance used by the browser.
        project_a = expect_status(
            context.request.post(base + "/api/projects", data={"name": "Qualification E2E A", "description": "Projet isolé A"}),
            201,
            "création projet A",
        ).json()
        project_b = expect_status(
            context.request.post(base + "/api/projects", data={"name": "Qualification E2E B", "description": "Projet isolé B"}),
            201,
            "création projet B",
        ).json()
        project_a_id, project_b_id = project_a["id"], project_b["id"]
        workflow["projects"] = [project_a_id, project_b_id]

        expect_status(
            context.request.patch(base + f"/api/projects/{project_a_id}", data={"name": "Qualification E2E A modifié"}),
            200,
            "modification projet A",
        )
        projects = expect_status(context.request.get(base + "/api/projects"), 200, "liste projets").json()
        require(any(row["id"] == project_a_id and row["name"] == "Qualification E2E A modifié" for row in projects), "Projet A modifié absent")

        preferences = {
            "auto_download": False,
            "max_download_bytes": 10_000_000,
            "max_resources_per_acquisition": 8,
            "allowed_formats": ["csv", "geojson"],
        }
        expect_status(context.request.put(base + f"/api/projects/{project_a_id}/preferences", data=preferences), 200, "préférences projet A")
        stored_preferences = expect_status(context.request.get(base + f"/api/projects/{project_a_id}/preferences"), 200, "lecture préférences projet A").json()
        require(stored_preferences["max_resources_per_acquisition"] == 8, "Préférence projet non persistée")

        source_parameters = {
            "query": "cholera",
            "date_from": "2026-03-01",
            "date_to": "2026-03-31",
            "location": "Mozambique",
            "result_limit": 7,
            "auto_download": False,
        }
        source_payload = {"enabled": True, "parameters": source_parameters, "schedule_defaults": {}}
        expect_status(context.request.put(base + f"/api/projects/{project_a_id}/sources/hdx", data=source_payload), 200, "configuration HDX projet A")
        source_b = expect_status(context.request.get(base + f"/api/projects/{project_b_id}/sources/hdx"), 200, "configuration HDX projet B").json()
        require(source_b["parameters"].get("query", "") != "cholera", "Les paramètres HDX ont fui entre projets")
        preview = expect_status(
            context.request.post(base + f"/api/projects/{project_a_id}/sources/hdx/preview", data={"parameters": {}}),
            200,
            "preview HDX projet A",
        ).json()
        require(preview["parameters"]["query"] == "cholera", "La valeur UI/HDP query n'atteint pas le preview")
        require(preview["request"]["query_parameters"].get("q") == "cholera", "query HDP non transmise à q HDX")
        require(preview["request"]["query_parameters"].get("rows") == 7, "result_limit HDP non transmis à rows HDX")
        workflow["hdx_request"] = preview["request"]["query_parameters"]

        csv_bytes = b"iso3,cases\nMOZ,120\n"
        expected_sha = hashlib.sha256(csv_bytes).hexdigest()
        upload = expect_status(
            context.request.post(
                base + f"/api/projects/{project_a_id}/uploads",
                multipart={
                    "file": {"name": "cholera.csv", "mimeType": "text/csv", "buffer": csv_bytes},
                    "category": "data",
                    "title": "Cholera Mozambique",
                    "geographic_scope": "Mozambique",
                    "update_frequency": "daily",
                },
            ),
            201,
            "upload CSV projet A",
        ).json()
        resource_id = upload["id"]
        require(upload["sha256"] == expected_sha, "SHA-256 upload incorrect")
        resources_a = expect_status(context.request.get(base + f"/api/resources?project_id={project_a_id}"), 200, "ressources projet A").json()
        resources_b = expect_status(context.request.get(base + f"/api/resources?project_id={project_b_id}"), 200, "ressources projet B").json()
        require(any(row["id"] == resource_id and row["sha256"] == expected_sha for row in resources_a), "Ressource uploadée absente du projet A")
        require(all(row["id"] != resource_id for row in resources_b), "Ressource du projet A visible dans le projet B")
        downloaded = expect_status(context.request.get(base + f"/api/resources/{resource_id}/file"), 200, "récupération fichier uploadé")
        require(downloaded.body() == csv_bytes, "Le fichier récupéré diffère du fichier uploadé")
        workflow["upload_sha256"] = expected_sha

        sql_read = expect_status(
            context.request.post(base + f"/api/projects/{project_a_id}/sql/query", data={"query": "SELECT count(*) AS n FROM hdp_resources", "max_rows": 10}),
            200,
            "SQL read-only SELECT",
        ).json()
        require(sql_read["row_count"] == 1 and int(sql_read["rows"][0][0]) >= 1, "SQL read-only ne voit pas la ressource du projet")
        sql_write = context.request.post(base + f"/api/projects/{project_a_id}/sql/query", data={"query": "DELETE FROM hdp_resources", "max_rows": 10})
        require(sql_write.status == 422, f"Une écriture SQL a été acceptée: HTTP {sql_write.status}")
        workflow["sql_write_rejected"] = True

        expect_status(context.request.delete(base + f"/api/projects/{project_b_id}"), 204, "archivage projet B")
        expect_status(context.request.delete(base + f"/api/projects/{project_a_id}"), 204, "archivage projet A")
        remaining = expect_status(context.request.get(base + "/api/projects"), 200, "liste projets après archivage").json()
        require(all(row["id"] not in {project_a_id, project_b_id} for row in remaining), "Projet archivé encore exposé")

        browser.close()

    require(not failures, "; ".join(failures))
    # Expected negative requests are issued through APIRequestContext and therefore do not
    # pollute page response monitoring. Any browser-driven 4xx/5xx remains a failure.
    local_api_errors = [item for item in api_errors if item.startswith(("4", "5")) and base in item]
    require(not local_api_errors, f"Réponses API HDP en erreur: {local_api_errors[:20]}")

    report: dict[str, Any] = {
        "result": "passed",
        "visited_views": visited,
        "view_count": len(visited),
        "api_status": api_status,
        "workflow": workflow,
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

#!/usr/bin/env python3
from __future__ import annotations

import base64
import csv
import json
import lzma
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.0.0"


def replace(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if old in text:
        p.write_text(text.replace(old, new), encoding="utf-8")


def normalize_versions() -> None:
    for path in [
        "source/src/installer.c",
        "source/src/installer.rc",
        "source/build-windows.ps1",
        "source/payload/api/app/main.py",
        "source/payload/api/static/index.html",
    ]:
        replace(path, "5.0.2", VERSION)
        replace(path, "5,0,2,0", "6,0,0,0")

    # Use the same strict single-stream decoder in the runtime inventory loader.
    p = ROOT / "source/payload/api/app/api_inventory.py"
    text = p.read_text(encoding="utf-8")
    old = '    rows = json.loads(lzma.decompress(base64.b85decode(encoded.encode("ascii"))).decode("utf-8"))'
    new = '''    decoded = base64.b85decode(encoded.encode("ascii"))\n    decoder = lzma.LZMADecompressor()\n    payload = decoder.decompress(decoded)\n    if not decoder.eof:\n        raise RuntimeError("Inventaire API V6: flux LZMA incomplet")\n    rows = json.loads(payload.decode("utf-8"))'''
    if old in text:
        p.write_text(text.replace(old, new), encoding="utf-8")


def ensure_inventory_tab() -> None:
    p = ROOT / "source/payload/api/static/index.html"
    text = p.read_text(encoding="utf-8")
    if 'data-view="inventory"' not in text:
        anchor = '    <button data-view="source-settings">Paramètres des sources</button>'
        if anchor not in text:
            raise SystemExit("Navigation principale introuvable pour insertion Inventaire API")
        text = text.replace(anchor, anchor + '\n    <button data-view="inventory">Inventaire API</button>')
    if 'id="view-inventory"' not in text:
        marker = '  <section id="view-projects"'
        if marker not in text:
            raise SystemExit("Point d’insertion de la vue Inventaire introuvable")
        section = '''  <section id="view-inventory" class="view">\n    <div class="card">\n      <h2>Inventaire exhaustif des paramètres API</h2>\n      <p>Cette rubrique expose l’intégralité des paramètres catalogués pour chaque source, y compris les champs informatifs ou en lecture seule. Recherche textuelle et filtre par source sont disponibles.</p>\n      <div class="actions"><a class="button" href="/api-inventory" target="_blank" rel="noopener">Ouvrir l’inventaire dans une fenêtre dédiée</a></div>\n      <iframe class="inventory-frame" src="/api-inventory" title="Inventaire exhaustif des paramètres API HDP V6"></iframe>\n    </div>\n  </section>\n\n'''
        text = text.replace(marker, section + marker)
    if '.inventory-frame {' not in text:
        css_anchor = '    .table-wrap { overflow:auto; max-height:520px; }'
        if css_anchor not in text:
            raise SystemExit("Point d’insertion CSS Inventaire introuvable")
        text = text.replace(css_anchor, css_anchor + '\n    .inventory-frame { width:100%; min-height:760px; border:1px solid var(--line); border-radius:12px; background:#fff; margin-top:16px; }')
    p.write_text(text, encoding="utf-8")


def decode_inventory(encoded: str) -> list[dict]:
    decoded = base64.b85decode(encoded.encode("ascii"))
    decoder = lzma.LZMADecompressor()
    payload = decoder.decompress(decoded)
    if not decoder.eof:
        raise SystemExit("Inventaire API: flux LZMA incomplet")
    rows = json.loads(payload.decode("utf-8"))
    if not isinstance(rows, list):
        raise SystemExit("Inventaire API: racine JSON non tabulaire")
    return rows


def load_inventory() -> list[dict]:
    parts = ROOT / "source/payload/api/app/api_inventory_parts"
    encoded = "".join(p.read_text(encoding="ascii") for p in sorted(parts.glob("part*.txt")))
    rows = decode_inventory(encoded)
    if len(rows) != 2057:
        raise SystemExit(f"Inventaire invalide: {len(rows)} paramètres au lieu de 2057")
    sources = {str(r.get("source_slug", "")) for r in rows}
    operations = {(r.get("Source"), r.get("Opération"), r.get("Endpoint"), r.get("Méthode")) for r in rows}
    if len(sources) != 10 or len(operations) != 440:
        raise SystemExit(f"Inventaire invalide: {len(sources)} sources / {len(operations)} opérations")
    return rows


def inventory_docs(rows: list[dict]) -> None:
    docs = ROOT / "docs/versions/6.0.0"
    docs.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("Source", "Source inconnue"))].append(row)

    out = [
        "# HDP V6.0.0 — Inventaire exhaustif des paramètres API", "",
        f"Inventaire généré automatiquement depuis le catalogue canonique embarqué. **{len(rows)} paramètres**, **{len(grouped)} sources**.", "",
        "Chaque ligne indique l’opération, la méthode HTTP, l’endpoint, le paramètre, son emplacement, son type, son caractère obligatoire, le contrôle UI recommandé, sa classe d’accès et sa description.", "",
    ]
    for source in sorted(grouped):
        items = grouped[source]
        ops = {(r.get("Opération"), r.get("Endpoint"), r.get("Méthode")) for r in items}
        out += [f"## {source}", "", f"**{len(items)} paramètres · {len(ops)} opérations**", "",
                "| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | Obligatoire | Contrôle UI | Accès | Description |",
                "|---|---|---|---|---|---|---|---|---|---|"]
        for r in items:
            def esc(v): return str(v if v is not None else "").replace("|", "\\|").replace("\n", " ")
            access = "Lecture seule" if r.get("readonly") else r.get("Classe d’accès", "")
            control = r.get("Contrôle recommandé") or r.get("widget") or ""
            out.append("| " + " | ".join(esc(x) for x in [r.get("Opération"), r.get("Méthode"), r.get("Endpoint"), r.get("Paramètre"), r.get("Emplacement"), r.get("Type"), r.get("Obligatoire"), control, access, r.get("Description officielle / synthèse")]) + " |")
        out.append("")
    (docs / "API_INVENTORY.md").write_text("\n".join(out), encoding="utf-8")

    fields = ["Source", "source_slug", "Opération", "Méthode", "Endpoint", "Paramètre", "Emplacement", "Type", "Obligatoire", "Contrôle recommandé", "Classe d’accès", "Description officielle / synthèse", "readonly"]
    with (docs / "API_INVENTORY.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def audit_docs(rows: list[dict]) -> None:
    docs = ROOT / "docs/versions/6.0.0"
    source_counts = Counter(str(r.get("Source", "")) for r in rows)
    operation_count = len({(r.get("Source"), r.get("Opération"), r.get("Endpoint"), r.get("Méthode")) for r in rows})
    audit = f'''# Audit fonctionnel et interface — HDP V6.0.0

## Critères bloquants

La V6 n'est qualifiée que si la version 6.0.0 est native dans l’installateur, ses ressources Windows, le build, le backend et l’interface; si `app.main_v6:app` est le point d’entrée; si l’inventaire contient exactement 2 057 paramètres, 10 sources et 440 opérations; et si l’inventaire est accessible depuis l’interface principale.

## Inventaire API

- Paramètres: **{len(rows)}**
- Sources: **{len(source_counts)}**
- Opérations: **{operation_count}**
- Interface principale: onglet **Inventaire API**
- Vue dédiée: `/api-inventory`
- API: `/api-inventory/data`, `/api-inventory/sources`, `/api-inventory/source/{{slug}}`

Tous les enregistrements du catalogue sont affichables. Les paramètres `readonly` restent visibles comme informations.

## Matrice fonctionnelle

| Domaine | Backend / composant | Interface | État |
|---|---|---|---|
| Recherche fédérée multi-source | `federated_search.py`, sources sanitaires/humanitaires | Recherche, Data Grid & SIGNALS | Implémenté |
| Paramétrage individualisé des sources | `source_registry.py` | Paramètres des sources | Implémenté |
| Inventaire exhaustif API | `api_inventory.py` | Inventaire API | Implémenté, bloquant CI |
| Projets et préférences | `main.py`, `project_integrations.py` | Projets & préférences | Implémenté |
| COD officiels / M49 / HDX | `project_integrations.py` | Projets / recherche | Implémenté |
| Données locales / uploads | `local_library.py` | Données locales | Implémenté |
| Flux RSS | `rss_registry.py` | Flux RSS | Implémenté |
| Carte | `map_utils.py` | Carte | Implémenté |
| Scripts Python/R | `processing_recipes.py`, `script_runtime.py` | Scripts | Implémenté |
| Notebooks | API / runtime | Notebooks | Implémenté |
| Planifications | `scheduler_utils.py` | Planifications / Chronologie | Implémenté |
| SQL lecture seule | `sql_workspace.py` | Base SQL | Implémenté |
| GitHub par projet / synchronisation | `github_sync.py` | Projets & préférences | Implémenté |
| Technologies et code | `technology_registry.py` | USER · Technologies & code | Implémenté |
| Installation Windows | `installer.c`, `build-windows.ps1` | Installateur natif | Version native 6.0.0 |
| R/plumber optionnel | Compose / service R | Installateur + scripts | Implémenté |

## Limites

La CI qualifie le code, les tests, le PE x64 et l’intégrité du catalogue. Une exécution sur le poste Windows cible reste nécessaire pour Docker Desktop, WSL, proxy/réseau et disponibilité des API externes.
'''
    (docs / "AUDIT_FONCTIONNEL_UI.md").write_text(audit, encoding="utf-8")
    (docs / "README.md").write_text('''# Documentation HDP V6.0.0

- `AUDIT_FONCTIONNEL_UI.md` — audit fonctionnel et interface.
- `API_INVENTORY.md` — inventaire exhaustif groupé par source.
- `API_INVENTORY.csv` — inventaire tabulaire UTF-8.
- `ARCHITECTURE.md` — architecture.
- `USER_GUIDE.md` — guide utilisateur.
- `DEVELOPER_GUIDE.md` — guide développeur.
- `CHANGELOG_CONSOLIDE.md` — évolution consolidée.
- `CONSOLIDATION_BRANCHES.md` — traçabilité de consolidation.
- `qualification/` — preuves de qualification.

Dans HDP, ouvrir **Inventaire API** pour rechercher dans les 2 057 paramètres et filtrer par source. Tous les paramètres sont visibles; les non-modifiables sont explicitement en lecture seule.
''', encoding="utf-8")


def main() -> None:
    normalize_versions()
    ensure_inventory_tab()
    rows = load_inventory()
    inventory_docs(rows)
    audit_docs(rows)
    print(f"HDP V{VERSION}: {len(rows)} paramètres / 10 sources / 440 opérations documentés")


if __name__ == "__main__":
    main()

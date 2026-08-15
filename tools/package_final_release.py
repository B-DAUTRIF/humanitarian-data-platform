#!/usr/bin/env python3
"""Conditionne de façon reproductible les livrables finaux HDP 3.0.0."""

from __future__ import annotations

import hashlib
import shutil
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "v3.0.0"
VERSION = "3.0.0"
STAMP = (2026, 8, 15, 12, 5, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_zip(target: Path, entries: list[tuple[Path, str]]) -> None:
    seen: set[str] = set()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, name in sorted(entries, key=lambda item: item[1].casefold()):
            if name in seen:
                raise ValueError(f"entrée ZIP en double : {name}")
            seen.add(name)
            data = source.read_bytes()
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if source.suffix in {".sh", ".py"} else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.create_system = 3
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def tree_entries(directory: Path, prefix: str, exclude: set[str] | None = None) -> list[tuple[Path, str]]:
    excluded = exclude or set()
    result: list[tuple[Path, str]] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        if any(part in excluded for part in relative.parts):
            continue
        result.append((path, f"{prefix}/{relative.as_posix()}"))
    return result


def main() -> None:
    if DIST.exists():
        raise FileExistsError(f"répertoire de sortie déjà présent : {DIST}")
    DIST.mkdir(parents=True)

    exe_name = f"HumanitarianDataPlatform_Setup_Native_GUI_v{VERSION}.exe"
    exe_sha_name = exe_name + ".sha256"
    setup_name = f"HumanitarianDataPlatform_Setup_README_v{VERSION}.txt"
    prompt_name = f"HDP_Prompt_production_global_v{VERSION}.txt"
    html_name = f"Documentation_Humanitarian_Data_Platform_v{VERSION}.html"
    pdf_name = f"Notice_detaillee_Humanitarian_Data_Platform_v{VERSION}.pdf"

    direct = {
        exe_name: ROOT / "source" / exe_name,
        exe_sha_name: ROOT / "source" / exe_sha_name,
        setup_name: ROOT / "source" / setup_name,
        "HDP_Configurer_GitHub_v3.0.0.cmd": ROOT / "source/HDP_Configurer_GitHub_v3.0.0.cmd",
        "HDP_Diagnostic_v3.0.0.cmd": ROOT / "source/HDP_Diagnostic_v3.0.0.cmd",
        prompt_name: ROOT / prompt_name,
        html_name: ROOT / "docs" / html_name,
        pdf_name: ROOT / "docs" / pdf_name,
        "Rapport_validation_HDP_v3.0.0_final.md": ROOT / "Rapport_validation_HDP_v3.0.0_final.md",
        "Matrice_compatibilite_HDP_v3.0.0_final.md": ROOT / "Matrice_compatibilite_HDP_v3.0.0_final.md",
        "Registre_decisions_HDP_v3.0.0_final.md": ROOT / "Registre_decisions_HDP_v3.0.0_final.md",
        "LOG-Huma_2026_15_08_12-01-45_004.log": ROOT / "LOG-Huma_2026_15_08_12-01-45_004.log",
    }
    for name, source in direct.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, DIST / name)

    windows_name = f"HumanitarianDataPlatform_Windows_v{VERSION}.zip"
    windows_root = f"HumanitarianDataPlatform_Windows_v{VERSION}"
    windows_files = [exe_name, exe_sha_name, setup_name, "HDP_Configurer_GitHub_v3.0.0.cmd", "HDP_Diagnostic_v3.0.0.cmd", pdf_name]
    write_zip(DIST / windows_name, [(DIST / name, f"{windows_root}/{name}") for name in windows_files])

    source_name = f"HumanitarianDataPlatform_Source_v{VERSION}.zip"
    source_root = f"HumanitarianDataPlatform_Source_v{VERSION}"
    source_entries: list[tuple[Path, str]] = []
    for name in [
        "README.md", "CHANGELOG.md", prompt_name,
        "Rapport_validation_HDP_v3.0.0_final.md",
        "Matrice_compatibilite_HDP_v3.0.0_final.md",
        "Registre_decisions_HDP_v3.0.0_final.md",
        "LOG-Huma_2026_15_08_12-01-45_004.log",
    ]:
        source_entries.append((ROOT / name, f"{source_root}/{name}"))
    source_entries.extend(tree_entries(ROOT / "docs", f"{source_root}/docs"))
    source_entries.extend(tree_entries(ROOT / "tools", f"{source_root}/tools", {"__pycache__"}))
    for path in sorted((ROOT / "source").rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT / "source")
        if "__pycache__" in relative.parts:
            continue
        if path.suffix.lower() in {".exe", ".pdb", ".res"}:
            continue
        source_entries.append((path, f"{source_root}/source/{relative.as_posix()}"))
    write_zip(DIST / source_name, source_entries)

    manifest_name = f"MANIFESTE_HumanitarianDataPlatform_v{VERSION}.txt"
    manifest = f"""Humanitarian Data Platform {VERSION} — manifeste final
========================================================

Date de gel : 15 août 2026
Branche cible : B-DAUTRIF/humanitarian-data-platform / main
Parent GitHub observé avant publication : d99cad9026dd57eb7dddbe71a62ac12e6d1e6502

VALIDATION
- tests Python : 68/68 réussis
- API principale : 47 chemins / 63 opérations OpenAPI
- passerelle GitHub : 11 chemins / 12 opérations OpenAPI
- Compose : 6 services, YAML valide
- runner C17 : compilation stricte, succès, heartbeat et timeout validés
- payload : 39 fichiers reconstruits octet pour octet
- installateur : PE32+ GUI x64, HIGH_ENTROPY_VA, DYNAMIC_BASE, NX_COMPAT
- documentation : HTML et PDF A4 36 pages, rendu inspecté

EMPREINTES PRINCIPALES
- {exe_name}: {sha256(DIST / exe_name)}
- {windows_name}: {sha256(DIST / windows_name)}
- {source_name}: {sha256(DIST / source_name)}
- {html_name}: {sha256(DIST / html_name)}
- {pdf_name}: {sha256(DIST / pdf_name)}
- {prompt_name}: {sha256(DIST / prompt_name)}

LIMITES DE RECETTE
- Docker absent de l'environnement de construction : services non démarrés.
- Windows absent : installation et mise à niveau 2.5.0 non exécutées réellement.
- L'installateur n'est pas signé avec un certificat d'éditeur.

CONTENU
- installateur et empreinte ; paquet Windows ; archive des sources ;
- documentation Markdown, HTML et PDF ; prompt global autonome ;
- cahier des charges, référence API, architecture et sécurité ;
- rapports de validation/compatibilité/décisions et journaux LOG-Huma ;
- manifeste et sommes SHA-256.

L'archive complète ne contient pas sa propre empreinte. Celle-ci est fournie
dans HumanitarianDataPlatform_Archive_complete_v3.0.0.zip.sha256.
"""
    (DIST / manifest_name).write_text(manifest, encoding="utf-8")

    sums_name = "SHA256SUMS.txt"
    included_names = sorted(path.name for path in DIST.iterdir() if path.is_file() and path.name != sums_name)
    sums = "".join(f"{sha256(DIST / name)}  {name}\n" for name in included_names)
    (DIST / sums_name).write_text(sums, encoding="utf-8")

    complete_name = f"HumanitarianDataPlatform_Archive_complete_v{VERSION}.zip"
    complete_root = f"HumanitarianDataPlatform_v{VERSION}"
    complete_entries = [(path, f"{complete_root}/{path.name}") for path in sorted(DIST.iterdir()) if path.is_file()]
    complete_entries.extend(tree_entries(ROOT / "docs", f"{complete_root}/documentation_markdown"))
    complete_entries.extend([
        (ROOT / "README.md", f"{complete_root}/README.md"),
        (ROOT / "CHANGELOG.md", f"{complete_root}/CHANGELOG.md"),
        (ROOT / "LOG-Huma_2026_15_08_11-24-32_003.log", f"{complete_root}/historique/LOG-Huma_2026_15_08_11-24-32_003.log"),
        (ROOT / "HDP_v3.0.0_Iteration_2_Rapport_validation.md", f"{complete_root}/historique/HDP_v3.0.0_Iteration_2_Rapport_validation.md"),
        (ROOT / "HDP_v3.0.0_Iteration_2_Matrice_compatibilite.md", f"{complete_root}/historique/HDP_v3.0.0_Iteration_2_Matrice_compatibilite.md"),
        (ROOT / "HDP_v3.0.0_Iteration_2_Registre_decisions.md", f"{complete_root}/historique/HDP_v3.0.0_Iteration_2_Registre_decisions.md"),
        (ROOT / "HDP_v3.0.0_Iteration_2_Point_de_reprise.md", f"{complete_root}/historique/HDP_v3.0.0_Iteration_2_Point_de_reprise.md"),
    ])
    write_zip(DIST / complete_name, complete_entries)
    complete_sha = sha256(DIST / complete_name)
    (DIST / f"{complete_name}.sha256").write_text(f"{complete_sha}  {complete_name}\n", encoding="ascii")

    print(f"Livrables créés dans {DIST}")
    for path in sorted(DIST.iterdir()):
        if path.is_file():
            print(f"{sha256(path)}  {path.name}  {path.stat().st_size}")


if __name__ == "__main__":
    main()

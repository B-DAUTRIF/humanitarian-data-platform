#!/usr/bin/env python3
"""Construit de façon déterministe les livrables HDP 4.1.0."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import stat
import struct
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "v4.1.0"
VERSION = "4.1.0"
STAMP = (2026, 8, 15, 22, 30, 0)
TODO = ROOT / "TODO_Mises_a_jour_HDP.md"
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", "data"}
EXCLUDED_SUFFIXES = {".exe", ".pdb", ".pyc", ".res"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()


def include(path: Path, relative: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return True


def tree_entries(directory: Path, prefix: str) -> list[tuple[Path, str]]:
    entries: list[tuple[Path, str]] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        if include(path, relative):
            entries.append((path, f"{prefix}/{relative.as_posix()}"))
    return entries


def write_zip(target: Path, entries: list[tuple[Path, str]]) -> None:
    seen: set[str] = set()
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, name in sorted(entries, key=lambda item: item[1].casefold()):
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts:
                raise ValueError(f"chemin ZIP dangereux : {name}")
            if name in seen:
                raise ValueError(f"entrée ZIP en double : {name}")
            seen.add(name)
            info = zipfile.ZipInfo(name, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if source.suffix.lower() in {".sh", ".py"} else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.create_system = 3
            archive.writestr(
                info,
                source.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def verify_zip(path: Path) -> tuple[int, int]:
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"CRC invalide dans {path.name} : {bad}")
        infos = archive.infolist()
        for info in infos:
            pure = PurePosixPath(info.filename)
            if pure.is_absolute() or ".." in pure.parts:
                raise ValueError(f"chemin ZIP dangereux dans {path.name}")
        return len(infos), sum(info.file_size for info in infos)


def require_inputs(paths: list[Path]) -> None:
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)


def verify_windows_installer(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 0x100 or data[:2] != b"MZ":
        raise ValueError(f"installateur Windows invalide : {path}")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if pe_offset + 0x5E > len(data) or data[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError(f"signature PE absente : {path}")
    machine = struct.unpack_from("<H", data, pe_offset + 4)[0]
    optional = pe_offset + 24
    magic = struct.unpack_from("<H", data, optional)[0]
    subsystem = struct.unpack_from("<H", data, optional + 68)[0]
    characteristics = struct.unpack_from("<H", data, optional + 70)[0]
    required = 0x20 | 0x40 | 0x100  # haute entropie, ASLR et NX
    if machine != 0x8664 or magic != 0x20B or subsystem != 2:
        raise ValueError("l'installateur doit être un PE32+ GUI x64")
    if characteristics & required != required:
        raise ValueError("ASLR, NX et haute entropie doivent être activés")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--installer",
        required=True,
        type=Path,
        help="EXE 4.1.0 compilé et vérifié pour Windows x64",
    )
    parser.add_argument(
        "--installer-commit",
        default="construction-locale-zig",
        help="référence de construction ayant produit l'installateur",
    )
    args = parser.parse_args()
    installer = args.installer.resolve()
    installer_name = f"HumanitarianDataPlatform_Setup_Native_GUI_v{VERSION}.exe"
    if installer.name != installer_name:
        raise ValueError(f"nom d'installateur attendu : {installer_name}")
    require_inputs([installer])
    verify_windows_installer(installer)

    if DIST.exists():
        raise FileExistsError(
            f"répertoire de sortie déjà présent : {DIST}; le déplacer avant un nouveau gel"
        )
    source_commit = git_value("rev-parse", "HEAD")
    branch = git_value("branch", "--show-current")

    prompt = ROOT / "HDP_Prompt_production_global_v4.1.0.txt"
    html_doc = ROOT / "docs/Documentation_Humanitarian_Data_Platform_v4.1.0.html"
    pdf_doc = ROOT / "output/pdf/Notice_detaillee_Humanitarian_Data_Platform_v4.1.0.pdf"
    direct_docs = [
        prompt,
        html_doc,
        pdf_doc,
        ROOT / "docs/USER_GUIDE_V4.1.0.md",
        ROOT / "docs/CONFIGURATION_SOURCES_V4.1.0.md",
        ROOT / "docs/TECHNOLOGIES_ET_LIENS_V4.1.0.md",
        ROOT / "docs/INSTALLATION_V4.1.0.md",
        ROOT / "docs/API_REFERENCE_V4.1.0.md",
        ROOT / "docs/SOURCE_CAPABILITY_MATRIX_V4.1.0.md",
        ROOT / "docs/BACKUP_RESTORE_V4.1.0.md",
        ROOT / "docs/SECURITY_REVIEW_V4.1.0.md",
        ROOT / "docs/KNOWN_LIMITATIONS_V4.1.0.md",
        ROOT / "docs/VALIDATION_REPORT_V4.1.0.md",
        ROOT / "docs/SBOM_HDP_v4.1.0.cdx.json",
        ROOT / "docs/ARTIFACTS_V4.1.0.md",
        ROOT / "HDP_v4.1.0_Point_de_reprise.md",
        TODO,
    ]
    require_inputs(direct_docs)
    DIST.mkdir(parents=True)
    for source in direct_docs:
        shutil.copy2(source, DIST / source.name)
    shutil.copy2(installer, DIST / installer_name)
    installer_sha = sha256(DIST / installer_name)
    (DIST / f"{installer_name}.sha256").write_text(
        f"{installer_sha}  {installer_name}\n", encoding="ascii", newline="\n"
    )

    portable_name = f"HumanitarianDataPlatform_Windows_Portable_v{VERSION}.zip"
    portable_root = f"HumanitarianDataPlatform_Windows_Portable_v{VERSION}"
    portable_entries = tree_entries(ROOT / "source/payload", portable_root)
    write_zip(DIST / portable_name, portable_entries)

    source_name = f"HumanitarianDataPlatform_Source_v{VERSION}.zip"
    source_root = f"HumanitarianDataPlatform_Source_v{VERSION}"
    source_entries: list[tuple[Path, str]] = []
    for name in [
        "README.md",
        "CHANGELOG.md",
        "HDP_Prompt_production_global_v4.1.0.txt",
        "HDP_v4.1.0_Point_de_reprise.md",
    ]:
        source_entries.append((ROOT / name, f"{source_root}/{name}"))
    for directory in [".github", "docs", "source", "tools"]:
        source_entries.extend(tree_entries(ROOT / directory, f"{source_root}/{directory}"))
    source_entries.append((TODO, f"{source_root}/TODO_Mises_a_jour_HDP.md"))
    write_zip(DIST / source_name, source_entries)

    manifest_name = f"MANIFESTE_HumanitarianDataPlatform_v{VERSION}.txt"
    manifest = f"""Humanitarian Data Platform {VERSION} - manifeste de gel
======================================================

Date de gel : 15 août 2026
Branche locale : {branch}
Commit source : {source_commit}
Base GitHub 4.0.0 observée : 479b10f5c85bd213eb8465243b59b522220ece3d
Dossier Google Drive : https://drive.google.com/drive/folders/15rAjpoEWVnZfUzdmBaBOnO3sUeVZX7C0

VALIDATIONS LOCALES
- 101 tests Python réussis
- compilation Python réussie
- 2 scripts JavaScript inline analysés
- contrôles statiques de sécurité réussis
- SBOM CycloneDX 1.5 reproductible
- runner C17 compilé avec -Wall -Wextra -Werror
- payload embarqué reconstruit et contrôlé
- Compose : YAML valide, 6 services
- notice PDF rendue et inspectée, aucune page vide ou tronquée

LIVRABLE WINDOWS
- {installer_name}
- SHA-256 : {installer_sha}
- référence de construction : {args.installer_commit}
- PE32+ GUI x64, ASLR, NX et haute entropie contrôlés
- non signé Authenticode ; recette Windows 10/11 manuelle encore requise
- {portable_name}
- l'EXE historique 3.0.0 n'est ni copié ni renommé dans ce gel

CONTRÔLES EXTERNES RESTANTS
- démarrage réel Compose/PostGIS : Docker indisponible ici
- recette Windows 10/11 et mise à niveau : poste Windows indisponible
- appels directs aux API : réseau de test restreint
- signature Authenticode : certificat non fourni
- audit indépendant et choix de licence : décisions externes
- publication GitHub 4.1.0 : non effectuée par ce gel local

INTÉGRITÉ
- SHA256SUMS.txt couvre les livrables antérieurs à l'archive globale
- l'archive globale possède un fichier .sha256 adjacent
- chaque ZIP est testé par lecture CRC et validation de ses chemins
"""
    (DIST / manifest_name).write_text(manifest, encoding="utf-8", newline="\n")

    sums_name = "SHA256SUMS.txt"
    summed = sorted(path for path in DIST.iterdir() if path.is_file())
    sums = "".join(f"{sha256(path)}  {path.name}\n" for path in summed)
    (DIST / sums_name).write_text(sums, encoding="ascii", newline="\n")

    complete_name = f"HumanitarianDataPlatform_Archive_complete_v{VERSION}.zip"
    complete_root = f"HumanitarianDataPlatform_v{VERSION}"
    complete_entries = [
        (path, f"{complete_root}/{path.name}")
        for path in sorted(DIST.iterdir())
        if path.is_file()
    ]
    write_zip(DIST / complete_name, complete_entries)
    complete_sha = sha256(DIST / complete_name)
    (DIST / f"{complete_name}.sha256").write_text(
        f"{complete_sha}  {complete_name}\n", encoding="ascii", newline="\n"
    )

    print(f"Livrables créés dans {DIST}")
    for path in sorted(DIST.iterdir()):
        if not path.is_file():
            continue
        details = ""
        if path.suffix.lower() == ".zip":
            count, unpacked = verify_zip(path)
            details = f" entries={count} unpacked={unpacked}"
        print(f"{sha256(path)}  {path.name}  bytes={path.stat().st_size}{details}")


if __name__ == "__main__":
    main()

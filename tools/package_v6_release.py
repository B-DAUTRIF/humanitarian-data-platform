#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
VERSION = "6.0.0"
PACKAGE_ROOT = "HumanitarianDataPlatform_V6"
INSTALLER_NAME = f"HumanitarianDataPlatform_Setup_Native_GUI_v{VERSION}.exe"
ARCHIVE_NAME = f"HumanitarianDataPlatform_Archive_complete_v{VERSION}.zip"

EXCLUDED_PARTS = {
    ".git",
    ".agents",
    ".codex",
    ".pytest_cache",
    "__pycache__",
    "deliverables",
    "dist",
    "windows-build",
}
EXCLUDED_SUFFIXES = {".exe", ".obj", ".pyc", ".pyo", ".res"}
EXCLUDED_NAMES = {"payload_generated.h", ".env"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_pe32_x64_gui(path: Path) -> None:
    if path.name != INSTALLER_NAME:
        raise ValueError(f"nom d'installateur inattendu: {path.name}")
    data = path.read_bytes()
    if len(data) < 256 or data[:2] != b"MZ":
        raise ValueError("l'installateur n'est pas un exécutable PE")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if pe_offset + 96 > len(data) or data[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError("signature PE absente")
    machine = struct.unpack_from("<H", data, pe_offset + 4)[0]
    optional_magic = struct.unpack_from("<H", data, pe_offset + 24)[0]
    subsystem = struct.unpack_from("<H", data, pe_offset + 24 + 68)[0]
    if machine != 0x8664 or optional_magic != 0x20B or subsystem != 2:
        raise ValueError(
            f"PE inattendu: machine=0x{machine:04x}, magic=0x{optional_magic:04x}, subsystem={subsystem}"
        )


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if (
            path.name in EXCLUDED_NAMES
            or path.name.casefold().endswith(".exe.sha256")
            or path.suffix.casefold() in EXCLUDED_SUFFIXES
        ):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def zip_info(name: str, *, executable: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(2026, 8, 21, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = ((0o755 if executable else 0o644) & 0xFFFF) << 16
    return info


def build_archive(installer: Path, output_directory: Path) -> tuple[Path, Path, Path]:
    validate_pe32_x64_gui(installer)
    output_directory.mkdir(parents=True, exist_ok=True)
    archive = output_directory / ARCHIVE_NAME
    archive_hash_path = Path(f"{archive}.sha256")
    installer_copy = output_directory / INSTALLER_NAME
    installer_copy.write_bytes(installer.read_bytes())
    installer_hash = sha256(installer_copy)
    installer_hash_path = Path(f"{installer_copy}.sha256")
    installer_hash_path.write_text(f"{installer_hash}  {INSTALLER_NAME}\n", encoding="ascii")

    source_files = iter_source_files()
    required = {
        "HDP_Prompt_recreation_global_v6.0.0.txt",
        "docs/RAPPORT_CONFORMITE_ET_EVALUATION_V6.md",
        "docs/NOTICE_TECHNIQUE_FONCTIONNELLE_V6.md",
        "HDP_STATE.json",
        "TODO_Mises_a_jour_HDP.md",
        "source/spip-plugin/hdp/paquet.xml",
        "source/payload/compose.yaml",
    }
    present = {path.relative_to(ROOT).as_posix() for path in source_files}
    missing = sorted(required - present)
    if missing:
        raise ValueError(f"fichiers obligatoires absents: {missing}")

    generated_at = datetime.now(timezone.utc).isoformat()
    manifest_files = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in source_files
    ]
    manifest = {
        "schema_version": "1.0",
        "application": "Humanitarian Data Platform",
        "version": VERSION,
        "release_status": "qualification_candidate",
        "generated_at": generated_at,
        "installer": {
            "name": INSTALLER_NAME,
            "sha256": installer_hash,
            "format": "PE32+ GUI x86-64",
            "compiled": True,
            "windows_installation_recipe_executed": False,
        },
        "source_file_count": len(manifest_files),
        "source_files": manifest_files,
        "qualification_limits": [
            "installation Windows 10/11 et Docker Desktop non exécutée par le packaging",
            "recette Docker Compose distincte",
            "runtime PHP/SPIP distinct",
            "appels réels aux connecteurs et flux distincts",
            "restaurations de sauvegarde distinctes",
        ],
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        bundle.writestr(zip_info(f"{PACKAGE_ROOT}/{INSTALLER_NAME}"), installer_copy.read_bytes())
        bundle.writestr(
            zip_info(f"{PACKAGE_ROOT}/{INSTALLER_NAME}.sha256"),
            installer_hash_path.read_bytes(),
        )
        bundle.writestr(zip_info(f"{PACKAGE_ROOT}/BUILD_MANIFEST.json"), manifest_bytes)
        for path in source_files:
            relative = path.relative_to(ROOT)
            archive_path = PurePosixPath(PACKAGE_ROOT) / PurePosixPath(relative.as_posix())
            executable = os.access(path, os.X_OK) or path.suffix in {".sh", ".py"}
            bundle.writestr(zip_info(str(archive_path), executable=executable), path.read_bytes())

    archive_hash = sha256(archive)
    archive_hash_path.write_text(f"{archive_hash}  {ARCHIVE_NAME}\n", encoding="ascii")
    return archive, archive_hash_path, installer_hash_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Construire l'archive complète HDP 6.0.0")
    parser.add_argument("--installer", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    archive, archive_hash, installer_hash = build_archive(
        args.installer.resolve(), args.output_dir.resolve()
    )
    print(archive)
    print(archive_hash)
    print(installer_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

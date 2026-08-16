from __future__ import annotations

from pathlib import Path
from typing import Final
import json
import stat
import zipfile


UPLOAD_CATEGORIES: Final[dict[str, frozenset[str]]] = {
    "data": frozenset(
        {
            "csv", "tsv", "json", "geojson", "jsonl", "xlsx",
            "parquet", "geoparquet", "arrow", "feather", "gpkg", "zip",
        }
    ),
    "script": frozenset({"py", "r", "sql", "ipynb"}),
    "document": frozenset(
        {"txt", "md", "pdf", "docx", "odt", "html", "htm", "pptx", "png", "jpg", "jpeg", "webp"}
    ),
}

GEOGRAPHIC_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {"geojson", "gpkg", "geoparquet", "zip"}
)


def file_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def validate_upload_category(filename: str, category: str) -> tuple[str, bool]:
    normalized_category = category.strip().lower()
    if normalized_category not in UPLOAD_CATEGORIES:
        raise ValueError("Catégorie de téléversement inconnue")
    extension = file_extension(filename)
    if not extension or extension not in UPLOAD_CATEGORIES[normalized_category]:
        allowed = ", ".join(sorted(UPLOAD_CATEGORIES[normalized_category]))
        raise ValueError(
            f"Extension .{extension or '?'} refusée pour {normalized_category}; formats admis : {allowed}"
        )
    return extension, extension in GEOGRAPHIC_EXTENSIONS


def script_language(filename: str) -> str | None:
    return {"py": "python", "r": "r", "sql": "sql"}.get(file_extension(filename))


def normalize_update_frequency(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) > 120:
        raise ValueError("La périodicité de mise à jour est trop longue")
    return cleaned


def _validate_zip(path: Path, extension: str) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > 10_000:
                raise ValueError("Archive vide ou contenant trop d’entrées")
            total_size = 0
            names: set[str] = set()
            for entry in entries:
                normalized = entry.filename.replace("\\", "/")
                parts = Path(normalized).parts
                if (
                    not normalized
                    or normalized.startswith("/")
                    or any(part in {"..", ""} for part in parts)
                    or ":" in parts[0]
                ):
                    raise ValueError("Archive contenant un chemin dangereux")
                if stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError("Archive contenant un lien symbolique")
                if entry.flag_bits & 0x1:
                    raise ValueError("Archive chiffrée non prise en charge")
                total_size += int(entry.file_size)
                if total_size > 2_147_483_648:
                    raise ValueError("Archive dont la taille décompressée est excessive")
                if entry.compress_size and entry.file_size > max(100_000_000, entry.compress_size * 200):
                    raise ValueError("Archive présentant un taux de compression dangereux")
                names.add(normalized.casefold())
            if any(name.endswith(("vbaproject.bin", ".exe", ".dll", ".com", ".scr")) for name in names):
                raise ValueError("Archive contenant une macro ou un exécutable")
            required = {
                "xlsx": "xl/workbook.xml",
                "docx": "word/document.xml",
                "pptx": "ppt/presentation.xml",
                "odt": "content.xml",
            }.get(extension)
            if required and required not in names:
                raise ValueError(f"Structure .{extension} invalide")
    except zipfile.BadZipFile as exc:
        raise ValueError("Archive ZIP ou document Open XML invalide") from exc


def validate_upload_content(path: Path, extension: str, category: str) -> None:
    """Validate signatures and passive structure without executing or extracting."""
    size = path.stat().st_size
    if size <= 0:
        raise ValueError("Le fichier transmis est vide")
    with path.open("rb") as stream:
        header = stream.read(65_536)
        stream.seek(max(0, size - 8))
        trailer = stream.read(8)
    extension = extension.casefold()
    if extension in {"csv", "tsv", "jsonl", "py", "r", "sql", "txt", "md", "html", "htm"}:
        if b"\x00" in header:
            raise ValueError("Le contenu binaire ne correspond pas à un fichier texte")
        try:
            header.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Le fichier texte doit être encodé en UTF-8") from exc
    elif extension in {"json", "geojson", "ipynb"}:
        if size > 50 * 1024 * 1024:
            raise ValueError("Le document JSON dépasse la limite de validation de 50 Mio")
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Le fichier JSON est invalide") from exc
        if extension == "geojson" and (
            not isinstance(payload, dict)
            or payload.get("type") not in {"Feature", "FeatureCollection"}
        ):
            raise ValueError("Le fichier ne contient pas un Feature ou FeatureCollection GeoJSON")
        if extension == "ipynb" and (
            not isinstance(payload, dict) or not isinstance(payload.get("cells"), list)
        ):
            raise ValueError("Le carnet Jupyter est invalide")
    elif extension in {"zip", "xlsx", "docx", "pptx", "odt"}:
        _validate_zip(path, extension)
    elif extension in {"parquet", "geoparquet"}:
        if header[:4] != b"PAR1" or trailer[-4:] != b"PAR1":
            raise ValueError("Signature Parquet invalide")
    elif extension in {"arrow", "feather"}:
        if not (header.startswith(b"ARROW1") or trailer.endswith(b"ARROW1")):
            raise ValueError("Signature Arrow/Feather invalide")
    elif extension == "gpkg":
        if not header.startswith(b"SQLite format 3\x00"):
            raise ValueError("Signature GeoPackage/SQLite invalide")
    elif extension == "pdf":
        if not header.startswith(b"%PDF-"):
            raise ValueError("Signature PDF invalide")
    elif extension == "png":
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Signature PNG invalide")
    elif extension in {"jpg", "jpeg"}:
        if not header.startswith(b"\xff\xd8\xff"):
            raise ValueError("Signature JPEG invalide")
    elif extension == "webp":
        if not (header.startswith(b"RIFF") and header[8:12] == b"WEBP"):
            raise ValueError("Signature WebP invalide")
    else:
        raise ValueError(f"Contrôle de contenu indisponible pour .{extension}")

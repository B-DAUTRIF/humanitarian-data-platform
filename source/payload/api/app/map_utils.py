from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import Any


MAX_GEOJSON_BYTES = 20 * 1024 * 1024
MAX_GEOJSON_FEATURES = 5_000
MAX_PROPERTIES_BYTES = 64 * 1024


def load_geojson(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValueError("Le fichier GeoJSON local est absent")
    if path.stat().st_size > MAX_GEOJSON_BYTES:
        raise ValueError("Le GeoJSON dépasse la limite de 20 Mio pour la prévisualisation")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Le fichier n'est pas un GeoJSON UTF-8 valide") from exc
    if not isinstance(payload, dict):
        raise ValueError("La racine GeoJSON doit être un objet")
    if payload.get("type") == "Feature":
        features = [payload]
    elif payload.get("type") == "FeatureCollection" and isinstance(payload.get("features"), list):
        features = payload["features"]
    else:
        raise ValueError("Seuls Feature et FeatureCollection sont acceptés")
    if len(features) > MAX_GEOJSON_FEATURES:
        raise ValueError(f"Le GeoJSON dépasse {MAX_GEOJSON_FEATURES} entités")
    normalized: list[dict[str, Any]] = []
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("Chaque entrée GeoJSON doit être une Feature")
        geometry = feature.get("geometry")
        if geometry is not None and not isinstance(geometry, dict):
            raise ValueError("La géométrie GeoJSON est invalide")
        properties = feature.get("properties") or {}
        if not isinstance(properties, dict):
            raise ValueError("Les propriétés GeoJSON doivent former un objet")
        if len(json.dumps(properties, ensure_ascii=False).encode("utf-8")) > MAX_PROPERTIES_BYTES:
            raise ValueError("Une entité contient plus de 64 Kio de propriétés")
        normalized.append({"type": "Feature", "geometry": geometry, "properties": properties})
    return normalized


def safe_layer_name(value: str) -> str:
    cleaned = " ".join(str(value).split()).strip()[:120]
    return cleaned or "Couche GeoJSON"


def export_bundle(destination: Path, layer_name: str, feature_collection: dict[str, Any]) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", layer_name).strip("-")[:60] or "layer"
    geojson_name = f"{slug}.geojson"
    r_script = (
        "# Import HDP dans R avec sf\n"
        "# install.packages('sf') si nécessaire\n"
        "library(sf)\n"
        f"layer <- st_read('{geojson_name}', quiet = FALSE)\n"
        "print(layer)\n"
    )
    qgis_script = (
        "# À exécuter dans la console Python de QGIS après avoir adapté bundle_dir.\n"
        "from pathlib import Path\n"
        "from qgis.core import QgsProject, QgsVectorLayer\n"
        "bundle_dir = Path(r'C:/chemin/vers/le/dossier/decompresse')\n"
        f"path = bundle_dir / '{geojson_name}'\n"
        f"layer = QgsVectorLayer(str(path), {layer_name!r}, 'ogr')\n"
        "if not layer.isValid():\n"
        "    raise RuntimeError('Couche GeoJSON invalide')\n"
        "QgsProject.instance().addMapLayer(layer)\n"
    )
    readme = (
        "Export Humanitarian Data Platform 4.0.0\n\n"
        f"Couche : {layer_name}\n"
        f"Fichier : {geojson_name}\n\n"
        "QGIS : décompressez l'archive puis ouvrez directement le GeoJSON, ou utilisez import_qgis.py.\n"
        "R : placez le dossier de travail dans le répertoire décompressé puis exécutez import_R.R.\n"
        "Les propriétés proviennent de la ressource locale importée ; vérifiez sa licence et sa provenance.\n"
    )
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(geojson_name, json.dumps(feature_collection, ensure_ascii=False, separators=(",", ":")))
        archive.writestr("import_R.R", r_script)
        archive.writestr("import_qgis.py", qgis_script)
        archive.writestr("README.txt", readme)
    return destination

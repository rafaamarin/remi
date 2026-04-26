"""Utilidades para la carga de recursos de audio desde el sistema de archivos."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Final, cast

from src.core.types import PAD_IDS, PadId

# Mapeo estándar por nombre de archivo (case-insensitive)
_FILE_MAP: dict[str, PadId] = {
    "l1": "L1", "kick": "L1", "bd": "L1",
    "r1": "R1", "snare": "R1", "sd": "R1",
    "l2": "L2", "hh_closed": "L2", "ch": "L2",
    "r2": "R2", "hh_open": "R2", "oh": "R2",
}

_IGNORED_DIRS: frozenset[str] = frozenset({
    ".git", ".venv", ".mypy_cache", "__pycache__", "src", "remi.egg-info",
})

# Límite de seguridad: 25MB por sample (evita OOM en máquinas con poca RAM)
MAX_SAMPLE_SIZE_BYTES: Final[int] = 25 * 1024 * 1024


def scan_libraries(root: Path) -> list[Path]:
    """Devuelve directorios top-level de ``root`` que parezcan kits.

    Un directorio es candidato si tiene un ``remi.json`` o al menos un ``.wav``
    (recursivo). Se ordena alfabéticamente. Ignora dotdirs y carpetas internas
    del proyecto.
    """
    if not root.is_dir():
        return []

    candidates: list[Path] = []
    try:
        for entry in root.iterdir():
            if not entry.is_dir():
                continue
            if entry.name.startswith(".") or entry.name in _IGNORED_DIRS:
                continue
            if (entry / "remi.json").is_file() or next(entry.rglob("*.wav"), None) is not None:
                candidates.append(entry)
    except OSError:
        return []

    candidates.sort(key=lambda p: p.name.lower())
    return candidates


def load_kit_from_dir(dir_path: Path) -> dict[PadId, io.BytesIO]:
    """Escanea un directorio y carga los WAVs mapeados a pads.
    
    Busca un archivo 'remi.json' para el mapeo explícito. 
    Si no existe, usa el mapeo por nombre de archivo.
    """
    assets: dict[PadId, io.BytesIO] = {}
    
    if not dir_path.is_dir():
        return assets

    # Normalizar dir_path para validación de sandbox
    base_path = dir_path.resolve()

    # Intento 1: Mapeo explícito vía JSON
    mapping_file = base_path / "remi.json"
    if mapping_file.exists():
        try:
            mapping = json.loads(mapping_file.read_text())
            for pad_id_raw, rel_path in mapping.items():
                pad_id_str = pad_id_raw.upper()
                if pad_id_str not in PAD_IDS:
                    continue
                pad_id = cast(PadId, pad_id_str)
                
                # Seguridad: Evitar que el JSON apunte fuera de la carpeta (Path Traversal)
                target_path = (base_path / rel_path).resolve()
                if not target_path.is_relative_to(base_path):
                    continue
                
                if target_path.is_file() and target_path.suffix.lower() == ".wav":
                    # Seguridad: Evitar archivos gigantes (OOM)
                    if target_path.stat().st_size > MAX_SAMPLE_SIZE_BYTES:
                        continue
                    assets[pad_id] = io.BytesIO(target_path.read_bytes())
            if assets:
                return assets
        except (json.JSONDecodeError, KeyError, OSError):
            pass  # Fallback al escaneo si el JSON es basura o hay errores de IO

    # Intento 2: Escaneo por convención de nombres (shallow scan por seguridad)
    try:
        for file_path in base_path.glob("*.wav"):
            # Seguridad: Evitar archivos gigantes
            if file_path.stat().st_size > MAX_SAMPLE_SIZE_BYTES:
                continue
                
            name = file_path.stem.lower()
            pad_id_opt = _FILE_MAP.get(name)
            if pad_id_opt is not None and pad_id_opt not in assets:
                assets[pad_id_opt] = io.BytesIO(file_path.read_bytes())
    except OSError:
        pass

    return assets


def save_mapping(dir_path: Path, mapping: dict[PadId, str]) -> None:
    """Guarda un diccionario de mapeo PadId -> filename en remi.json.
    
    Solo guarda las entradas que tengan un archivo asignado.
    """
    if not dir_path.is_dir():
        return

    mapping_file = dir_path / "remi.json"
    
    # Filtrar solo entradas válidas
    clean_mapping = {
        pad_id: filename 
        for pad_id, filename in mapping.items() 
        if filename
    }
    
    try:
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(clean_mapping, f, indent=4)
    except OSError:
        pass

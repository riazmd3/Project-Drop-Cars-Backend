import json
from pathlib import Path
from typing import List

_CITIES_CACHE: List[str] | None = None

def load_cities_once(base_path: str) -> List[str]:
    global _CITIES_CACHE
    if _CITIES_CACHE is not None:
        return _CITIES_CACHE
    file_path = Path(base_path) / "load_data" / "cities.json"
    with open(file_path, "r", encoding="utf-8") as f:
        _CITIES_CACHE = json.load(f)
    return _CITIES_CACHE

def get_cities() -> List[str]:
    return _CITIES_CACHE or []



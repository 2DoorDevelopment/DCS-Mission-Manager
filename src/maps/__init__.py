from src.maps.caucasus import CAUCASUS_MAP
from src.maps.syria import SYRIA_MAP
from src.maps.cold_war_germany import COLD_WAR_GERMANY_MAP

MAP_REGISTRY = {
    "Caucasus": CAUCASUS_MAP,
    "Syria": SYRIA_MAP,
    "ColdWarGermany": COLD_WAR_GERMANY_MAP,
}

# Aliases for LLM output normalization
MAP_ALIASES = {
    "caucasus": "Caucasus",
    "caucuses": "Caucasus",
    "georgia": "Caucasus",
    "black sea": "Caucasus",
    "syria": "Syria",
    "syrian": "Syria",
    "levant": "Syria",
    "cold war germany": "ColdWarGermany",
    "germany": "ColdWarGermany",
    "cold war": "ColdWarGermany",
    "fulda": "ColdWarGermany",
    "fulda gap": "ColdWarGermany",
}


def resolve_map_name(name: str) -> str | None:
    """Resolve a map name from user/LLM input to registry key."""
    if not name:
        return None
    lower = name.lower().strip()
    if lower in MAP_ALIASES:
        return MAP_ALIASES[lower]
    # Direct match
    for key in MAP_REGISTRY:
        if key.lower() == lower:
            return key
    return None

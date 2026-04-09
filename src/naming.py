"""
Mission Name Generator
Creates unique, memorable mission names using NATO-style operation naming.
"""

import random
import time
import hashlib

# NATO-style adjective pools by theme
_ADJECTIVES = {
    "aggressive": [
        "Iron", "Steel", "Thunder", "Lightning", "Hammer",
        "Valiant", "Fierce", "Wrath", "Fury", "Storm",
        "Crimson", "Blazing", "Burning", "Raging", "Savage",
    ],
    "defensive": [
        "Vigilant", "Guardian", "Sentinel", "Shield", "Bastion",
        "Steadfast", "Resolute", "Enduring", "Unyielding", "Ironclad",
    ],
    "stealth": [
        "Silent", "Shadow", "Phantom", "Ghost", "Spectre",
        "Eclipse", "Midnight", "Dusk", "Whisper", "Veil",
    ],
    "general": [
        "Noble", "Sovereign", "Allied", "Unified", "Northern",
        "Southern", "Eastern", "Western", "Pacific", "Atlantic",
        "Arctic", "Desert", "Mountain", "Coastal", "Rapid",
        "Swift", "Bold", "Bright", "Golden", "Silver",
    ],
}

_NOUNS = {
    "air": [
        "Eagle", "Falcon", "Hawk", "Raptor", "Talon",
        "Viper", "Phoenix", "Thunderbolt", "Sabre", "Javelin",
        "Arrow", "Spear", "Lance", "Trident", "Condor",
    ],
    "ground": [
        "Anvil", "Fortress", "Rampart", "Bulwark", "Citadel",
        "Phalanx", "Legion", "Titan", "Colossus", "Chariot",
        "Sledgehammer", "Gauntlet", "Avalanche", "Tempest", "Maelstrom",
    ],
    "naval": [
        "Neptune", "Poseidon", "Triton", "Leviathan", "Kraken",
        "Typhoon", "Tsunami", "Monsoon", "Mariner", "Corsair",
    ],
    "general": [
        "Freedom", "Liberty", "Justice", "Resolve", "Valor",
        "Honor", "Courage", "Dawn", "Dagger", "Saber",
        "Lancer", "Striker", "Reaper", "Warden", "Harbinger",
        "Nexus", "Apex", "Zenith", "Prism", "Vortex",
    ],
}

# Mission type to theme mapping
_MISSION_THEMES = {
    "SEAD": ("aggressive", "air"),
    "CAS": ("aggressive", "ground"),
    "CAP": ("defensive", "air"),
    "strike": ("stealth", "air"),
    "anti-ship": ("aggressive", "naval"),
    "escort": ("defensive", "air"),
    "convoy_attack": ("aggressive", "ground"),
    "convoy_defense": ("defensive", "ground"),
}


def generate_mission_name(mission_type: str = "general", map_name: str = "",
                          seed: int | None = None) -> str:
    """
    Generate a unique operation name like 'Operation Iron Eagle' or 'Operation Silent Viper'.

    Args:
        mission_type: The mission type for themed naming
        map_name: Map name for additional context
        seed: Optional seed for reproducibility

    Returns:
        A unique operation name string
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        # Use time + random for uniqueness
        entropy = f"{time.time_ns()}{random.random()}"
        hash_val = int(hashlib.md5(entropy.encode()).hexdigest()[:8], 16)
        rng = random.Random(hash_val)

    adj_theme, noun_theme = _MISSION_THEMES.get(mission_type, ("general", "general"))

    # Pick from themed pool + general pool
    adj_pool = _ADJECTIVES.get(adj_theme, []) + _ADJECTIVES["general"]
    noun_pool = _NOUNS.get(noun_theme, []) + _NOUNS["general"]

    adjective = rng.choice(adj_pool)
    noun = rng.choice(noun_pool)

    return f"Operation {adjective} {noun}"


def generate_campaign_name(map_name: str = "", seed: int | None = None) -> str:
    """Generate a campaign-level name."""
    rng = random.Random(seed) if seed else random.Random()

    prefixes = ["Campaign", "Theater", "Offensive", "Front"]
    adj_pool = _ADJECTIVES["general"] + _ADJECTIVES["aggressive"]
    noun_pool = _NOUNS["general"]

    prefix = rng.choice(prefixes)
    adj = rng.choice(adj_pool)
    noun = rng.choice(noun_pool)

    return f"{prefix} {adj} {noun}"


def generate_filename(mission_type: str, map_name: str, op_name: str) -> str:
    """
    Generate a unique filename for a .miz file.
    Format: OpName_MissionType_Map_timestamp.miz
    """
    # Sanitize operation name for filename
    safe_op = op_name.replace("Operation ", "Op_").replace(" ", "_")
    safe_map = map_name.replace(" ", "_")
    safe_type = mission_type.replace(" ", "_").replace("-", "_")
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    return f"{safe_op}_{safe_type}_{safe_map}_{timestamp}.miz"

"""
Difficulty Scaling System
Adjusts mission parameters based on difficulty level.
Easy/Medium/Hard affect:
  - Enemy AI skill levels
  - Enemy unit counts and group sizes
  - SAM system types (easy=older, hard=modern)
  - Number of enemy air flights
  - SHORAD density around SAM sites
  - Ground force composition quality
  - Friendly support availability
"""

import copy
import random

# Difficulty profiles
DIFFICULTY_PROFILES = {
    "easy": {
        "display": "Easy",
        # AI skill
        "enemy_air_skill": "Average",
        "enemy_ground_skill": "Average",
        "friendly_ai_skill": "Excellent",
        # Force multipliers (1.0 = template default)
        "enemy_air_count_mult": 0.6,       # Fewer enemy air
        "enemy_air_max_per_group": 2,       # Smaller groups
        "enemy_ground_count_mult": 0.7,
        "friendly_flight_count_mult": 1.3,  # More friendlies
        # SAM replacements: downgrade high-threat SAMs
        "sam_downgrades": {
            "SA-10": "SA-6",
            "SA-11": "SA-6",
            "SA-15": "SA-8",
        },
        "shorad_escort": False,             # No SHORAD around SAMs
        # Ground unit quality
        "red_armor_preference": ["T-55", "BMP-1", "BTR-80"],
        "blue_armor_preference": ["M-1 Abrams", "M-2 Bradley", "M1126 Stryker ICV"],
        # Extra friendlies
        "extra_friendly_cap": True,
        "extra_friendly_sead": False,
    },
    "medium": {
        "display": "Medium",
        "enemy_air_skill": "High",
        "enemy_ground_skill": "High",
        "friendly_ai_skill": "High",
        "enemy_air_count_mult": 1.0,
        "enemy_air_max_per_group": 4,
        "enemy_ground_count_mult": 1.0,
        "friendly_flight_count_mult": 1.0,
        "sam_downgrades": {},
        "shorad_escort": False,
        "red_armor_preference": ["T-72B", "BMP-2", "BTR-80", "T-80UD"],
        "blue_armor_preference": ["M-1 Abrams", "M-2 Bradley", "LAV-25"],
        "extra_friendly_cap": False,
        "extra_friendly_sead": False,
    },
    "hard": {
        "display": "Hard",
        "enemy_air_skill": "Excellent",
        "enemy_ground_skill": "Excellent",
        "friendly_ai_skill": "High",
        "enemy_air_count_mult": 1.5,
        "enemy_air_max_per_group": 4,
        "enemy_ground_count_mult": 1.3,
        "friendly_flight_count_mult": 0.7,   # Fewer friendlies
        # SAM upgrades: replace medium with high-threat
        "sam_upgrades": {
            "SA-6": "SA-11",
            "SA-8": "SA-15",
        },
        "sam_downgrades": {},
        "shorad_escort": True,               # SA-15/Tunguska near SAM sites
        "shorad_types": ["SA-15", "SA-19", "ZSU-23-4"],
        "red_armor_preference": ["T-80UD", "T-72B", "BMP-2"],
        "blue_armor_preference": ["M-1 Abrams", "M-2 Bradley"],
        # Fewer friendly assets
        "extra_friendly_cap": False,
        "extra_friendly_sead": False,
        # Extra enemy threats
        "extra_enemy_cap": True,
        "extra_enemy_interceptors": True,
        "extra_sam_sites": 1,                # Add 1 extra SAM site
    },
}


def get_profile(difficulty: str) -> dict:
    """Get the difficulty profile dict."""
    return DIFFICULTY_PROFILES.get(difficulty, DIFFICULTY_PROFILES["medium"])


def scale_plan(plan: dict) -> dict:
    """
    Apply difficulty scaling to a mission plan BEFORE it goes to the builder.
    Modifies enemy compositions, SAM types, counts, and adds/removes forces.
    """
    difficulty = plan.get("difficulty", "medium")
    profile = get_profile(difficulty)
    scaled = copy.deepcopy(plan)

    # --- Scale enemy air ---
    enemy_air = scaled.get("enemy_air", [])
    air_mult = profile["enemy_air_count_mult"]
    max_per = profile["enemy_air_max_per_group"]

    for flight in enemy_air:
        base_count = flight.get("count", 2)
        new_count = max(1, min(max_per, round(base_count * air_mult)))
        flight["count"] = new_count
        flight["skill"] = profile["enemy_air_skill"]

    # Extra enemy CAP on hard
    if profile.get("extra_enemy_cap") and enemy_air:
        extra_ac = random.choice(["MiG-29S", "Su-27"])
        enemy_air.append({
            "aircraft": extra_ac,
            "task": "CAP",
            "count": 2,
            "skill": profile["enemy_air_skill"],
        })

    # Extra interceptors on hard
    if profile.get("extra_enemy_interceptors"):
        enemy_air.append({
            "aircraft": "MiG-31",
            "task": "intercept",
            "count": 2,
            "skill": profile["enemy_air_skill"],
        })

    scaled["enemy_air"] = enemy_air

    # --- Scale SAM sites ---
    sam_sites = scaled.get("enemy_sam_sites", [])

    # Apply downgrades (easy)
    for site in sam_sites:
        sam_type = site.get("type", "SA-6")
        if sam_type in profile.get("sam_downgrades", {}):
            site["type"] = profile["sam_downgrades"][sam_type]

    # Apply upgrades (hard)
    for site in sam_sites:
        sam_type = site.get("type", "SA-6")
        if sam_type in profile.get("sam_upgrades", {}):
            site["type"] = profile["sam_upgrades"][sam_type]

    # Add extra SAM sites on hard
    extra_sams = profile.get("extra_sam_sites", 0)
    for _ in range(extra_sams):
        extra_type = random.choice(["SA-11", "SA-10", "SA-6"])
        sam_sites.append({
            "type": extra_type,
            "location_desc": "forward position",
        })

    # Flag for SHORAD escorts
    scaled["_shorad_escort"] = profile.get("shorad_escort", False)
    scaled["_shorad_types"] = profile.get("shorad_types", [])

    scaled["enemy_sam_sites"] = sam_sites

    # --- Scale friendly flights ---
    friendly = scaled.get("friendly_flights", [])
    friendly_mult = profile["friendly_flight_count_mult"]

    for flight in friendly:
        base_count = flight.get("count", 2)
        new_count = max(1, min(4, round(base_count * friendly_mult)))
        flight["count"] = new_count

    # Extra friendly CAP on easy
    if profile.get("extra_friendly_cap"):
        friendly.append({
            "task": "CAP",
            "aircraft": "F-15C",
            "count": 2,
        })

    scaled["friendly_flights"] = friendly

    # --- Scale ground forces ---
    enemy_ground = scaled.get("enemy_ground", [])
    ground_mult = profile["enemy_ground_count_mult"]

    for group in enemy_ground:
        base_count = group.get("count", 4)
        new_count = max(2, min(6, round(base_count * ground_mult)))
        group["count"] = new_count

    scaled["enemy_ground"] = enemy_ground

    # --- Store skill overrides for builder ---
    scaled["_enemy_air_skill"] = profile["enemy_air_skill"]
    scaled["_enemy_ground_skill"] = profile["enemy_ground_skill"]
    scaled["_friendly_ai_skill"] = profile["friendly_ai_skill"]
    scaled["_red_armor_preference"] = profile.get("red_armor_preference", [])
    scaled["_blue_armor_preference"] = profile.get("blue_armor_preference", [])

    return scaled

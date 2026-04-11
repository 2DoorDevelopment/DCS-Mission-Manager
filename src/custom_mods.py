"""
Custom Aircraft Mod System
Allows adding new aircraft modules by dropping a JSON file into the custom_aircraft/ folder.
No code changes needed — just create a .json file with the aircraft data.

Each JSON file defines:
  - DCS type string (must match the mod's internal name exactly)
  - Display name
  - Category (fighter/attacker/bomber)
  - Roles it can fly
  - Performance profile for flight planning
  - Default loadouts per mission type (with CLSID pylon data)
  - Fuel, chaff, flare counts
  - Aliases for natural language matching

Example: See custom_aircraft/_template.json for the format.
"""

import json
import sys
from pathlib import Path

# Default location for custom aircraft configs
# When running as exe (PyInstaller), use directory next to the exe
# When running as script, use directory next to the project root
def _get_base_dir() -> Path:
    """Get the base directory — handles both script and frozen exe."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent.parent

CUSTOM_AIRCRAFT_DIR = _get_base_dir() / "custom_aircraft"

# Valid categories for custom aircraft
_VALID_CATEGORIES = {"fighter", "attacker", "bomber", "helicopter", "transport"}

# Valid mission roles
_VALID_ROLES = {
    "SEAD", "CAS", "CAP", "strike", "anti-ship", "escort", "sweep",
    "convoy_attack", "convoy_defense", "CSAR", "FAC",
}


def validate_custom_aircraft_data(data: dict, filename: str) -> list[str]:
    """
    Validate a custom aircraft JSON definition.

    Returns list of warning strings. Empty list means valid.
    """
    warnings = []

    # Category validation
    cat = data.get("category", "fighter")
    if cat not in _VALID_CATEGORIES:
        warnings.append(f"{filename}: invalid category '{cat}' — expected one of {_VALID_CATEGORIES}")

    # Roles validation
    roles = data.get("roles", [])
    if not isinstance(roles, list) or len(roles) == 0:
        warnings.append(f"{filename}: 'roles' must be a non-empty list")
    else:
        for role in roles:
            if role not in _VALID_ROLES:
                warnings.append(f"{filename}: unknown role '{role}' — expected one of {_VALID_ROLES}")

    # Numeric field validation
    for field in ("fuel", "chaff", "flare"):
        val = data.get(field)
        if val is not None and not isinstance(val, (int, float)):
            warnings.append(f"{filename}: '{field}' must be a number, got {type(val).__name__}")
        elif val is not None and val < 0:
            warnings.append(f"{filename}: '{field}' must be non-negative")

    # radio_freq validation
    freq = data.get("radio_freq")
    if freq is not None:
        if not isinstance(freq, (int, float)):
            warnings.append(f"{filename}: 'radio_freq' must be a number")
        elif not (30.0 <= freq <= 400.0):
            warnings.append(f"{filename}: 'radio_freq' {freq} outside valid range (30-400 MHz)")

    # Loadout validation
    loadouts = data.get("loadouts", {})
    if not isinstance(loadouts, dict):
        warnings.append(f"{filename}: 'loadouts' must be a dict")
    else:
        for lo_name, lo_data in loadouts.items():
            if not isinstance(lo_data, dict):
                warnings.append(f"{filename}: loadout '{lo_name}' must be a dict")
                continue
            pylons = lo_data.get("pylons", {})
            if not isinstance(pylons, dict):
                warnings.append(f"{filename}: loadout '{lo_name}' pylons must be a dict")
                continue
            for pylon_key, clsid_val in pylons.items():
                # Pylon keys should be convertible to int
                try:
                    pnum = int(pylon_key)
                    if pnum < 1 or pnum > 20:
                        warnings.append(f"{filename}: loadout '{lo_name}' pylon {pnum} out of range (1-20)")
                except (ValueError, TypeError):
                    warnings.append(f"{filename}: loadout '{lo_name}' invalid pylon key '{pylon_key}'")

                # CLSID format check
                if isinstance(clsid_val, str):
                    if not clsid_val.startswith("{") or not clsid_val.endswith("}"):
                        warnings.append(
                            f"{filename}: loadout '{lo_name}' pylon {pylon_key} "
                            f"CLSID '{clsid_val}' should be wrapped in curly braces"
                        )

    # Aliases validation
    aliases = data.get("aliases", [])
    if not isinstance(aliases, list):
        warnings.append(f"{filename}: 'aliases' must be a list")

    return warnings


def load_custom_aircraft(directory: Path | None = None) -> dict:
    """
    Load all custom aircraft definitions from JSON files.

    Returns:
        dict mapping aircraft key (e.g. "F-22A") to its full data dict,
        in the same format as PLAYER_AIRCRAFT entries in units.py
    """
    if directory is None:
        directory = CUSTOM_AIRCRAFT_DIR

    if not directory.exists():
        return {}

    aircraft = {}
    for json_file in sorted(directory.glob("*.json")):
        if json_file.name.startswith("_"):
            continue  # Skip template/example files

        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            key = data.get("key")
            if not key:
                print(f"  WARNING: {json_file.name} missing 'key' field, skipping")
                continue

            # Validate required fields
            required = ["key", "type", "display_name", "roles"]
            missing = [r for r in required if r not in data]
            if missing:
                print(f"  WARNING: {json_file.name} missing fields: {missing}, skipping")
                continue

            # Deep validation
            validation_warnings = validate_custom_aircraft_data(data, json_file.name)
            for w in validation_warnings:
                print(f"  WARNING: {w}")

            # Treat critical validation failures as skips
            critical = [w for w in validation_warnings if "must be" in w and "non-empty" in w]
            if critical:
                print(f"  WARNING: {json_file.name} has critical validation errors, skipping")
                continue

            # Build the aircraft entry in the same format as PLAYER_AIRCRAFT
            entry = {
                "type": data["type"],
                "display_name": data["display_name"],
                "category": data.get("category", "fighter"),
                "roles": data["roles"],
                "fuel": data.get("fuel", 4000),
                "chaff": data.get("chaff", 60),
                "flare": data.get("flare", 60),
                "radio_freq": data.get("radio_freq", 305.0),
                "default_loadouts": {},
                "_is_mod": True,
                "_source_file": json_file.name,
            }

            # Process loadouts
            for loadout_name, loadout_data in data.get("loadouts", {}).items():
                if isinstance(loadout_data, dict):
                    pylons = {}
                    for pylon_num_str, clsid in loadout_data.get("pylons", {}).items():
                        try:
                            pylon_num = int(pylon_num_str)
                            if isinstance(clsid, str):
                                pylons[pylon_num] = {"CLSID": clsid}
                            elif isinstance(clsid, dict):
                                pylons[pylon_num] = clsid
                        except ValueError:
                            print(f"  WARNING: Invalid pylon number '{pylon_num_str}' in {loadout_name} loadout — skipping")
                            continue

                    entry["default_loadouts"][loadout_name] = {
                        "description": loadout_data.get("description", f"{loadout_name} loadout"),
                        "pylons": pylons,
                    }

            # Performance profile (for flight_profile.py)
            if "performance" in data:
                entry["_performance"] = data["performance"]

            aircraft[key] = entry

            # Store aliases for later registration
            entry["_aliases"] = data.get("aliases", [])

        except json.JSONDecodeError as e:
            print(f"  WARNING: {json_file.name} invalid JSON: {e}")
        except Exception as e:
            print(f"  WARNING: {json_file.name} error: {e}")

    return aircraft


def register_custom_aircraft(custom: dict):
    """
    Register custom aircraft into the main PLAYER_AIRCRAFT dict and alias tables.
    Call this at startup after loading.
    """
    from src.units import PLAYER_AIRCRAFT, AIRCRAFT_ALIASES

    for key, data in custom.items():
        # Add to player aircraft
        PLAYER_AIRCRAFT[key] = data

        # Register aliases
        aliases = data.get("_aliases", [])
        # Always add lowercase key as alias
        AIRCRAFT_ALIASES[key.lower()] = key
        for alias in aliases:
            AIRCRAFT_ALIASES[alias.lower()] = key

        # Register performance profile if provided
        if "_performance" in data:
            from src.flight_profile import AIRCRAFT_PROFILES
            AIRCRAFT_PROFILES[key] = data["_performance"]

    if custom:
        print(f"  Loaded {len(custom)} custom aircraft: {', '.join(custom.keys())}")


def ensure_custom_dir():
    """Create the custom_aircraft directory and template if they don't exist."""
    CUSTOM_AIRCRAFT_DIR.mkdir(exist_ok=True)

    template_path = CUSTOM_AIRCRAFT_DIR / "_template.json"
    if not template_path.exists():
        template = {
            "_comment": "Copy this file, rename it (e.g. F-22A.json), and fill in your mod's data.",
            "_comment2": "The 'type' field MUST match the mod's DCS internal type string exactly.",
            "_comment3": "To find it: open any .miz using the mod, unzip it, search the mission file for the aircraft type.",
            "key": "F-22A",
            "type": "F-22A",
            "display_name": "F-22A Raptor",
            "category": "fighter",
            "roles": ["CAP", "SEAD", "strike", "escort", "sweep"],
            "fuel": 8200,
            "chaff": 120,
            "flare": 60,
            "radio_freq": 305.0,
            "aliases": ["f-22", "f22", "raptor", "f-22a"],
            "loadouts": {
                "CAP": {
                    "description": "6x AIM-120D, 2x AIM-9X (internal)",
                    "pylons": {
                        "_comment": "Put pylon number (as string) -> CLSID string pairs here",
                        "_comment2": "Get CLSIDs from an existing .miz file or the mod documentation"
                    }
                },
                "SEAD": {
                    "description": "Example SEAD loadout",
                    "pylons": {}
                },
                "strike": {
                    "description": "Example strike loadout",
                    "pylons": {}
                }
            },
            "performance": {
                "climb_rate_fpm": 62000,
                "cruise_speed_kts": 520,
                "cruise_alt_m": 10000,
                "combat_speed_kts": 500,
                "ingress_speed_kts": 480,
                "egress_speed_kts": 550,
                "approach_speed_kts": 170,
                "fuel_flow_cruise_kg_hr": 3000,
                "fuel_flow_combat_kg_hr": 8000,
                "internal_fuel_kg": 8200,
                "low_alt_ingress_m": 150,
                "medium_alt_m": 5000,
                "pop_up_alt_m": 3000
            }
        }
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=4)

    return CUSTOM_AIRCRAFT_DIR

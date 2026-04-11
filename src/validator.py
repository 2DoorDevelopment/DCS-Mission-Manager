"""
Mission Validator — Pre-Flight Checks
Runs sanity checks on the built mission data before packaging.
Catches issues that would cause broken .miz files or DCS errors.
"""

import math
import re
from src.maps import MAP_REGISTRY
from src.units import PLAYER_AIRCRAFT, SAM_SYSTEMS

# Full GUID pattern: {8hex-4hex-4hex-4hex-12hex}
_GUID_RE = re.compile(
    r"^\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}$"
)
# DCS shorthand pattern: {WORD} — letters, digits, hyphens, underscores only
_SHORTHAND_RE = re.compile(r"^\{[A-Za-z0-9_\-\.]+\}$")

# Known-good DCS CLSIDs collected from the units database — used for cross-reference warnings
KNOWN_CLSIDS: set[str] = set()


def _build_known_clsids():
    """Scan PLAYER_AIRCRAFT and AI_AIRCRAFT to build a set of known-good CLSIDs."""
    from src.units import AI_AIRCRAFT
    for db in (PLAYER_AIRCRAFT, AI_AIRCRAFT):
        for ac_data in db.values():
            loadouts = ac_data.get("default_loadouts", ac_data.get("loadouts", {}))
            for loadout in loadouts.values():
                if isinstance(loadout, str):
                    continue  # alias
                pylons = loadout.get("pylons", {})
                for pylon_data in pylons.values():
                    clsid = pylon_data.get("CLSID", "")
                    if clsid:
                        KNOWN_CLSIDS.add(clsid)


_build_known_clsids()


class ValidationResult:
    """Holds results of mission validation."""

    def __init__(self):
        self.errors: list[str] = []      # Will cause DCS to fail
        self.warnings: list[str] = []    # May cause issues
        self.info: list[str] = []        # FYI

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"  ERRORS ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"    ✗ {e}")
        if self.warnings:
            lines.append(f"  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"    ⚠ {w}")
        if self.info:
            lines.append(f"  INFO ({len(self.info)}):")
            for i in self.info:
                lines.append(f"    ℹ {i}")
        if self.passed and not self.warnings:
            lines.append("  ✓ All pre-flight checks passed")
        elif self.passed:
            lines.append(f"  ✓ Passed with {len(self.warnings)} warning(s)")
        else:
            lines.append(f"  ✗ FAILED — {len(self.errors)} error(s) must be fixed")
        return "\n".join(lines)


def validate_mission(mission_data: dict, plan: dict) -> ValidationResult:
    """
    Run all pre-flight checks on a built mission.

    Args:
        mission_data: The built mission data dict from MissionBuilder
        plan: The mission plan dict

    Returns:
        ValidationResult with errors, warnings, and info
    """
    result = ValidationResult()

    _check_map(mission_data, plan, result)
    _check_player(mission_data, plan, result)
    _check_airfields(mission_data, plan, result)
    _check_units_in_bounds(mission_data, plan, result)
    _check_fuel(mission_data, plan, result)
    _check_waypoints(mission_data, plan, result)
    _check_group_integrity(mission_data, result)
    _check_clsids(mission_data, result)
    _check_sam_placement(mission_data, plan, result)

    return result


def _check_map(data: dict, plan: dict, r: ValidationResult):
    """Verify the map exists and is valid."""
    map_name = plan.get("map_name", "")
    if map_name not in MAP_REGISTRY:
        r.errors.append(f"Unknown map: '{map_name}'. Available: {', '.join(MAP_REGISTRY.keys())}")
        return

    theater = data.get("theater", "")
    if not theater:
        r.errors.append("Theater name is empty — DCS won't load this mission")


def _check_player(data: dict, plan: dict, r: ValidationResult):
    """Verify player aircraft and group are valid."""
    ac_key = plan.get("player_aircraft", "")
    if ac_key not in PLAYER_AIRCRAFT:
        r.errors.append(f"Unknown player aircraft: '{ac_key}'. "
                        f"Available: {', '.join(PLAYER_AIRCRAFT.keys())}")

    player_group = data.get("player_group")
    if not player_group:
        r.errors.append("No player group — mission has no playable aircraft")
        return

    units = player_group.get("units", [])
    if not units:
        r.errors.append("Player group has no units")

    # Check for Player skill
    has_player = any(u.get("skill") == "Player" for u in units)
    if not has_player:
        r.errors.append("No unit with 'Player' skill — you won't be able to fly")

    waypoints = player_group.get("waypoints", [])
    if len(waypoints) < 3:
        r.warnings.append(f"Player has only {len(waypoints)} waypoints — may be too few for navigation")


def _check_airfields(data: dict, plan: dict, r: ValidationResult):
    """Verify airfield references are valid."""
    map_name = plan.get("map_name", "")
    map_data = MAP_REGISTRY.get(map_name, {})
    airfield_ids = {af["id"] for af in map_data.get("airfields", [])}
    airfield_names = {af["name"].lower() for af in map_data.get("airfields", [])}

    # Check player departure
    player_af = plan.get("player_airfield", "")
    if player_af and player_af.lower() not in airfield_names:
        r.warnings.append(f"Player airfield '{player_af}' not found in {map_name} database — "
                          f"DCS may not recognize it")

    # Check runway length for player aircraft
    ac_key = plan.get("player_aircraft", "")
    ac_data = PLAYER_AIRCRAFT.get(ac_key, {})
    category = ac_data.get("category", "fighter")

    min_runway = {"fighter": 2000, "attacker": 1500, "bomber": 2500}.get(category, 2000)

    for af in map_data.get("airfields", []):
        if af["name"].lower() == player_af.lower():
            max_rwy = max((rwy.get("length", 0) for rwy in af.get("runways", [{"length": 0}])), default=0)
            if max_rwy < min_runway:
                r.warnings.append(f"Runway at {af['name']} is {max_rwy}m — {ac_key} typically needs {min_runway}m+")
            break

    # Check that air groups reference valid airfield IDs
    for group_list_name in ("blue_air", "red_air"):
        for group in data.get(group_list_name, []):
            af_id = group.get("airfield_id", 0)
            if af_id and af_id not in airfield_ids:
                if group.get("start_type") != "In Air":
                    r.warnings.append(f"Group '{group.get('name', '?')}' references airfield ID {af_id} "
                                      f"which doesn't exist on {map_name}")


def _check_units_in_bounds(data: dict, plan: dict, r: ValidationResult):
    """Check that units are placed within the map boundaries."""
    map_name = plan.get("map_name", "")
    map_data = MAP_REGISTRY.get(map_name, {})
    bounds = map_data.get("bounds", {})

    if not bounds:
        return

    x_min = bounds.get("x_min", -999999)
    x_max = bounds.get("x_max", 999999)
    y_min = bounds.get("y_min", -999999)
    y_max = bounds.get("y_max", 999999)

    # Expand bounds by 50% — units near edges are fine, units way outside are not
    margin = 0.5
    x_range = (x_max - x_min) * margin
    y_range = (y_max - y_min) * margin

    out_of_bounds = 0
    for group_key in ("blue_air", "red_air", "blue_ground", "red_ground", "blue_sam", "red_sam"):
        for group in data.get(group_key, []):
            for unit in group.get("units", []):
                x = unit.get("x", 0)
                y = unit.get("y", 0)
                if (x < x_min - x_range or x > x_max + x_range or
                        y < y_min - y_range or y > y_max + y_range):
                    out_of_bounds += 1

    if out_of_bounds > 0:
        r.warnings.append(f"{out_of_bounds} unit(s) placed far outside normal map boundaries — "
                          f"they may not appear in DCS")


def _check_fuel(data: dict, plan: dict, r: ValidationResult):
    """Check fuel adequacy."""
    fuel_est = data.get("fuel_estimate", {})
    if not fuel_est:
        return

    if not fuel_est.get("fuel_ok", True):
        ac_key = plan.get("player_aircraft", "?")
        required = fuel_est.get("fuel_required_kg", 0)
        available = fuel_est.get("fuel_available_kg", 0)
        r.warnings.append(f"Fuel may be insufficient for {ac_key}: need ~{required} kg, "
                          f"have {available} kg. Consider managing throttle or adding a tanker stop.")


def _check_waypoints(data: dict, plan: dict, r: ValidationResult):
    """Check waypoint sanity."""
    player_group = data.get("player_group") or {}
    waypoints = player_group.get("waypoints", [])

    if not waypoints:
        return

    # Check for takeoff waypoint
    has_takeoff = any(wp.get("type") == "TakeOff" for wp in waypoints)
    if not has_takeoff:
        r.warnings.append("No takeoff waypoint — player may start in a weird state")

    # Check for landing waypoint
    has_landing = any(wp.get("type") == "Land" for wp in waypoints)
    if not has_landing:
        r.warnings.append("No landing waypoint — no RTB point set")

    # Check for negative altitudes
    for wp in waypoints:
        alt = wp.get("alt", 0)
        if alt < 0:
            r.warnings.append(f"Waypoint '{wp.get('name', '?')}' has negative altitude: {alt}m")

    # Check for extremely high speeds
    for wp in waypoints:
        speed = wp.get("speed", 0)
        if speed > 400:  # ~780 kts — unreasonable for subsonic profile
            name = wp.get("name", "?")
            kts = int(speed / 0.514)
            r.info.append(f"Waypoint '{name}' speed is {kts} kts — verify this is intended")


def _check_group_integrity(data: dict, r: ValidationResult):
    """Check that all groups have valid structure."""
    group_ids = set()
    unit_ids = set()

    all_groups = []
    for key in ("blue_air", "red_air", "blue_ground", "red_ground", "blue_sam", "red_sam"):
        all_groups.extend(data.get(key, []))

    player = data.get("player_group")
    if player:
        all_groups.append(player)

    for group in all_groups:
        gid = group.get("group_id", 0)
        if gid in group_ids:
            r.warnings.append(f"Duplicate group ID: {gid} (group '{group.get('name', '?')}')")
        group_ids.add(gid)

        for unit in group.get("units", []):
            uid = unit.get("unit_id", 0)
            if uid in unit_ids:
                r.warnings.append(f"Duplicate unit ID: {uid} in group '{group.get('name', '?')}'")
            unit_ids.add(uid)

            if not unit.get("type"):
                r.errors.append(f"Unit '{unit.get('name', '?')}' in group '{group.get('name', '?')}' "
                                f"has no type string — DCS will reject this")

    total = len(unit_ids)
    if total > 150:
        r.warnings.append(f"Mission has {total} units — may cause performance issues. "
                          f"Consider reducing ground forces or using lighter difficulty.")
    elif total > 100:
        r.info.append(f"Mission has {total} units — should be fine but watch FPS")


def _check_clsids(data: dict, r: ValidationResult):
    """Validate weapon CLSID strings on all units to catch typos before packaging."""
    all_groups = []
    for key in ("blue_air", "red_air"):
        all_groups.extend(data.get(key, []))
    player = data.get("player_group")
    if player:
        all_groups.append(player)

    for group in all_groups:
        group_name = group.get("name", "?")
        for unit in group.get("units", []):
            pylons: dict = unit.get("pylons", {})
            for pylon_num, pylon_data in pylons.items():
                clsid = pylon_data.get("CLSID", "")
                if not clsid:
                    r.warnings.append(
                        f"Group '{group_name}' pylon {pylon_num} has empty CLSID — "
                        f"weapon slot will be ignored"
                    )
                elif not (_GUID_RE.match(clsid) or _SHORTHAND_RE.match(clsid)):
                    r.errors.append(
                        f"Group '{group_name}' pylon {pylon_num} has invalid CLSID: "
                        f"'{clsid}' — DCS will fail to load this unit's loadout"
                    )
                elif KNOWN_CLSIDS and clsid not in KNOWN_CLSIDS:
                    r.warnings.append(
                        f"Group '{group_name}' pylon {pylon_num} CLSID '{clsid}' "
                        f"not found in known weapons database — verify it exists in DCS"
                    )


def _check_sam_placement(data: dict, plan: dict, r: ValidationResult):
    """Check that SAM sites are not placed in water zones or on airfields."""
    map_name = plan.get("map_name", "")
    map_data = MAP_REGISTRY.get(map_name, {})
    water_zones = map_data.get("water_zones", [])
    airfields = map_data.get("airfields", [])

    for group_key in ("red_sam", "blue_sam"):
        for group in data.get(group_key, []):
            group_name = group.get("name", "?")
            units = group.get("units", [])
            if not units:
                continue
            # Use first unit position as representative
            x = units[0].get("x", 0)
            y = units[0].get("y", 0)

            # Check water zones
            for wz in water_zones:
                cx, cy = wz.get("x", 0), wz.get("y", 0)
                radius = wz.get("radius", 0)
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if dist < radius:
                    r.warnings.append(
                        f"SAM group '{group_name}' placed in water zone "
                        f"'{wz.get('name', 'unknown')}' — SAMs can't float"
                    )
                    break

            # Check too close to airfields (within 500m)
            for af in airfields:
                af_x, af_y = af.get("x", 0), af.get("y", 0)
                dist = math.sqrt((x - af_x) ** 2 + (y - af_y) ** 2)
                if dist < 500:
                    r.warnings.append(
                        f"SAM group '{group_name}' placed on top of airfield "
                        f"'{af.get('name', '?')}' — may block runway"
                    )
                    break


def validate_lua_syntax(lua_files: dict[str, str]) -> ValidationResult:
    """
    Validate generated Lua files for basic syntax correctness.
    Checks bracket/brace balance, string quoting, trailing commas before
    closing braces, and key structural requirements.

    Args:
        lua_files: Dict mapping filename to Lua content string

    Returns:
        ValidationResult with any syntax issues found
    """
    result = ValidationResult()

    for filename, content in lua_files.items():
        if filename == "theatre":
            # Theatre is just a plain text string, not Lua
            if not content.strip():
                result.errors.append(f"{filename}: Theatre name is empty")
            continue

        _check_lua_brackets(filename, content, result)
        _check_lua_strings(filename, content, result)
        _check_lua_structure(filename, content, result)

    return result


def _check_lua_brackets(filename: str, content: str, r: ValidationResult):
    """Check that braces and brackets are balanced in Lua content."""
    open_braces = 0
    open_brackets = 0

    in_string = False
    escape_next = False

    for i, ch in enumerate(content):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\':
            escape_next = True
            continue
        if ch == '"' and not in_string:
            in_string = True
            continue
        if ch == '"' and in_string:
            in_string = False
            continue
        if in_string:
            continue

        if ch == '{':
            open_braces += 1
        elif ch == '}':
            open_braces -= 1
        elif ch == '[':
            open_brackets += 1
        elif ch == ']':
            open_brackets -= 1

        if open_braces < 0:
            line_num = content[:i].count('\n') + 1
            r.errors.append(f"{filename}:{line_num}: Extra closing brace '}}' — unbalanced")
            return
        if open_brackets < 0:
            line_num = content[:i].count('\n') + 1
            r.errors.append(f"{filename}:{line_num}: Extra closing bracket ']' — unbalanced")
            return

    if open_braces != 0:
        r.errors.append(
            f"{filename}: Unbalanced braces — {abs(open_braces)} "
            f"{'unclosed' if open_braces > 0 else 'extra closing'}"
        )
    if open_brackets != 0:
        r.errors.append(
            f"{filename}: Unbalanced brackets — {abs(open_brackets)} "
            f"{'unclosed' if open_brackets > 0 else 'extra closing'}"
        )


def _check_lua_strings(filename: str, content: str, r: ValidationResult):
    """Check for unclosed string literals in Lua content."""
    lines = content.split('\n')
    for line_num, line in enumerate(lines, 1):
        # Strip comments
        stripped = line.split('--')[0]
        # Count unescaped quotes
        quote_count = 0
        escape = False
        for ch in stripped:
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"':
                quote_count += 1
        if quote_count % 2 != 0:
            r.errors.append(
                f"{filename}:{line_num}: Unclosed string literal (odd number of quotes)"
            )


def _check_lua_structure(filename: str, content: str, r: ValidationResult):
    """Check key structural requirements for DCS Lua files."""
    if filename == "mission":
        if "mission =" not in content and "mission=" not in content:
            r.errors.append(f"{filename}: Missing 'mission = ' assignment — DCS won't load this")
        if '["coalition"]' not in content:
            r.errors.append(f"{filename}: Missing coalition block — no units will appear")
        if '["theatre"]' not in content:
            r.warnings.append(f"{filename}: Missing theatre field")
        if '["date"]' not in content:
            r.warnings.append(f"{filename}: Missing date field")
    elif filename == "warehouses":
        if "warehouses =" not in content and "warehouses=" not in content:
            r.errors.append(f"{filename}: Missing 'warehouses = ' assignment")
    elif filename == "options":
        if "options =" not in content and "options=" not in content:
            r.errors.append(f"{filename}: Missing 'options = ' assignment")
    elif filename == "dictionary":
        if "dictionary =" not in content and "dictionary=" not in content:
            r.errors.append(f"{filename}: Missing 'dictionary = ' assignment")

"""
Mission Parser
Converts natural language mission descriptions into structured mission plans
using Ollama LLM with schema validation and smart defaults.
"""

import json
import copy
from src.llm.ollama_client import OllamaClient
from src.units import (
    PLAYER_AIRCRAFT, MISSION_TEMPLATES, SAM_SYSTEMS,
    resolve_aircraft, resolve_mission_type,
    AIRCRAFT_ALIASES, MISSION_TYPE_ALIASES,
)
from src.maps import MAP_REGISTRY, MAP_ALIASES, resolve_map_name

def _build_system_prompt() -> str:
    """Build the LLM system prompt dynamically with current map/aircraft data."""
    # Get current aircraft list (including mods)
    aircraft_keys = list(PLAYER_AIRCRAFT.keys())

    # Build map-specific reference data
    map_details = []
    for map_key, md in MAP_REGISTRY.items():
        airfields = [af["name"] for af in md.get("airfields", [])]
        cities = [c["name"] for c in md.get("cities", [])]
        blue_afs = [af["name"] for af in md.get("airfields", []) if af.get("default_coalition") == "blue"]
        red_afs = [af["name"] for af in md.get("airfields", []) if af.get("default_coalition") == "red"]

        map_details.append(
            f"  {map_key}:\n"
            f"    Blue airfields: {', '.join(blue_afs[:6])}\n"
            f"    Red airfields: {', '.join(red_afs[:6])}\n"
            f"    Cities/locations: {', '.join(cities[:8])}"
        )

    map_info = "\n".join(map_details)

    return f"""You are a DCS World mission planning assistant. Your job is to parse natural language mission descriptions into structured JSON mission plans.

You MUST respond with ONLY valid JSON — no explanation, no markdown, no extra text.

Available player aircraft: {', '.join(aircraft_keys)}
Available maps: {', '.join(MAP_REGISTRY.keys())}
Available mission types: SEAD, CAS, CAP, strike, anti-ship, escort, convoy_attack, convoy_defense, CSAR, FAC
Available enemy SAM systems: SA-2, SA-3, SA-6, SA-8, SA-10, SA-11, SA-15, SA-19
Available enemy aircraft: Su-27, Su-33, MiG-29A, MiG-29S, MiG-31, Su-25, Su-25T, Su-24M, Tu-22M3
Available friendly AI aircraft: F-15C, F-16C_AI, F/A-18C_AI, A-10C_AI

Map reference data (use these real names for airfields and locations):
{map_info}

Output this exact JSON schema:
{{
    "map_name": "{"|".join(MAP_REGISTRY.keys())}",
    "player_aircraft": "{"|".join(aircraft_keys)}",
    "mission_type": "SEAD|CAS|CAP|strike|anti-ship|escort|convoy_attack|convoy_defense|CSAR|FAC",
    "player_airfield": "airfield name from the map data above, or AUTO",
    "time_of_day": "morning|afternoon|evening|night",
    "weather": "clear|scattered|overcast|rain|storm",
    "difficulty": "easy|medium|hard",
    "player_count": 1,
    "wingman": true,
    "friendly_flights": [
        {{"task": "SEAD|CAS|CAP|sweep|escort|strike", "aircraft": "aircraft_key", "count": 2}}
    ],
    "enemy_air": [
        {{"aircraft": "aircraft_key", "task": "CAP|intercept|sweep|strike", "count": 2}}
    ],
    "enemy_sam_sites": [
        {{"type": "SA-6|SA-11|etc", "location_desc": "near [city/feature from map data]"}}
    ],
    "enemy_ground": [
        {{"type": "armor|infantry|mixed|artillery", "count": 4, "role": "defending|advancing|patrol"}}
    ],
    "ground_war": {{
        "enabled": true,
        "front_line_desc": "description using real location names from the map",
        "blue_advancing": true,
        "red_advancing": true,
        "intensity": "light|medium|heavy"
    }},
    "objectives": ["objective 1", "objective 2"],
    "special_requests": "any unusual requirements from the user"
}}

Rules:
- If the user doesn't specify something, use null or omit it (defaults will be filled in later)
- For player_airfield, pick an appropriate blue airfield from the map data if the user mentions a preference, otherwise use "AUTO"
- For enemy_sam_sites location_desc, use real city/feature names from the map data above (e.g., "near Sukhumi", "covering the Gali approach", "defending Aleppo")
- Parse counts realistically: "a couple" = 2, "a few" = 3, "several" = 4-5
- Match aircraft and SAM names to the exact keys listed above
- The objectives should be clear tactical objectives that make sense for the mission type
- If mission type isn't clear, infer it from context (e.g., "destroy SAMs" = SEAD, "hit convoy" = convoy_attack, "rescue" = CSAR, "forward air control" = FAC)
- Always set wingman to true unless user says "solo" or "alone"
- For convoy_attack: the player is attacking an enemy convoy. For convoy_defense: protecting a friendly convoy.

EXAMPLES — follow these patterns exactly:

Input: "SEAD mission in the F-16 on Caucasus with SA-11 and SA-6, hard difficulty, afternoon"
Output:
{{
    "map_name": "Caucasus",
    "player_aircraft": "F-16C",
    "mission_type": "SEAD",
    "player_airfield": "AUTO",
    "time_of_day": "afternoon",
    "weather": "clear",
    "difficulty": "hard",
    "player_count": 1,
    "wingman": true,
    "friendly_flights": [],
    "enemy_air": [{{"aircraft": "MiG-29A", "task": "CAP", "count": 2}}],
    "enemy_sam_sites": [
        {{"type": "SA-11", "location_desc": "near Sukhumi"}},
        {{"type": "SA-6", "location_desc": "north of Gudauta"}}
    ],
    "enemy_ground": [],
    "ground_war": {{"enabled": true, "front_line_desc": "Dynamic front line", "blue_advancing": true, "red_advancing": false, "intensity": "heavy"}},
    "objectives": ["Destroy SA-11 and SA-6 sites", "RTB safely"],
    "special_requests": ""
}}

Input: "CAS in the A-10 over Syria, easy, support ground troops near Palmyra"
Output:
{{
    "map_name": "Syria",
    "player_aircraft": "A-10C",
    "mission_type": "CAS",
    "player_airfield": "AUTO",
    "time_of_day": "morning",
    "weather": "clear",
    "difficulty": "easy",
    "player_count": 1,
    "wingman": true,
    "friendly_flights": [],
    "enemy_air": [],
    "enemy_sam_sites": [{{"type": "SA-8", "location_desc": "near Palmyra"}}],
    "enemy_ground": [{{"type": "armor", "count": 4, "role": "advancing"}}, {{"type": "infantry", "count": 4, "role": "defending"}}],
    "ground_war": {{"enabled": true, "front_line_desc": "Near Palmyra", "blue_advancing": true, "red_advancing": false, "intensity": "medium"}},
    "objectives": ["Destroy enemy armor near Palmyra", "Support friendly ground advance"],
    "special_requests": ""
}}
"""


_CACHED_SYSTEM_PROMPT = None


def _get_system_prompt() -> str:
    """Get the system prompt, building it on first use (after mods are loaded)."""
    global _CACHED_SYSTEM_PROMPT
    if _CACHED_SYSTEM_PROMPT is None:
        _CACHED_SYSTEM_PROMPT = _build_system_prompt()
    return _CACHED_SYSTEM_PROMPT


def rebuild_system_prompt():
    """Force rebuild of system prompt (call after loading custom aircraft)."""
    global _CACHED_SYSTEM_PROMPT
    _CACHED_SYSTEM_PROMPT = None

REFINE_PROMPT = """You are modifying an existing DCS mission plan based on user feedback.
Current plan: {current_plan}
User requested changes: {changes}

Apply the requested changes and output the complete updated JSON plan.
Output ONLY valid JSON — no explanation, no markdown.
Use the same schema as before."""

# Default mission plan structure
DEFAULT_PLAN = {
    "map_name": "Caucasus",
    "player_aircraft": "F-16C",
    "mission_type": "SEAD",
    "player_airfield": "AUTO",
    "time_of_day": "morning",
    "weather": "clear",
    "difficulty": "medium",
    "player_count": 1,
    "wingman": True,
    "friendly_flights": [],
    "enemy_air": [],
    "enemy_sam_sites": [],
    "enemy_ground": [],
    "ground_war": {
        "enabled": True,
        "front_line_desc": "Dynamic front line",
        "blue_advancing": True,
        "red_advancing": True,
        "intensity": "medium",
    },
    "objectives": [],
    "special_requests": "",
}


class MissionParser:
    """Parse natural language into structured mission plans."""

    def __init__(self, client: OllamaClient):
        self.client = client

    def parse_description(self, description: str) -> dict | None:
        """
        Parse a natural language mission description into a structured plan.
        Uses LLM for parsing, then validates and fills defaults.
        """
        prompt = f"Parse this DCS mission description into JSON:\n\n\"{description}\""

        print("  Sending to LLM for parsing...")
        result = self.client.generate_json(prompt, system=_get_system_prompt(), temperature=0.2)

        if result is None:
            print("  LLM parsing failed. Attempting rule-based fallback...")
            result = self._rule_based_parse(description)

        if result is None:
            return None

        # Validate and fill defaults
        plan = self._validate_and_fill(result, description)
        return plan

    def refine_plan(self, current_plan: dict, changes: str) -> dict | None:
        """Refine an existing plan based on user feedback."""
        system = REFINE_PROMPT.format(
            current_plan=json.dumps(current_plan, indent=2),
            changes=changes,
        )
        prompt = f"Apply these changes: {changes}"

        result = self.client.generate_json(prompt, system=system, temperature=0.2)
        if result is None:
            return None

        return self._validate_and_fill(result, changes)

    def _validate_and_fill(self, raw: dict, original_desc: str = "") -> dict:
        """Validate LLM output and fill in smart defaults for missing fields."""
        plan = copy.deepcopy(DEFAULT_PLAN)

        # Resolve map name
        map_name = raw.get("map_name", "")
        resolved_map = resolve_map_name(map_name)
        if resolved_map:
            plan["map_name"] = resolved_map
        else:
            # Try to find map name in the original description
            desc_lower = original_desc.lower()
            for alias, key in MAP_ALIASES.items():
                if alias in desc_lower:
                    plan["map_name"] = key
                    break

        # Resolve player aircraft
        aircraft = raw.get("player_aircraft", "")
        resolved_ac = resolve_aircraft(aircraft)
        if resolved_ac:
            plan["player_aircraft"] = resolved_ac
        else:
            desc_lower = original_desc.lower()
            for alias, key in AIRCRAFT_ALIASES.items():
                if alias in desc_lower:
                    plan["player_aircraft"] = key
                    break

        # Resolve mission type
        mt = raw.get("mission_type", "")
        resolved_mt = resolve_mission_type(mt)
        if resolved_mt:
            plan["mission_type"] = resolved_mt
        else:
            import re
            desc_lower = original_desc.lower()
            # Sort by length descending so "convoy attack" matches before "attack"
            sorted_aliases = sorted(MISSION_TYPE_ALIASES.items(), key=lambda x: len(x[0]), reverse=True)
            for alias, key in sorted_aliases:
                if re.search(r'\b' + re.escape(alias) + r'\b', desc_lower):
                    plan["mission_type"] = key
                    break

        # Simple fields
        for field in ["player_airfield", "time_of_day", "weather", "difficulty",
                      "player_count", "wingman", "special_requests"]:
            if raw.get(field) is not None:
                plan[field] = raw[field]

        # Ensure player airfield is valid
        if plan["player_airfield"] == "AUTO" or not plan["player_airfield"]:
            plan["player_airfield"] = self._pick_airfield(plan["map_name"], "blue")

        # Fill template defaults if LLM didn't provide forces
        template = MISSION_TEMPLATES.get(plan["mission_type"], {})

        # Friendly flights
        if raw.get("friendly_flights"):
            plan["friendly_flights"] = raw["friendly_flights"]
        elif template.get("default_friendly_flights"):
            plan["friendly_flights"] = copy.deepcopy(template["default_friendly_flights"])

        # Enemy air
        if raw.get("enemy_air"):
            plan["enemy_air"] = raw["enemy_air"]
        elif template.get("default_enemy_air"):
            plan["enemy_air"] = [
                {"aircraft": ac, "task": "CAP", "count": 2}
                for ac in template["default_enemy_air"]
            ]

        # Enemy SAM sites
        if raw.get("enemy_sam_sites"):
            plan["enemy_sam_sites"] = raw["enemy_sam_sites"]
        elif template.get("default_enemy_sam"):
            map_data = MAP_REGISTRY.get(plan["map_name"], {})
            sam_zones = [z for z in map_data.get("sam_zones", []) if z["side"] == "red"]
            plan["enemy_sam_sites"] = []
            for i, sam_type in enumerate(template["default_enemy_sam"]):
                zone = sam_zones[i % len(sam_zones)] if sam_zones else {"name": "Forward position"}
                plan["enemy_sam_sites"].append({
                    "type": sam_type,
                    "location_desc": zone["name"],
                })

        # Enemy ground
        if raw.get("enemy_ground"):
            plan["enemy_ground"] = raw["enemy_ground"]
        elif plan["mission_type"] in ("CAS",) or template.get("ground_war_default"):
            plan["enemy_ground"] = [
                {"type": "armor", "count": 4, "role": "advancing"},
                {"type": "infantry", "count": 4, "role": "defending"},
            ]

        # Ground war
        if raw.get("ground_war"):
            gw = raw["ground_war"]
            if isinstance(gw, dict):
                plan["ground_war"].update(gw)
        elif template.get("ground_war_default") is not None:
            plan["ground_war"]["enabled"] = template["ground_war_default"]

        # Objectives
        if raw.get("objectives"):
            plan["objectives"] = raw["objectives"]
        else:
            plan["objectives"] = self._generate_objectives(plan)

        return plan

    def _pick_airfield(self, map_name: str, coalition: str) -> str:
        """Pick a sensible default airfield for the given map and coalition."""
        map_data = MAP_REGISTRY.get(map_name, {})
        airfields = map_data.get("airfields", [])

        # Prefer airfields matching the coalition
        matching = [af for af in airfields if af.get("default_coalition") == coalition]
        if matching:
            # Pick the first one with decent runway length
            for af in matching:
                runways = af.get("runways", [])
                if any(r.get("length", 0) >= 2400 for r in runways):
                    return af["name"]
            return matching[0]["name"]

        return airfields[0]["name"] if airfields else "Unknown"

    def _generate_objectives(self, plan: dict) -> list[str]:
        """Generate sensible objectives based on mission type."""
        mt = plan["mission_type"]
        ac = plan.get("player_aircraft", "Unknown")

        objectives = []
        if mt == "SEAD":
            sam_types = [s.get("type", "SAM") for s in plan.get("enemy_sam_sites", [])]
            if sam_types:
                objectives.append(f"Destroy enemy air defense sites: {', '.join(sam_types)}")
            else:
                objectives.append("Suppress/destroy enemy air defense network in the AO")
            objectives.append("RTB safely after ordnance expended")

        elif mt == "CAS":
            objectives.append("Provide close air support to friendly ground forces")
            objectives.append("Destroy enemy armor and infantry in the engagement zone")
            objectives.append("Coordinate with friendly SEAD flights — wait for SAM suppression")
            objectives.append("RTB when Winchester or Bingo fuel")

        elif mt == "CAP":
            objectives.append("Maintain combat air patrol over assigned area")
            objectives.append("Intercept and destroy enemy aircraft entering the patrol zone")
            objectives.append("Protect friendly ground forces and assets from enemy air attack")

        elif mt == "strike":
            objectives.append("Strike designated target area")
            objectives.append("Avoid engagement with enemy air defenses — rely on SEAD package")
            objectives.append("RTB after weapons release")

        elif mt == "anti-ship":
            objectives.append("Locate and destroy enemy naval group")
            objectives.append("Launch anti-ship weapons from standoff range")
            objectives.append("Avoid enemy ship-based air defenses")

        elif mt == "escort":
            objectives.append("Escort friendly strike package to and from target area")
            objectives.append("Engage any enemy interceptors threatening the package")
            objectives.append("Maintain formation with strike flight")

        elif mt == "convoy_attack":
            objectives.append("Locate and destroy enemy supply convoy")
            objectives.append("Prioritize fuel and ammo trucks — escort vehicles secondary")
            objectives.append("Watch for convoy SHORAD escorts (AAA, MANPADS)")
            objectives.append("RTB after convoy destroyed or ordnance expended")

        elif mt == "convoy_defense":
            objectives.append("Protect friendly supply convoy from enemy air attack")
            objectives.append("Maintain overhead CAP — intercept inbound strike aircraft")
            objectives.append("Do NOT stray from convoy — stay within visual range")
            objectives.append("Convoy must reach its destination intact")

        return objectives

    def _rule_based_parse(self, description: str) -> dict | None:
        """Fallback: parse description using keyword matching with word boundaries."""
        import re
        desc_lower = description.lower()
        result = {}

        # Map — use word boundary to avoid false matches
        for alias, key in MAP_ALIASES.items():
            if re.search(r'\b' + re.escape(alias) + r'\b', desc_lower):
                result["map_name"] = key
                break

        # Aircraft — these are specific enough for substring match
        for alias, key in AIRCRAFT_ALIASES.items():
            if alias in desc_lower:
                result["player_aircraft"] = key
                break

        # Mission type — MUST use word boundary and match longest phrases first
        # Sort aliases by length descending so "convoy attack" matches before "attack"
        sorted_aliases = sorted(MISSION_TYPE_ALIASES.items(), key=lambda x: len(x[0]), reverse=True)
        for alias, key in sorted_aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', desc_lower):
                result["mission_type"] = key
                break

        # SAM sites
        sam_keywords = {
            "sa-2": "SA-2", "sa-6": "SA-6", "sa-8": "SA-8",
            "sa-10": "SA-10", "sa-11": "SA-11", "sa-15": "SA-15",
            "s-300": "SA-10", "buk": "SA-11", "kub": "SA-6",
        }
        sam_sites = []
        for keyword, sam_type in sam_keywords.items():
            if keyword in desc_lower:
                sam_sites.append({"type": sam_type, "location_desc": "auto"})
        if sam_sites:
            result["enemy_sam_sites"] = sam_sites

        # Weather
        for w in ["clear", "overcast", "rain", "storm", "scattered"]:
            if w in desc_lower:
                result["weather"] = w
                break

        # Time
        for t in ["morning", "afternoon", "evening", "night"]:
            if t in desc_lower:
                result["time_of_day"] = t
                break

        # Scale hints
        if any(w in desc_lower for w in ["large", "big", "full scale", "theater"]):
            result["ground_war"] = {"enabled": True, "intensity": "heavy"}
        if any(w in desc_lower for w in ["simple", "small", "quick", "training"]):
            result["ground_war"] = {"enabled": False}

        # Difficulty
        if "easy" in desc_lower:
            result["difficulty"] = "easy"
        elif "hard" in desc_lower:
            result["difficulty"] = "hard"
        elif "medium" in desc_lower:
            result["difficulty"] = "medium"

        return result if result else None

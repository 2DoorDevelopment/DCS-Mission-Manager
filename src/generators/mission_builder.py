"""
Mission Builder
Takes a validated mission plan and builds full mission data structures
with proper coordinates, waypoints, group compositions, and timing.

The heavy lifting is delegated to sub-modules:
  - group_builders.py  — air groups, SAM sites, ground war, convoys, support
  - waypoint_builders.py — player and AI waypoint sequences
"""

import math
import random
from src.maps import MAP_REGISTRY
from src.units import MISSION_TEMPLATES
from src.flight_profile import estimate_fuel
from src.callsigns import CallsignAssigner, FrequencyAssigner
from src.mission_events import generate_message_triggers, generate_win_conditions
from src.generators.group_builders import (
    build_player_group, build_friendly_flights, build_enemy_sams,
    build_friendly_sams, build_enemy_air, build_ground_war,
    build_convoy, build_support, build_reinforcements,
    build_naval_groups, build_csar_objective, build_fac_targets,
)


class BuilderState:
    """Shared mutable state passed to all sub-builder functions."""

    def __init__(self, plan: dict):
        self.plan = plan
        self.map_name = plan["map_name"]
        self.map_data = MAP_REGISTRY.get(self.map_name, {})
        self.mission_type = plan["mission_type"]
        self.template = MISSION_TEMPLATES.get(self.mission_type, {})

        # ID counters
        self._group_id = 1
        self._unit_id = 1

        # Generated data
        self.blue_air_groups: list[dict] = []
        self.red_air_groups: list[dict] = []
        self.blue_ground_groups: list[dict] = []
        self.red_ground_groups: list[dict] = []
        self.blue_sam_groups: list[dict] = []
        self.red_sam_groups: list[dict] = []
        self.triggers: list[dict] = []
        self.player_group: dict | None = None

        # Performance cap
        self.total_units = 0
        self.max_units = 120

        # Naval groups (for anti-ship missions)
        self.blue_naval_groups: list[dict] = []
        self.red_naval_groups: list[dict] = []

        # Callsign and frequency assignment
        self.callsigns = CallsignAssigner()
        self.frequencies = FrequencyAssigner()
        self.assigned_callsigns: dict = {}

        # Convoy route (populated by build_convoy)
        self.convoy_route: list[dict] | None = None

        # CSAR objective position (populated by build_csar_objective)
        self.csar_position: dict | None = None

    # --- ID helpers -------------------------------------------------------

    def next_group_id(self) -> int:
        gid = self._group_id
        self._group_id += 1
        return gid

    def next_unit_id(self) -> int:
        uid = self._unit_id
        self._unit_id += 1
        return uid

    # --- Shared query helpers used by sub-builders ------------------------

    def get_airfield(self, name: str) -> dict | None:
        for af in self.map_data.get("airfields", []):
            if af["name"].lower() == name.lower():
                return af
        for af in self.map_data.get("airfields", []):
            if name.lower() in af["name"].lower():
                return af
        return None

    def get_mission_time(self) -> int:
        times = {
            "morning": 6 * 3600 + random.randint(0, 7200),
            "afternoon": 13 * 3600 + random.randint(0, 7200),
            "evening": 17 * 3600 + random.randint(0, 3600),
            "night": 21 * 3600 + random.randint(0, 7200),
        }
        return times.get(self.plan.get("time_of_day", "morning"), 7 * 3600)

    def get_weather(self) -> dict:
        weather_type = self.plan.get("weather", "clear")
        presets = {
            "clear": {
                "atmosphere_type": 0,
                "clouds": {"preset": "Preset1", "base": 2500, "thickness": 200, "is_ceiling": False},
                "visibility": 80000,
                "wind": {"at_ground": {"speed": 3, "dir": 180}},
                "turbulence": 0,
                "fog": {"enabled": False},
            },
            "scattered": {
                "atmosphere_type": 0,
                "clouds": {"preset": "Preset4", "base": 2000, "thickness": 400, "is_ceiling": False},
                "visibility": 60000,
                "wind": {"at_ground": {"speed": 5, "dir": 220}},
                "turbulence": 3,
                "fog": {"enabled": False},
            },
            "overcast": {
                "atmosphere_type": 0,
                "clouds": {"preset": "Preset10", "base": 1500, "thickness": 800, "is_ceiling": True},
                "visibility": 40000,
                "wind": {"at_ground": {"speed": 8, "dir": 240}},
                "turbulence": 5,
                "fog": {"enabled": False},
            },
            "rain": {
                "atmosphere_type": 0,
                "clouds": {"preset": "RainyPreset1", "base": 800, "thickness": 1500, "is_ceiling": True},
                "visibility": 20000,
                "wind": {"at_ground": {"speed": 10, "dir": 250}},
                "turbulence": 8,
                "fog": {"enabled": True, "visibility": 5000, "thickness": 200},
            },
            "storm": {
                "atmosphere_type": 0,
                "clouds": {"preset": "RainyPreset3", "base": 500, "thickness": 2000, "is_ceiling": True},
                "visibility": 10000,
                "wind": {"at_ground": {"speed": 15, "dir": 270}},
                "turbulence": 12,
                "fog": {"enabled": True, "visibility": 3000, "thickness": 300},
            },
        }
        return presets.get(weather_type, presets["clear"])

    def get_target_position(self) -> dict:
        sam_zones = [z for z in self.map_data.get("sam_zones", []) if z["side"] == "red"]
        cities = [c for c in self.map_data.get("cities", []) if c["side"] in ("contested", "red")]
        front_lines = self.map_data.get("front_lines", [])

        if self.mission_type == "SEAD" and sam_zones:
            zone = sam_zones[0]
            return {"x": zone["x"], "y": zone["y"]}
        elif self.mission_type == "CAS" and front_lines:
            fl = front_lines[0]
            return {
                "x": (fl["blue_start"]["x"] + fl["red_start"]["x"]) / 2,
                "y": (fl["blue_start"]["y"] + fl["red_start"]["y"]) / 2,
            }
        elif self.mission_type in ("strike",) and cities:
            city = random.choice(cities[:3])
            return {"x": city["x"], "y": city["y"]}
        elif self.mission_type == "anti-ship":
            naval = self.map_data.get("naval_zones", [])
            if naval:
                zone = naval[0]
                return {"x": zone["x"], "y": zone["y"]}
        elif self.mission_type == "CAP":
            orbits = [o for o in self.map_data.get("cap_orbits", []) if o["side"] == "blue"]
            if orbits:
                orbit = orbits[0]
                return {"x": orbit["x1"], "y": orbit["y1"]}
        elif self.mission_type in ("convoy_attack", "convoy_defense"):
            if self.convoy_route and len(self.convoy_route) >= 2:
                mid_idx = len(self.convoy_route) // 2
                wp = self.convoy_route[mid_idx]
                return {"x": wp["x"], "y": wp["y"]}
            convoy_side = "red" if self.mission_type == "convoy_attack" else "blue"
            routes = self.map_data.get("convoy_routes", {}).get(convoy_side, [])
            if routes:
                wps = routes[0]["waypoints"]
                mid = wps[len(wps) // 2]
                return {"x": mid["x"], "y": mid["y"]}
        elif self.mission_type == "CSAR":
            if self.csar_position:
                return self.csar_position
            # Fall back to front line area
            if front_lines:
                fl = front_lines[0]
                return {
                    "x": (fl["blue_start"]["x"] + fl["red_start"]["x"]) / 2,
                    "y": (fl["blue_start"]["y"] + fl["red_start"]["y"]) / 2,
                }
        elif self.mission_type == "FAC":
            if front_lines:
                fl = front_lines[0]
                return {
                    "x": (fl["blue_start"]["x"] + fl["red_start"]["x"]) / 2,
                    "y": (fl["blue_start"]["y"] + fl["red_start"]["y"]) / 2,
                }

        if cities:
            return {"x": cities[0]["x"], "y": cities[0]["y"]}
        if sam_zones:
            return {"x": sam_zones[0]["x"], "y": sam_zones[0]["y"]}
        return {"x": 0, "y": 0}

    def get_wp_tasks_for_ip(self) -> list:
        if self.mission_type == "SEAD":
            return [{"id": "EngageTargets", "params": {"targetTypes": ["Air Defence"]}}]
        elif self.mission_type in ("CAS", "convoy_attack"):
            return [{"id": "EngageTargets", "params": {"targetTypes": ["Armor", "Vehicles"]}}]
        elif self.mission_type == "convoy_defense":
            return [{"id": "EngageTargets", "params": {"targetTypes": ["Air"]}}]
        elif self.mission_type == "CSAR":
            return [{"id": "EngageTargets", "params": {"targetTypes": ["Air Defence", "Armor"]}}]
        elif self.mission_type == "FAC":
            return [{"id": "FAC", "params": {}}]
        return []

    def get_wp_tasks_for_target(self) -> list:
        if self.mission_type == "SEAD":
            return [{"id": "EngageTargets", "params": {"targetTypes": ["Air Defence"], "priority": 0}}]
        elif self.mission_type == "CAS":
            return [{"id": "CAS", "params": {}}]
        elif self.mission_type == "strike":
            return [{"id": "Bombing", "params": {}}]
        elif self.mission_type == "anti-ship":
            return [{"id": "AntishipStrike", "params": {}}]
        elif self.mission_type in ("CAP", "escort", "convoy_defense"):
            return [{"id": "CAP", "params": {}}]
        elif self.mission_type == "convoy_attack":
            return [{"id": "EngageTargets", "params": {"targetTypes": ["Vehicles", "Armor"]}}]
        elif self.mission_type == "CSAR":
            return [{"id": "Orbit", "params": {"pattern": "Circle", "speed": 80, "altitude": 300}}]
        elif self.mission_type == "FAC":
            return [{"id": "FAC", "params": {}}]
        return []

    def avoid_water(self, x: float, y: float, max_retries: int = 5) -> tuple[float, float]:
        water_zones = self.map_data.get("water_zones", [])
        if not water_zones:
            return x, y
        for _ in range(max_retries):
            in_water = False
            for wz in water_zones:
                cx, cy = wz.get("x", 0), wz.get("y", 0)
                radius = wz.get("radius", 0)
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if dist < radius:
                    if dist == 0:
                        angle = random.uniform(0, 2 * math.pi)
                    else:
                        angle = math.atan2(y - cy, x - cx)
                    x = cx + (radius + 2000) * math.cos(angle)
                    y = cy + (radius + 2000) * math.sin(angle)
                    in_water = True
                    break
            if not in_water:
                break
        return x, y


class MissionBuilder:
    """Builds complete mission data from a structured plan.

    Public API is unchanged: ``MissionBuilder(plan).build()``
    Internally delegates to BuilderState + sub-builder modules.
    """

    def __init__(self, plan: dict):
        self.plan = plan
        self._state = BuilderState(plan)

    def build(self) -> dict:
        """Build the complete mission data structure."""
        s = self._state

        # Resolve player airfield
        player_af = s.get_airfield(self.plan["player_airfield"])
        if not player_af:
            blue_afs = [af for af in s.map_data.get("airfields", [])
                        if af.get("default_coalition") == "blue"]
            all_afs = s.map_data.get("airfields", [])
            if blue_afs:
                player_af = blue_afs[0]
            elif all_afs:
                player_af = all_afs[0]
            else:
                raise ValueError(f"No airfields defined for map '{self.plan.get('map_name', 'unknown')}'.")

        # Convoy first (target position depends on it)
        if s.mission_type in ("convoy_attack", "convoy_defense"):
            build_convoy(s)

        # CSAR objective (downed pilot) before player group so target position is set
        if s.mission_type == "CSAR":
            build_csar_objective(s)

        # FAC ground targets before player group
        if s.mission_type == "FAC":
            build_fac_targets(s)

        build_player_group(s, player_af)
        build_friendly_flights(s, player_af)
        build_enemy_sams(s)
        build_friendly_sams(s)
        build_enemy_air(s)

        # Naval groups for anti-ship missions
        if s.mission_type == "anti-ship":
            build_naval_groups(s)

        if self.plan.get("ground_war", {}).get("enabled", False):
            build_ground_war(s)

        build_support(s)
        build_reinforcements(s)
        self._apply_staggered_spawns()
        self._apply_radio_presets()

        messages = generate_message_triggers(self.plan, s.assigned_callsigns)
        conditions = generate_win_conditions(self.plan)

        target_pos = s.get_target_position()
        af_data = s.get_airfield(self.plan["player_airfield"]) or {"x": 0, "y": 0}
        dist = math.sqrt((target_pos["x"] - af_data["x"])**2 +
                         (target_pos["y"] - af_data["y"])**2)
        fuel_est = estimate_fuel(self.plan["player_aircraft"], dist)

        mission_data = {
            "theater": s.map_data.get("dcs_theater", s.map_name),
            "map_name": s.map_name,
            "date": s.map_data.get("default_date", {"year": 2024, "month": 6, "day": 15}),
            "time": s.get_mission_time(),
            "weather": s.get_weather(),
            "player_group": s.player_group,
            "blue_air": s.blue_air_groups,
            "red_air": s.red_air_groups,
            "blue_ground": s.blue_ground_groups,
            "red_ground": s.red_ground_groups,
            "blue_sam": s.blue_sam_groups,
            "red_sam": s.red_sam_groups,
            "blue_naval": s.blue_naval_groups,
            "red_naval": s.red_naval_groups,
            "triggers": s.triggers,
            "messages": messages,
            "conditions": conditions,
            "callsigns": s.assigned_callsigns,
            "fuel_estimate": fuel_est,
            "plan": self.plan,
        }

        print(f"    Built {s.total_units} total units "
              f"({len(s.blue_air_groups) + len(s.red_air_groups)} air groups, "
              f"{len(s.blue_ground_groups) + len(s.red_ground_groups)} ground groups, "
              f"{len(s.blue_sam_groups) + len(s.red_sam_groups)} SAM sites)")

        return mission_data

    def _apply_staggered_spawns(self):
        """Convert late_activation flags to start_time delays for staggered spawning."""
        s = self._state
        delay = 300

        all_groups = (s.blue_air_groups + s.red_air_groups +
                      s.blue_ground_groups + s.red_ground_groups)

        for group in all_groups:
            if group.get("late_activation"):
                group["_start_delay"] = delay
                delay += 180
                del group["late_activation"]
            else:
                group["_start_delay"] = 0

    def _apply_radio_presets(self):
        """Populate radio presets on player aircraft units with mission frequencies."""
        s = self._state
        if not s.player_group:
            return

        # Build a frequency list from assigned callsigns
        channels = []

        # Channel 1: Player flight frequency
        player_cs = s.assigned_callsigns.get("player", {})
        channels.append(player_cs.get("freq", 305.0))

        # Channels for support assets
        tanker_cs = s.assigned_callsigns.get("tanker", {})
        if tanker_cs.get("freq"):
            channels.append(tanker_cs["freq"])

        awacs_cs = s.assigned_callsigns.get("awacs", {})
        if awacs_cs.get("freq"):
            channels.append(awacs_cs["freq"])

        # Channels for friendly flights
        for key, cs_data in s.assigned_callsigns.items():
            if key.startswith("friendly_") and cs_data.get("freq"):
                channels.append(cs_data["freq"])

        # SEAD package frequency
        sead_cs = s.assigned_callsigns.get("sead", {})
        if sead_cs.get("freq"):
            channels.append(sead_cs["freq"])

        # Guard frequency
        channels.append(243.0)

        # Pad to 20 channels with common defaults
        default_freqs = [253.0, 254.0, 255.0, 256.0, 257.0, 258.0, 259.0,
                         260.0, 261.0, 262.0, 263.0, 264.0, 265.0, 266.0]
        while len(channels) < 20:
            if default_freqs:
                f = default_freqs.pop(0)
                if f not in channels:
                    channels.append(f)
                    continue
            channels.append(305.0)

        radio_presets = [{"channels": channels[:20]}]

        for unit in s.player_group.get("units", []):
            unit["_radio_presets"] = radio_presets

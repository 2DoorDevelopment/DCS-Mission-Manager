"""
Mission Builder
Takes a validated mission plan and builds full mission data structures
with proper coordinates, waypoints, group compositions, and timing.
"""

import math
import random
import copy
from src.maps import MAP_REGISTRY
from src.units import (
    PLAYER_AIRCRAFT, AI_AIRCRAFT, SAM_SYSTEMS,
    GROUND_UNITS, NAVAL_UNITS, MISSION_TEMPLATES,
    resolve_ai_loadout, CONVOY_UNITS,
)
from src.flight_profile import compute_flight_profile, estimate_fuel
from src.callsigns import CallsignAssigner, FrequencyAssigner
from src.mission_events import (
    generate_message_triggers, generate_win_conditions,
    generate_reinforcement_waves,
)


class MissionBuilder:
    """Builds complete mission data from a structured plan."""

    def __init__(self, plan: dict):
        self.plan = plan
        self.map_name = plan["map_name"]
        self.map_data = MAP_REGISTRY.get(self.map_name, {})
        self.mission_type = plan["mission_type"]
        self.template = MISSION_TEMPLATES.get(self.mission_type, {})

        # ID counters
        self._group_id = 1
        self._unit_id = 1
        self._route_id = 1

        # Generated data
        self.blue_air_groups = []
        self.red_air_groups = []
        self.blue_ground_groups = []
        self.red_ground_groups = []
        self.blue_sam_groups = []
        self.red_sam_groups = []
        self.blue_static = []
        self.red_static = []
        self.triggers = []
        self.player_group = None

        # Performance: track total active units
        self._total_units = 0
        self._max_units = 120  # hard cap for performance

        # Callsign and frequency assignment
        self._callsigns = CallsignAssigner()
        self._frequencies = FrequencyAssigner()
        self._assigned_callsigns = {}  # role -> callsign info for briefing

    def _next_group_id(self) -> int:
        gid = self._group_id
        self._group_id += 1
        return gid

    def _next_unit_id(self) -> int:
        uid = self._unit_id
        self._unit_id += 1
        return uid

    def build(self) -> dict:
        """Build the complete mission data structure."""
        # Resolve player airfield to coordinates
        player_af = self._get_airfield(self.plan["player_airfield"])
        if not player_af:
            blue_afs = [af for af in self.map_data.get("airfields", [])
                        if af.get("default_coalition") == "blue"]
            player_af = blue_afs[0] if blue_afs else self.map_data["airfields"][0]

        # Build convoy FIRST if convoy mission (so target position is available for player waypoints)
        self._convoy_route = None
        if self.mission_type in ("convoy_attack", "convoy_defense"):
            self._build_convoy()

        # Build player group
        self._build_player_group(player_af)

        # Build friendly AI flights
        self._build_friendly_flights(player_af)

        # Build enemy SAM sites (with random placement + SHORAD)
        self._build_enemy_sams()

        # Build friendly SAM sites
        self._build_friendly_sams()

        # Build enemy air groups
        self._build_enemy_air()

        # Build ground war
        if self.plan.get("ground_war", {}).get("enabled", False):
            self._build_ground_war()

        # Build support aircraft (tanker, AWACS)
        self._build_support()

        # Build timed enemy reinforcement waves
        self._build_reinforcements()

        # Build triggers for performance (late activation / staggered spawns)
        self._build_triggers()

        # Generate message triggers and win/loss conditions
        messages = generate_message_triggers(self.plan, self._assigned_callsigns)
        conditions = generate_win_conditions(self.plan)

        # Compute fuel estimate
        target_pos = self._get_target_position()
        player_af_data = self._get_airfield(self.plan["player_airfield"]) or {"x": 0, "y": 0}
        dist = math.sqrt((target_pos["x"] - player_af_data["x"])**2 +
                         (target_pos["y"] - player_af_data["y"])**2)
        fuel_est = estimate_fuel(self.plan["player_aircraft"], dist)

        # Assemble mission data
        mission_data = {
            "theater": self.map_data.get("dcs_theater", self.map_name),
            "map_name": self.map_name,
            "date": self.map_data.get("default_date", {"year": 2024, "month": 6, "day": 15}),
            "time": self._get_mission_time(),
            "weather": self._get_weather(),
            "player_group": self.player_group,
            "blue_air": self.blue_air_groups,
            "red_air": self.red_air_groups,
            "blue_ground": self.blue_ground_groups,
            "red_ground": self.red_ground_groups,
            "blue_sam": self.blue_sam_groups,
            "red_sam": self.red_sam_groups,
            "triggers": self.triggers,
            "messages": messages,
            "conditions": conditions,
            "callsigns": self._assigned_callsigns,
            "fuel_estimate": fuel_est,
            "plan": self.plan,
        }

        print(f"    Built {self._total_units} total units "
              f"({len(self.blue_air_groups) + len(self.red_air_groups)} air groups, "
              f"{len(self.blue_ground_groups) + len(self.red_ground_groups)} ground groups, "
              f"{len(self.blue_sam_groups) + len(self.red_sam_groups)} SAM sites)")

        return mission_data

    def _get_airfield(self, name: str) -> dict | None:
        """Find airfield data by name."""
        for af in self.map_data.get("airfields", []):
            if af["name"].lower() == name.lower():
                return af
        # Partial match
        for af in self.map_data.get("airfields", []):
            if name.lower() in af["name"].lower():
                return af
        return None

    def _get_mission_time(self) -> int:
        """Convert time_of_day to seconds since midnight."""
        times = {
            "morning": 6 * 3600 + random.randint(0, 7200),   # 06:00-08:00
            "afternoon": 13 * 3600 + random.randint(0, 7200), # 13:00-15:00
            "evening": 17 * 3600 + random.randint(0, 3600),   # 17:00-18:00
            "night": 21 * 3600 + random.randint(0, 7200),     # 21:00-23:00
        }
        return times.get(self.plan.get("time_of_day", "morning"), 7 * 3600)

    def _get_weather(self) -> dict:
        """Build weather preset data."""
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

    def _build_player_group(self, airfield: dict):
        """Build the player's aircraft group with realistic flight profile waypoints."""
        ac_key = self.plan["player_aircraft"]
        ac_data = PLAYER_AIRCRAFT.get(ac_key, {})

        # Determine loadout
        loadout_key = self.mission_type
        loadout = ac_data.get("default_loadouts", {}).get(loadout_key, {})

        # Assign player callsign
        player_cs = self._callsigns.assign_player(self.mission_type)
        player_freq = self._frequencies.assign_flight(player_cs["callsign"])
        self._assigned_callsigns["player"] = {**player_cs, "freq": player_freq}

        # Compute flight profile (altitude/speed based on aircraft + mission + weather)
        target_pos = self._get_target_position()
        dist = math.sqrt((target_pos["x"] - airfield["x"])**2 +
                         (target_pos["y"] - airfield["y"])**2)
        weather = self._get_weather()
        profile = compute_flight_profile(ac_key, self.mission_type, weather, dist)
        self.plan["_flight_profile"] = profile  # Store for briefing

        # Fuel estimate
        fuel_est = estimate_fuel(ac_key, dist)
        self.plan["_fuel_estimate"] = fuel_est

        # Build waypoints with realistic profile
        waypoints = self._build_player_waypoints_profiled(airfield, target_pos, profile)

        group_id = self._next_group_id()
        unit_id = self._next_unit_id()

        player_units = [{
            "unit_id": unit_id,
            "type": ac_data.get("type", "F-16C_50"),
            "name": player_cs["full"],
            "skill": "Player",
            "x": airfield["x"],
            "y": airfield["y"],
            "alt": airfield.get("alt", 0),
            "heading": math.radians(airfield.get("runways", [{"heading": 0}])[0]["heading"]),
            "pylons": loadout.get("pylons", {}),
            "chaff": ac_data.get("chaff", 60),
            "flare": ac_data.get("flare", 60),
            "fuel": ac_data.get("fuel", 3249),
            "callsign_name": player_cs["callsign"],
            "callsign_flight": player_cs["flight"],
        }]

        # Add wingman
        if self.plan.get("wingman", True):
            wm_id = self._next_unit_id()
            wm = copy.deepcopy(player_units[0])
            wm["unit_id"] = wm_id
            wm["name"] = f"{player_cs['callsign']} 1-2"
            wm["skill"] = "High"
            wm["y"] = airfield["y"] + 30
            player_units.append(wm)
            self._total_units += 1

        self._total_units += 1

        self.player_group = {
            "group_id": group_id,
            "name": f"{player_cs['callsign']} Flight",
            "coalition": "blue",
            "category": "plane",
            "task": self.mission_type,
            "units": player_units,
            "waypoints": waypoints,
            "frequency": player_freq,
            "communication": True,
            "start_type": "Takeoff from Parking",
            "airfield_id": airfield.get("id", 0),
            "late_activation": False,
            "uncontrolled": False,
        }

    def _build_player_waypoints_profiled(self, airfield: dict, target_pos: dict,
                                          profile: dict) -> list[dict]:
        """Build player waypoints with realistic altitude/speed profiles."""
        waypoints = []
        wp_id = 0

        # WP0: Takeoff
        waypoints.append({
            "id": wp_id, "name": "TAKEOFF", "type": "TakeOff",
            "action": "From Parking Area",
            "x": airfield["x"], "y": airfield["y"],
            "alt": airfield.get("alt", 0), "speed": 0,
            "airfield_id": airfield.get("id", 0),
        })
        wp_id += 1

        angle = math.atan2(target_pos["y"] - airfield["y"],
                           target_pos["x"] - airfield["x"])

        # WP1: Departure — climbing
        depart_x = airfield["x"] + (target_pos["x"] - airfield["x"]) * 0.12
        depart_y = airfield["y"] + (target_pos["y"] - airfield["y"]) * 0.12
        waypoints.append({
            "id": wp_id, "name": "DEPART", "type": "Turning Point",
            "action": "Turning Point",
            "x": depart_x, "y": depart_y,
            "alt": profile["depart_alt"], "speed": profile["depart_speed"],
        })
        wp_id += 1

        # WP2: Cruise — top of climb
        cruise_x = airfield["x"] + (target_pos["x"] - airfield["x"]) * 0.4
        cruise_y = airfield["y"] + (target_pos["y"] - airfield["y"]) * 0.4
        waypoints.append({
            "id": wp_id, "name": "CRUISE", "type": "Turning Point",
            "action": "Turning Point",
            "x": cruise_x, "y": cruise_y,
            "alt": profile["cruise_alt"], "speed": profile["cruise_speed"],
        })
        wp_id += 1

        # WP3: Push — begin descent to ingress altitude
        push_x = airfield["x"] + (target_pos["x"] - airfield["x"]) * 0.65
        push_y = airfield["y"] + (target_pos["y"] - airfield["y"]) * 0.65
        waypoints.append({
            "id": wp_id, "name": "PUSH", "type": "Turning Point",
            "action": "Turning Point",
            "x": push_x, "y": push_y,
            "alt": profile["push_alt"], "speed": profile["push_speed"],
        })
        wp_id += 1

        # WP4: IP — at ingress altitude, combat speed
        ip_offset = 15000
        ip_x = target_pos["x"] - ip_offset * math.cos(angle)
        ip_y = target_pos["y"] - ip_offset * math.sin(angle)
        waypoints.append({
            "id": wp_id, "name": "IP", "type": "Turning Point",
            "action": "Turning Point",
            "x": ip_x, "y": ip_y,
            "alt": profile["ip_alt"], "speed": profile["ip_speed"],
            "tasks": self._get_wp_tasks_for_ip(),
        })
        wp_id += 1

        # WP5: Target — attack altitude
        waypoints.append({
            "id": wp_id, "name": "TARGET", "type": "Turning Point",
            "action": "Turning Point",
            "x": target_pos["x"], "y": target_pos["y"],
            "alt": profile["target_alt"], "speed": profile["target_speed"],
            "tasks": self._get_wp_tasks_for_target(),
        })
        wp_id += 1

        # WP6: Egress — fast, at egress altitude
        egress_angle = angle + math.pi + math.radians(random.randint(-30, 30))
        egress_x = target_pos["x"] + 20000 * math.cos(egress_angle)
        egress_y = target_pos["y"] + 20000 * math.sin(egress_angle)
        waypoints.append({
            "id": wp_id, "name": "EGRESS", "type": "Turning Point",
            "action": "Turning Point",
            "x": egress_x, "y": egress_y,
            "alt": profile["egress_alt"], "speed": profile["egress_speed"],
        })
        wp_id += 1

        # WP7: RTB / Landing
        waypoints.append({
            "id": wp_id, "name": "LANDING", "type": "Land",
            "action": "Landing",
            "x": airfield["x"], "y": airfield["y"],
            "alt": airfield.get("alt", 0), "speed": 0,
            "airfield_id": airfield.get("id", 0),
        })

        return waypoints

    def _get_target_position(self) -> dict:
        """Determine target position based on mission type and enemies."""
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
            # Target is the midpoint of the convoy route
            convoy_route = getattr(self, "_convoy_route", None)
            if convoy_route and len(convoy_route) >= 2:
                mid_idx = len(convoy_route) // 2
                wp = convoy_route[mid_idx]
                return {"x": wp["x"], "y": wp["y"]}
            # Fallback: grab midpoint from map convoy route data
            convoy_side = "red" if self.mission_type == "convoy_attack" else "blue"
            routes = self.map_data.get("convoy_routes", {}).get(convoy_side, [])
            if routes:
                wps = routes[0]["waypoints"]
                mid = wps[len(wps) // 2]
                return {"x": mid["x"], "y": mid["y"]}

        # Fallback: pick a contested city or first enemy zone
        if cities:
            return {"x": cities[0]["x"], "y": cities[0]["y"]}
        if sam_zones:
            return {"x": sam_zones[0]["x"], "y": sam_zones[0]["y"]}

        return {"x": 0, "y": 0}

    def _get_wp_tasks_for_ip(self) -> list:
        """Get DCS waypoint tasks for the IP."""
        if self.mission_type == "SEAD":
            return [{"id": "EngageTargets", "params": {"targetTypes": ["Air Defence"]}}]
        elif self.mission_type in ("CAS", "convoy_attack"):
            return [{"id": "EngageTargets", "params": {"targetTypes": ["Armor", "Vehicles"]}}]
        elif self.mission_type == "convoy_defense":
            return [{"id": "EngageTargets", "params": {"targetTypes": ["Air"]}}]
        return []

    def _get_wp_tasks_for_target(self) -> list:
        """Get DCS waypoint tasks for the target."""
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
        return []

    def _build_friendly_flights(self, player_af: dict):
        """Build friendly AI flight groups."""
        for flight in self.plan.get("friendly_flights", []):
            if self._total_units >= self._max_units:
                break

            ac_key = flight.get("aircraft", "F-15C")
            ac_data = AI_AIRCRAFT.get(ac_key, AI_AIRCRAFT.get("F-15C"))
            task = flight.get("task", "escort")
            count = min(flight.get("count", 2), 4)

            group_id = self._next_group_id()
            units = []

            # Resolve AI loadout for this task
            ai_pylons = resolve_ai_loadout(ac_key, task)
            friendly_skill = self.plan.get("_friendly_ai_skill", ac_data.get("skill", "High"))

            for i in range(count):
                uid = self._next_unit_id()
                units.append({
                    "unit_id": uid,
                    "type": ac_data.get("type", "F-15C"),
                    "name": f"{ac_data.get('display_name', 'AI')} {i+1}",
                    "skill": friendly_skill,
                    "x": player_af["x"] + random.randint(-200, 200),
                    "y": player_af["y"] + random.randint(-200, 200),
                    "alt": player_af.get("alt", 0),
                    "heading": 0,
                    "pylons": ai_pylons,
                    "fuel": 3249,
                    "chaff": 60,
                    "flare": 60,
                })
                self._total_units += 1

            # Build waypoints for this AI flight
            waypoints = self._build_ai_air_waypoints(player_af, task)

            # Determine timing: SEAD goes first, then sweep, then strike
            late_activation = False
            task_lower = task.lower()
            if task_lower in ("sead", "sweep"):
                late_activation = False  # Go immediately or early
            elif task_lower in ("strike", "cas"):
                late_activation = True   # Wait for SEAD

            blue_afs = [af for af in self.map_data.get("airfields", [])
                        if af.get("default_coalition") == "blue"]
            start_af = random.choice(blue_afs) if blue_afs else player_af

            # Assign callsign
            flight_cs = self._callsigns.assign(task)
            flight_freq = self._frequencies.assign_flight(flight_cs["callsign"])
            self._assigned_callsigns[f"friendly_{group_id}"] = {**flight_cs, "freq": flight_freq, "task": task}

            self.blue_air_groups.append({
                "group_id": group_id,
                "name": f"{flight_cs['callsign']} Flight",
                "coalition": "blue",
                "category": "plane",
                "task": task,
                "units": units,
                "waypoints": waypoints,
                "frequency": flight_freq,
                "start_type": "Takeoff from Parking",
                "airfield_id": start_af.get("id", 0),
                "late_activation": late_activation,
            })

            # Store SEAD callsign for message triggers
            if task.lower() == "sead":
                self._assigned_callsigns["sead"] = {**flight_cs, "freq": flight_freq}

    def _build_ai_air_waypoints(self, base_af: dict, task: str) -> list:
        """Build waypoints for AI air groups based on their task."""
        target = self._get_target_position()
        waypoints = []

        # Takeoff
        waypoints.append({
            "id": 0,
            "name": "TAKEOFF",
            "type": "TakeOff",
            "action": "From Parking Area",
            "x": base_af["x"],
            "y": base_af["y"],
            "alt": base_af.get("alt", 0),
            "speed": 0,
            "airfield_id": base_af.get("id", 0),
        })

        task_lower = task.lower()
        if task_lower in ("cap", "escort"):
            # Orbit near the player's target area
            orbit_x = target["x"] + random.randint(-10000, 10000)
            orbit_y = target["y"] + random.randint(-10000, 10000)
            waypoints.append({
                "id": 1,
                "name": "STATION",
                "type": "Turning Point",
                "action": "Turning Point",
                "x": orbit_x,
                "y": orbit_y,
                "alt": 7000,
                "speed": 250,
                "tasks": [{"id": "EngageTargets", "params": {"targetTypes": ["Air"]}}],
                "orbit": {"pattern": "Race-Track", "speed": 230, "altitude": 7000},
            })
        elif task_lower in ("sead",):
            # Head to SAM area
            waypoints.append({
                "id": 1,
                "name": "SEAD TARGET",
                "type": "Turning Point",
                "action": "Turning Point",
                "x": target["x"],
                "y": target["y"],
                "alt": 6000,
                "speed": 250,
                "tasks": [{"id": "EngageTargets", "params": {"targetTypes": ["Air Defence"]}}],
            })
        elif task_lower in ("sweep",):
            # Sweep ahead of target
            sweep_x = target["x"] + random.randint(-20000, 20000)
            sweep_y = target["y"] + random.randint(-20000, 20000)
            waypoints.append({
                "id": 1,
                "name": "SWEEP",
                "type": "Turning Point",
                "action": "Turning Point",
                "x": sweep_x,
                "y": sweep_y,
                "alt": 8000,
                "speed": 280,
                "tasks": [{"id": "FighterSweep", "params": {}}],
            })
        else:
            # Generic: head to target
            waypoints.append({
                "id": 1,
                "name": "TARGET",
                "type": "Turning Point",
                "action": "Turning Point",
                "x": target["x"],
                "y": target["y"],
                "alt": 6000,
                "speed": 250,
            })

        # RTB
        waypoints.append({
            "id": 2,
            "name": "RTB",
            "type": "Land",
            "action": "Landing",
            "x": base_af["x"],
            "y": base_af["y"],
            "alt": base_af.get("alt", 0),
            "speed": 0,
            "airfield_id": base_af.get("id", 0),
        })

        return waypoints

    def _build_enemy_sams(self):
        """Build enemy SAM site groups with randomized placement and optional SHORAD."""
        sam_zones = [z for z in self.map_data.get("sam_zones", []) if z["side"] == "red"]
        # Shuffle zones for random placement each generation
        shuffled_zones = list(sam_zones)
        random.shuffle(shuffled_zones)

        for i, sam_plan in enumerate(self.plan.get("enemy_sam_sites", [])):
            if self._total_units >= self._max_units:
                break

            sam_type = sam_plan.get("type", "SA-6")
            sam_data = SAM_SYSTEMS.get(sam_type)
            if not sam_data:
                continue

            # Random position within a zone
            if i < len(shuffled_zones):
                zone = shuffled_zones[i]
                radius = zone.get("radius", 10000)
                # Random position within the zone radius
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(0, radius * 0.7)
                base_x = zone["x"] + dist * math.cos(angle)
                base_y = zone["y"] + dist * math.sin(angle)
            else:
                target = self._get_target_position()
                base_x = target["x"] + random.randint(-25000, 25000)
                base_y = target["y"] + random.randint(-25000, 25000)

            group_id = self._next_group_id()
            units = []

            # Build SAM components in a circular layout
            for j, component in enumerate(sam_data.get("units", [])):
                for k in range(component.get("count", 1)):
                    uid = self._next_unit_id()
                    comp_angle = (2 * math.pi * (j * 3 + k)) / max(len(sam_data["units"]) * 2, 1)
                    comp_radius = 100 + j * 50
                    units.append({
                        "unit_id": uid,
                        "type": component["type"],
                        "name": f"{sam_type} {component['name']} {k+1}",
                        "skill": self.plan.get("_enemy_ground_skill", "High"),
                        "x": base_x + comp_radius * math.cos(comp_angle),
                        "y": base_y + comp_radius * math.sin(comp_angle),
                        "heading": random.uniform(0, 2 * math.pi),
                    })
                    self._total_units += 1

            self.red_sam_groups.append({
                "group_id": group_id,
                "name": f"Red {sam_data['display_name']} Site {i+1}",
                "coalition": "red",
                "category": "vehicle",
                "units": units,
                "late_activation": False,
                "hidden": False,
            })

            # SHORAD escort if difficulty demands it
            if self.plan.get("_shorad_escort") and self._total_units < self._max_units:
                shorad_types = self.plan.get("_shorad_types", ["SA-15", "ZSU-23-4"])
                shorad_type = random.choice(shorad_types)
                shorad_data = SAM_SYSTEMS.get(shorad_type)
                if shorad_data:
                    sg_id = self._next_group_id()
                    shorad_units = []
                    # Place SHORAD 500-1500m from main SAM
                    s_angle = random.uniform(0, 2 * math.pi)
                    s_dist = random.randint(500, 1500)
                    s_x = base_x + s_dist * math.cos(s_angle)
                    s_y = base_y + s_dist * math.sin(s_angle)

                    for comp in shorad_data.get("units", []):
                        for k in range(comp.get("count", 1)):
                            uid = self._next_unit_id()
                            shorad_units.append({
                                "unit_id": uid,
                                "type": comp["type"],
                                "name": f"SHORAD {shorad_type} {comp['name']}",
                                "skill": self.plan.get("_enemy_ground_skill", "High"),
                                "x": s_x + k * 40,
                                "y": s_y + k * 30,
                                "heading": random.uniform(0, 2 * math.pi),
                            })
                            self._total_units += 1

                    self.red_sam_groups.append({
                        "group_id": sg_id,
                        "name": f"Red SHORAD {shorad_type} (escort SAM {i+1})",
                        "coalition": "red",
                        "category": "vehicle",
                        "units": shorad_units,
                        "late_activation": False,
                    })

    def _build_friendly_sams(self):
        """Build blue SAM sites for defense."""
        blue_sam_zones = [z for z in self.map_data.get("sam_zones", []) if z["side"] == "blue"]

        # Place 1-2 blue SAM sites
        for i, zone in enumerate(blue_sam_zones[:2]):
            if self._total_units >= self._max_units:
                break

            sam_type = "Hawk" if i == 0 else "Patriot"
            sam_data = SAM_SYSTEMS.get(sam_type)
            if not sam_data:
                continue

            group_id = self._next_group_id()
            units = []

            for j, comp in enumerate(sam_data.get("units", [])):
                for k in range(comp.get("count", 1)):
                    uid = self._next_unit_id()
                    angle = (2 * math.pi * (j * 3 + k)) / max(len(sam_data["units"]) * 2, 1)
                    radius = 80 + j * 40
                    units.append({
                        "unit_id": uid,
                        "type": comp["type"],
                        "name": f"Blue {sam_type} {comp['name']} {k+1}",
                        "skill": "High",
                        "x": zone["x"] + radius * math.cos(angle),
                        "y": zone["y"] + radius * math.sin(angle),
                        "heading": random.uniform(0, 2 * math.pi),
                    })
                    self._total_units += 1

            self.blue_sam_groups.append({
                "group_id": group_id,
                "name": f"Blue {sam_type} Site",
                "coalition": "blue",
                "category": "vehicle",
                "units": units,
                "late_activation": False,
            })

    def _build_enemy_air(self):
        """Build enemy air groups."""
        red_afs = [af for af in self.map_data.get("airfields", [])
                   if af.get("default_coalition") == "red"]

        for flight in self.plan.get("enemy_air", []):
            if self._total_units >= self._max_units:
                break

            ac_key = flight.get("aircraft", "MiG-29A")
            ac_data = AI_AIRCRAFT.get(ac_key, AI_AIRCRAFT.get("MiG-29A"))
            count = min(flight.get("count", 2), 4)
            task = flight.get("task", "CAP")

            group_id = self._next_group_id()
            units = []

            # Pick a red airfield or use CAP orbit
            orbits = [o for o in self.map_data.get("cap_orbits", []) if o["side"] == "red"]
            start_af = random.choice(red_afs) if red_afs else None

            start_x = start_af["x"] if start_af else 0
            start_y = start_af["y"] if start_af else 0

            for i in range(count):
                uid = self._next_unit_id()
                enemy_skill = flight.get("skill",
                    self.plan.get("_enemy_air_skill", ac_data.get("skill", "High")))
                enemy_pylons = resolve_ai_loadout(ac_key, task)
                units.append({
                    "unit_id": uid,
                    "type": ac_data.get("type", "MiG-29A"),
                    "name": f"Red {ac_data.get('display_name', 'Fighter')} {i+1}",
                    "skill": enemy_skill,
                    "x": start_x + random.randint(-100, 100),
                    "y": start_y + random.randint(-100, 100),
                    "heading": 0,
                    "pylons": enemy_pylons,
                    "fuel": 3249,
                    "chaff": 60,
                    "flare": 60,
                })
                self._total_units += 1

            # CAP orbit waypoints
            waypoints = []
            if start_af:
                waypoints.append({
                    "id": 0,
                    "name": "TAKEOFF",
                    "type": "TakeOff",
                    "action": "From Parking Area",
                    "x": start_af["x"],
                    "y": start_af["y"],
                    "alt": start_af.get("alt", 0),
                    "speed": 0,
                    "airfield_id": start_af.get("id", 0),
                })

            if orbits:
                orbit = random.choice(orbits)
                waypoints.append({
                    "id": len(waypoints),
                    "name": "CAP STATION",
                    "type": "Turning Point",
                    "action": "Turning Point",
                    "x": orbit["x1"],
                    "y": orbit["y1"],
                    "alt": orbit.get("alt", 7000),
                    "speed": 250,
                    "tasks": [{"id": "EngageTargets", "params": {"targetTypes": ["Air"]}}],
                    "orbit": {
                        "pattern": "Race-Track",
                        "point2": {"x": orbit["x2"], "y": orbit["y2"]},
                        "speed": 230,
                        "altitude": orbit.get("alt", 7000),
                    },
                })

            if start_af:
                waypoints.append({
                    "id": len(waypoints),
                    "name": "RTB",
                    "type": "Land",
                    "action": "Landing",
                    "x": start_af["x"],
                    "y": start_af["y"],
                    "alt": start_af.get("alt", 0),
                    "speed": 0,
                    "airfield_id": start_af.get("id", 0),
                })

            # Some enemy air should be late activated for performance
            late = len(self.red_air_groups) > 0  # First group immediate, rest late

            red_cs = self._callsigns.assign(task, "red")
            red_freq = self._frequencies.assign_flight(red_cs["callsign"], "red")

            self.red_air_groups.append({
                "group_id": group_id,
                "name": f"{red_cs['callsign']} Flight",
                "coalition": "red",
                "category": "plane",
                "task": task,
                "units": units,
                "waypoints": waypoints,
                "frequency": red_freq,
                "start_type": "Takeoff from Parking" if start_af else "In Air",
                "airfield_id": start_af.get("id", 0) if start_af else 0,
                "late_activation": late,
            })

    def _build_ground_war(self):
        """Build dynamic ground forces with advancing waypoints."""
        front_lines = self.map_data.get("front_lines", [])
        if not front_lines:
            return

        gw = self.plan.get("ground_war", {})
        intensity = gw.get("intensity", "medium")
        group_sizes = {"light": 3, "medium": 4, "heavy": 5}
        num_groups = {"light": 2, "medium": 3, "heavy": 4}

        gs = group_sizes.get(intensity, 4)
        ng = num_groups.get(intensity, 3)

        for fl in front_lines[:2]:  # Max 2 front lines for performance
            # Blue ground advancing
            if gw.get("blue_advancing", True):
                for i in range(min(ng, 3)):
                    if self._total_units >= self._max_units:
                        break
                    self._build_ground_group(
                        coalition="blue",
                        start=fl["blue_start"],
                        end=fl["red_start"],
                        group_size=gs,
                        index=i,
                        width=fl.get("width", 15000),
                        late=(i > 0),  # First group active, rest late
                    )

            # Red ground advancing
            if gw.get("red_advancing", True):
                for i in range(min(ng, 3)):
                    if self._total_units >= self._max_units:
                        break
                    self._build_ground_group(
                        coalition="red",
                        start=fl["red_start"],
                        end=fl["blue_start"],
                        group_size=gs,
                        index=i,
                        width=fl.get("width", 15000),
                        late=(i > 0),
                    )

    def _build_ground_group(self, coalition: str, start: dict, end: dict,
                            group_size: int, index: int, width: int, late: bool):
        """Build a single ground group with advance waypoints."""
        group_id = self._next_group_id()

        # Offset perpendicular to axis of advance
        offset = (index - 1) * (width / 3)
        dx = end["x"] - start["x"]
        dy = end["y"] - start["y"]
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            dist = 1

        # Perpendicular offset
        perp_x = -dy / dist * offset
        perp_y = dx / dist * offset

        sx = start["x"] + perp_x + random.randint(-1000, 1000)
        sy = start["y"] + perp_y + random.randint(-1000, 1000)

        # Pick units — use difficulty-scaled preferences if available
        if coalition == "blue":
            pref = self.plan.get("_blue_armor_preference", [])
            all_units = GROUND_UNITS["blue_armor"]
            if pref:
                unit_pool = [u for u in all_units if u["type"] in pref]
                if not unit_pool:
                    unit_pool = all_units
            else:
                unit_pool = all_units
        else:
            pref = self.plan.get("_red_armor_preference", [])
            all_units = GROUND_UNITS["red_armor"]
            if pref:
                unit_pool = [u for u in all_units if u["type"] in pref]
                if not unit_pool:
                    unit_pool = all_units
            else:
                unit_pool = all_units

        ground_skill = self.plan.get(
            f"_{'enemy' if coalition == 'red' else 'friendly_ai'}_ground_skill",
            self.plan.get("_enemy_ground_skill", "Average")
        )

        units = []
        for i in range(min(group_size, 5)):
            uid = self._next_unit_id()
            unit_template = unit_pool[i % len(unit_pool)]
            units.append({
                "unit_id": uid,
                "type": unit_template["type"],
                "name": f"{unit_template['name']} {i+1}",
                "skill": ground_skill,
                "x": sx + i * 30,
                "y": sy + i * 20,
                "heading": math.atan2(dy, dx),
            })
            self._total_units += 1

        # Waypoints: advance toward enemy position
        waypoints = [
            {
                "id": 0,
                "name": "START",
                "type": "Turning Point",
                "action": "On Road",
                "x": sx,
                "y": sy,
                "speed": 10,  # ~36 km/h
                "tasks": [{"id": "EngageTargets", "params": {"targetTypes": ["Armor", "Vehicles", "Infantry"]}}],
            },
            {
                "id": 1,
                "name": "ADVANCE",
                "type": "Turning Point",
                "action": "On Road",
                "x": (sx + end["x"] + perp_x) / 2,
                "y": (sy + end["y"] + perp_y) / 2,
                "speed": 10,
            },
            {
                "id": 2,
                "name": "OBJECTIVE",
                "type": "Turning Point",
                "action": "On Road",
                "x": end["x"] + perp_x + random.randint(-2000, 2000),
                "y": end["y"] + perp_y + random.randint(-2000, 2000),
                "speed": 8,
            },
        ]

        group = {
            "group_id": group_id,
            "name": f"{'Blue' if coalition == 'blue' else 'Red'} Armor {group_id}",
            "coalition": coalition,
            "category": "vehicle",
            "units": units,
            "waypoints": waypoints,
            "late_activation": late,
        }

        if coalition == "blue":
            self.blue_ground_groups.append(group)
        else:
            self.red_ground_groups.append(group)

    def _build_convoy(self):
        """Build convoy groups for convoy_attack or convoy_defense missions."""
        template = MISSION_TEMPLATES.get(self.mission_type, {})
        convoy_side = template.get("convoy_side", "red")

        routes = self.map_data.get("convoy_routes", {}).get(convoy_side, [])
        if not routes:
            # Fallback: generate a simple straight-line route between two cities
            cities = self.map_data.get("cities", [])
            side_cities = [c for c in cities if c.get("side") == convoy_side]
            if len(side_cities) >= 2:
                c1, c2 = side_cities[0], side_cities[1]
                routes = [{"name": "Fallback Route", "waypoints": [
                    {"x": c1["x"], "y": c1["y"]},
                    {"x": (c1["x"] + c2["x"]) / 2, "y": (c1["y"] + c2["y"]) / 2},
                    {"x": c2["x"], "y": c2["y"]},
                ]}]

        if not routes:
            return

        route = random.choice(routes)
        route_wps = route["waypoints"]

        # Build supply vehicles group
        supply_key = f"{convoy_side}_supply"
        escort_key = f"{convoy_side}_escort"
        supply_units_pool = CONVOY_UNITS.get(supply_key, [])
        escort_units_pool = CONVOY_UNITS.get(escort_key, [])

        if not supply_units_pool:
            return

        # Supply convoy group
        group_id = self._next_group_id()
        units = []
        start_wp = route_wps[0]

        for i, template_unit in enumerate(supply_units_pool[:5]):
            if self._total_units >= self._max_units:
                break
            uid = self._next_unit_id()
            units.append({
                "unit_id": uid,
                "type": template_unit["type"],
                "name": f"Convoy {template_unit['name']} {i+1}",
                "skill": "Average",
                "x": start_wp["x"] + i * 50,
                "y": start_wp["y"] + i * 30,
                "heading": 0,
            })
            self._total_units += 1

        waypoints = []
        for wi, wp in enumerate(route_wps):
            waypoints.append({
                "id": wi,
                "name": f"ROUTE {wi+1}" if wi > 0 else "START",
                "type": "Turning Point",
                "action": "On Road",
                "x": wp["x"],
                "y": wp["y"],
                "speed": 8,
            })

        convoy_group = {
            "group_id": group_id,
            "name": f"{'Red' if convoy_side == 'red' else 'Blue'} Supply Convoy",
            "coalition": convoy_side,
            "category": "vehicle",
            "units": units,
            "waypoints": waypoints,
            "late_activation": False,
        }

        if convoy_side == "red":
            self.red_ground_groups.append(convoy_group)
        else:
            self.blue_ground_groups.append(convoy_group)

        # Escort group
        if escort_units_pool and self._total_units < self._max_units:
            eg_id = self._next_group_id()
            escort_units = []
            for i, template_unit in enumerate(escort_units_pool[:3]):
                if self._total_units >= self._max_units:
                    break
                uid = self._next_unit_id()
                escort_units.append({
                    "unit_id": uid,
                    "type": template_unit["type"],
                    "name": f"Escort {template_unit['name']}",
                    "skill": self.plan.get("_enemy_ground_skill", "High"),
                    "x": start_wp["x"] - 100 + i * 60,
                    "y": start_wp["y"] - 80 + i * 40,
                    "heading": 0,
                })
                self._total_units += 1

            escort_group = {
                "group_id": eg_id,
                "name": f"{'Red' if convoy_side == 'red' else 'Blue'} Convoy Escort",
                "coalition": convoy_side,
                "category": "vehicle",
                "units": escort_units,
                "waypoints": waypoints,  # Same route
                "late_activation": False,
            }

            if convoy_side == "red":
                self.red_ground_groups.append(escort_group)
            else:
                self.blue_ground_groups.append(escort_group)

        # Store convoy position for player waypoints
        self._convoy_route = route_wps

    def _build_support(self):
        """Build tanker and AWACS with proper callsigns."""
        support = self.map_data.get("support_orbits", {})

        # Tanker
        tanker_data = support.get("tanker")
        if tanker_data:
            tanker_cs = self._callsigns.assign_support("tanker", tanker_data.get("name", "Texaco"))
            self._assigned_callsigns["tanker"] = {**tanker_cs, "freq": tanker_data.get("freq", 251.0),
                                                   "tacan": tanker_data.get("tacan", "51Y")}
            group_id = self._next_group_id()
            uid = self._next_unit_id()
            self.blue_air_groups.append({
                "group_id": group_id,
                "name": tanker_cs["callsign"],
                "coalition": "blue",
                "category": "plane",
                "task": "Refueling",
                "units": [{
                    "unit_id": uid, "type": "KC135MPRS",
                    "name": tanker_cs["callsign"], "skill": "High",
                    "x": tanker_data["x1"], "y": tanker_data["y1"],
                    "alt": tanker_data.get("alt", 6000), "heading": 0,
                }],
                "waypoints": [{
                    "id": 0, "name": "ORBIT START", "type": "Turning Point",
                    "action": "Turning Point",
                    "x": tanker_data["x1"], "y": tanker_data["y1"],
                    "alt": tanker_data.get("alt", 6000), "speed": 200,
                    "tasks": [{"id": "Tanker", "params": {}}],
                    "orbit": {"pattern": "Race-Track",
                              "point2": {"x": tanker_data["x2"], "y": tanker_data["y2"]},
                              "speed": 200, "altitude": tanker_data.get("alt", 6000)},
                }],
                "frequency": tanker_data.get("freq", 251.0),
                "start_type": "In Air", "late_activation": False,
                "tacan": tanker_data.get("tacan", "51Y"),
            })
            self._total_units += 1

        # AWACS
        awacs_data = support.get("awacs")
        if awacs_data:
            awacs_cs = self._callsigns.assign_support("awacs", awacs_data.get("name", "Overlord"))
            self._assigned_callsigns["awacs"] = {**awacs_cs, "freq": awacs_data.get("freq", 252.0)}
            group_id = self._next_group_id()
            uid = self._next_unit_id()
            self.blue_air_groups.append({
                "group_id": group_id,
                "name": awacs_cs["callsign"],
                "coalition": "blue",
                "category": "plane",
                "task": "AWACS",
                "units": [{
                    "unit_id": uid, "type": "E-3A",
                    "name": awacs_cs["callsign"], "skill": "High",
                    "x": awacs_data["x1"], "y": awacs_data["y1"],
                    "alt": awacs_data.get("alt", 9000), "heading": 0,
                }],
                "waypoints": [{
                    "id": 0, "name": "ORBIT START", "type": "Turning Point",
                    "action": "Turning Point",
                    "x": awacs_data["x1"], "y": awacs_data["y1"],
                    "alt": awacs_data.get("alt", 9000), "speed": 220,
                    "tasks": [{"id": "AWACS", "params": {}}],
                    "orbit": {"pattern": "Race-Track",
                              "point2": {"x": awacs_data["x2"], "y": awacs_data["y2"]},
                              "speed": 220, "altitude": awacs_data.get("alt", 9000)},
                }],
                "frequency": awacs_data.get("freq", 252.0),
                "start_type": "In Air", "late_activation": False,
            })
            self._total_units += 1

    def _build_reinforcements(self):
        """Build timed enemy reinforcement waves as late-activated groups."""
        waves = generate_reinforcement_waves(self.plan)
        red_afs = [af for af in self.map_data.get("airfields", [])
                   if af.get("default_coalition") == "red"]
        if not red_afs:
            return

        for wave in waves:
            if self._total_units >= self._max_units:
                break

            ac_key = wave["aircraft"]
            ac_data = AI_AIRCRAFT.get(ac_key, AI_AIRCRAFT.get("MiG-29A"))
            count = wave.get("count", 2)
            task = wave.get("task", "intercept")

            start_af = random.choice(red_afs)
            group_id = self._next_group_id()
            units = []

            enemy_skill = self.plan.get("_enemy_air_skill", "High")
            enemy_pylons = resolve_ai_loadout(ac_key, task)

            for i in range(count):
                uid = self._next_unit_id()
                units.append({
                    "unit_id": uid,
                    "type": ac_data.get("type", "MiG-29A"),
                    "name": f"Reinf {ac_data.get('display_name', 'Fighter')} {i+1}",
                    "skill": enemy_skill,
                    "x": start_af["x"] + random.randint(-100, 100),
                    "y": start_af["y"] + random.randint(-100, 100),
                    "heading": 0,
                    "pylons": enemy_pylons,
                    "fuel": 3249, "chaff": 60, "flare": 60,
                })
                self._total_units += 1

            # Orbit near target after takeoff
            target = self._get_target_position()
            waypoints = [
                {"id": 0, "name": "TAKEOFF", "type": "TakeOff",
                 "action": "From Parking Area",
                 "x": start_af["x"], "y": start_af["y"],
                 "alt": start_af.get("alt", 0), "speed": 0,
                 "airfield_id": start_af.get("id", 0)},
                {"id": 1, "name": "ENGAGE", "type": "Turning Point",
                 "action": "Turning Point",
                 "x": target["x"] + random.randint(-15000, 15000),
                 "y": target["y"] + random.randint(-15000, 15000),
                 "alt": 7000, "speed": 250,
                 "tasks": [{"id": "EngageTargets", "params": {"targetTypes": ["Air"]}}]},
                {"id": 2, "name": "RTB", "type": "Land", "action": "Landing",
                 "x": start_af["x"], "y": start_af["y"],
                 "alt": start_af.get("alt", 0), "speed": 0,
                 "airfield_id": start_af.get("id", 0)},
            ]

            self.red_air_groups.append({
                "group_id": group_id,
                "name": wave["name"],
                "coalition": "red",
                "category": "plane",
                "task": task,
                "units": units,
                "waypoints": waypoints,
                "frequency": 124.0 + group_id * 0.5,
                "start_type": "Takeoff from Parking",
                "airfield_id": start_af.get("id", 0),
                "late_activation": True,  # Activated by trigger
            })

            # Add activation trigger
            self.triggers.append({
                "type": "time",
                "time": wave["time"],
                "action": "activate_group",
                "group_name": wave["name"],
                "group_id": group_id,
            })

    def _build_triggers(self):
        """Convert late_activation flags to start_time delays for staggered spawning.
        DCS start_time delays a group's activation from mission start (in seconds)."""
        delay = 300  # First delayed group starts at T+5 min

        all_groups = (self.blue_air_groups + self.red_air_groups +
                      self.blue_ground_groups + self.red_ground_groups)

        for group in all_groups:
            if group.get("late_activation"):
                group["_start_delay"] = delay
                delay += 180  # Stagger by 3 minutes
                del group["late_activation"]  # Clean up
            else:
                group["_start_delay"] = 0

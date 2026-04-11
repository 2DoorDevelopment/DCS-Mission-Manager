"""
Group Builders — Extracted from MissionBuilder
Handles construction of air groups, SAM groups, ground groups, convoys, and support aircraft.
Each builder function takes the shared state and produces group dicts.
"""

import math
import random
import copy
from src.units import (
    PLAYER_AIRCRAFT, AI_AIRCRAFT, SAM_SYSTEMS,
    GROUND_UNITS, CONVOY_UNITS, MISSION_TEMPLATES,
    resolve_ai_loadout,
)
from src.flight_profile import compute_flight_profile, estimate_fuel
from src.mission_events import generate_reinforcement_waves


def build_player_group(state: "BuilderState", airfield: dict):
    """Build the player's aircraft group with realistic flight profile waypoints."""
    from src.generators.waypoint_builders import build_player_waypoints_profiled

    ac_key = state.plan["player_aircraft"]
    ac_data = PLAYER_AIRCRAFT.get(ac_key, {})

    # Determine loadout
    loadout_key = state.mission_type
    loadout = ac_data.get("default_loadouts", {}).get(loadout_key, {})

    # Assign player callsign
    player_cs = state.callsigns.assign_player(state.mission_type)
    player_freq = state.frequencies.assign_flight(player_cs["callsign"])
    state.assigned_callsigns["player"] = {**player_cs, "freq": player_freq}

    # Compute flight profile
    target_pos = state.get_target_position()
    dist = math.sqrt((target_pos["x"] - airfield["x"])**2 +
                     (target_pos["y"] - airfield["y"])**2)
    weather = state.get_weather()
    profile = compute_flight_profile(ac_key, state.mission_type, weather, dist)
    state.plan["_flight_profile"] = profile

    # Fuel estimate
    fuel_est = estimate_fuel(ac_key, dist)
    state.plan["_fuel_estimate"] = fuel_est

    # Build waypoints
    waypoints = build_player_waypoints_profiled(state, airfield, target_pos, profile)

    group_id = state.next_group_id()
    unit_id = state.next_unit_id()

    player_count = max(1, int(state.plan.get("player_count", 1)))

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
    state.total_units += 1

    # Additional co-op player slots
    for slot in range(2, player_count + 1):
        co_id = state.next_unit_id()
        co = copy.deepcopy(player_units[0])
        co["unit_id"] = co_id
        co["name"] = f"{player_cs['callsign']} 1-{slot}"
        co["skill"] = "Client"
        co["y"] = airfield["y"] + (slot - 1) * 30
        player_units.append(co)
        state.total_units += 1

    # Add AI wingman only when solo player with no extra slots
    if player_count == 1 and state.plan.get("wingman", True):
        wm_id = state.next_unit_id()
        wm = copy.deepcopy(player_units[0])
        wm["unit_id"] = wm_id
        wm["name"] = f"{player_cs['callsign']} 1-2"
        wm["skill"] = "High"
        wm["y"] = airfield["y"] + 30
        player_units.append(wm)
        state.total_units += 1

    state.player_group = {
        "group_id": group_id,
        "name": f"{player_cs['callsign']} Flight",
        "coalition": "blue",
        "category": "plane",
        "task": state.mission_type,
        "units": player_units,
        "waypoints": waypoints,
        "frequency": player_freq,
        "communication": True,
        "start_type": "Takeoff from Parking",
        "airfield_id": airfield.get("id", 0),
        "late_activation": False,
        "uncontrolled": False,
    }


def build_friendly_flights(state: "BuilderState", player_af: dict):
    """Build friendly AI flight groups."""
    from src.generators.waypoint_builders import build_ai_air_waypoints

    for flight in state.plan.get("friendly_flights", []):
        if state.total_units >= state.max_units:
            break

        ac_key = flight.get("aircraft", "F-15C")
        ac_data = AI_AIRCRAFT.get(ac_key, AI_AIRCRAFT.get("F-15C"))
        task = flight.get("task", "escort")
        count = min(flight.get("count", 2), 4)

        group_id = state.next_group_id()
        units = []

        ai_pylons = resolve_ai_loadout(ac_key, task)
        friendly_skill = state.plan.get("_friendly_ai_skill", ac_data.get("skill", "High"))

        for i in range(count):
            uid = state.next_unit_id()
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
            state.total_units += 1

        waypoints = build_ai_air_waypoints(state, player_af, task)

        late_activation = False
        task_lower = task.lower()
        if task_lower in ("strike", "cas"):
            late_activation = True

        blue_afs = [af for af in state.map_data.get("airfields", [])
                    if af.get("default_coalition") == "blue"]
        start_af = random.choice(blue_afs) if blue_afs else player_af

        flight_cs = state.callsigns.assign(task)
        flight_freq = state.frequencies.assign_flight(flight_cs["callsign"])
        state.assigned_callsigns[f"friendly_{group_id}"] = {
            **flight_cs, "freq": flight_freq, "task": task
        }

        state.blue_air_groups.append({
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

        if task.lower() == "sead":
            state.assigned_callsigns["sead"] = {**flight_cs, "freq": flight_freq}


def build_enemy_sams(state: "BuilderState"):
    """Build enemy SAM site groups with randomized placement and optional SHORAD."""
    sam_zones = [z for z in state.map_data.get("sam_zones", []) if z["side"] == "red"]
    shuffled_zones = list(sam_zones)
    random.shuffle(shuffled_zones)

    for i, sam_plan in enumerate(state.plan.get("enemy_sam_sites", [])):
        if state.total_units >= state.max_units:
            break

        sam_type = sam_plan.get("type", "SA-6")
        sam_data = SAM_SYSTEMS.get(sam_type)
        if not sam_data:
            continue

        if i < len(shuffled_zones):
            zone = shuffled_zones[i]
            radius = zone.get("radius", 10000)
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, radius * 0.7)
            base_x = zone["x"] + dist * math.cos(angle)
            base_y = zone["y"] + dist * math.sin(angle)
        else:
            target = state.get_target_position()
            base_x = target["x"] + random.randint(-25000, 25000)
            base_y = target["y"] + random.randint(-25000, 25000)

        # Avoid placing SAMs in water zones
        base_x, base_y = state.avoid_water(base_x, base_y)

        group_id = state.next_group_id()
        units = []

        for j, component in enumerate(sam_data.get("units", [])):
            for k in range(component.get("count", 1)):
                uid = state.next_unit_id()
                comp_angle = (2 * math.pi * (j * 3 + k)) / max(len(sam_data["units"]) * 2, 1)
                comp_radius = 100 + j * 50
                units.append({
                    "unit_id": uid,
                    "type": component["type"],
                    "name": f"{sam_type} {component['name']} {k+1}",
                    "skill": state.plan.get("_enemy_ground_skill", "High"),
                    "x": base_x + comp_radius * math.cos(comp_angle),
                    "y": base_y + comp_radius * math.sin(comp_angle),
                    "heading": random.uniform(0, 2 * math.pi),
                })
                state.total_units += 1

        state.red_sam_groups.append({
            "group_id": group_id,
            "name": f"Red {sam_data['display_name']} Site {i+1}",
            "coalition": "red",
            "category": "vehicle",
            "units": units,
            "late_activation": False,
            "hidden": False,
        })

        # SHORAD escort
        if state.plan.get("_shorad_escort") and state.total_units < state.max_units:
            shorad_types = state.plan.get("_shorad_types", ["SA-15", "ZSU-23-4"])
            shorad_type = random.choice(shorad_types)
            shorad_data = SAM_SYSTEMS.get(shorad_type)
            if shorad_data:
                sg_id = state.next_group_id()
                shorad_units = []
                s_angle = random.uniform(0, 2 * math.pi)
                s_dist = random.randint(500, 1500)
                s_x = base_x + s_dist * math.cos(s_angle)
                s_y = base_y + s_dist * math.sin(s_angle)

                for comp in shorad_data.get("units", []):
                    for k in range(comp.get("count", 1)):
                        uid = state.next_unit_id()
                        shorad_units.append({
                            "unit_id": uid,
                            "type": comp["type"],
                            "name": f"SHORAD {shorad_type} {comp['name']}",
                            "skill": state.plan.get("_enemy_ground_skill", "High"),
                            "x": s_x + k * 40,
                            "y": s_y + k * 30,
                            "heading": random.uniform(0, 2 * math.pi),
                        })
                        state.total_units += 1

                state.red_sam_groups.append({
                    "group_id": sg_id,
                    "name": f"Red SHORAD {shorad_type} (escort SAM {i+1})",
                    "coalition": "red",
                    "category": "vehicle",
                    "units": shorad_units,
                    "late_activation": False,
                })


def build_friendly_sams(state: "BuilderState"):
    """Build blue SAM sites for defense."""
    blue_sam_zones = [z for z in state.map_data.get("sam_zones", []) if z["side"] == "blue"]

    for i, zone in enumerate(blue_sam_zones[:2]):
        if state.total_units >= state.max_units:
            break

        sam_type = "Hawk" if i == 0 else "Patriot"
        sam_data = SAM_SYSTEMS.get(sam_type)
        if not sam_data:
            continue

        group_id = state.next_group_id()
        units = []

        for j, comp in enumerate(sam_data.get("units", [])):
            for k in range(comp.get("count", 1)):
                uid = state.next_unit_id()
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
                state.total_units += 1

        state.blue_sam_groups.append({
            "group_id": group_id,
            "name": f"Blue {sam_type} Site",
            "coalition": "blue",
            "category": "vehicle",
            "units": units,
            "late_activation": False,
        })


def build_enemy_air(state: "BuilderState"):
    """Build enemy air groups."""
    red_afs = [af for af in state.map_data.get("airfields", [])
               if af.get("default_coalition") == "red"]

    for flight in state.plan.get("enemy_air", []):
        if state.total_units >= state.max_units:
            break

        ac_key = flight.get("aircraft", "MiG-29A")
        ac_data = AI_AIRCRAFT.get(ac_key, AI_AIRCRAFT.get("MiG-29A"))
        count = min(flight.get("count", 2), 4)
        task = flight.get("task", "CAP")

        group_id = state.next_group_id()
        units = []

        orbits = [o for o in state.map_data.get("cap_orbits", []) if o["side"] == "red"]
        start_af = random.choice(red_afs) if red_afs else None
        start_x = start_af["x"] if start_af else 0
        start_y = start_af["y"] if start_af else 0

        for i in range(count):
            uid = state.next_unit_id()
            enemy_skill = flight.get("skill",
                state.plan.get("_enemy_air_skill", ac_data.get("skill", "High")))
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
            state.total_units += 1

        waypoints = []
        if start_af:
            waypoints.append({
                "id": 0, "name": "TAKEOFF", "type": "TakeOff",
                "action": "From Parking Area",
                "x": start_af["x"], "y": start_af["y"],
                "alt": start_af.get("alt", 0), "speed": 0,
                "airfield_id": start_af.get("id", 0),
            })

        if orbits:
            orbit = random.choice(orbits)
            waypoints.append({
                "id": len(waypoints), "name": "CAP STATION",
                "type": "Turning Point", "action": "Turning Point",
                "x": orbit["x1"], "y": orbit["y1"],
                "alt": orbit.get("alt", 7000), "speed": 250,
                "tasks": [{"id": "EngageTargets", "params": {"targetTypes": ["Air"]}}],
                "orbit": {
                    "pattern": "Race-Track",
                    "point2": {"x": orbit["x2"], "y": orbit["y2"]},
                    "speed": 230, "altitude": orbit.get("alt", 7000),
                },
            })

        if start_af:
            waypoints.append({
                "id": len(waypoints), "name": "RTB", "type": "Land",
                "action": "Landing",
                "x": start_af["x"], "y": start_af["y"],
                "alt": start_af.get("alt", 0), "speed": 0,
                "airfield_id": start_af.get("id", 0),
            })

        late = len(state.red_air_groups) > 0
        red_cs = state.callsigns.assign(task, "red")
        red_freq = state.frequencies.assign_flight(red_cs["callsign"], "red")

        state.red_air_groups.append({
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


def build_ground_war(state: "BuilderState"):
    """Build dynamic ground forces with advancing waypoints."""
    front_lines = state.map_data.get("front_lines", [])
    if not front_lines:
        return

    gw = state.plan.get("ground_war", {})
    intensity = gw.get("intensity", "medium")
    group_sizes = {"light": 3, "medium": 4, "heavy": 5}
    num_groups = {"light": 2, "medium": 3, "heavy": 4}

    gs = group_sizes.get(intensity, 4)
    ng = num_groups.get(intensity, 3)

    for fl in front_lines[:2]:
        if gw.get("blue_advancing", True):
            for i in range(min(ng, 3)):
                if state.total_units >= state.max_units:
                    break
                _build_ground_group(state, "blue", fl["blue_start"], fl["red_start"],
                                    gs, i, fl.get("width", 15000), late=(i > 0))

        if gw.get("red_advancing", True):
            for i in range(min(ng, 3)):
                if state.total_units >= state.max_units:
                    break
                _build_ground_group(state, "red", fl["red_start"], fl["blue_start"],
                                    gs, i, fl.get("width", 15000), late=(i > 0))


def _build_ground_group(state: "BuilderState", coalition: str, start: dict, end: dict,
                        group_size: int, index: int, width: int, late: bool):
    """Build a single ground group with advance waypoints."""
    group_id = state.next_group_id()

    offset = (index - 1) * (width / 3)
    dx = end["x"] - start["x"]
    dy = end["y"] - start["y"]
    dist = math.sqrt(dx**2 + dy**2)
    if dist == 0:
        dist = 1

    perp_x = -dy / dist * offset
    perp_y = dx / dist * offset

    sx = start["x"] + perp_x + random.randint(-1000, 1000)
    sy = start["y"] + perp_y + random.randint(-1000, 1000)

    if coalition == "blue":
        pref = state.plan.get("_blue_armor_preference", [])
        all_units = GROUND_UNITS["blue_armor"]
        if pref:
            unit_pool = [u for u in all_units if u["type"] in pref]
            if not unit_pool:
                unit_pool = all_units
        else:
            unit_pool = all_units
    else:
        pref = state.plan.get("_red_armor_preference", [])
        all_units = GROUND_UNITS["red_armor"]
        if pref:
            unit_pool = [u for u in all_units if u["type"] in pref]
            if not unit_pool:
                unit_pool = all_units
        else:
            unit_pool = all_units

    ground_skill = state.plan.get(
        f"_{'enemy' if coalition == 'red' else 'friendly_ai'}_ground_skill",
        state.plan.get("_enemy_ground_skill", "Average")
    )

    units = []
    for i in range(min(group_size, 5)):
        uid = state.next_unit_id()
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
        state.total_units += 1

    waypoints = [
        {"id": 0, "name": "START", "type": "Turning Point", "action": "On Road",
         "x": sx, "y": sy, "speed": 10,
         "tasks": [{"id": "EngageTargets",
                    "params": {"targetTypes": ["Armor", "Vehicles", "Infantry"]}}]},
        {"id": 1, "name": "ADVANCE", "type": "Turning Point", "action": "On Road",
         "x": (sx + end["x"] + perp_x) / 2, "y": (sy + end["y"] + perp_y) / 2,
         "speed": 10},
        {"id": 2, "name": "OBJECTIVE", "type": "Turning Point", "action": "On Road",
         "x": end["x"] + perp_x + random.randint(-2000, 2000),
         "y": end["y"] + perp_y + random.randint(-2000, 2000), "speed": 8},
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
        state.blue_ground_groups.append(group)
    else:
        state.red_ground_groups.append(group)


def build_convoy(state: "BuilderState"):
    """Build convoy groups for convoy_attack or convoy_defense missions."""
    template = MISSION_TEMPLATES.get(state.mission_type, {})
    convoy_side = template.get("convoy_side", "red")

    routes = state.map_data.get("convoy_routes", {}).get(convoy_side, [])
    if not routes:
        cities = state.map_data.get("cities", [])
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

    supply_key = f"{convoy_side}_supply"
    escort_key = f"{convoy_side}_escort"
    supply_units_pool = CONVOY_UNITS.get(supply_key, [])
    escort_units_pool = CONVOY_UNITS.get(escort_key, [])

    if not supply_units_pool:
        return

    group_id = state.next_group_id()
    units = []
    start_wp = route_wps[0]

    for i, template_unit in enumerate(supply_units_pool[:5]):
        if state.total_units >= state.max_units:
            break
        uid = state.next_unit_id()
        units.append({
            "unit_id": uid,
            "type": template_unit["type"],
            "name": f"Convoy {template_unit['name']} {i+1}",
            "skill": "Average",
            "x": start_wp["x"] + i * 50,
            "y": start_wp["y"] + i * 30,
            "heading": 0,
        })
        state.total_units += 1

    waypoints = []
    for wi, wp in enumerate(route_wps):
        waypoints.append({
            "id": wi,
            "name": f"ROUTE {wi+1}" if wi > 0 else "START",
            "type": "Turning Point",
            "action": "On Road",
            "x": wp["x"], "y": wp["y"], "speed": 8,
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
        state.red_ground_groups.append(convoy_group)
    else:
        state.blue_ground_groups.append(convoy_group)

    # Escort group
    if escort_units_pool and state.total_units < state.max_units:
        eg_id = state.next_group_id()
        escort_units = []
        for i, template_unit in enumerate(escort_units_pool[:3]):
            if state.total_units >= state.max_units:
                break
            uid = state.next_unit_id()
            escort_units.append({
                "unit_id": uid,
                "type": template_unit["type"],
                "name": f"Escort {template_unit['name']}",
                "skill": state.plan.get("_enemy_ground_skill", "High"),
                "x": start_wp["x"] - 100 + i * 60,
                "y": start_wp["y"] - 80 + i * 40,
                "heading": 0,
            })
            state.total_units += 1

        escort_group = {
            "group_id": eg_id,
            "name": f"{'Red' if convoy_side == 'red' else 'Blue'} Convoy Escort",
            "coalition": convoy_side,
            "category": "vehicle",
            "units": escort_units,
            "waypoints": waypoints,
            "late_activation": False,
        }

        if convoy_side == "red":
            state.red_ground_groups.append(escort_group)
        else:
            state.blue_ground_groups.append(escort_group)

    state.convoy_route = route_wps


def build_support(state: "BuilderState"):
    """Build tanker and AWACS with proper callsigns."""
    support = state.map_data.get("support_orbits", {})

    tanker_data = support.get("tanker")
    if tanker_data:
        tanker_cs = state.callsigns.assign_support("tanker", tanker_data.get("name", "Texaco"))
        state.assigned_callsigns["tanker"] = {
            **tanker_cs, "freq": tanker_data.get("freq", 251.0),
            "tacan": tanker_data.get("tacan", "51Y"),
        }
        group_id = state.next_group_id()
        uid = state.next_unit_id()
        state.blue_air_groups.append({
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
        state.total_units += 1

    awacs_data = support.get("awacs")
    if awacs_data:
        awacs_cs = state.callsigns.assign_support("awacs", awacs_data.get("name", "Overlord"))
        state.assigned_callsigns["awacs"] = {**awacs_cs, "freq": awacs_data.get("freq", 252.0)}
        group_id = state.next_group_id()
        uid = state.next_unit_id()
        state.blue_air_groups.append({
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
        state.total_units += 1


def build_reinforcements(state: "BuilderState"):
    """Build timed enemy reinforcement waves as late-activated groups."""
    waves = generate_reinforcement_waves(state.plan)
    red_afs = [af for af in state.map_data.get("airfields", [])
               if af.get("default_coalition") == "red"]
    if not red_afs:
        return

    for wave in waves:
        if state.total_units >= state.max_units:
            break

        ac_key = wave["aircraft"]
        ac_data = AI_AIRCRAFT.get(ac_key, AI_AIRCRAFT.get("MiG-29A"))
        count = wave.get("count", 2)
        task = wave.get("task", "intercept")

        start_af = random.choice(red_afs)
        group_id = state.next_group_id()
        units = []

        enemy_skill = state.plan.get("_enemy_air_skill", "High")
        enemy_pylons = resolve_ai_loadout(ac_key, task)

        for i in range(count):
            uid = state.next_unit_id()
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
            state.total_units += 1

        target = state.get_target_position()
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

        state.red_air_groups.append({
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
            "late_activation": True,
        })

        state.triggers.append({
            "type": "time",
            "time": wave["time"],
            "action": "activate_group",
            "group_name": wave["name"],
            "group_id": group_id,
        })

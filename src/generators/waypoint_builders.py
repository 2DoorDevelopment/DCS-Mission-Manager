"""
Waypoint Builders — Extracted from MissionBuilder
Handles construction of waypoint sequences for player and AI aircraft.
"""

import math
import random


def build_player_waypoints_profiled(state: "BuilderState", airfield: dict,
                                     target_pos: dict, profile: dict) -> list[dict]:
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
        "tasks": state.get_wp_tasks_for_ip(),
    })
    wp_id += 1

    # WP5: Target — attack altitude
    waypoints.append({
        "id": wp_id, "name": "TARGET", "type": "Turning Point",
        "action": "Turning Point",
        "x": target_pos["x"], "y": target_pos["y"],
        "alt": profile["target_alt"], "speed": profile["target_speed"],
        "tasks": state.get_wp_tasks_for_target(),
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


def build_ai_air_waypoints(state: "BuilderState", base_af: dict, task: str) -> list:
    """Build waypoints for AI air groups based on their task."""
    target = state.get_target_position()
    waypoints = []

    # Takeoff
    waypoints.append({
        "id": 0, "name": "TAKEOFF", "type": "TakeOff",
        "action": "From Parking Area",
        "x": base_af["x"], "y": base_af["y"],
        "alt": base_af.get("alt", 0), "speed": 0,
        "airfield_id": base_af.get("id", 0),
    })

    task_lower = task.lower()
    if task_lower in ("cap", "escort"):
        orbit_x = target["x"] + random.randint(-10000, 10000)
        orbit_y = target["y"] + random.randint(-10000, 10000)
        waypoints.append({
            "id": 1, "name": "STATION", "type": "Turning Point",
            "action": "Turning Point",
            "x": orbit_x, "y": orbit_y, "alt": 7000, "speed": 250,
            "tasks": [{"id": "EngageTargets", "params": {"targetTypes": ["Air"]}}],
            "orbit": {"pattern": "Race-Track", "speed": 230, "altitude": 7000},
        })
    elif task_lower in ("sead",):
        waypoints.append({
            "id": 1, "name": "SEAD TARGET", "type": "Turning Point",
            "action": "Turning Point",
            "x": target["x"], "y": target["y"], "alt": 6000, "speed": 250,
            "tasks": [{"id": "EngageTargets", "params": {"targetTypes": ["Air Defence"]}}],
        })
    elif task_lower in ("sweep",):
        sweep_x = target["x"] + random.randint(-20000, 20000)
        sweep_y = target["y"] + random.randint(-20000, 20000)
        waypoints.append({
            "id": 1, "name": "SWEEP", "type": "Turning Point",
            "action": "Turning Point",
            "x": sweep_x, "y": sweep_y, "alt": 8000, "speed": 280,
            "tasks": [{"id": "FighterSweep", "params": {}}],
        })
    else:
        waypoints.append({
            "id": 1, "name": "TARGET", "type": "Turning Point",
            "action": "Turning Point",
            "x": target["x"], "y": target["y"], "alt": 6000, "speed": 250,
        })

    # RTB
    waypoints.append({
        "id": 2, "name": "RTB", "type": "Land", "action": "Landing",
        "x": base_af["x"], "y": base_af["y"],
        "alt": base_af.get("alt", 0), "speed": 0,
        "airfield_id": base_af.get("id", 0),
    })

    return waypoints

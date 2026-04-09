"""
Mission Events System
Generates:
  - Radio message triggers (timed events that play during the mission)
  - Win/loss conditions (mission success/failure logic)
  - Timed enemy reinforcement waves
"""

import random


def generate_message_triggers(plan: dict, callsigns: dict) -> list[dict]:
    """
    Generate timed radio message triggers that make the mission feel alive.
    Kept restrained — a few key messages, not constant chatter.

    Args:
        plan: Mission plan dict
        callsigns: Dict mapping role -> callsign info

    Returns:
        List of trigger dicts for the Lua generator
    """
    messages = []
    mt = plan.get("mission_type", "SEAD")
    awacs_name = callsigns.get("awacs", {}).get("callsign", "Overlord")
    player_cs = callsigns.get("player", {}).get("full", "Player")
    tanker_name = callsigns.get("tanker", {}).get("callsign", "Texaco")

    # T+0: Takeoff — no message needed, you're busy

    # T+2min: AWACS check-in
    messages.append({
        "time": 120,
        "text": f"{awacs_name}: {player_cs}, {awacs_name} on station. "
                f"Picture clean at this time. Check in when airborne.",
        "sound": "radio",
        "coalition": "blue",
    })

    # Mission-type specific messages
    if mt == "SEAD":
        sead_flights = [f for f in plan.get("friendly_flights", [])
                        if f.get("task", "").lower() == "sead"]
        if sead_flights:
            cs = callsigns.get("sead", {}).get("full", "Weasel 1-1")
            messages.append({
                "time": 360,
                "text": f"{cs}: Pushing to target area. Magnum in two mikes.",
                "sound": "radio",
                "coalition": "blue",
            })

        # AWACS threat warning after 8-12 minutes
        messages.append({
            "time": random.randint(480, 720),
            "text": f"{awacs_name}: {player_cs}, {awacs_name}. "
                    f"Threat radar active in your sector. Recommend defensive checks.",
            "sound": "radio",
            "coalition": "blue",
        })

    elif mt == "CAS":
        messages.append({
            "time": 300,
            "text": f"JTAC: {player_cs}, contact. Friendlies marked with smoke. "
                    f"Cleared hot on enemy armor south of smoke.",
            "sound": "radio",
            "coalition": "blue",
        })

    elif mt == "CAP":
        messages.append({
            "time": random.randint(300, 600),
            "text": f"{awacs_name}: {player_cs}, {awacs_name}. "
                    f"Bandits, bearing hot, medium altitude. Recommend intercept.",
            "sound": "radio",
            "coalition": "blue",
        })

    elif mt == "strike":
        messages.append({
            "time": 300,
            "text": f"{awacs_name}: {player_cs}, strike package is on timeline. "
                    f"Push to target in five mikes.",
            "sound": "radio",
            "coalition": "blue",
        })

    elif mt in ("convoy_attack",):
        messages.append({
            "time": 420,
            "text": f"{awacs_name}: {player_cs}, {awacs_name}. "
                    f"Enemy convoy confirmed moving along the road. Multiple vehicles.",
            "sound": "radio",
            "coalition": "blue",
        })

    elif mt in ("convoy_defense",):
        messages.append({
            "time": 300,
            "text": f"{awacs_name}: {player_cs}, {awacs_name}. "
                    f"Convoy is rolling. Stay overhead. Report any inbound contacts.",
            "sound": "radio",
            "coalition": "blue",
        })

    # T+15-20min: Tanker availability (if present)
    if plan.get("_has_tanker", True):
        messages.append({
            "time": random.randint(900, 1200),
            "text": f"{tanker_name}: All players, {tanker_name} on station. "
                    f"Ready for receivers.",
            "sound": "radio",
            "coalition": "blue",
        })

    # T+20-30min: Mid-mission update
    messages.append({
        "time": random.randint(1200, 1800),
        "text": f"{awacs_name}: {player_cs}, {awacs_name}. "
                f"Situation update — enemy activity {'increasing' if random.random() > 0.5 else 'steady'} in your sector.",
        "sound": "radio",
        "coalition": "blue",
    })

    # Sort by time
    messages.sort(key=lambda m: m["time"])
    return messages


def generate_win_conditions(plan: dict) -> list[dict]:
    """
    Generate mission success conditions.
    Returns a list of condition dicts that the Lua generator will embed.
    """
    mt = plan.get("mission_type", "SEAD")
    conditions = []

    if mt == "SEAD":
        # Win: all SAM groups destroyed
        conditions.append({
            "type": "group_dead",
            "coalition": "red",
            "group_pattern": "SAM",
            "description": "All enemy SAM sites destroyed",
            "result": "success",
        })

    elif mt == "CAS":
        # Win: most enemy ground forces destroyed
        conditions.append({
            "type": "group_dead_percent",
            "coalition": "red",
            "group_pattern": "Armor",
            "percent": 70,
            "description": "Enemy ground forces destroyed (70%+)",
            "result": "success",
        })

    elif mt == "CAP":
        # Win: all enemy air groups destroyed or RTB
        conditions.append({
            "type": "group_dead",
            "coalition": "red",
            "group_pattern": "CAP",
            "description": "Enemy air threat neutralized",
            "result": "success",
        })

    elif mt == "strike":
        conditions.append({
            "type": "group_dead",
            "coalition": "red",
            "group_pattern": "Target",
            "description": "Target destroyed",
            "result": "success",
        })

    elif mt == "anti-ship":
        conditions.append({
            "type": "group_dead",
            "coalition": "red",
            "group_pattern": "Naval",
            "description": "Enemy naval group destroyed",
            "result": "success",
        })

    elif mt == "convoy_attack":
        conditions.append({
            "type": "group_dead",
            "coalition": "red",
            "group_pattern": "Convoy",
            "description": "Enemy supply convoy destroyed",
            "result": "success",
        })

    elif mt == "convoy_defense":
        # Win: convoy reaches destination (time-based, or convoy group alive at end)
        conditions.append({
            "type": "group_alive_at_time",
            "coalition": "blue",
            "group_pattern": "Convoy",
            "time": 2400,  # 40 minutes
            "description": "Friendly convoy reached destination",
            "result": "success",
        })

    elif mt == "escort":
        conditions.append({
            "type": "group_alive_at_time",
            "coalition": "blue",
            "group_pattern": "strike",
            "time": 1800,
            "description": "Strike package completed mission",
            "result": "success",
        })

    # Universal loss condition: player dead
    conditions.append({
        "type": "player_dead",
        "description": "Player aircraft lost",
        "result": "failure",
    })

    return conditions


def generate_reinforcement_waves(plan: dict) -> list[dict]:
    """
    Generate timed enemy reinforcement spawns.
    Keeps things unpredictable — randomized timing and composition.

    Returns list of reinforcement dicts with time, group type, and units.
    """
    waves = []
    mt = plan.get("mission_type", "SEAD")
    difficulty = plan.get("difficulty", "medium")

    # Base timing — when reinforcements appear
    if difficulty == "easy":
        wave_times = [random.randint(1200, 1800)]  # 1 wave, late
    elif difficulty == "medium":
        wave_times = [
            random.randint(600, 900),    # ~10-15 min
            random.randint(1200, 1800),  # ~20-30 min
        ]
    else:  # hard
        wave_times = [
            random.randint(480, 720),    # ~8-12 min
            random.randint(900, 1200),   # ~15-20 min
            random.randint(1500, 2100),  # ~25-35 min
        ]

    # Possible reinforcement types
    air_reinforcements = [
        {"aircraft": "MiG-29A", "task": "intercept", "count": 2},
        {"aircraft": "MiG-29S", "task": "CAP", "count": 2},
        {"aircraft": "Su-27", "task": "sweep", "count": 2},
    ]

    cas_reinforcements = [
        {"aircraft": "Su-25", "task": "CAS", "count": 2},
        {"aircraft": "Su-25T", "task": "CAS", "count": 2},
    ]

    for i, wave_time in enumerate(wave_times):
        # Randomize what arrives
        if mt in ("convoy_defense",):
            # Convoy defense: enemy strike aircraft come in waves
            reinforcement = random.choice(cas_reinforcements)
        elif mt in ("CAP", "escort"):
            # Air missions: more fighters
            reinforcement = random.choice(air_reinforcements)
        else:
            # Mixed: could be fighters or CAS
            reinforcement = random.choice(air_reinforcements + cas_reinforcements)

        waves.append({
            "time": wave_time,
            "type": "air",
            "coalition": "red",
            "aircraft": reinforcement["aircraft"],
            "task": reinforcement["task"],
            "count": reinforcement["count"],
            "wave_number": i + 1,
            "name": f"Red Reinforcement Wave {i+1}",
        })

    return waves

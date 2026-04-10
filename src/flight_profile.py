"""
Flight Profile Calculator
Computes realistic altitude profiles, speed schedules, and fuel estimates.
Weather-aware: adjusts profiles based on cloud base, visibility, and ceiling.
"""

# Aircraft performance profiles (simplified but realistic)
AIRCRAFT_PROFILES = {
    "F-16C": {
        "climb_rate_fpm": 50000,     # ft/min at mil power
        "cruise_speed_kts": 450,      # M0.85 at altitude
        "cruise_alt_m": 7600,         # FL250
        "combat_speed_kts": 400,
        "ingress_speed_kts": 420,
        "egress_speed_kts": 500,      # Afterburner egress
        "approach_speed_kts": 180,
        "fuel_flow_cruise_kg_hr": 2500,
        "fuel_flow_combat_kg_hr": 5000,
        "internal_fuel_kg": 3249,
        "low_alt_ingress_m": 150,     # Terrain following altitude
        "medium_alt_m": 4500,         # FL150
        "pop_up_alt_m": 3000,         # Pop-up attack altitude
    },
    "F/A-18C": {
        "climb_rate_fpm": 45000,
        "cruise_speed_kts": 430,
        "cruise_alt_m": 7000,
        "combat_speed_kts": 380,
        "ingress_speed_kts": 400,
        "egress_speed_kts": 480,
        "approach_speed_kts": 160,
        "fuel_flow_cruise_kg_hr": 2800,
        "fuel_flow_combat_kg_hr": 5500,
        "internal_fuel_kg": 4900,
        "low_alt_ingress_m": 150,
        "medium_alt_m": 4500,
        "pop_up_alt_m": 3000,
    },
    "A-10C": {
        "climb_rate_fpm": 6000,
        "cruise_speed_kts": 250,
        "cruise_alt_m": 4500,         # A-10 cruises lower
        "combat_speed_kts": 220,
        "ingress_speed_kts": 230,
        "egress_speed_kts": 280,
        "approach_speed_kts": 130,
        "fuel_flow_cruise_kg_hr": 1500,
        "fuel_flow_combat_kg_hr": 2500,
        "internal_fuel_kg": 5029,
        "low_alt_ingress_m": 50,      # A-10 gets low
        "medium_alt_m": 3000,
        "pop_up_alt_m": 1500,
    },
    "JF-17": {
        "climb_rate_fpm": 30000,
        "cruise_speed_kts": 420,
        "cruise_alt_m": 7000,
        "combat_speed_kts": 380,
        "ingress_speed_kts": 400,
        "egress_speed_kts": 470,
        "approach_speed_kts": 170,
        "fuel_flow_cruise_kg_hr": 2200,
        "fuel_flow_combat_kg_hr": 4500,
        "internal_fuel_kg": 2325,
        "low_alt_ingress_m": 150,
        "medium_alt_m": 4500,
        "pop_up_alt_m": 3000,
    },
}

# Mission type profiles — how each mission type shapes the flight
MISSION_PROFILES = {
    "SEAD": {
        "ingress_alt": "medium",      # Medium altitude for HARM employment
        "target_alt": "medium",
        "egress_alt": "low",          # Get low after shooting
        "attack_desc": "Medium altitude ingress for HARM lock, descend after weapons release",
    },
    "CAS": {
        "ingress_alt": "medium",
        "target_alt": "low",          # Low for gun/rocket runs
        "egress_alt": "medium",
        "attack_desc": "Hold at medium altitude, descend for attack passes, climb between runs",
    },
    "CAP": {
        "ingress_alt": "high",
        "target_alt": "high",         # Stay high for radar advantage
        "egress_alt": "high",
        "attack_desc": "Maintain patrol altitude for radar advantage, descend only for engagement",
    },
    "strike": {
        "ingress_alt": "medium",
        "target_alt": "medium",       # Medium for GPS/laser delivery
        "egress_alt": "low",
        "attack_desc": "Ingress at medium altitude, weapons release, egress low and fast",
    },
    "anti-ship": {
        "ingress_alt": "low",         # Sea-skimming approach
        "target_alt": "low",
        "egress_alt": "low",
        "attack_desc": "Low altitude ingress below ship radar, pop up for launch, egress low",
    },
    "escort": {
        "ingress_alt": "high",
        "target_alt": "high",
        "egress_alt": "high",
        "attack_desc": "Match strike package altitude, maintain formation, engage threats",
    },
    "convoy_attack": {
        "ingress_alt": "medium",
        "target_alt": "low",
        "egress_alt": "medium",
        "attack_desc": "Medium altitude to find convoy, descend for attack passes, climb to egress",
    },
    "convoy_defense": {
        "ingress_alt": "high",
        "target_alt": "medium",
        "egress_alt": "high",
        "attack_desc": "Overhead CAP above convoy, descend to intercept inbound threats",
    },
}


def get_profile(aircraft_key: str) -> dict:
    """Get aircraft performance profile with fallback."""
    return AIRCRAFT_PROFILES.get(aircraft_key, AIRCRAFT_PROFILES["F-16C"])


def kts_to_ms(kts: float) -> float:
    """Convert knots to meters/second for DCS waypoints."""
    return kts * 0.514444


def compute_flight_profile(aircraft_key: str, mission_type: str,
                           weather: dict, distance_m: float) -> dict:
    """
    Compute realistic altitude and speed for each waypoint phase.

    Returns dict with altitude/speed for each phase:
      depart, cruise, push, ip, target, egress, approach

    Weather-aware: if cloud base is below cruise altitude, adjusts down.
    """
    ac = get_profile(aircraft_key)
    mp = MISSION_PROFILES.get(mission_type, MISSION_PROFILES["CAP"])

    # Weather constraints
    cloud_base = weather.get("clouds", {}).get("base", 5000)
    is_ceiling = weather.get("clouds", {}).get("is_ceiling", True)
    visibility = weather.get("visibility", 80000)

    # Altitude selection based on mission profile + weather
    alt_map = {
        "high": ac["cruise_alt_m"],
        "medium": ac["medium_alt_m"],
        "low": ac["low_alt_ingress_m"],
    }

    cruise_alt = ac["cruise_alt_m"]
    ingress_alt = alt_map.get(mp["ingress_alt"], ac["medium_alt_m"])
    target_alt = alt_map.get(mp["target_alt"], ac["medium_alt_m"])
    egress_alt = alt_map.get(mp["egress_alt"], ac["medium_alt_m"])

    # Weather adjustments — only cap altitudes for actual ceilings (overcast/rain/storm)
    # Clear and scattered layers you fly right through
    weather_adjusted = False
    if is_ceiling and cloud_base < 2000:
        # Very low ceiling — everything goes low
        cruise_alt = min(cruise_alt, cloud_base - 300)
        ingress_alt = min(ingress_alt, cloud_base - 300)
        target_alt = min(target_alt, cloud_base - 300)
        egress_alt = min(egress_alt, cloud_base - 300)
        weather_adjusted = True
    elif is_ceiling and cloud_base < 4000:
        # Medium ceiling — cruise below clouds, attack below
        cruise_alt = min(cruise_alt, cloud_base - 500)
        ingress_alt = min(ingress_alt, cloud_base - 300)
        target_alt = min(target_alt, cloud_base - 300)
        weather_adjusted = True

    # Never go below 50m for safety
    cruise_alt = max(cruise_alt, 50)
    ingress_alt = max(ingress_alt, 50)
    target_alt = max(target_alt, 50)
    egress_alt = max(egress_alt, 50)

    # Speed adjustments for low visibility
    combat_speed = ac["combat_speed_kts"]
    if visibility < 10000:
        combat_speed = max(200, combat_speed - 50)  # Slower in poor vis

    return {
        "depart_alt": min(cruise_alt, 3000),
        "depart_speed": kts_to_ms(min(ac["cruise_speed_kts"], 350)),
        "cruise_alt": cruise_alt,
        "cruise_speed": kts_to_ms(ac["cruise_speed_kts"]),
        "push_alt": ingress_alt + (cruise_alt - ingress_alt) * 0.5,
        "push_speed": kts_to_ms(ac["ingress_speed_kts"]),
        "ip_alt": ingress_alt,
        "ip_speed": kts_to_ms(combat_speed),
        "target_alt": target_alt,
        "target_speed": kts_to_ms(combat_speed),
        "egress_alt": egress_alt,
        "egress_speed": kts_to_ms(ac["egress_speed_kts"]),
        "approach_alt": 1000,
        "approach_speed": kts_to_ms(ac["approach_speed_kts"]),
        "attack_desc": mp.get("attack_desc", ""),
        "weather_adjusted": weather_adjusted,
        "weather_note": _weather_note(cloud_base, visibility, is_ceiling),
    }


def estimate_fuel(aircraft_key: str, distance_m: float,
                  loiter_minutes: int = 10) -> dict:
    """
    Estimate fuel consumption for a mission.

    Returns:
        dict with fuel_required_kg, fuel_available_kg, fuel_ok, bingo_fuel_kg
    """
    ac = get_profile(aircraft_key)

    cruise_hours = (distance_m * 2) / (ac["cruise_speed_kts"] * 1852) # Round trip
    combat_hours = loiter_minutes / 60

    fuel_cruise = cruise_hours * ac["fuel_flow_cruise_kg_hr"]
    fuel_combat = combat_hours * ac["fuel_flow_combat_kg_hr"]
    fuel_reserve = ac["internal_fuel_kg"] * 0.15  # 15% reserve
    fuel_required = fuel_cruise + fuel_combat + fuel_reserve

    return {
        "fuel_required_kg": round(fuel_required),
        "fuel_available_kg": ac["internal_fuel_kg"],
        "fuel_ok": fuel_required <= ac["internal_fuel_kg"],
        "bingo_fuel_kg": round(fuel_reserve),
        "loiter_minutes": loiter_minutes,
    }


def _weather_note(cloud_base: float, visibility: float, is_ceiling: bool = True) -> str:
    """Generate a weather advisory note for the briefing."""
    notes = []
    if is_ceiling:
        if cloud_base < 1500:
            notes.append(f"WEATHER WARNING: Ceiling {cloud_base}m — all operations below clouds")
        elif cloud_base < 3000:
            notes.append(f"Low ceiling {cloud_base}m — attack profiles adjusted below cloud base")
    if visibility < 10000:
        notes.append(f"Reduced visibility {visibility/1000:.0f}km — TGP/radar required for target acquisition")
    if not notes:
        return "Weather clear — no impact on flight profile"
    return ". ".join(notes)

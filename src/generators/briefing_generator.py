"""
Briefing Generator v3 — Full Realistic Mission Brief
Covers every section of a real tactical mission briefing,
written for someone who flies DCS but isn't military.

Sections:
  1. SITUATION   — Why this mission matters, what's happening
  2. MISSION     — Your specific objectives
  3. EXECUTION   — How to fly it: flight profile, attack plan, timeline
  4. ROE         — Rules of engagement: what you can shoot and when
  5. SPINS       — Quick reference numbers: bingo, joker, abort, bullseye
  6. THREATS     — SAMs with range rings, enemy air, SHORAD
  7. FLIGHT PLAN — Steerpoints table
  8. PACKAGE     — Friendly forces, callsigns, who does what
  9. COMMS       — Full frequency/TACAN card
  10. FUEL & LOADOUT — Fuel plan, weapons
  11. WEATHER & ENVIRONMENT — Ceiling, visibility, sunrise/sunset, QNH
  12. CONTINGENCY — Alternate airfield, CSAR plan, abort procedures
  13. TACTICAL NOTES — Mission-specific tips
"""

import random
from src.maps import MAP_REGISTRY
from src.units import PLAYER_AIRCRAFT, SAM_SYSTEMS, MISSION_TEMPLATES

# ══════════════════════════════════════════════════════════
# MISSION CONTEXT — the "WHY" for each mission type
# ══════════════════════════════════════════════════════════
MISSION_CONTEXT = {
    "SEAD": "Enemy air defense network is preventing friendly air operations in the area. "
            "Multiple radar-guided SAM systems are active and covering the airspace your "
            "strike and CAS flights need to operate in. Your job is to destroy or suppress "
            "these SAM sites to open a corridor for follow-on packages. Until you do your "
            "job, nobody else can do theirs.",
    "CAS": "Friendly ground forces are in direct contact with the enemy and are requesting "
           "immediate air support. SEAD flights have been working ahead of you to suppress "
           "enemy air defenses in your operating area, but SHORAD threats (short-range AA guns "
           "and missiles) may still be active near the front line. Your job is to find and "
           "destroy enemy ground forces that are threatening our troops.",
    "CAP": "Intelligence reports indicate significant enemy air activity in the theater. "
           "Friendly ground forces, supply convoys, and support aircraft (tankers, AWACS) "
           "all depend on us controlling the sky. Your job is to maintain air superiority "
           "over the assigned patrol zone — intercept and destroy any enemy aircraft that "
           "enter your area.",
    "strike": "A high-value enemy target has been identified by intelligence. SEAD and sweep "
              "flights are clearing the path ahead of you — your job is to deliver precision "
              "ordnance on the target and get out. Speed and accuracy matter: get in, hit the "
              "target on the first pass if possible, and egress before the enemy can react.",
    "anti-ship": "Enemy naval forces are operating in the area and threaten friendly shipping "
                 "and coastal operations. Your job is to locate and destroy the enemy surface "
                 "group using standoff anti-ship weapons. Stay low on approach to avoid ship-based "
                 "radar, pop up only to get a lock, launch, and get back down.",
    "escort": "A friendly strike package is heading to a heavily defended target. Enemy fighters "
              "will try to intercept them before they can deliver their weapons. Your job is to "
              "protect the strikers — stay with the package, engage any enemy fighters that "
              "threaten them, and resist the urge to chase bandits away from the group.",
    "convoy_attack": "Intelligence has identified an enemy supply convoy moving reinforcements "
                     "and ammunition toward the front lines. If this convoy reaches its destination, "
                     "enemy ground forces will be resupplied and our troops will face a tougher fight. "
                     "Your job is to find the convoy on the road and destroy as many vehicles as possible, "
                     "prioritizing supply trucks over escort vehicles.",
    "convoy_defense": "A critical friendly supply convoy is moving through contested territory to "
                      "resupply our forward positions. Enemy air assets — likely Su-25 Frogfoots and "
                      "Su-24 Fencers — are expected to try to destroy the convoy. Your job is to "
                      "provide overhead air cover and intercept any enemy aircraft before they can "
                      "attack the trucks. Do not leave the convoy unprotected.",
}

# ══════════════════════════════════════════════════════════
# ROE — Rules of Engagement per mission type
# ══════════════════════════════════════════════════════════
ROE_TEMPLATES = {
    "SEAD": {
        "weapons_status": "WEAPONS FREE in the target area",
        "detail": "You are cleared to engage any radar emitter or SAM system in the designated "
                  "target area without further authorization. If it's radiating, kill it. "
                  "Outside the target area, WEAPONS TIGHT — only engage if engaged first or "
                  "if positively identified as hostile by AWACS.",
        "fires": "Do not fire on any aircraft unless AWACS confirms hostile (BANDIT call) or "
                 "you have positive radar/visual ID on a threat aircraft. Friendly SEAD and "
                 "sweep flights are operating in the same area.",
    },
    "CAS": {
        "weapons_status": "WEAPONS TIGHT until cleared by JTAC",
        "detail": "Friendly ground forces are close to enemy positions. Do NOT drop ordnance "
                  "until you have positive identification of enemy targets. Use your targeting pod "
                  "to confirm targets before attacking. When in doubt, ask — it's better to make "
                  "another pass than to hit friendlies.",
        "fires": "JTAC (ground controller) will talk you onto targets and clear you hot. If you "
                 "can't reach JTAC, use visual markings (smoke) to identify friendly positions.",
    },
    "CAP": {
        "weapons_status": "WEAPONS FREE on confirmed bandits",
        "detail": "You are cleared to engage any aircraft confirmed hostile by AWACS (BANDIT call) "
                  "or by your own positive ID (radar type, IFF, visual). Use BVR (beyond visual range) "
                  "engagement when possible — don't close to merge if you can avoid it.",
        "fires": "IFF your targets before launch. If your radar shows a contact that AWACS hasn't "
                 "called, get a confirmation before shooting. Multiple friendly flights are in the area.",
    },
    "strike": {
        "weapons_status": "WEAPONS FREE on designated target",
        "detail": "Your target has been pre-briefed and coordinates are in your steerpoints. "
                  "You are cleared to employ weapons on the target coordinates. Do not attack "
                  "any targets of opportunity — stay focused on the primary objective and egress.",
        "fires": "Self-defense only against air threats unless your escort is overwhelmed. "
                 "If engaged by fighters, jettison ordnance and defend yourself.",
    },
    "anti-ship": {
        "weapons_status": "WEAPONS FREE on enemy naval group",
        "detail": "You are cleared to engage the enemy surface group with anti-ship weapons. "
                  "Launch from maximum standoff range. Positive ID is required — confirm the "
                  "target is enemy before launch (check coordinates against briefed position).",
        "fires": "Do not engage any vessel that doesn't match the briefed target description. "
                 "Neutral shipping may be in the area.",
    },
    "escort": {
        "weapons_status": "WEAPONS FREE on threats to the package",
        "detail": "Engage any aircraft that threatens the strike package. Prioritize targets "
                  "that are closing on the strikers over distant contacts. You're the shield, "
                  "not the sword — protect the package first, score kills second.",
        "fires": "IFF all contacts. Friendly sweep flights may be operating ahead of the package. "
                 "Coordinate with AWACS for the big picture.",
    },
    "convoy_attack": {
        "weapons_status": "WEAPONS FREE on enemy convoy",
        "detail": "You are cleared to engage all vehicles in the enemy convoy. Prioritize "
                  "supply trucks (soft-skinned vehicles) over armored escorts. Watch for mobile "
                  "AAA in the convoy — Shilkas and SA-8s may be mixed in with the trucks.",
        "fires": "Do not attack vehicles off the briefed convoy route — they may be civilian. "
                 "Stick to the road and the convoy column.",
    },
    "convoy_defense": {
        "weapons_status": "WEAPONS FREE on inbound enemy air",
        "detail": "Engage any enemy aircraft approaching the convoy. Priority targets are "
                  "ground-attack aircraft (Su-25, Su-24) — these are the ones that will actually "
                  "hit the trucks. Enemy fighters may try to draw you away from the convoy: don't "
                  "take the bait.",
        "fires": "Stay within visual range of the convoy. If you chase a bandit 30 miles away, "
                 "a second flight of Su-25s will hit the convoy while you're gone.",
    },
}

# Default ROE for types not listed
_DEFAULT_ROE = {
    "weapons_status": "WEAPONS TIGHT — engage only hostile contacts",
    "detail": "Engage targets only when positively identified as hostile. Use IFF and "
              "AWACS confirmation before employing weapons.",
    "fires": "Check fire on all unidentified contacts.",
}


class BriefingGenerator:
    """Generate a full realistic mission briefing."""

    def __init__(self, mission_data: dict, plan: dict):
        self.data = mission_data
        self.plan = plan
        self.map_data = MAP_REGISTRY.get(plan.get("map_name", "Caucasus"), {})
        self.callsigns = mission_data.get("callsigns", {})
        self.fuel_est = mission_data.get("fuel_estimate", {})
        self.mt = plan.get("mission_type", "SEAD")

        # Pre-compute shared data
        self.player_cs = self.callsigns.get("player", {})
        self.ac_key = plan.get("player_aircraft", "F-16C")
        self.ac_data = PLAYER_AIRCRAFT.get(self.ac_key, {})
        self.player_af = self._find_airfield(plan.get("player_airfield", ""))
        self.alt_af = self._find_alternate_airfield()
        self.bullseye = self._compute_bullseye()

    def generate(self) -> str:
        sections = [
            self._header(),
            self._situation(),
            self._mission(),
            self._execution(),
            self._roe(),
            self._spins(),
            self._threats(),
            self._flight_plan(),
            self._package(),
            self._comms(),
            self._fuel_and_loadout(),
            self._weather_environment(),
            self._contingency(),
            self._tactical_notes(),
            self._footer(),
        ]
        return "\n".join(sections)

    # ── 0. HEADER ──
    def _header(self) -> str:
        lines = []
        op_name = self.plan.get("_operation_name", "MISSION BRIEFING")
        lines.append("=" * 60)
        lines.append(f"  {op_name}")
        lines.append("  MISSION BRIEFING")
        lines.append("=" * 60)

        mt_desc = MISSION_TEMPLATES.get(self.mt, {}).get("description", self.mt)
        lines.append("")
        lines.append(f"  SORTIE:     {mt_desc}")
        lines.append(f"  THEATER:    {self.plan.get('map_name', '?')}")
        lines.append(f"  AIRCRAFT:   {self.ac_data.get('display_name', self.ac_key)}")
        lines.append(f"  CALLSIGN:   {self.player_cs.get('full', 'Player 1-1')}")
        lines.append(f"  DEPARTURE:  {self.plan.get('player_airfield', '?')}")
        if self.alt_af:
            lines.append(f"  ALTERNATE:  {self.alt_af['name']}")
        lines.append(f"  DIFFICULTY: {self.plan.get('difficulty', 'medium').upper()}")
        lines.append("")
        return "\n".join(lines)

    # ── 1. SITUATION (WHY) ──
    def _situation(self) -> str:
        lines = ["-" * 60, "  1. SITUATION", "-" * 60, ""]
        context = MISSION_CONTEXT.get(self.mt, "Complete assigned mission objectives.")
        lines.extend(self._wrap(context))
        gw = self.plan.get("ground_war", {})
        if gw.get("enabled"):
            lines.append("")
            if gw.get("front_line_desc"):
                lines.append(f"  Ground situation: {gw['front_line_desc']}")
            lines.append(f"  Combat intensity: {gw.get('intensity', 'medium').upper()}")
        if self.plan.get("_campaign_mission_num"):
            lines.append("")
            lines.append(f"  Campaign: {self.plan.get('_campaign_name', '?')} — "
                         f"Mission {self.plan['_campaign_mission_num']}/{self.plan.get('_campaign_total', '?')}")
            if self.plan.get("_campaign_desc"):
                lines.append(f"  Phase: {self.plan['_campaign_desc']}")
        lines.append("")
        return "\n".join(lines)

    # ── 2. MISSION (WHAT) ──
    def _mission(self) -> str:
        lines = ["-" * 60, "  2. MISSION", "-" * 60, ""]
        objectives = self.plan.get("objectives", ["Complete assigned mission and RTB."])
        for i, obj in enumerate(objectives, 1):
            lines.append(f"    {i}. {obj}")
        lines.append("")
        return "\n".join(lines)

    # ── 3. EXECUTION (HOW) ──
    def _execution(self) -> str:
        lines = ["-" * 60, "  3. EXECUTION", "-" * 60, ""]

        # Flight profile
        profile = self.plan.get("_flight_profile", {})
        if profile:
            lines.append("  FLIGHT PROFILE:")
            if profile.get("attack_desc"):
                lines.append(f"    {profile['attack_desc']}")
            lines.append("")
            lines.append(f"    Phase      Altitude     Speed")
            lines.append(f"    ─────      ────────     ─────")
            phases = [
                ("Cruise", profile.get("cruise_alt", 0), profile.get("cruise_speed", 0)),
                ("Ingress", profile.get("ip_alt", 0), profile.get("ip_speed", 0)),
                ("Target", profile.get("target_alt", 0), profile.get("target_speed", 0)),
                ("Egress", profile.get("egress_alt", 0), profile.get("egress_speed", 0)),
            ]
            for name, alt, spd in phases:
                spd_kts = int(spd / 0.514) if spd > 0 else 0
                lines.append(f"    {name:<10} {alt:>6.0f}m      {spd_kts:>4} kts")
            if profile.get("weather_adjusted"):
                lines.append(f"    *** WEATHER ADJUSTED — see Section 11 ***")

        # Timeline
        lines.append("")
        lines.append("  MISSION TIMELINE:")
        timeline = self._build_timeline()
        for entry in timeline:
            lines.append(f"    {entry}")

        lines.append("")
        return "\n".join(lines)

    # ── 4. ROE ──
    def _roe(self) -> str:
        lines = ["-" * 60, "  4. RULES OF ENGAGEMENT", "-" * 60, ""]
        roe = ROE_TEMPLATES.get(self.mt, _DEFAULT_ROE)
        lines.append(f"  STATUS: {roe['weapons_status']}")
        lines.append("")
        lines.extend(self._wrap(roe["detail"]))
        lines.append("")
        lines.append("  FIRE CONTROL:")
        lines.extend(self._wrap(roe["fires"]))
        lines.append("")
        return "\n".join(lines)

    # ── 5. SPINS ──
    def _spins(self) -> str:
        lines = ["-" * 60, "  5. SPINS (Quick Reference Numbers)", "-" * 60, ""]

        fuel = self.plan.get("_fuel_estimate", self.fuel_est)
        bingo = fuel.get("bingo_fuel_kg", 500)
        joker = int(bingo * 1.5)

        lines.append(f"  BINGO FUEL:  {bingo} kg  (RTB immediately — minimum to get home)")
        lines.append(f"  JOKER FUEL:  {joker} kg  (start thinking about heading home)")
        lines.append("")

        # Bullseye
        if self.bullseye:
            lines.append(f"  BULLSEYE:    {self.bullseye['name']} ({self.bullseye['desc']})")
            lines.append(f"               AWACS calls use bullseye as reference.")
            lines.append(f"               Example: \"Bandit, bullseye 040/60\" means")
            lines.append(f"               040 degrees from bullseye at 60 nautical miles.")
        lines.append("")

        # Abort
        abort_code = f"{''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ', k=2))}{random.randint(10,99)}"
        lines.append(f"  ABORT CODE:  {abort_code}")
        lines.append(f"               If you hear this code on guard, the mission is")
        lines.append(f"               cancelled. Jettison ordnance and RTB immediately.")
        lines.append("")

        # MSL floor
        if self.mt in ("CAS", "convoy_attack"):
            lines.append(f"  MSL FLOOR:   500 ft AGL (do not descend below this)")
        elif self.mt in ("anti-ship",):
            lines.append(f"  MSL FLOOR:   50 ft MSL (sea-skimming ingress)")
        else:
            lines.append(f"  MSL FLOOR:   1000 ft AGL (safety altitude)")
        lines.append("")
        return "\n".join(lines)

    # ── 6. THREATS ──
    def _threats(self) -> str:
        lines = ["-" * 60, "  6. THREAT ASSESSMENT", "-" * 60, ""]

        sams = self.plan.get("enemy_sam_sites", [])
        if sams:
            lines.append("  SAM THREATS:")
            for i, sam in enumerate(sams, 1):
                sd = SAM_SYSTEMS.get(sam.get("type", ""), {})
                name = sd.get("display_name", sam.get("type", "?"))
                rng = sd.get("range_km", "?")
                rng_nm = round(rng * 0.54) if isinstance(rng, (int, float)) else "?"
                threat = sd.get("threat_level", "?").upper()
                lines.append(f"    {i}. {name}")
                lines.append(f"       Range: {rng} km ({rng_nm} nm) | Threat: {threat}")
                lines.append(f"       MEZ: Stay outside {rng_nm} nm until ready to commit.")
            if self.plan.get("_shorad_escort"):
                lines.append("")
                lines.append("    SHORAD: SA-15/Tunguska escorting main SAM sites.")
                lines.append("    These are short-range (8-12 km) but deadly if you fly over them.")
        else:
            lines.append("  No significant SAM threat in the AO.")

        lines.append("")
        enemy_air = self.plan.get("enemy_air", [])
        if enemy_air:
            lines.append("  AIR THREATS:")
            for ea in enemy_air:
                cnt = ea.get("count", 2)
                ac = ea.get("aircraft", "?")
                task = ea.get("task", "CAP")
                lines.append(f"    - {cnt}x {ac} ({task})")
            lines.append("")
            lines.append("  Enemy reinforcements may arrive during the mission.")
            lines.append("  Stay alert — new contacts can appear 10-30 minutes in.")
        else:
            lines.append("  No significant air threat reported.")
        lines.append("")
        return "\n".join(lines)

    # ── 7. FLIGHT PLAN ──
    def _flight_plan(self) -> str:
        lines = ["-" * 60, "  7. FLIGHT PLAN / STEERPOINTS", "-" * 60, ""]

        wps = self.data.get("player_group", {}).get("waypoints", [])
        lines.append(f"  {'STP':>4}  {'NAME':<12}  {'ALT':>8}  {'SPEED':>9}  NOTES")
        lines.append(f"  {'───':>4}  {'────':<12}  {'───':>8}  {'─────':>9}  ─────")

        notes_map = {
            "TAKEOFF": "Runway heading, gear up at 200 kts",
            "DEPART": "Climb to cruise altitude",
            "CRUISE": "Level off, set cruise speed",
            "PUSH": "Descend to ingress altitude, combat checks",
            "IP": "Final attack heading, master arm ON",
            "TARGET": "Weapons employment",
            "EGRESS": "Get low, get fast, defensive checks",
            "LANDING": "Contact tower, set up for approach",
        }

        for wp in wps:
            stpt = wp.get("id", 0) + 1
            name = wp.get("name", "?")
            alt = wp.get("alt", 0)
            spd = wp.get("speed", 0)
            spd_kts = f"{int(spd / 0.514)} kts" if spd > 0 else "---"
            note = notes_map.get(name, "")
            lines.append(f"  {stpt:>4}  {name:<12}  {alt:>7.0f}m  {spd_kts:>9}  {note}")
        lines.append("")
        return "\n".join(lines)

    # ── 8. PACKAGE ──
    def _package(self) -> str:
        lines = ["-" * 60, "  8. FRIENDLY PACKAGE", "-" * 60, ""]

        lines.append(f"  YOUR FLIGHT:")
        lines.append(f"    {self.player_cs.get('full', 'Player 1-1')}: "
                     f"{self.ac_data.get('display_name', '?')} ({self.mt})"
                     f"{' + wingman' if self.plan.get('wingman') else ' (solo)'}")
        lines.append("")

        friendly_flights = [(k, v) for k, v in self.callsigns.items() if k.startswith("friendly_")]
        if friendly_flights:
            lines.append("  SUPPORTING FLIGHTS:")
            for _, cs in friendly_flights:
                task = cs.get("task", "?").upper()
                lines.append(f"    {cs.get('full', '?')}: {task} ({cs.get('freq', 0):.1f} MHz)")
                # Add what this flight does in plain English
                role_desc = {
                    "SEAD": "Suppressing enemy SAMs ahead of you",
                    "SWEEP": "Clearing enemy fighters from your route",
                    "ESCORT": "Protecting you from enemy interceptors",
                    "CAP": "Maintaining air cover over the area",
                    "CAS": "Providing ground attack support",
                    "STRIKE": "Hitting assigned ground targets",
                }
                desc = role_desc.get(task, "")
                if desc:
                    lines.append(f"      → {desc}")
            lines.append("")

        # Support assets
        tanker = self.callsigns.get("tanker", {})
        awacs = self.callsigns.get("awacs", {})
        if tanker or awacs:
            lines.append("  SUPPORT ASSETS:")
            if awacs:
                lines.append(f"    {awacs.get('callsign', 'AWACS')}: Airborne early warning & control")
                lines.append(f"      Provides threat calls, bandit/friendly ID, and intercept vectors")
            if tanker:
                lines.append(f"    {tanker.get('callsign', 'Tanker')}: Air-to-air refueling")
                lines.append(f"      Available if you need gas — call for vectors")
        lines.append("")
        return "\n".join(lines)

    # ── 9. COMMS ──
    def _comms(self) -> str:
        lines = ["-" * 60, "  9. COMMUNICATIONS CARD", "-" * 60, ""]

        lines.append(f"  {'ASSET':<20} {'CALLSIGN':<14} {'FREQ':>7}  {'TACAN':>6}")
        lines.append(f"  {'─'*20} {'─'*14} {'─'*7}  {'─'*6}")

        # Player
        lines.append(f"  {'Your Flight':<20} {self.player_cs.get('full', '?'):<14} "
                     f"{self.player_cs.get('freq', 0):>7.1f}  {'---':>6}")

        # AWACS
        awacs = self.callsigns.get("awacs", {})
        if awacs:
            lines.append(f"  {'AWACS':<20} {awacs.get('callsign', '?'):<14} "
                         f"{awacs.get('freq', 252.0):>7.1f}  {'---':>6}")

        # Tanker
        tanker = self.callsigns.get("tanker", {})
        if tanker:
            lines.append(f"  {'Tanker':<20} {tanker.get('callsign', '?'):<14} "
                         f"{tanker.get('freq', 251.0):>7.1f}  {tanker.get('tacan', '---'):>6}")

        # Friendly flights
        for key, cs in self.callsigns.items():
            if key.startswith("friendly_"):
                task = cs.get("task", "?").upper()
                lines.append(f"  {task + ' Flight':<20} {cs.get('full', '?'):<14} "
                             f"{cs.get('freq', 0):>7.1f}  {'---':>6}")

        # Airfields
        if self.player_af:
            tacan = self.player_af.get("tacan", "---")
            ils = self.player_af.get("ils", "---")
            atis = self.player_af.get("atis", "---")
            lines.append(f"  {'Home Base':<20} {self.player_af['name']:<14} {'':>7}  {tacan:>6}")
            if ils != "---":
                lines.append(f"  {'  ILS':<20} {'':14} {ils:>7}")
            if atis != "---":
                lines.append(f"  {'  ATIS':<20} {'':14} {atis:>7}")

        if self.alt_af:
            at = self.alt_af.get("tacan", "---")
            ai = self.alt_af.get("ils", "---")
            lines.append(f"  {'Alternate':<20} {self.alt_af['name']:<14} {'':>7}  {at:>6}")
            if ai != "---":
                lines.append(f"  {'  ILS':<20} {'':14} {ai:>7}")

        lines.append(f"  {'Guard (Emergency)':<20} {'':14} {'243.0':>7}")
        lines.append("")
        return "\n".join(lines)

    # ── 10. FUEL & LOADOUT ──
    def _fuel_and_loadout(self) -> str:
        lines = ["-" * 60, "  10. FUEL & LOADOUT", "-" * 60, ""]

        fuel = self.plan.get("_fuel_estimate", self.fuel_est)
        if fuel:
            lines.append(f"  FUEL:")
            lines.append(f"    Internal fuel:     {fuel.get('fuel_available_kg', 0):,} kg")
            lines.append(f"    Estimated needed:  {fuel.get('fuel_required_kg', 0):,} kg")
            lines.append(f"    Reserve (15%):     {fuel.get('bingo_fuel_kg', 0):,} kg")
            lines.append(f"    Joker fuel:        {int(fuel.get('bingo_fuel_kg', 0) * 1.5):,} kg")
            if not fuel.get("fuel_ok", True):
                lines.append(f"    *** WARNING: Fuel may be tight — manage throttle ***")
            lines.append("")

        loadout = self.ac_data.get("default_loadouts", {}).get(self.mt, {})
        if loadout:
            lines.append(f"  LOADOUT: {loadout.get('description', 'Standard')}")
        lines.append("")
        return "\n".join(lines)

    # ── 11. WEATHER & ENVIRONMENT ──
    def _weather_environment(self) -> str:
        lines = ["-" * 60, "  11. WEATHER & ENVIRONMENT", "-" * 60, ""]

        weather = self.plan.get("weather", "clear").title()
        tod = self.plan.get("time_of_day", "morning")
        profile = self.plan.get("_flight_profile", {})

        lines.append(f"  Conditions:     {weather}")
        lines.append(f"  Time of day:    {tod.title()}")

        # Sunrise/sunset approximations
        sunrise_map = {"morning": "05:45", "afternoon": "05:45", "evening": "05:45", "night": "05:45"}
        sunset_map = {"morning": "20:30", "afternoon": "20:30", "evening": "20:30", "night": "20:30"}
        lines.append(f"  Sunrise:        ~{sunrise_map.get(tod, '06:00')} local")
        lines.append(f"  Sunset:         ~{sunset_map.get(tod, '20:00')} local")
        lines.append(f"  QNH:            760 mmHg / 29.92 inHg (standard)")
        lines.append(f"  Mag variation:  ~6° East (Caucasus)") # Approximate

        if profile.get("weather_note"):
            lines.append("")
            lines.append(f"  *** {profile['weather_note']} ***")

        lines.append("")
        return "\n".join(lines)

    # ── 12. CONTINGENCY ──
    def _contingency(self) -> str:
        lines = ["-" * 60, "  12. CONTINGENCY", "-" * 60, ""]

        # Alternate airfield
        lines.append("  DIVERT / ALTERNATE:")
        if self.alt_af:
            lines.append(f"    If you can't make it home, divert to {self.alt_af['name']}.")
            tacan = self.alt_af.get("tacan", "")
            ils = self.alt_af.get("ils", "")
            if tacan:
                lines.append(f"    TACAN: {tacan}" + (f"  |  ILS: {ils}" if ils else ""))
            rwy = (self.alt_af.get("runways") or [{}])[0]
            if rwy:
                lines.append(f"    Runway heading: {rwy.get('heading', '?')}°, {rwy.get('length', '?')}m")
        else:
            lines.append("    No suitable alternate — manage fuel to make it home.")
        lines.append("")

        # CSAR
        lines.append("  CSAR (If you get shot down):")
        lines.append("    1. Eject and select a safe position on the ground")
        lines.append("    2. Switch radio to GUARD: 243.0 MHz")
        lines.append("    3. Transmit your callsign and position")
        lines.append("    4. Stay hidden and wait for rescue")
        csar_cs = "Pedro"
        lines.append(f"    Rescue helicopter callsign: {csar_cs}")
        lines.append(f"    Safe area: South of the front line / behind friendly positions")
        lines.append("")

        # Abort
        lines.append("  MISSION ABORT:")
        lines.append("    If you hear the abort code on guard frequency, or if AWACS")
        lines.append("    calls 'KNOCK IT OFF' — the mission is cancelled.")
        lines.append("    Jettison stores, set heading for home base, RTB immediately.")
        lines.append("")
        return "\n".join(lines)

    # ── 13. TACTICAL NOTES ──
    def _tactical_notes(self) -> str:
        lines = ["-" * 60, "  13. TACTICAL NOTES", "-" * 60, ""]

        notes = self._get_notes()
        for note in notes:
            lines.append(f"    › {note}")
        lines.append("")
        return "\n".join(lines)

    # ── FOOTER ──
    def _footer(self) -> str:
        lines = []
        lines.append("  Generated by DCS Mission Generator v2.0")
        lines.append("  Good hunting.")
        lines.append("=" * 60)
        lines.append("")
        return "\n".join(lines)

    # ══════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════

    def _wrap(self, text: str, width: int = 56) -> list[str]:
        """Wrap text to fit the briefing format."""
        words = text.split()
        lines = []
        current = "  "
        for word in words:
            if len(current) + len(word) + 1 > width:
                lines.append(current)
                current = "  " + word
            else:
                current += " " + word if current.strip() else "  " + word
        if current.strip():
            lines.append(current)
        return lines

    def _find_airfield(self, name: str) -> dict | None:
        for af in self.map_data.get("airfields", []):
            if af["name"].lower() == name.lower() or name.lower() in af["name"].lower():
                return af
        return None

    def _find_alternate_airfield(self) -> dict | None:
        """Find the nearest blue airfield that isn't the departure base."""
        home = self.plan.get("player_airfield", "")
        blue_afs = [af for af in self.map_data.get("airfields", [])
                    if af.get("default_coalition") == "blue" and af["name"].lower() != home.lower()]
        if not blue_afs:
            return None
        # Pick the one with the longest runway (most suitable as alternate)
        blue_afs.sort(key=lambda af: max((r.get("length", 0) for r in af.get("runways", [{"length": 0}])), default=0), reverse=True)
        return blue_afs[0] if blue_afs else None

    def _compute_bullseye(self) -> dict | None:
        """Pick a bullseye reference point — a recognizable city near the center of the AO."""
        cities = self.map_data.get("cities", [])
        contested = [c for c in cities if c.get("side") == "contested"]
        if contested:
            c = contested[0]
            return {"name": c["name"], "desc": f"City used as reference point for AWACS calls",
                    "x": c["x"], "y": c["y"]}
        blue_cities = [c for c in cities if c.get("side") == "blue"]
        if blue_cities:
            c = blue_cities[0]
            return {"name": c["name"], "desc": f"Reference point for range/bearing calls",
                    "x": c["x"], "y": c["y"]}
        return None

    def _build_timeline(self) -> list[str]:
        """Build a mission timeline based on mission type and package."""
        entries = []
        has_sead = any(f.get("task", "").lower() == "sead"
                       for f in self.plan.get("friendly_flights", []))

        entries.append("T+0:00   Takeoff and climb to cruise altitude")
        entries.append("T+0:05   Departure point — set course for AO")

        if has_sead and self.mt not in ("SEAD",):
            entries.append("T+0:08   SEAD flight pushes to target area")
            entries.append("T+0:12   Sweep flight clears enemy fighters")
            entries.append("T+0:15   SEAD reports SAMs suppressed")
            entries.append("T+0:18   You push from IP to target")
        elif self.mt == "SEAD":
            entries.append("T+0:10   Sweep flight clears ahead of you")
            entries.append("T+0:13   Push from IP — begin SEAD run")
        elif self.mt == "CAP":
            entries.append("T+0:12   Arrive on station — begin patrol")
            entries.append("T+0:12+  Engage bandits as detected by AWACS")
        elif self.mt in ("convoy_attack", "convoy_defense"):
            entries.append("T+0:10   Arrive in convoy area")
            entries.append("T+0:12   Locate convoy on road")
        else:
            entries.append("T+0:12   Push from IP")

        entries.append("T+0:25   Target area — weapons employment")
        entries.append("T+0:30   Egress — head for home")
        entries.append("T+0:40   Estimated RTB / landing")
        return entries

    def _get_notes(self) -> list[str]:
        notes = {
            "SEAD": [
                "Prioritize tracking radars (TR) over launchers — kill the radar and the missiles are blind",
                "Use HARM in PB or HAS mode for best results",
                "Terrain masking on approach — use hills to hide from the radar until you're ready",
                "Egress perpendicular to SAM threat axis — don't fly straight back the way you came",
                "If you see a launch, break hard and dispense chaff — then resume attack",
            ],
            "CAS": [
                "Wait for SEAD to suppress area defenses before entering the AO",
                "Use your targeting pod (TGP) to positively ID targets before dropping",
                "Watch for friendlies — they're close to the enemy. When in doubt, don't shoot.",
                "RTB when Winchester (out of weapons) or at Bingo fuel, whichever comes first",
                "Multiple passes are better than one rushed attack — take your time",
            ],
            "CAP": [
                "Stay at patrol altitude for best radar performance — altitude is your advantage",
                "Use AWACS for early warning — they see farther than your radar",
                "Engage BVR (beyond visual range) when possible — don't merge if you don't have to",
                "Keep track of your wingman — check six frequently",
                "If fuel gets to Joker, start heading home while still watching for threats",
            ],
            "strike": [
                "Follow the SEAD timeline — don't push ahead of schedule or the SAMs will be waiting",
                "Ingress at the planned altitude to stay below/above the threat envelope",
                "First pass is best pass — set up your attack early and deliver on the first run",
                "After weapons release, egress low and fast — don't circle back to admire your work",
                "If you can't acquire the target, RTB with ordnance rather than dropping blind",
            ],
            "anti-ship": [
                "Launch at maximum standoff range — don't close with the ship group",
                "Ship-based SAMs (SA-N series) are dangerous — stay below their radar until launch",
                "Pop up just enough to get radar lock, launch, and get back down",
                "Coordinate with your escort — they should keep enemy fighters off you",
                "If carrying multiple weapons, ripple them on a 5-second interval",
            ],
            "escort": [
                "Your job is protecting the strikers, NOT getting kills. Stay with the package.",
                "Engage threats to the strike group first — a bandit 50 miles away isn't a threat yet",
                "Maintain comms with the strike lead — they'll call threats they see",
                "If a bandit breaks through, call it out and intercept. Don't leave silently.",
                "RTB with the package, not independently — they still need cover on the way home",
            ],
            "convoy_attack": [
                "The convoy is moving — plan your attack run on the road AHEAD of the convoy",
                "Prioritize the trucks (fuel, ammo) over the armored escort vehicles",
                "Watch for mobile AAA in the convoy — Shilkas and SA-8s mixed in with the trucks",
                "Ingress perpendicular to the road for best target acquisition",
                "If the convoy stops, it's easier to hit — but also means the AAA is setting up",
            ],
            "convoy_defense": [
                "Stay overhead — if you chase a bandit 30 miles away, a second flight hits the convoy",
                "Enemy Su-25 and Su-24 are your primary targets — they're the convoy killers",
                "Use AWACS for early warning on inbound strike packages",
                "Watch for low-altitude ingress — enemy CAS likes to come in under your radar",
                "The convoy's survival is the success metric, not your kill count",
            ],
        }
        return notes.get(self.mt, ["Complete assigned objectives and RTB safely."])

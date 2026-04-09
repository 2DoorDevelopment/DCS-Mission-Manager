"""
Campaign System — Interactive Mission Chaining (Hybrid Debrief)

Flow:
  1. User requests a campaign ("3 mission SEAD campaign on Caucasus")
  2. Tool generates mission 1 and saves the .miz
  3. User flies the mission in DCS
  4. User comes back and types "next mission" or "campaign"
  5. Tool asks a few quick debrief questions about what happened
  6. Answers drive the state for mission 2 — destroyed SAMs stay dead,
     front line shifts, attrition accumulates, enemy escalates
  7. Repeat until campaign complete

State is saved to disk between sessions so you can close the tool,
fly the mission, and come back later.
"""

import json
import copy
import random
import time
from pathlib import Path


# ════════════════════════════════════════════════════════════
# DEBRIEF QUESTIONS — asked after each mission
# ════════════════════════════════════════════════════════════

DEBRIEF_QUESTIONS = {
    "SEAD": [
        {
            "key": "sams_killed",
            "question": "How many enemy SAM sites did you destroy?",
            "options": ["All of them", "Most (left 1 standing)", "Some (half survived)", "None / had to abort"],
            "effects": {
                "All of them":           {"sams_destroyed": "all", "result": "success"},
                "Most (left 1 standing)": {"sams_destroyed": "most", "result": "success"},
                "Some (half survived)":   {"sams_destroyed": "some", "result": "partial"},
                "None / had to abort":    {"sams_destroyed": "none", "result": "failure"},
            },
        },
        {
            "key": "air_threats",
            "question": "How was the enemy air opposition?",
            "options": ["Shot them all down", "Got a couple kills", "They were tough — lost wingman", "Got overwhelmed"],
            "effects": {
                "Shot them all down":              {"red_air_attrition": 0.20, "blue_air_attrition": 0.02},
                "Got a couple kills":              {"red_air_attrition": 0.10, "blue_air_attrition": 0.05},
                "They were tough — lost wingman":  {"red_air_attrition": 0.05, "blue_air_attrition": 0.15},
                "Got overwhelmed":                 {"red_air_attrition": 0.02, "blue_air_attrition": 0.20},
            },
        },
    ],
    "CAS": [
        {
            "key": "ground_effect",
            "question": "How effective was your CAS?",
            "options": ["Destroyed most enemy armor", "Good hits but some survived", "Couldn't find targets / bad weather", "Had to bug out early"],
            "effects": {
                "Destroyed most enemy armor":       {"front_shift": -0.15, "result": "success"},
                "Good hits but some survived":      {"front_shift": -0.08, "result": "success"},
                "Couldn't find targets / bad weather": {"front_shift": 0.0, "result": "partial"},
                "Had to bug out early":             {"front_shift": 0.05, "result": "failure"},
            },
        },
        {
            "key": "friendly_ground",
            "question": "How are friendly ground forces doing?",
            "options": ["Pushing forward strong", "Holding the line", "Taking losses", "In retreat"],
            "effects": {
                "Pushing forward strong": {"front_shift": -0.10, "blue_ground_attrition": 0.02},
                "Holding the line":       {"front_shift": 0.0, "blue_ground_attrition": 0.05},
                "Taking losses":          {"front_shift": 0.05, "blue_ground_attrition": 0.12},
                "In retreat":             {"front_shift": 0.15, "blue_ground_attrition": 0.20},
            },
        },
    ],
    "CAP": [
        {
            "key": "air_kills",
            "question": "How did the air battle go?",
            "options": ["Total air superiority — cleaned house", "Won the fight, some got through", "Even exchange", "They owned the sky"],
            "effects": {
                "Total air superiority — cleaned house": {"red_air_attrition": 0.25, "blue_air_attrition": 0.02, "result": "success"},
                "Won the fight, some got through":       {"red_air_attrition": 0.15, "blue_air_attrition": 0.05, "result": "success"},
                "Even exchange":                         {"red_air_attrition": 0.08, "blue_air_attrition": 0.10, "result": "partial"},
                "They owned the sky":                    {"red_air_attrition": 0.03, "blue_air_attrition": 0.20, "result": "failure"},
            },
        },
    ],
    "strike": [
        {
            "key": "target_hit",
            "question": "Did you hit the target?",
            "options": ["Direct hit — target destroyed", "Hit but not sure about damage", "Missed / couldn't acquire", "Had to jettison and abort"],
            "effects": {
                "Direct hit — target destroyed":   {"result": "success", "front_shift": -0.10},
                "Hit but not sure about damage":   {"result": "partial", "front_shift": -0.03},
                "Missed / couldn't acquire":       {"result": "partial", "front_shift": 0.0},
                "Had to jettison and abort":       {"result": "failure", "front_shift": 0.05},
            },
        },
    ],
    "anti-ship": [
        {
            "key": "ship_damage",
            "question": "How did the anti-ship strike go?",
            "options": ["Sank the target ship", "Hit it — smoking but still afloat", "Missile missed or was defeated by CIWS", "Couldn't get in range / had to abort"],
            "effects": {
                "Sank the target ship":                      {"result": "success", "red_air_attrition": 0.05},
                "Hit it — smoking but still afloat":         {"result": "partial", "red_air_attrition": 0.02},
                "Missile missed or was defeated by CIWS":    {"result": "partial"},
                "Couldn't get in range / had to abort":      {"result": "failure", "blue_air_attrition": 0.05},
            },
        },
        {
            "key": "air_threats_naval",
            "question": "Did you encounter enemy air resistance?",
            "options": ["No fighters — clear skies", "Some CAP but escorts handled them", "Had to defend myself — dropped ordnance", "Heavy air opposition"],
            "effects": {
                "No fighters — clear skies":                  {"red_air_attrition": 0.05},
                "Some CAP but escorts handled them":          {"red_air_attrition": 0.10, "blue_air_attrition": 0.03},
                "Had to defend myself — dropped ordnance":    {"red_air_attrition": 0.03, "blue_air_attrition": 0.08},
                "Heavy air opposition":                       {"red_air_attrition": 0.05, "blue_air_attrition": 0.15},
            },
        },
    ],
    "escort": [
        {
            "key": "package_status",
            "question": "Did the strike package make it to the target?",
            "options": ["Package delivered ordnance on target", "Most got through — lost one striker", "Half the package turned back", "Package was scattered — mission failed"],
            "effects": {
                "Package delivered ordnance on target":  {"result": "success", "front_shift": -0.08, "red_air_attrition": 0.08},
                "Most got through — lost one striker":   {"result": "success", "blue_air_attrition": 0.08, "red_air_attrition": 0.05},
                "Half the package turned back":          {"result": "partial", "blue_air_attrition": 0.12},
                "Package was scattered — mission failed": {"result": "failure", "blue_air_attrition": 0.18},
            },
        },
    ],
    "convoy_attack": [
        {
            "key": "convoy_damage",
            "question": "How much of the convoy did you destroy?",
            "options": ["Wiped it out — nothing left moving", "Got most of the trucks, escort survived", "Hit a few vehicles but most got through", "Couldn't find it / had to abort"],
            "effects": {
                "Wiped it out — nothing left moving":       {"result": "success", "front_shift": -0.12, "red_air_attrition": 0.03},
                "Got most of the trucks, escort survived":  {"result": "success", "front_shift": -0.06},
                "Hit a few vehicles but most got through":  {"result": "partial", "front_shift": -0.02},
                "Couldn't find it / had to abort":          {"result": "failure", "blue_air_attrition": 0.05},
            },
        },
        {
            "key": "convoy_threats",
            "question": "How was the convoy's air defense?",
            "options": ["No threat — easy pickings", "Shilkas lit me up but no hits", "Took AAA damage", "SHORAD was deadly — barely survived"],
            "effects": {
                "No threat — easy pickings":               {},
                "Shilkas lit me up but no hits":           {"blue_air_attrition": 0.02},
                "Took AAA damage":                        {"blue_air_attrition": 0.08},
                "SHORAD was deadly — barely survived":    {"blue_air_attrition": 0.15},
            },
        },
    ],
    "convoy_defense": [
        {
            "key": "convoy_survived",
            "question": "Did the convoy make it through?",
            "options": ["All trucks arrived safely", "Lost a couple vehicles but most made it", "Convoy took heavy losses", "Convoy was destroyed"],
            "effects": {
                "All trucks arrived safely":              {"result": "success", "front_shift": -0.08},
                "Lost a couple vehicles but most made it": {"result": "success", "front_shift": -0.03},
                "Convoy took heavy losses":               {"result": "partial", "front_shift": 0.05, "blue_air_attrition": 0.05},
                "Convoy was destroyed":                   {"result": "failure", "front_shift": 0.12, "blue_air_attrition": 0.10},
            },
        },
        {
            "key": "enemy_attackers",
            "question": "How many enemy strike aircraft got through to the convoy?",
            "options": ["None — intercepted them all", "One or two slipped past", "Most of them got attack runs in", "Couldn't stop them"],
            "effects": {
                "None — intercepted them all":           {"red_air_attrition": 0.15},
                "One or two slipped past":               {"red_air_attrition": 0.08, "blue_air_attrition": 0.03},
                "Most of them got attack runs in":       {"red_air_attrition": 0.03, "blue_air_attrition": 0.08},
                "Couldn't stop them":                    {"red_air_attrition": 0.01, "blue_air_attrition": 0.15},
            },
        },
    ],
    # Fallback for types not listed above
    "_default": [
        {
            "key": "overall",
            "question": "How did the mission go overall?",
            "options": ["Nailed it", "Decent — got most objectives", "Rough — barely made it back", "Total disaster"],
            "effects": {
                "Nailed it":                         {"result": "success", "red_air_attrition": 0.10, "blue_air_attrition": 0.03},
                "Decent — got most objectives":      {"result": "partial", "red_air_attrition": 0.05, "blue_air_attrition": 0.05},
                "Rough — barely made it back":       {"result": "partial", "red_air_attrition": 0.03, "blue_air_attrition": 0.12},
                "Total disaster":                    {"result": "failure", "red_air_attrition": 0.01, "blue_air_attrition": 0.20},
            },
        },
    ],
}


class CampaignState:
    """Tracks persistent state across chained missions."""

    def __init__(self, base_plan: dict, num_missions: int = 3):
        self.base_plan = copy.deepcopy(base_plan)
        self.num_missions = num_missions
        self.current_mission = 0

        # Persistent state
        self.destroyed_sams: list[str] = []
        self.front_line_shift = 0.0       # negative = blue advancing, positive = red advancing
        self.blue_attrition = 0.0         # 0.0 to 1.0
        self.red_attrition = 0.0
        self.escalation_level = 0         # 0=normal, 1=reinforced, 2=heavy
        self.mission_results: list[dict] = []
        self.campaign_name = ""
        self.last_mission_type = ""

    def to_dict(self) -> dict:
        return {
            "base_plan": self.base_plan,
            "num_missions": self.num_missions,
            "current_mission": self.current_mission,
            "destroyed_sams": self.destroyed_sams,
            "front_line_shift": self.front_line_shift,
            "blue_attrition": self.blue_attrition,
            "red_attrition": self.red_attrition,
            "escalation_level": self.escalation_level,
            "mission_results": self.mission_results,
            "campaign_name": self.campaign_name,
            "last_mission_type": self.last_mission_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CampaignState":
        state = cls(data["base_plan"], data["num_missions"])
        state.current_mission = data.get("current_mission", 0)
        state.destroyed_sams = data.get("destroyed_sams", [])
        state.front_line_shift = data.get("front_line_shift", 0.0)
        state.blue_attrition = data.get("blue_attrition", 0.0)
        state.red_attrition = data.get("red_attrition", 0.0)
        state.escalation_level = data.get("escalation_level", 0)
        state.mission_results = data.get("mission_results", [])
        state.campaign_name = data.get("campaign_name", "")
        state.last_mission_type = data.get("last_mission_type", "")
        return state

    def save(self, path: str | Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "CampaignState":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def is_complete(self) -> bool:
        return self.current_mission >= self.num_missions

    def needs_debrief(self) -> bool:
        """True if we've generated a mission but haven't debriefed yet."""
        return self.current_mission > len(self.mission_results)

    def summary(self) -> str:
        """Human-readable campaign status."""
        lines = []
        lines.append(f"  Campaign: {self.campaign_name}")
        lines.append(f"  Progress: Mission {self.current_mission}/{self.num_missions}")

        if self.front_line_shift < -0.2:
            lines.append(f"  Front Line: Blue pushing deep into enemy territory")
        elif self.front_line_shift < -0.05:
            lines.append(f"  Front Line: Blue gaining ground")
        elif self.front_line_shift > 0.15:
            lines.append(f"  Front Line: Red counterattacking — under pressure")
        else:
            lines.append(f"  Front Line: Contested")

        if self.red_attrition > 0.3:
            lines.append(f"  Enemy Status: Weakened (attrition {self.red_attrition:.0%})")
        elif self.red_attrition > 0.1:
            lines.append(f"  Enemy Status: Degraded")
        else:
            lines.append(f"  Enemy Status: Full strength")

        if self.blue_attrition > 0.3:
            lines.append(f"  Friendly Status: Taking losses (attrition {self.blue_attrition:.0%})")
        elif self.blue_attrition > 0.1:
            lines.append(f"  Friendly Status: Some losses")
        else:
            lines.append(f"  Friendly Status: Strong")

        if self.destroyed_sams:
            lines.append(f"  SAMs Destroyed: {len(self.destroyed_sams)} ({', '.join(self.destroyed_sams)})")

        if self.escalation_level > 0:
            lines.append(f"  Enemy Escalation: Level {self.escalation_level} — reinforcements active")

        for mr in self.mission_results:
            lines.append(f"    Mission {mr['mission']}: {mr['result'].upper()}")

        return "\n".join(lines)


class CampaignGenerator:
    """Generates chained missions with interactive debrief between each."""

    CAMPAIGN_PROGRESSIONS = {
        "air_superiority": [
            {"type": "SEAD", "desc": "Soften enemy air defenses"},
            {"type": "CAP", "desc": "Establish air superiority"},
            {"type": "strike", "desc": "Strike enemy infrastructure"},
            {"type": "CAS", "desc": "Support ground offensive"},
            {"type": "escort", "desc": "Escort final push"},
        ],
        "ground_offensive": [
            {"type": "SEAD", "desc": "Destroy forward SAM coverage"},
            {"type": "CAS", "desc": "Soften enemy front line positions"},
            {"type": "strike", "desc": "Hit enemy supply lines"},
            {"type": "CAS", "desc": "Support breakthrough"},
            {"type": "CAP", "desc": "Defend captured territory"},
        ],
        "deep_strike": [
            {"type": "CAP", "desc": "Gain local air superiority"},
            {"type": "SEAD", "desc": "Suppress route air defenses"},
            {"type": "strike", "desc": "Deep strike on strategic target"},
            {"type": "escort", "desc": "Escort second strike wave"},
            {"type": "CAP", "desc": "Cover withdrawal"},
        ],
    }

    def __init__(self, state: CampaignState):
        self.state = state

    def get_next_mission_plan(self) -> dict | None:
        """Generate the next mission plan with cumulative state applied."""
        if self.state.is_complete():
            return None

        mission_num = self.state.current_mission
        plan = copy.deepcopy(self.state.base_plan)

        # Determine mission type from progression
        progression = self._pick_progression(plan)
        if mission_num < len(progression):
            step = progression[mission_num]
            plan["mission_type"] = step["type"]
            plan["_campaign_desc"] = step["desc"]

        self.state.last_mission_type = plan.get("mission_type", "SEAD")

        # Apply cumulative state from previous debriefs
        plan = self._apply_destroyed_sams(plan)
        plan = self._apply_front_line_shift(plan)
        plan = self._apply_attrition(plan)
        plan = self._apply_escalation(plan)

        # Tag with campaign metadata
        plan["_campaign_mission_num"] = mission_num + 1
        plan["_campaign_total"] = self.state.num_missions
        plan["_campaign_name"] = self.state.campaign_name

        return plan

    def get_debrief_questions(self) -> list[dict]:
        """Get the debrief questions for the most recently generated mission type."""
        mt = self.state.last_mission_type
        questions = DEBRIEF_QUESTIONS.get(mt, DEBRIEF_QUESTIONS["_default"])
        return questions

    def apply_debrief(self, answers: dict[str, dict]):
        """
        Apply debrief answers to campaign state.

        Args:
            answers: dict mapping question key to the chosen effect dict
                     e.g. {"sams_killed": {"sams_destroyed": "all", "result": "success"},
                           "air_threats": {"red_air_attrition": 0.20, ...}}
        """
        mission_num = self.state.current_mission
        overall_result = "partial"  # default

        for key, effects in answers.items():
            # Track overall result
            if "result" in effects:
                r = effects["result"]
                # Worst result wins (failure > partial > success)
                if r == "failure":
                    overall_result = "failure"
                elif r == "success" and overall_result != "failure":
                    overall_result = "success"

            # SAM destruction
            sams_destroyed = effects.get("sams_destroyed", "")
            if sams_destroyed:
                plan_sams = self.state.base_plan.get("enemy_sam_sites", [])
                if sams_destroyed == "all":
                    for s in plan_sams:
                        self.state.destroyed_sams.append(s.get("type", "SA-6"))
                elif sams_destroyed == "most":
                    for s in plan_sams[:-1]:  # All but last
                        self.state.destroyed_sams.append(s.get("type", "SA-6"))
                elif sams_destroyed == "some":
                    if plan_sams:
                        self.state.destroyed_sams.append(plan_sams[0].get("type", "SA-6"))

            # Air attrition
            if "red_air_attrition" in effects:
                self.state.red_attrition = min(0.85, self.state.red_attrition + effects["red_air_attrition"])
            if "blue_air_attrition" in effects:
                self.state.blue_attrition = min(0.85, self.state.blue_attrition + effects["blue_air_attrition"])

            # Front line shift
            if "front_shift" in effects:
                self.state.front_line_shift += effects["front_shift"]

            # Ground attrition
            if "blue_ground_attrition" in effects:
                self.state.blue_attrition = min(0.85, self.state.blue_attrition + effects["blue_ground_attrition"] * 0.5)

        # Record result
        self.state.mission_results.append({
            "mission": mission_num + 1,
            "result": overall_result,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

        # Escalation over time regardless of result
        if mission_num >= 2:
            self.state.escalation_level = max(self.state.escalation_level, 1)
        if mission_num >= 4:
            self.state.escalation_level = max(self.state.escalation_level, 2)

        # Advance to next mission
        self.state.current_mission += 1

    def _pick_progression(self, plan: dict) -> list:
        mt = plan.get("mission_type", "SEAD")
        if mt in ("SEAD", "strike"):
            return self.CAMPAIGN_PROGRESSIONS["air_superiority"]
        elif mt == "CAS":
            return self.CAMPAIGN_PROGRESSIONS["ground_offensive"]
        else:
            return self.CAMPAIGN_PROGRESSIONS["deep_strike"]

    def _apply_destroyed_sams(self, plan: dict) -> dict:
        sam_sites = plan.get("enemy_sam_sites", [])
        destroyed_copy = list(self.state.destroyed_sams)
        remaining = []
        for site in sam_sites:
            if site.get("type") in destroyed_copy:
                destroyed_copy.remove(site["type"])
                continue
            remaining.append(site)

        # Enemy reinforces if too many destroyed
        if self.state.escalation_level >= 1 and len(remaining) < 2:
            remaining.append({
                "type": random.choice(["SA-6", "SA-8", "SA-11"]),
                "location_desc": "reinforcement position",
            })

        plan["enemy_sam_sites"] = remaining
        return plan

    def _apply_front_line_shift(self, plan: dict) -> dict:
        gw = plan.get("ground_war", {})
        if not gw.get("enabled"):
            return plan

        shift = self.state.front_line_shift

        if shift < -0.3:
            gw["front_line_desc"] = "Blue forces have pushed deep into enemy territory"
            gw["blue_advancing"] = True
            gw["red_advancing"] = False
        elif shift < -0.1:
            gw["front_line_desc"] = "Blue gaining ground — front line shifting forward"
            gw["blue_advancing"] = True
            gw["red_advancing"] = True
        elif shift > 0.2:
            gw["front_line_desc"] = "Red counterattack — friendly forces under pressure"
            gw["blue_advancing"] = False
            gw["red_advancing"] = True
        else:
            gw["front_line_desc"] = "Front line contested — both sides fighting"

        plan["ground_war"] = gw
        return plan

    def _apply_attrition(self, plan: dict) -> dict:
        for flight in plan.get("enemy_air", []):
            base = flight.get("count", 2)
            flight["count"] = max(1, round(base * (1.0 - self.state.red_attrition * 0.5)))

        for flight in plan.get("friendly_flights", []):
            base = flight.get("count", 2)
            flight["count"] = max(1, round(base * (1.0 - self.state.blue_attrition * 0.4)))

        return plan

    def _apply_escalation(self, plan: dict) -> dict:
        enemy_air = plan.get("enemy_air", [])

        if self.state.escalation_level >= 1:
            enemy_air.append({
                "aircraft": random.choice(["MiG-29S", "Su-27"]),
                "task": "CAP",
                "count": 2,
            })

        if self.state.escalation_level >= 2:
            enemy_air.append({
                "aircraft": "MiG-31",
                "task": "intercept",
                "count": 2,
            })
            sams = plan.get("enemy_sam_sites", [])
            sams.append({
                "type": "SA-10",
                "location_desc": "strategic reserve deployment",
            })

        plan["enemy_air"] = enemy_air
        return plan


def parse_campaign_request(description: str) -> tuple[int, str]:
    """
    Check if a description is requesting a campaign/chain.
    Returns (num_missions, cleaned_description).
    If not a campaign request, returns (0, original_description).
    """
    import re
    desc_lower = description.lower()

    campaign_keywords = [
        "campaign", "chain", "linked missions", "mission chain",
        "series", "connected missions", "multi-mission",
    ]

    is_campaign = any(kw in desc_lower for kw in campaign_keywords)
    if not is_campaign:
        return 0, description

    num_match = re.search(r'(\d+)\s*(?:mission|sortie|flight)', desc_lower)
    if num_match:
        num = int(num_match.group(1))
        num = max(2, min(10, num))
    else:
        num = 3

    cleaned = description
    for kw in campaign_keywords:
        cleaned = re.sub(re.escape(kw), "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\d+\s*(?:mission|sortie|flight)s?', "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip(" .,;-")

    return num, cleaned


def find_active_campaign(output_dir: Path) -> Path | None:
    """Find the most recent incomplete campaign state file."""
    state_files = sorted(output_dir.glob("*_state.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for sf in state_files:
        try:
            state = CampaignState.load(sf)
            if not state.is_complete():
                return sf
        except (json.JSONDecodeError, KeyError):
            continue
    return None

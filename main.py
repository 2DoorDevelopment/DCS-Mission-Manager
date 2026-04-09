#!/usr/bin/env python3
"""
DCS World Mission Generator v2.0
Generate realistic .miz mission files from natural language descriptions.
Features: Random threat placement, convoy missions, AI loadouts, difficulty scaling,
          mission chaining/campaigns, DCS auto-detect, unique operation names.
"""

import sys
import os
import json
import time
from pathlib import Path

from src.llm.ollama_client import OllamaClient
from src.llm.mission_parser import MissionParser
from src.generators.mission_builder import MissionBuilder
from src.generators.lua_generator import LuaGenerator
from src.generators.miz_packager import MizPackager
from src.generators.briefing_generator import BriefingGenerator
from src.maps import MAP_REGISTRY
from src.naming import generate_mission_name, generate_campaign_name, generate_filename
from src.difficulty import scale_plan
from src.campaign import (
    CampaignState, CampaignGenerator, parse_campaign_request,
    find_active_campaign,
)
from src.dcs_detect import find_dcs_missions_folder, deploy_mission, deploy_briefing
from src.custom_mods import load_custom_aircraft, register_custom_aircraft, ensure_custom_dir
from src.validator import validate_mission
from src.history import record_mission, display_history

OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║           DCS WORLD MISSION GENERATOR v2.0                  ║
║     Natural Language → .miz Mission Files                   ║
╠══════════════════════════════════════════════════════════════╣
║  Maps: Caucasus, Syria, Cold War Germany                     ║
║  Modules: F-16C, F/A-18C, A-10C II, JF-17                   ║
║  NEW: Convoys, Campaigns, Difficulty Scaling, Auto-Deploy    ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Commands:
  (just type)     - Describe a mission in plain English
  quick <desc>    - Skip confirmation, generate instantly
  maps            - List available maps and airfields
  examples        - Show example mission descriptions
  history         - View your generated mission log
  campaign        - Resume an in-progress campaign
  settings        - View current settings
  quit / exit     - Exit the generator

Mission types:
  SEAD, CAS, CAP, Strike, Anti-Ship, Escort
  Convoy Attack   - Interdict enemy supply convoy
  Convoy Defense  - Protect friendly supply convoy

Campaign mode (generates linked missions with debrief between each):
  "3 mission SEAD campaign on Caucasus in the F-16"
  After flying, type "next mission" to debrief and generate the next

Quick mode:
  "quick SEAD F-16 Caucasus"    - Instant generation, no questions

Difficulty (add to any description):
  easy / medium / hard
"""

EXAMPLES = [
    "SEAD mission in the F-16 on Caucasus with SA-6 and SA-11 sites and enemy CAP",
    "A-10C CAS on Syria, friendly armor pushing north, SEAD goes first. Hard difficulty.",
    "F-18 convoy attack on Caucasus. Hit the enemy supply line.",
    "JF-17 convoy defense on Syria. Protect our supply trucks from enemy air.",
    "3 mission campaign: F-16 SEAD on Caucasus, medium difficulty",
    "5 mission chain starting with CAS in the A-10 on Syria, easy",
    "Large scale air war on Cold War Germany. F-16 SEAD. Hard. Full ground war.",
    "Simple F-16 vs 2 MiG-29s dogfight over Caucasus. Easy.",
]


def print_banner():
    print(BANNER)


def check_ollama_connection(client: OllamaClient) -> bool:
    print("  Checking Ollama connection...", end=" ", flush=True)
    if client.check_connection():
        print("OK")
        return True
    else:
        print("FAILED")
        print("\n  Running in offline mode — rule-based parsing active.")
        print("  Start Ollama for full NL support: ollama serve\n")
        return False


def display_mission_plan(plan: dict):
    op_name = plan.get("_operation_name", "")
    campaign_info = ""
    if plan.get("_campaign_mission_num"):
        campaign_info = f" (Mission {plan['_campaign_mission_num']}/{plan['_campaign_total']})"

    print("\n" + "=" * 60)
    if op_name:
        print(f"  {op_name}{campaign_info}")
    print("  MISSION PLAN SUMMARY")
    print("=" * 60)

    print(f"\n  Map:          {plan.get('map_name', 'Unknown')}")
    print(f"  Player:       {plan.get('player_aircraft', 'Unknown')}")
    print(f"  Mission Type: {plan.get('mission_type', 'Unknown')}")
    print(f"  Departure:    {plan.get('player_airfield', 'Unknown')}")
    print(f"  Difficulty:   {plan.get('difficulty', 'medium').upper()}")
    print(f"  Time of Day:  {plan.get('time_of_day', 'Morning')}")
    print(f"  Weather:      {plan.get('weather', 'Clear')}")

    friendly = plan.get("friendly_flights", [])
    if friendly:
        print(f"\n  Friendly Package ({len(friendly)} flights):")
        for f in friendly:
            print(f"    - {f.get('task', '?')}: {f.get('count', 1)}x {f.get('aircraft', '?')}")

    enemies_air = plan.get("enemy_air", [])
    enemies_sam = plan.get("enemy_sam_sites", [])

    if enemies_air:
        print(f"\n  Enemy Air ({len(enemies_air)} groups):")
        for e in enemies_air:
            skill = e.get("skill", "")
            skill_str = f" [{skill}]" if skill else ""
            print(f"    - {e.get('task', 'CAP')}: {e.get('count', 2)}x {e.get('aircraft', '?')}{skill_str}")

    if enemies_sam:
        print(f"\n  Enemy SAM Sites ({len(enemies_sam)}):")
        for s in enemies_sam:
            print(f"    - {s.get('type', '?')} near {s.get('location_desc', 'auto')}")

    if plan.get("_shorad_escort"):
        print(f"    + SHORAD escorts on SAM sites")

    ground_war = plan.get("ground_war", {})
    if ground_war.get("enabled"):
        print(f"\n  Ground War:   ACTIVE ({ground_war.get('intensity', 'medium').upper()})")
        if ground_war.get("front_line_desc"):
            print(f"    {ground_war['front_line_desc']}")

    objectives = plan.get("objectives", [])
    if objectives:
        print(f"\n  Objectives:")
        for i, obj in enumerate(objectives, 1):
            print(f"    {i}. {obj}")

    print("\n" + "=" * 60)


def build_and_save_mission(plan: dict, skip_prompts: bool = False) -> tuple:
    """Build mission from plan, return (miz_path, briefing_path) or (None, None)."""
    try:
        # Apply difficulty scaling
        print("  Applying difficulty scaling...")
        scaled_plan = scale_plan(plan)

        # Build mission
        print("  Building mission structure...")
        builder = MissionBuilder(scaled_plan)
        mission_data = builder.build()

        # Validate before packaging
        print("\n  Running pre-flight checks...")
        validation = validate_mission(mission_data, scaled_plan)
        print(validation.summary())

        if not validation.passed:
            if skip_prompts:
                print("  Validation errors found — continuing anyway (quick mode)...")
            else:
                print("\n  Mission has validation errors (listed above).")
                print("  These may cause DCS to reject or break the mission.")
                print("  Continue anyway? (y/n): ", end="", flush=True)
                try:
                    if input().strip().lower() != "y":
                        print("  Generation cancelled.")
                        return None, None
                    print("  Continuing despite errors...")
                except EOFError:
                    return None, None
        elif validation.warnings and not skip_prompts:
            print("\n  Mission has warnings (listed above).")
            print("  These probably won't break anything but worth knowing.")
            print("  Continue? (y/n): ", end="", flush=True)
            try:
                if input().strip().lower() != "y":
                    print("  Generation cancelled.")
                    return None, None
            except EOFError:
                return None, None

        # Generate Lua
        print("  Generating Lua files...")
        lua_gen = LuaGenerator(mission_data)
        lua_files = lua_gen.generate_all()

        # Generate briefing
        print("  Generating kneeboard briefing...")
        briefing_gen = BriefingGenerator(mission_data, scaled_plan)
        briefing_text = briefing_gen.generate()

        # Generate unique filename
        op_name = plan.get("_operation_name", "Mission")
        filename = generate_filename(
            plan.get("mission_type", "mission"),
            plan.get("map_name", "unknown"),
            op_name,
        )
        output_path = OUTPUT_DIR / filename

        # Package .miz
        print("  Packaging .miz file...")
        packager = MizPackager()
        packager.package(lua_files, briefing_text, str(output_path))

        # Save briefing
        briefing_path = output_path.with_suffix(".txt")
        with open(briefing_path, "w", encoding="utf-8") as f:
            f.write(briefing_text)

        print(f"\n  ✓ {op_name}")
        print(f"  ✓ Saved: {output_path.name}")

        # Record to history
        record_mission(OUTPUT_DIR, plan, output_path.name)

        # Auto-deploy to DCS
        dcs_folder = find_dcs_missions_folder()
        if dcs_folder:
            deployed = deploy_mission(output_path, dcs_folder)
            if deployed:
                print(f"  ✓ Auto-deployed to: {deployed}")
                deploy_briefing(briefing_path, dcs_folder)
            else:
                print(f"  ⚠ Auto-deploy failed. Copy manually from output/")
        else:
            print(f"  ℹ DCS not detected. Copy .miz to your Missions folder.")

        return output_path, briefing_path

    except KeyError as e:
        print(f"\n  ERROR: Missing data field: {e}")
        print(f"  This usually means a map or aircraft database is incomplete.")
        print(f"  Check your custom_aircraft JSON if using a mod.")
        return None, None
    except (OSError, IOError) as e:
        print(f"\n  ERROR: File system error: {e}")
        print(f"  Check that the output directory is writable.")
        return None, None
    except Exception as e:
        print(f"\n  ERROR: Unexpected error during generation: {e}")
        print(f"  Please report this bug. Details:")
        import traceback
        traceback.print_exc()
        return None, None


def run_single_mission(description: str, client: OllamaClient):
    """Generate a single mission."""
    parser = MissionParser(client)

    print("\n  Parsing mission description...")
    mission_plan = parser.parse_description(description)

    if not mission_plan:
        print("  ERROR: Failed to parse. Try rephrasing.")
        return

    # Generate unique operation name
    op_name = generate_mission_name(mission_plan.get("mission_type", "general"))
    mission_plan["_operation_name"] = op_name

    display_mission_plan(mission_plan)

    print("\n  Does this look good? (y/n/edit): ", end="", flush=True)
    response = input().strip().lower()

    if response == "n":
        print("  Mission cancelled.")
        return
    elif response == "edit":
        print("  Describe changes: ", end="", flush=True)
        changes = input().strip()
        print("  Applying changes...")
        mission_plan = parser.refine_plan(mission_plan, changes)
        if not mission_plan:
            print("  ERROR: Failed to apply changes.")
            return
        mission_plan["_operation_name"] = op_name
        display_mission_plan(mission_plan)
        print("\n  Proceed? (y/n): ", end="", flush=True)
        if input().strip().lower() != "y":
            print("  Mission cancelled.")
            return

    build_and_save_mission(mission_plan)


def run_campaign_start(description: str, num_missions: int, client: OllamaClient):
    """Start a new campaign — generates only mission 1."""
    parser = MissionParser(client)

    print(f"\n  Parsing campaign base mission ({num_missions} missions)...")
    base_plan = parser.parse_description(description)

    if not base_plan:
        print("  ERROR: Failed to parse. Try rephrasing.")
        return

    campaign_name = generate_campaign_name(base_plan.get("map_name", ""))
    state = CampaignState(base_plan, num_missions)
    state.campaign_name = campaign_name

    gen = CampaignGenerator(state)
    progression = gen._pick_progression(base_plan)

    print(f"\n  ═══ {campaign_name} ═══")
    print(f"  {num_missions} missions, {base_plan.get('map_name', '?')} theater")
    print(f"  Aircraft: {base_plan.get('player_aircraft', '?')}")
    print(f"  Difficulty: {base_plan.get('difficulty', 'medium').upper()}")
    print(f"\n  Campaign progression:")
    for i in range(min(num_missions, len(progression))):
        step = progression[i]
        print(f"    Mission {i+1}: {step['type'].upper()} — {step['desc']}")

    print(f"\n  Generate Mission 1? (y/n): ", end="", flush=True)
    if input().strip().lower() != "y":
        print("  Campaign cancelled.")
        return

    # Generate mission 1
    _generate_campaign_mission(state, gen)


def run_campaign_resume():
    """Resume an active campaign — debrief last mission, then generate next."""
    state_path = find_active_campaign(OUTPUT_DIR)
    if not state_path:
        print("\n  No active campaign found.")
        print("  Start one with: \"3 mission SEAD campaign on Caucasus in the F-16\"")
        return

    state = CampaignState.load(state_path)
    gen = CampaignGenerator(state)

    print(f"\n  ═══ Resuming: {state.campaign_name} ═══")
    print(state.summary())

    if state.is_complete():
        print(f"\n  Campaign complete! All {state.num_missions} missions generated.")
        return

    # If we need a debrief (mission was generated but not debriefed)
    if state.needs_debrief():
        print(f"\n  ── DEBRIEF: Mission {state.current_mission} ──")
        print(f"  You just flew: {state.last_mission_type.upper()}")
        print(f"  Tell me how it went.\n")

        _run_debrief(state, gen)

        # Save state after debrief
        state.save(state_path)

        print(f"\n  ── Updated Campaign Status ──")
        print(state.summary())

        if state.is_complete():
            print(f"\n  ═══ CAMPAIGN COMPLETE ═══")
            print(f"  {state.campaign_name} finished in {state.num_missions} missions.")
            return

    # Generate next mission
    print(f"\n  Ready to generate Mission {state.current_mission + 1}/{state.num_missions}.")
    print(f"  Generate it now? (y/n): ", end="", flush=True)
    if input().strip().lower() != "y":
        print("  Come back anytime with 'campaign' or 'next mission'.")
        return

    _generate_campaign_mission(state, gen, state_path)


def _run_debrief(state: CampaignState, gen: CampaignGenerator):
    """Ask debrief questions and apply answers to campaign state."""
    questions = gen.get_debrief_questions()
    all_answers = {}

    for q in questions:
        print(f"  {q['question']}")
        options = q["options"]
        for i, opt in enumerate(options, 1):
            print(f"    {i}. {opt}")

        while True:
            print(f"  Choice (1-{len(options)}): ", end="", flush=True)
            try:
                choice = int(input().strip())
                if 1 <= choice <= len(options):
                    chosen = options[choice - 1]
                    effects = q["effects"][chosen]
                    all_answers[q["key"]] = effects
                    print(f"  → {chosen}\n")
                    break
            except (ValueError, IndexError):
                pass
            print(f"  Enter a number 1-{len(options)}")

    gen.apply_debrief(all_answers)

    # Show immediate impact
    last_result = state.mission_results[-1] if state.mission_results else {}
    result_str = last_result.get("result", "?").upper()
    print(f"  Mission result: {result_str}")


def _generate_campaign_mission(state: CampaignState, gen: CampaignGenerator,
                                state_path: Path | None = None):
    """Generate the next mission in a campaign."""
    mission_num = state.current_mission + 1

    print(f"\n  ── GENERATING MISSION {mission_num}/{state.num_missions} ──")

    plan = gen.get_next_mission_plan()
    if plan is None:
        print("  Campaign complete — no more missions.")
        return

    op_name = generate_mission_name(plan.get("mission_type", "general"))
    plan["_operation_name"] = op_name

    display_mission_plan(plan)

    miz_path, _ = build_and_save_mission(plan, skip_prompts=True)

    # Save campaign state (mission generated, awaiting debrief)
    if state_path is None:
        safe_name = state.campaign_name.replace(" ", "_")
        state_path = OUTPUT_DIR / f"{safe_name}_state.json"
    state.save(state_path)

    print(f"\n  Go fly Mission {mission_num}!")
    print(f"  When you're done, come back and type 'campaign' or 'next mission'")
    print(f"  to debrief and generate the next one.")


def run_quick_mission(description: str, client: OllamaClient):
    """Quick mode — skip confirmation, generate instantly."""
    parser = MissionParser(client)
    print("\n  Quick mode — parsing and generating...")
    mission_plan = parser.parse_description(description)
    if not mission_plan:
        print("  ERROR: Failed to parse. Try rephrasing.")
        return
    op_name = generate_mission_name(mission_plan.get("mission_type", "general"))
    mission_plan["_operation_name"] = op_name
    build_and_save_mission(mission_plan, skip_prompts=True)


def run_generation(description: str, client: OllamaClient):
    """Route to single mission, quick, campaign start, or campaign resume."""
    desc_lower = description.lower().strip()

    # Check for campaign resume commands
    if desc_lower in ("campaign", "next mission", "next", "continue campaign",
                      "resume", "resume campaign", "debrief"):
        run_campaign_resume()
        return

    # Check for quick mode
    if desc_lower.startswith("quick "):
        run_quick_mission(description[6:], client)
        return

    # Check for new campaign request
    num_missions, cleaned_desc = parse_campaign_request(description)
    if num_missions > 0:
        run_campaign_start(cleaned_desc, num_missions, client)
    else:
        run_single_mission(description, client)


def show_maps():
    print("\n  Available Maps:\n")
    for map_id, map_data in MAP_REGISTRY.items():
        print(f"  {map_data['display_name']}")
        print(f"    Airfields ({len(map_data['airfields'])}):")
        for af in map_data["airfields"][:6]:
            side = af.get("default_coalition", "neutral")
            print(f"      - {af['name']} ({side})")
        if len(map_data["airfields"]) > 6:
            print(f"      ... and {len(map_data['airfields']) - 6} more")
        routes = map_data.get("convoy_routes", {})
        if routes:
            total = sum(len(v) for v in routes.values())
            print(f"    Convoy routes: {total}")
        print()


def main():
    print_banner()

    # Load custom aircraft mods
    custom_dir = ensure_custom_dir()
    custom_aircraft = load_custom_aircraft(custom_dir)
    if custom_aircraft:
        register_custom_aircraft(custom_aircraft)
        # Rebuild LLM prompt so it knows about new aircraft
        from src.llm.mission_parser import rebuild_system_prompt
        rebuild_system_prompt()

    client = OllamaClient(model="llama3.1:8b")
    check_ollama_connection(client)

    dcs_folder = find_dcs_missions_folder()
    if dcs_folder:
        print(f"  DCS Missions folder: {dcs_folder}")
    print(f"  Output directory: {OUTPUT_DIR.resolve()}")
    print(f"\n  Type 'help' for commands, 'examples' for ideas, or just describe a mission.\n")

    while True:
        try:
            print("  DCS-MG> ", end="", flush=True)
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("quit", "exit", "q"):
            print("  Goodbye!")
            break
        elif cmd in ("help", "h", "?"):
            print(HELP_TEXT)
        elif cmd == "maps":
            show_maps()
        elif cmd in ("examples", "ex"):
            print("\n  Example descriptions:\n")
            for i, ex in enumerate(EXAMPLES, 1):
                print(f"  {i}. \"{ex}\"")
            print()
        elif cmd in ("history", "log", "missions"):
            display_history(OUTPUT_DIR)
        elif cmd in ("settings", "config"):
            dcs_f = find_dcs_missions_folder()
            from src.units import PLAYER_AIRCRAFT
            mod_aircraft = [k for k, v in PLAYER_AIRCRAFT.items() if v.get("_is_mod")]
            print(f"\n  Ollama:    {client.model} @ {client.base_url}")
            print(f"  Output:    {OUTPUT_DIR.resolve()}")
            if dcs_f:
                print(f"  DCS Auto:  {dcs_f} ✓")
            else:
                print(f"  DCS Auto:  Not detected")
            print(f"  Aircraft:  F-16C, F/A-18C, A-10C, JF-17" +
                  (f", {', '.join(mod_aircraft)}" if mod_aircraft else ""))
            if mod_aircraft:
                print(f"  Mods:      {len(mod_aircraft)} loaded from custom_aircraft/")
            print(f"  Mod folder: {custom_dir.resolve()}")
            print()
        else:
            run_generation(user_input, client)


if __name__ == "__main__":
    main()

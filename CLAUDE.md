# DCS Mission Manager — Claude Context

## Project Overview

DCS Mission Generator v2.0 is a Python tool that generates realistic DCS World `.miz` mission files from plain-English descriptions. Users describe a mission (e.g., "SEAD mission in the F-16 on Caucasus with SA-11s") and the tool builds a complete, playable mission with waypoints, threat placement, friendly packages, briefings, and win/loss conditions.

**No external Python dependencies** — stdlib only, with optional Ollama (local LLM) for natural language parsing.

## Running the Project

```bash
# Console interface
python main.py

# Headless generation (no interactive prompt)
python main.py --generate "SEAD in the F-16 on Persian Gulf, hard"

# GUI interface (tkinter)
python gui.py

# Run tests
python -m pytest tests/ -v

# Build standalone Windows EXE
build_exe.bat
```

**Console commands:** `quick <desc>`, `maps`, `examples`, `history`, `campaign`, `settings`, `quit`

## Architecture

```
main.py              Console entry point
gui.py               GUI entry point (tkinter)
tests/
  test_smoke.py      22-test smoke suite (units, maps, builder, kneeboard)
src/
  generators/
    mission_builder.py    Core: plan → mission data structures
    lua_generator.py      Mission data → DCS Lua table files
    miz_packager.py       Lua files → .miz zip archive (incl. kneeboard PNG)
    briefing_generator.py 13-section tactical briefing generator
    kneeboard_generator.py Pure-stdlib PNG renderer for DCS kneeboard cards
  llm/
    ollama_client.py      Ollama REST API client
    mission_parser.py     Natural language → structured plan (LLM + fallback)
  maps/
    caucasus.py           Caucasus map
    syria.py              Syria map
    cold_war_germany.py   Cold War Germany map
    persian_gulf.py       Persian Gulf map (UAE, Iran, Strait of Hormuz)
    mariana_islands.py    Mariana Islands map (Guam, Saipan, Pacific carrier ops)
  units.py               Aircraft, SAM, ground unit databases
  difficulty.py          Easy/Medium/Hard scaling logic
  naming.py              Operation name generator
  callsigns.py           Callsign and frequency assignment
  flight_profile.py      Altitude/speed/fuel calculations
  mission_events.py      Radio messages, win/loss, reinforcements
  campaign.py            Campaign system with debrief logic
  custom_mods.py         JSON mod loader for custom aircraft
  dcs_detect.py          DCS install auto-detection and deploy
  validator.py           Pre-flight mission validation
  history.py             Mission log tracker (JSON)
custom_aircraft/         User-extensible aircraft mod configs (JSON)
```

## Key Concepts

- **Mission plan**: A structured dict produced by `mission_parser.py` from user input — contains aircraft, map, task type, difficulty, threat types, etc.
- **Mission builder**: `src/generators/mission_builder.py` takes a plan and produces DCS-ready data structures (waypoints, units, groups, etc.).
- **Lua generator + packager**: Converts data structures to DCS Lua tables, then zips them into a `.miz` file. The packager also renders a kneeboard PNG card and places it inside `KNEEBOARD/<aircraft_type>/` in the archive.
- **Custom aircraft**: Drop a JSON file in `custom_aircraft/` following `_template.json` to add modded aircraft without editing source.
- **Multiplayer**: Set `player_count` > 1 to generate co-op slots (slot 1 = `Player` skill, additional slots = `Client` skill for DCS multiplayer).

## Player Aircraft

F-16C Viper, F/A-18C Hornet, F-15C Eagle, F-15E Strike Eagle, AV-8B Harrier II, Mirage 2000C, A-10C II Thunderbolt, JF-17 Thunder, AH-64D Apache — plus any custom mods in `custom_aircraft/`.

## Maps

Caucasus, Syria, Cold War Germany, Persian Gulf, Mariana Islands.

## Mission Types

SEAD, CAS, CAP, Strike, Anti-Ship, Escort, Convoy Attack, Convoy Defense, CSAR, FAC(A).

## Code Style

- Python 3.10+, snake_case functions/variables, CamelCase classes
- Type hints used throughout (e.g., `str | None`, `list[dict]`)
- Module-level docstrings on all source files
- No linting or formatting tools are configured — follow existing style

## Testing

```bash
python -m pytest tests/ -v
```

22 smoke tests cover: unit registry, map registry, flight profiles, mission builder (incl. multiplayer slots), kneeboard PNG generation, naming, and difficulty scaling. Run these after any change to verify nothing is broken.

## Output

Generated `.miz` files are saved to the current directory (or auto-deployed to DCS Saved Games if DCS is detected). Each `.miz` includes an embedded kneeboard card PNG. `mission_history.json` is auto-created to log generated missions.

# DCS Mission Manager — Claude Context

## Project Overview

DCS Mission Generator v2.0 is a Python tool that generates realistic DCS World `.miz` mission files from plain-English descriptions. Users describe a mission (e.g., "SEAD mission in the F-16 on Caucasus with SA-11s") and the tool builds a complete, playable mission with waypoints, threat placement, friendly packages, briefings, and win/loss conditions.

**No external Python dependencies** — stdlib only, with optional Ollama (local LLM) for natural language parsing.

## Running the Project

```bash
# Console interface
python main.py

# GUI interface (tkinter)
python gui.py

# Build standalone Windows EXE
build_exe.bat
```

**Console commands:** `quick <desc>`, `maps`, `examples`, `history`, `campaign`, `settings`, `quit`

## Architecture

```
main.py              Console entry point
gui.py               GUI entry point (tkinter)
src/
  generators/
    mission_builder.py    Core: plan → mission data structures
    lua_generator.py      Mission data → DCS Lua table files
    miz_packager.py       Lua files → .miz zip archive
    briefing_generator.py 13-section tactical briefing generator
  llm/
    ollama_client.py      Ollama REST API client
    mission_parser.py     Natural language → structured plan (LLM + fallback)
  maps/
    caucasus.py           Caucasus map with airfields and SAM zones
    syria.py              Syria map
    cold_war_germany.py   Cold War Germany map
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
- **Lua generator + packager**: Converts data structures to DCS Lua tables, then zips them into a `.miz` file (DCS's mission format).
- **Custom aircraft**: Drop a JSON file in `custom_aircraft/` following `_template.json` to add modded aircraft without editing source.

## Code Style

- Python 3.10+, snake_case functions/variables, CamelCase classes
- Type hints used throughout (e.g., `str | None`, `list[dict]`)
- Module-level docstrings on all source files
- No linting or formatting tools are configured — follow existing style

## Testing

There is no automated test suite. Validate changes by running `python main.py` with example mission descriptions and confirming `.miz` output is generated correctly.

## Output

Generated `.miz` files are saved to the current directory (or auto-deployed to DCS Saved Games if DCS is detected). `mission_history.json` is auto-created to log generated missions.

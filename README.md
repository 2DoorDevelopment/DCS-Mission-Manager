# DCS World Mission Generator v2.0

Generate realistic DCS World `.miz` mission files from plain English descriptions. Describe what you want to fly, and the tool builds a complete mission with proper waypoints, enemy threats, friendly package, realistic briefing, and win/loss conditions — ready to load directly in DCS.

## Quick Start

```
cd dcs-mission-gen
python main.py
DCS-MG> SEAD mission in the F-16 on Caucasus with SA-11s. Hard difficulty.
```

Or use the GUI:
```
python gui.py
```

Or build a standalone exe (see below).

## Requirements

- **Python 3.10+**
- **Ollama** (optional but recommended) with `llama3.1:8b` for natural language parsing
- No additional Python packages needed — stdlib only

Without Ollama, the tool uses a rule-based parser that handles straightforward descriptions. With Ollama, you get smarter parsing that understands context and nuance.

## Features

### Mission Types
- **SEAD / DEAD** — Destroy enemy SAM sites
- **CAS** — Close air support for friendly ground forces
- **CAP** — Combat air patrol / air superiority
- **Strike** — Precision strike on high-value targets
- **Anti-Ship** — Naval strike with standoff weapons
- **Escort** — Protect friendly strike package
- **Convoy Attack** — Interdict enemy supply convoy
- **Convoy Defense** — Protect friendly convoy from enemy air

### Player Aircraft
- F-16C Viper
- F/A-18C Hornet
- A-10C II Thunderbolt
- JF-17 Thunder
- F-22A Raptor (mod — included)
- Any additional mods you add (see Custom Aircraft below)

### Maps
- Caucasus (Georgia / Abkhazia / Russia)
- Syria (Turkey / Syria / Israel / Cyprus)
- Cold War Germany (Fulda Gap / NATO vs Warsaw Pact)

### Difficulty Scaling
- **Easy** — Weaker enemies (Average skill), downgraded SAMs (SA-11→SA-6), more friendly flights, extra friendly CAP
- **Medium** — Balanced (default)
- **Hard** — Elite AI (Excellent skill), upgraded SAMs (SA-6→SA-11), SA-10 additions, SHORAD escorts on SAM sites, MiG-31 interceptors, fewer friendly flights

### Flight Profiles
Each aircraft has a realistic performance profile. The F-16 cruises at FL250/450kts, the A-10 at FL150/250kts, the F-22 at FL330/520kts. Mission type shapes the altitude plan — SEAD stays medium for HARM employment, CAS descends for attack passes, anti-ship comes in sea-skimming. Weather automatically adjusts profiles below cloud ceilings.

### Callsigns & Frequencies
Every flight gets a unique callsign from role-appropriate pools (SEAD flights get "Weasel", "Magnum"; escorts get "Guardian", "Shield"; enemies get "Bandit", "Flanker"). Each flight gets a unique radio frequency on the comms card.

### Living Battlefield
- Ground forces on both sides advance toward each other with waypoints
- Enemy air flies CAP orbits and intercepts
- Timed reinforcement waves (randomized timing and composition)
- Enemy density scales with difficulty

### Mission Briefing
Full 13-section tactical briefing covering:
1. **Situation** — Why you're flying this mission
2. **Mission** — Your specific objectives
3. **Execution** — Flight profile, altitude/speed plan, mission timeline
4. **Rules of Engagement** — What you can shoot and when
5. **SPINS** — Bingo fuel, joker fuel, bullseye reference, abort code, minimum altitude
6. **Threats** — SAM types with range rings and MEZ guidance, enemy air, SHORAD
7. **Flight Plan** — Steerpoints table with altitude, speed, and notes per waypoint
8. **Package** — Friendly flights with callsigns and what each one does
9. **Communications** — Full frequency/TACAN card
10. **Fuel & Loadout** — Fuel plan with reserve calculations, weapon loadout
11. **Weather** — Conditions, sunrise/sunset, QNH, impact on flight profile
12. **Contingency** — Alternate airfield, CSAR procedure, abort instructions
13. **Tactical Notes** — Mission-specific tips

### Win/Loss Conditions
Missions have embedded success/failure logic. SEAD wins when all SAMs are dead, CAS wins when 70%+ of enemy armor is destroyed, convoy defense wins when the convoy survives 40 minutes.

### Radio Messages
Restrained timed messages during the mission — AWACS check-in, SEAD push call, threat warnings, tanker availability. Enough to feel alive, not constant chatter.

### Campaign Mode
Generate linked missions where your results carry forward:
```
DCS-MG> 3 mission SEAD campaign on Caucasus in the F-16
```
After flying each mission, come back and type `next mission`. The tool asks 2-3 debrief questions about how it went:
- "How many SAM sites did you destroy?" → Destroyed SAMs are removed from future missions
- "How was the enemy air?" → Affects attrition on both sides
- Front lines shift, enemy escalates with reinforcements, friendly forces take losses

Campaign state saves to disk — close the tool, fly the mission over multiple days, come back whenever.

### Quick Mode
```
DCS-MG> quick SEAD F-16 Caucasus hard
```
Skips confirmation, generates instantly.

### DCS Auto-Deploy
Automatically detects your DCS Saved Games folder and copies the .miz into `Missions/Generated/`. Supports DCS stable, openbeta, and custom installs.

### Mission History
```
DCS-MG> history
```
View a log of every mission you've generated — operation name, aircraft, type, map, difficulty, date.

### Pre-Flight Validation
Every mission runs through a validation check before packaging:
- Verifies airfield IDs exist on the map
- Checks runway length for your aircraft
- Validates units are within map bounds
- Checks fuel adequacy
- Verifies waypoint integrity
- Detects duplicate group/unit IDs
- Warns on high unit counts

## Custom Aircraft Mods

Add any aircraft mod by dropping a JSON file into `custom_aircraft/`:

1. Copy `custom_aircraft/_template.json` → `custom_aircraft/YourAircraft.json`
2. Fill in the DCS type string, display name, roles, performance numbers
3. Add aliases (what you can type to select it, like "raptor" for F-22)
4. Optionally add loadout CLSIDs per mission type

To find your mod's DCS type string: create a mission with the mod in the DCS editor, save it, rename `.miz` to `.zip`, extract, open the `mission` file, search for the aircraft type value.

The tool auto-loads everything from `custom_aircraft/` at startup. No code changes needed.

## Building the EXE

```
build_exe.bat
```

This installs PyInstaller (if needed) and builds `dist/DCS_Mission_Generator.exe`. Double-click to run. The `custom_aircraft/` folder is created next to the exe on first launch.

## GUI

Run `python gui.py` for a dark military-themed desktop interface with:
- Natural language input box
- Manual dropdowns for aircraft, map, mission type, difficulty, weather
- Full briefing output panel
- Ollama and DCS connection status indicators
- Auto-deploy and output folder buttons

## Console Commands

| Command | Description |
|---------|-------------|
| *(just type)* | Describe a mission in plain English |
| `quick <desc>` | Skip confirmation, generate instantly |
| `maps` | List available maps and airfields |
| `examples` | Show example descriptions |
| `history` | View generated mission log |
| `campaign` / `next mission` | Resume in-progress campaign / debrief |
| `settings` | View current settings |
| `quit` | Exit |

## Project Structure

```
dcs-mission-gen/
├── main.py                    Console entry point
├── gui.py                     GUI entry point (tkinter)
├── build_exe.bat              Windows EXE builder
├── custom_aircraft/           Drop mod JSON configs here
│   ├── _template.json         Template with instructions
│   └── F-22A.json             F-22 Raptor mod (included)
├── output/                    Generated .miz files
└── src/
    ├── units.py               Aircraft, SAM, ground unit databases
    ├── difficulty.py           Easy/medium/hard scaling
    ├── naming.py              Operation name generator
    ├── callsigns.py           Callsign & frequency assignment
    ├── flight_profile.py      Altitude/speed/fuel calculator
    ├── mission_events.py      Radio messages, win/loss, reinforcements
    ├── campaign.py            Campaign system with interactive debrief
    ├── custom_mods.py         JSON mod loader
    ├── dcs_detect.py          DCS install auto-detection
    ├── validator.py           Pre-flight mission validation
    ├── history.py             Mission log tracker
    ├── maps/
    │   ├── caucasus.py        Airfields, cities, SAM zones, convoy routes
    │   ├── syria.py
    │   └── cold_war_germany.py
    ├── llm/
    │   ├── ollama_client.py   Ollama API client
    │   └── mission_parser.py  NL → structured plan (LLM + rule-based fallback)
    └── generators/
        ├── mission_builder.py  Plan → full mission data with coordinates
        ├── lua_generator.py    Mission data → DCS Lua table files
        ├── miz_packager.py     Lua files → .miz zip archive
        └── briefing_generator.py  Full 13-section tactical briefing
```

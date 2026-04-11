# DCS World Mission Generator v2.0

Generate realistic DCS World `.miz` mission files from plain English descriptions. Describe what you want to fly, and the tool builds a complete mission with waypoints, enemy threats, friendly package, realistic briefing, and win/loss conditions — ready to load directly in DCS.

## Quick Start

```
cd DCS-Mission-Manager
python main.py
DCS-MG> SEAD mission in the F-16 on Caucasus with SA-11s. Hard difficulty.
```

Or use the GUI:
```
python gui.py
```

---

## Requirements

- **Python 3.10+** — [python.org](https://python.org)
- **Ollama** (optional, but highly recommended) — see setup below
- No additional Python packages — stdlib only

---

## Ollama Setup (AI Natural Language Parsing)

Ollama runs a local AI model on your PC that converts plain English into mission parameters. **It is completely optional** — without it the tool uses a keyword-based fallback parser that handles simple descriptions. With it, you can describe missions naturally and the AI figures out the details.

### 1. Install Ollama

Download from **[ollama.com](https://ollama.com)** and run the installer. Ollama runs silently in the background after install.

### 2. Pull the model

Open a terminal and run:

```
ollama pull llama3.1:8b
```

This downloads the ~4.7 GB Llama 3.1 8B model. You only need to do this once.

### 3. That's it

Restart the tool. The Ollama indicator in the title bar will turn green when it connects. The tool auto-detects Ollama on `localhost:11434` — no configuration needed.

> **Better results with a larger model:** If your PC has 16+ GB VRAM or RAM you can try `llama3.1:70b` or `mistral-nemo` for significantly better parsing quality. Change the model in `gui.py` line ~119: `OllamaClient(model="llama3.1:70b")`.

### Without Ollama

The rule-based fallback parser handles straightforward descriptions:
```
SEAD F-16 Caucasus SA-11 hard
CAS in the Hornet over Syria, morning
CAP mission, Persian Gulf, medium
```
More complex or conversational phrasing may not parse correctly without the AI.

---

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
- **CSAR** — Combat search and rescue
- **FAC(A)** — Forward air control (airborne), coordinate with ground

### Player Aircraft
- F-16C Viper
- F/A-18C Hornet
- F-15C Eagle
- F-15E Strike Eagle
- A-10C II Thunderbolt
- AV-8B Harrier II
- Mirage 2000C
- AH-64D Apache
- JF-17 Thunder
- Any additional mods you add (see Custom Aircraft below)

### Maps
- Caucasus (Georgia / Abkhazia / Russia)
- Syria (Turkey / Syria / Israel / Cyprus)
- Cold War Germany (Fulda Gap / NATO vs Warsaw Pact)
- Persian Gulf (UAE / Iran / Strait of Hormuz)
- Mariana Islands (Guam / Saipan / Pacific carrier ops)

### Difficulty Scaling
- **Easy** — Weaker enemies (Average skill), downgraded SAMs (SA-11→SA-6), more friendly flights, extra friendly CAP
- **Medium** — Balanced (default)
- **Hard** — Elite AI (Excellent skill), upgraded SAMs (SA-6→SA-11), SA-10 additions, SHORAD escorts on SAM sites, MiG-31 interceptors, fewer friendly flights

### Flight Profiles
Each aircraft has a realistic performance profile. The F-16 cruises at FL250/450kts, the A-10 at FL150/250kts, the AH-64D NOE at 50ft/120kts. Mission type shapes the altitude plan — SEAD stays medium for HARM employment, CAS descends for attack passes, anti-ship comes in sea-skimming. Weather automatically adjusts profiles below cloud ceilings.

### Custom Loadouts
In the GUI's manual selector, every mission has a **Loadout** row showing the preset weapons. Click **✏** to open the loadout editor and pick weapons per pylon from the aircraft's available catalog. Apply to use your custom load instead of the preset.

### Multiplayer Co-op
Set **Players** to 2–4 in the GUI (or `"player_count": N` in the plan). Slot 1 spawns as `Player`, additional slots spawn as `Client` for DCS multiplayer.

### Mission Briefing
Full 13-section tactical briefing:
1. **Situation** — Why you're flying this mission
2. **Mission** — Your specific objectives
3. **Execution** — Flight profile, altitude/speed plan, timeline
4. **Rules of Engagement**
5. **SPINS** — Bingo fuel, joker fuel, bullseye, abort code
6. **Threats** — SAMs with range rings, enemy air, SHORAD
7. **Flight Plan** — Steerpoints table
8. **Package** — Friendly flights with callsigns
9. **Communications** — Frequency/TACAN card
10. **Fuel & Loadout** — Fuel plan, weapon loadout
11. **Weather** — Ceiling, visibility, QNH, sunrise/sunset
12. **Contingency** — Alternate airfield, CSAR, abort
13. **Tactical Notes** — Mission-specific tips

An embedded kneeboard PNG with key briefing data is automatically placed in the `.miz` and shows in-game under `RSHIFT+K`.

### Campaign Mode
Generate linked missions where your results carry forward:
```
DCS-MG> 3 mission SEAD campaign on Caucasus in the F-16
```
After flying, type `next mission`. The tool asks debrief questions and adjusts the next mission accordingly — destroyed SAMs stay dead, front lines shift, enemy reinforces.

### DCS Auto-Deploy
Automatically detects your DCS Saved Games folder and copies the `.miz` into `Missions/Generated/`. Supports DCS stable, openbeta, and custom installs.

### Pre-Flight Validation
Every mission is validated before packaging — checks airfield IDs, runway lengths, unit bounds, fuel, waypoints, and now CLSID format on all weapons.

---

## Custom Aircraft Mods

Add any aircraft mod by dropping a JSON file into `custom_aircraft/`:

1. Copy `custom_aircraft/_template.json` → `custom_aircraft/YourAircraft.json`
2. Fill in the DCS type string, display name, roles, performance numbers
3. Add aliases (e.g. `"raptor"` for F-22)
4. Optionally add loadout CLSIDs per mission type

To find your mod's DCS type string: create a mission with the mod in the DCS editor, save it, rename `.miz` to `.zip`, extract, open the `mission` file, search for the aircraft type value.

The tool auto-loads everything from `custom_aircraft/` at startup. No code changes needed.

---

## Building the EXE

```
build_exe.bat
```

Installs PyInstaller if needed and builds `dist/DCS_Mission_Generator.exe`. Double-click to run — no Python required. The `custom_aircraft/` folder is created next to the exe on first launch.

---

## GUI

Run `python gui.py` for a dark military-themed interface:
- Natural language input box
- Manual dropdowns for aircraft, map, mission type, difficulty, weather, time, players
- Per-pylon custom loadout editor (✏ button on the Loadout row)
- Full briefing output panel with syntax coloring
- Ollama and DCS connection status indicators in the title bar
- Auto-deploy toggle and output folder button

---

## Console Commands

| Command | Description |
|---------|-------------|
| *(just type)* | Describe a mission in plain English |
| `quick <desc>` | Skip confirmation, generate instantly |
| `maps` | List available maps and airfields |
| `examples` | Show example descriptions |
| `history` | View generated mission log |
| `campaign` / `next mission` | Start/resume campaign |
| `settings` | View current settings |
| `quit` | Exit |

---

## Project Structure

```
DCS-Mission-Manager/
├── main.py                    Console entry point
├── gui.py                     GUI entry point (tkinter)
├── build_exe.bat              Windows EXE builder
├── custom_aircraft/           Drop mod JSON configs here
│   └── _template.json         Template with instructions
└── src/
    ├── units.py               Aircraft, SAM, ground unit databases + weapon catalog
    ├── difficulty.py          Easy/medium/hard scaling
    ├── naming.py              Operation name generator
    ├── callsigns.py           Callsign & frequency assignment
    ├── flight_profile.py      Altitude/speed/fuel calculator
    ├── mission_events.py      Radio messages, win/loss, reinforcements
    ├── campaign.py            Campaign system with debrief
    ├── custom_mods.py         JSON mod loader
    ├── dcs_detect.py          DCS install auto-detection
    ├── validator.py           Pre-flight mission validation
    ├── history.py             Mission log tracker
    ├── maps/
    │   ├── caucasus.py
    │   ├── syria.py
    │   ├── cold_war_germany.py
    │   ├── persian_gulf.py
    │   └── mariana_islands.py
    ├── llm/
    │   ├── ollama_client.py   Ollama API client (format=json, retry logic)
    │   └── mission_parser.py  NL → structured plan (LLM + rule-based fallback)
    └── generators/
        ├── mission_builder.py  Plan → full mission data
        ├── lua_generator.py    Mission data → DCS Lua tables
        ├── miz_packager.py     Lua files → .miz zip + kneeboard PNG
        ├── briefing_generator.py  13-section tactical briefing
        └── kneeboard_generator.py Pure-stdlib PNG renderer
```

---

## License

MIT License — © 2026 2DoorDevelopment

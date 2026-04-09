"""
Mission History — Tracks every generated mission.
Stores a simple JSON log of all missions you've created.
Type 'history' to see your recent missions.
"""

import json
import time
from pathlib import Path


HISTORY_FILE = "mission_history.json"


def _get_history_path(output_dir: Path) -> Path:
    """Get path to the history file."""
    return output_dir / HISTORY_FILE


def load_history(output_dir: Path) -> list[dict]:
    """Load mission history from disk."""
    path = _get_history_path(output_dir)
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_history(output_dir: Path, history: list[dict]):
    """Save mission history to disk."""
    path = _get_history_path(output_dir)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except OSError as e:
        print(f"  WARNING: Could not save history: {e}")


def record_mission(output_dir: Path, plan: dict, filename: str):
    """Record a generated mission to history."""
    history = load_history(output_dir)

    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "operation": plan.get("_operation_name", "Unknown"),
        "aircraft": plan.get("player_aircraft", "?"),
        "mission_type": plan.get("mission_type", "?"),
        "map": plan.get("map_name", "?"),
        "difficulty": plan.get("difficulty", "medium"),
        "weather": plan.get("weather", "clear"),
        "filename": filename,
        "callsign": plan.get("_assigned_callsigns", {}).get("player", {}).get("full", "?")
            if isinstance(plan.get("_assigned_callsigns"), dict) else "?",
        "campaign": plan.get("_campaign_name", ""),
        "campaign_mission": plan.get("_campaign_mission_num", 0),
    }

    history.append(entry)

    # Keep last 200 entries
    if len(history) > 200:
        history = history[-200:]

    save_history(output_dir, history)


def display_history(output_dir: Path, count: int = 20):
    """Display recent mission history."""
    history = load_history(output_dir)

    if not history:
        print("\n  No missions generated yet.")
        return

    recent = history[-count:]
    recent.reverse()  # Most recent first

    print(f"\n  ── MISSION HISTORY ({len(history)} total, showing last {min(count, len(history))}) ──\n")
    print(f"  {'DATE':<20} {'OPERATION':<28} {'TYPE':<8} {'AIRCRAFT':<10} {'MAP':<12} {'DIFF':<6}")
    print(f"  {'─'*20} {'─'*28} {'─'*8} {'─'*10} {'─'*12} {'─'*6}")

    for entry in recent:
        date = entry.get("timestamp", "?")[:16]
        op = entry.get("operation", "?")[:27]
        mt = entry.get("mission_type", "?")[:7]
        ac = entry.get("aircraft", "?")[:9]
        mp = entry.get("map", "?")[:11]
        diff = entry.get("difficulty", "?")[:5]

        campaign = entry.get("campaign", "")
        cm = entry.get("campaign_mission", 0)
        suffix = f" [C{cm}]" if campaign else ""

        print(f"  {date:<20} {op + suffix:<28} {mt:<8} {ac:<10} {mp:<12} {diff:<6}")

    print()

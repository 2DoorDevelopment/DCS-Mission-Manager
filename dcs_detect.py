"""
DCS Install Detector
Finds the DCS World Saved Games folder on Windows to auto-deploy .miz files.
Supports DCS World (stable), DCS World OpenBeta, and custom installs.
"""

import os
import shutil
from pathlib import Path


# Standard DCS Saved Games paths (relative to USERPROFILE)
_DCS_SAVED_GAMES_PATHS = [
    "Saved Games/DCS",
    "Saved Games/DCS.openbeta",
    "Saved Games/DCS.stable",
]


def find_dcs_missions_folder() -> Path | None:
    """
    Auto-detect the DCS Missions folder.
    Checks standard Windows paths under %USERPROFILE%/Saved Games/.

    Returns:
        Path to the Missions folder, or None if not found.
    """
    user_profile = os.environ.get("USERPROFILE", "")
    if not user_profile:
        # Try HOME as fallback (Linux/Mac dev environment)
        user_profile = os.environ.get("HOME", "")

    if not user_profile:
        return None

    user_path = Path(user_profile)

    for rel_path in _DCS_SAVED_GAMES_PATHS:
        dcs_root = user_path / rel_path
        if dcs_root.is_dir():
            missions_dir = dcs_root / "Missions"
            missions_dir.mkdir(exist_ok=True)
            return missions_dir

    return None


def find_all_dcs_installs() -> list[Path]:
    """Find all DCS install variants on this system."""
    user_profile = os.environ.get("USERPROFILE", os.environ.get("HOME", ""))
    if not user_profile:
        return []

    user_path = Path(user_profile)
    found = []

    for rel_path in _DCS_SAVED_GAMES_PATHS:
        dcs_root = user_path / rel_path
        if dcs_root.is_dir():
            found.append(dcs_root)

    return found


def deploy_mission(miz_path: str | Path, missions_folder: Path | None = None) -> Path | None:
    """
    Copy a .miz file to the DCS Missions folder.

    Args:
        miz_path: Path to the generated .miz file
        missions_folder: Target folder (auto-detected if None)

    Returns:
        Path to the deployed file, or None on failure
    """
    miz_path = Path(miz_path)

    if not miz_path.exists():
        print(f"  ERROR: .miz file not found: {miz_path}")
        return None

    if missions_folder is None:
        missions_folder = find_dcs_missions_folder()

    if missions_folder is None:
        print("  Could not auto-detect DCS Missions folder.")
        print("  Set it manually with: set DCS_MISSIONS_PATH=<path>")
        return None

    # Ensure subfolder for generated missions
    gen_folder = missions_folder / "Generated"
    gen_folder.mkdir(exist_ok=True)

    dest = gen_folder / miz_path.name
    try:
        shutil.copy2(str(miz_path), str(dest))
        return dest
    except (shutil.Error, OSError) as e:
        print(f"  ERROR: Failed to copy to DCS folder: {e}")
        return None


def deploy_briefing(txt_path: str | Path, missions_folder: Path | None = None) -> Path | None:
    """Copy a briefing .txt file alongside the .miz."""
    txt_path = Path(txt_path)

    if not txt_path.exists():
        return None

    if missions_folder is None:
        missions_folder = find_dcs_missions_folder()

    if missions_folder is None:
        return None

    gen_folder = missions_folder / "Generated"
    gen_folder.mkdir(exist_ok=True)

    dest = gen_folder / txt_path.name
    try:
        shutil.copy2(str(txt_path), str(dest))
        return dest
    except (shutil.Error, OSError):
        return None


def get_custom_missions_path() -> Path | None:
    """Check for user-specified DCS missions path via environment variable."""
    custom = os.environ.get("DCS_MISSIONS_PATH", "")
    if custom:
        p = Path(custom)
        if p.is_dir():
            return p
    return None

"""
Smoke tests for DCS Mission Manager.
These tests validate that the core pipeline doesn't crash end-to-end.
No .miz file is written to disk; we test up to the Lua generation stage.
"""

import sys
import os
import pytest

# Ensure project root is on the path regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Unit registry tests
# ---------------------------------------------------------------------------

class TestUnits:
    def test_player_aircraft_present(self):
        from src.units import PLAYER_AIRCRAFT
        assert len(PLAYER_AIRCRAFT) >= 4, "Expected at least 4 player aircraft"

    def test_new_aircraft_present(self):
        from src.units import PLAYER_AIRCRAFT
        for key in ("F-15C", "F-15E", "AV-8B", "M-2000C", "AH-64D"):
            assert key in PLAYER_AIRCRAFT, f"Missing player aircraft: {key}"

    def test_mission_templates_present(self):
        from src.units import MISSION_TEMPLATES
        for mt in ("SEAD", "CAS", "CAP", "strike", "anti-ship", "escort",
                   "convoy_attack", "convoy_defense", "CSAR", "FAC"):
            assert mt in MISSION_TEMPLATES, f"Missing mission template: {mt}"

    def test_aircraft_aliases_resolve(self):
        from src.units import resolve_aircraft
        assert resolve_aircraft("viper") == "F-16C"
        assert resolve_aircraft("hornet") == "F/A-18C"
        assert resolve_aircraft("eagle") == "F-15C"
        assert resolve_aircraft("apache") == "AH-64D"
        assert resolve_aircraft("mirage") == "M-2000C"

    def test_mission_type_aliases_resolve(self):
        from src.units import resolve_mission_type
        assert resolve_mission_type("wild weasel") == "SEAD"
        assert resolve_mission_type("rescue") == "CSAR"
        assert resolve_mission_type("fac") == "FAC"


# ---------------------------------------------------------------------------
# Map registry tests
# ---------------------------------------------------------------------------

class TestMaps:
    def test_all_maps_registered(self):
        from src.maps import MAP_REGISTRY
        for key in ("Caucasus", "Syria", "ColdWarGermany", "PersianGulf", "MarianaIslands"):
            assert key in MAP_REGISTRY, f"Map not registered: {key}"

    def test_maps_have_airfields(self):
        from src.maps import MAP_REGISTRY
        for key, data in MAP_REGISTRY.items():
            assert len(data.get("airfields", [])) > 0, f"{key} has no airfields"

    def test_map_aliases_resolve(self):
        from src.maps import MAP_ALIASES
        assert MAP_ALIASES.get("persian gulf") == "PersianGulf"
        assert MAP_ALIASES.get("guam") == "MarianaIslands"
        assert MAP_ALIASES.get("caucasus") == "Caucasus"

    def test_persian_gulf_has_blue_airfields(self):
        from src.maps import MAP_REGISTRY
        pg = MAP_REGISTRY["PersianGulf"]
        blue = [af for af in pg["airfields"] if af.get("default_coalition") == "blue"]
        assert len(blue) >= 5, "Persian Gulf should have at least 5 blue airfields"

    def test_mariana_islands_has_andersen(self):
        from src.maps import MAP_REGISTRY
        mi = MAP_REGISTRY["MarianaIslands"]
        names = [af["name"] for af in mi["airfields"]]
        assert any("Andersen" in n for n in names), "Mariana Islands missing Andersen AFB"


# ---------------------------------------------------------------------------
# Flight profile tests
# ---------------------------------------------------------------------------

class TestFlightProfile:
    def test_profiles_for_new_aircraft(self):
        from src.flight_profile import AIRCRAFT_PROFILES, get_profile
        for key in ("F-15C", "F-15E", "AV-8B", "M-2000C", "AH-64D"):
            assert key in AIRCRAFT_PROFILES, f"No flight profile for {key}"
            p = get_profile(key)
            assert p["cruise_speed_kts"] > 0

    def test_fallback_profile(self):
        from src.flight_profile import get_profile
        # Unknown aircraft should fall back to F-16C profile
        p = get_profile("UNKNOWN_TYPE")
        assert p["cruise_speed_kts"] == get_profile("F-16C")["cruise_speed_kts"]

    def test_mission_profiles_for_new_types(self):
        from src.flight_profile import MISSION_PROFILES
        assert "CSAR" in MISSION_PROFILES
        assert "FAC" in MISSION_PROFILES


# ---------------------------------------------------------------------------
# Mission builder smoke test
# ---------------------------------------------------------------------------

class TestMissionBuilder:
    def _minimal_plan(self, mission_type="SEAD", map_name="Caucasus", aircraft="F-16C"):
        return {
            "player_aircraft": aircraft,
            "map_name": map_name,
            "mission_type": mission_type,
            "player_airfield": "AUTO",
            "difficulty": "medium",
            "time_of_day": "morning",
            "weather": "clear",
            "player_count": 1,
            "wingman": False,
            "enemy_sam_sites": [{"type": "SA-6", "location_desc": "Forward position"}],
            "enemy_air": [{"aircraft": "MiG-29A", "task": "CAP", "count": 2}],
            "friendly_flights": [],
            "ground_war": {"enabled": False},
            "_operation_name": "TEST OP",
        }

    def test_build_sead_caucasus(self):
        from src.generators.mission_builder import MissionBuilder
        plan = self._minimal_plan("SEAD", "Caucasus", "F-16C")
        data = MissionBuilder(plan).build()
        assert "player_group" in data
        assert data["player_group"]["units"][0]["skill"] == "Player"

    def test_build_cas_persian_gulf(self):
        from src.generators.mission_builder import MissionBuilder
        plan = self._minimal_plan("CAS", "PersianGulf", "A-10C")
        data = MissionBuilder(plan).build()
        assert "player_group" in data

    def test_multiplayer_slots(self):
        from src.generators.mission_builder import MissionBuilder
        plan = self._minimal_plan("CAP", "Caucasus", "F-15C")
        plan["player_count"] = 3
        plan["wingman"] = False
        data = MissionBuilder(plan).build()
        units = data["player_group"]["units"]
        assert len(units) == 3
        assert units[0]["skill"] == "Player"
        assert units[1]["skill"] == "Client"
        assert units[2]["skill"] == "Client"

    def test_build_mariana_islands(self):
        from src.generators.mission_builder import MissionBuilder
        plan = self._minimal_plan("CAP", "MarianaIslands", "F/A-18C")
        data = MissionBuilder(plan).build()
        assert "player_group" in data

    def test_custom_pylons_override_preset(self):
        from src.generators.mission_builder import MissionBuilder
        from src.units import WEAPON_CATALOG
        plan = self._minimal_plan("SEAD", "Caucasus", "F-16C")
        # Pick a specific custom loadout — two AIM-120C on pylons 1 & 9 only
        clsid = next(w["CLSID"] for w in WEAPON_CATALOG["F-16C"] if "AIM-120C" in w["name"])
        plan["custom_pylons"] = {1: {"CLSID": clsid}, 9: {"CLSID": clsid}}
        data = MissionBuilder(plan).build()
        pylons = data["player_group"]["units"][0]["pylons"]
        assert pylons == {1: {"CLSID": clsid}, 9: {"CLSID": clsid}}, \
            "Custom pylons were not passed through to the built mission"

    def test_weapon_catalog_clsids_are_valid(self):
        from src.units import WEAPON_CATALOG
        import re
        guid_re = re.compile(
            r"^\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}"
            r"-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}$"
        )
        shorthand_re = re.compile(r"^\{[A-Za-z0-9_\-\.]+\}$")
        for ac_key, weapons in WEAPON_CATALOG.items():
            for w in weapons:
                clsid = w["CLSID"]
                assert guid_re.match(clsid) or shorthand_re.match(clsid), \
                    f"{ac_key} weapon '{w['name']}' has malformed CLSID: {clsid}"


# ---------------------------------------------------------------------------
# Kneeboard generator tests
# ---------------------------------------------------------------------------

class TestKneeboard:
    def test_generates_valid_png(self):
        from src.generators.kneeboard_generator import generate_kneeboard_png
        briefing = "1. SITUATION\nTest mission briefing text.\n\n2. MISSION\nDestroy targets."
        png_bytes = generate_kneeboard_png(briefing, "F-16C_50")
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n", "Output is not a valid PNG"
        assert len(png_bytes) > 1000, "PNG seems too small"

    def test_aircraft_folder_mapping(self):
        from src.generators.kneeboard_generator import get_dcs_aircraft_folder
        assert get_dcs_aircraft_folder("F-16C_50") == "F-16C_50"
        assert get_dcs_aircraft_folder("FA-18C_hornet") == "FA-18C_hornet"
        assert get_dcs_aircraft_folder("UNKNOWN") == "UNKNOWN"


# ---------------------------------------------------------------------------
# Naming / difficulty tests
# ---------------------------------------------------------------------------

class TestNaming:
    def test_generates_operation_name(self):
        from src.naming import generate_mission_name
        name = generate_mission_name("SEAD")
        assert isinstance(name, str) and len(name) > 3

    def test_generates_filename(self):
        from src.naming import generate_filename
        fn = generate_filename("SEAD", "Caucasus", "Operation Iron Fist")
        assert fn.endswith(".miz")


class TestDifficulty:
    def test_scale_does_not_crash(self):
        from src.difficulty import scale_plan
        plan = {
            "difficulty": "hard",
            "enemy_sam_sites": [{"type": "SA-6"}],
            "enemy_air": [{"aircraft": "MiG-29A", "task": "CAP", "count": 2}],
            "friendly_flights": [],
        }
        scaled = scale_plan(plan)
        assert "enemy_sam_sites" in scaled

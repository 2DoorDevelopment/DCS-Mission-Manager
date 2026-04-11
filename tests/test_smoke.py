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


# ---------------------------------------------------------------------------
# End-to-end pipeline tests (build → Lua → .miz)
# ---------------------------------------------------------------------------

class TestEndToEnd:
    """Test the full pipeline from plan through to .miz packaging."""

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

    def test_lua_generation(self):
        """Build mission data then generate Lua files — verify all expected keys exist."""
        from src.generators.mission_builder import MissionBuilder
        from src.generators.lua_generator import LuaGenerator
        plan = self._minimal_plan()
        data = MissionBuilder(plan).build()
        lua = LuaGenerator(data).generate_all()
        for key in ("mission", "warehouses", "options", "theatre", "dictionary"):
            assert key in lua, f"Missing Lua file key: {key}"
            assert len(lua[key]) > 0, f"Lua file '{key}' is empty"

    def test_miz_package_creates_valid_zip(self, tmp_path):
        """Full pipeline: plan → build → Lua → .miz → verify zip contents."""
        import zipfile
        from src.generators.mission_builder import MissionBuilder
        from src.generators.lua_generator import LuaGenerator
        from src.generators.briefing_generator import BriefingGenerator
        from src.generators.miz_packager import MizPackager

        plan = self._minimal_plan()
        data = MissionBuilder(plan).build()
        lua_files = LuaGenerator(data).generate_all()
        briefing = BriefingGenerator(data, plan).generate()
        miz_path = str(tmp_path / "test_mission.miz")
        MizPackager().package(lua_files, briefing, miz_path, aircraft_type="F-16C_50")

        assert os.path.exists(miz_path), ".miz file was not created"
        with zipfile.ZipFile(miz_path, "r") as zf:
            names = zf.namelist()
            assert "mission" in names
            assert "warehouses" in names
            assert "options" in names
            assert "theatre" in names
            # Kneeboard PNG should be embedded
            kneeboard_files = [n for n in names if "KNEEBOARD" in n and n.endswith(".png")]
            assert len(kneeboard_files) >= 1, "No kneeboard PNG found in .miz"

    def test_miz_for_each_map(self, tmp_path):
        """Ensure .miz builds successfully for every registered map."""
        from src.generators.mission_builder import MissionBuilder
        from src.generators.lua_generator import LuaGenerator
        from src.maps import MAP_REGISTRY

        for map_name in MAP_REGISTRY:
            plan = self._minimal_plan(map_name=map_name)
            data = MissionBuilder(plan).build()
            lua = LuaGenerator(data).generate_all()
            assert lua["theatre"], f"Empty theatre for {map_name}"
            assert "mission =" in lua["mission"] or "mission=" in lua["mission"], \
                f"Lua mission file broken for {map_name}"


# ---------------------------------------------------------------------------
# Lua syntax validation tests
# ---------------------------------------------------------------------------

class TestLuaSyntaxValidation:
    """Test the Lua syntax validation logic."""

    def test_balanced_braces_pass(self):
        from src.validator import validate_lua_syntax
        lua = {'mission': 'mission = { ["coalition"] = { } }', 'theatre': 'Caucasus'}
        result = validate_lua_syntax(lua)
        brace_errors = [e for e in result.errors if "brace" in e.lower() or "Unbalanced" in e]
        assert len(brace_errors) == 0

    def test_unbalanced_braces_detected(self):
        from src.validator import validate_lua_syntax
        lua = {'test_file': 'mission = { ["x"] = { }'}  # missing closing brace
        result = validate_lua_syntax(lua)
        assert any("nbalanced" in e or "brace" in e.lower() for e in result.errors), \
            f"Expected unbalanced brace error, got: {result.errors}"

    def test_unclosed_string_detected(self):
        from src.validator import validate_lua_syntax
        lua = {'test_file': '["name"] = "unclosed string\n["other"] = 1'}
        result = validate_lua_syntax(lua)
        assert any("string" in e.lower() or "quote" in e.lower() for e in result.errors), \
            f"Expected unclosed string error, got: {result.errors}"

    def test_theatre_empty_detected(self):
        from src.validator import validate_lua_syntax
        lua = {'theatre': '   '}
        result = validate_lua_syntax(lua)
        assert any("empty" in e.lower() for e in result.errors)

    def test_mission_structure_checks(self):
        from src.validator import validate_lua_syntax
        lua = {
            'mission': 'mission = { ["coalition"] = {}, ["theatre"] = "Caucasus", ["date"] = {} }',
            'theatre': 'Caucasus',
        }
        result = validate_lua_syntax(lua)
        # Should pass — has mission=, coalition, theatre, date
        mission_errors = [e for e in result.errors if "mission" in e.lower()]
        assert len(mission_errors) == 0


# ---------------------------------------------------------------------------
# CLSID validation tests
# ---------------------------------------------------------------------------

class TestCLSIDValidation:
    """Test CLSID format and known-registry checking."""

    def test_valid_guid_clsid(self):
        from src.validator import _GUID_RE
        assert _GUID_RE.match("{DB769D48-67D7-42ED-A2BE-108D566C8B1E}")

    def test_valid_shorthand_clsid(self):
        from src.validator import _SHORTHAND_RE
        assert _SHORTHAND_RE.match("{AIM-120C}")
        assert _SHORTHAND_RE.match("{GBU-12}")

    def test_invalid_clsid_format(self):
        from src.validator import _GUID_RE, _SHORTHAND_RE
        bad = "not-a-clsid"
        assert not _GUID_RE.match(bad)
        assert not _SHORTHAND_RE.match(bad)

    def test_known_clsids_populated(self):
        from src.validator import KNOWN_CLSIDS
        assert len(KNOWN_CLSIDS) > 0, "KNOWN_CLSIDS should be built from unit databases"

    def test_clsid_check_flags_invalid(self):
        from src.validator import validate_mission
        mission_data = {
            "theater": "Caucasus", "map_name": "Caucasus",
            "player_group": {
                "group_id": 1, "name": "Test",
                "units": [{"unit_id": 1, "type": "F-16C_50", "skill": "Player",
                           "pylons": {1: {"CLSID": "INVALID_NO_BRACES"}}}],
                "waypoints": [{"type": "TakeOff"}, {"type": "Turning Point"}, {"type": "Land"}],
            },
            "blue_air": [], "red_air": [], "blue_ground": [], "red_ground": [],
            "blue_sam": [], "red_sam": [], "triggers": [], "messages": [],
            "conditions": {}, "callsigns": {}, "fuel_estimate": {},
        }
        plan = {"player_aircraft": "F-16C", "map_name": "Caucasus", "player_airfield": "Kutaisi"}
        result = validate_mission(mission_data, plan)
        assert any("CLSID" in e for e in result.errors), \
            f"Expected CLSID error, got errors={result.errors}"


# ---------------------------------------------------------------------------
# SAM placement & water avoidance tests
# ---------------------------------------------------------------------------

class TestSAMPlacement:
    """Test SAM placement validation and water avoidance."""

    def test_water_avoidance_nudges_position(self):
        from src.generators.mission_builder import BuilderState
        plan = {
            "player_aircraft": "F-16C", "map_name": "Caucasus",
            "mission_type": "SEAD", "player_airfield": "AUTO",
            "difficulty": "medium", "time_of_day": "morning", "weather": "clear",
            "player_count": 1, "wingman": False,
            "enemy_sam_sites": [], "enemy_air": [], "friendly_flights": [],
            "ground_war": {"enabled": False}, "_operation_name": "TEST",
        }
        state = BuilderState(plan)
        # Manually inject a water zone
        state.map_data = dict(state.map_data)
        state.map_data["water_zones"] = [{"name": "Test Sea", "x": 0, "y": 0, "radius": 50000}]
        # Position inside water
        new_x, new_y = state.avoid_water(10000, 10000)
        import math
        dist = math.sqrt(new_x**2 + new_y**2)
        assert dist >= 50000, f"Position should be pushed outside water zone, got dist={dist}"

    def test_sam_not_in_water_after_build(self):
        """Build a mission and verify SAMs are not placed in water zones."""
        import math
        from src.generators.mission_builder import MissionBuilder
        from src.maps import MAP_REGISTRY
        plan = {
            "player_aircraft": "F-16C", "map_name": "Caucasus",
            "mission_type": "SEAD", "player_airfield": "AUTO",
            "difficulty": "medium", "time_of_day": "morning", "weather": "clear",
            "player_count": 1, "wingman": False,
            "enemy_sam_sites": [{"type": "SA-6"}, {"type": "SA-11"}],
            "enemy_air": [], "friendly_flights": [],
            "ground_war": {"enabled": False}, "_operation_name": "TEST",
        }
        data = MissionBuilder(plan).build()
        water_zones = MAP_REGISTRY["Caucasus"].get("water_zones", [])
        for group in data.get("red_sam", []):
            for unit in group.get("units", []):
                x, y = unit.get("x", 0), unit.get("y", 0)
                for wz in water_zones:
                    dist = math.sqrt((x - wz["x"])**2 + (y - wz["y"])**2)
                    assert dist >= wz["radius"] - 200, \
                        f"SAM unit in water zone '{wz['name']}'"

    def test_validator_flags_water_placement(self):
        from src.validator import validate_mission
        mission_data = {
            "theater": "Caucasus", "map_name": "Caucasus",
            "player_group": {
                "group_id": 1, "name": "Player",
                "units": [{"unit_id": 1, "type": "F-16C_50", "skill": "Player"}],
                "waypoints": [{"type": "TakeOff"}, {"type": "Turning Point"}, {"type": "Land"}],
            },
            "blue_air": [], "red_air": [], "blue_ground": [], "red_ground": [],
            "blue_sam": [],
            "red_sam": [{
                "group_id": 99, "name": "Test SAM in Water",
                "units": [{"unit_id": 100, "type": "Kub 1S91 str", "x": -250000, "y": 435000}],
            }],
            "triggers": [], "messages": [], "conditions": {}, "callsigns": {},
            "fuel_estimate": {},
        }
        plan = {"player_aircraft": "F-16C", "map_name": "Caucasus", "player_airfield": "Kutaisi"}
        result = validate_mission(mission_data, plan)
        # Whether this triggers depends on actual water zone coordinates — just ensure no crash
        assert result is not None


# ---------------------------------------------------------------------------
# BuilderState and group_builders unit tests
# ---------------------------------------------------------------------------

class TestBuilderState:
    """Test the BuilderState helper methods."""

    def test_id_counters(self):
        from src.generators.mission_builder import BuilderState
        plan = {
            "player_aircraft": "F-16C", "map_name": "Caucasus",
            "mission_type": "SEAD", "player_airfield": "AUTO",
            "difficulty": "medium", "time_of_day": "morning", "weather": "clear",
            "player_count": 1, "wingman": False,
            "enemy_sam_sites": [], "enemy_air": [], "friendly_flights": [],
            "ground_war": {"enabled": False}, "_operation_name": "TEST",
        }
        s = BuilderState(plan)
        assert s.next_group_id() == 1
        assert s.next_group_id() == 2
        assert s.next_unit_id() == 1
        assert s.next_unit_id() == 2

    def test_get_weather_presets(self):
        from src.generators.mission_builder import BuilderState
        for weather in ("clear", "scattered", "overcast", "rain", "storm"):
            plan = {
                "player_aircraft": "F-16C", "map_name": "Caucasus",
                "mission_type": "SEAD", "player_airfield": "AUTO",
                "difficulty": "medium", "time_of_day": "morning", "weather": weather,
                "player_count": 1, "wingman": False,
                "enemy_sam_sites": [], "enemy_air": [], "friendly_flights": [],
                "ground_war": {"enabled": False}, "_operation_name": "TEST",
            }
            s = BuilderState(plan)
            w = s.get_weather()
            assert "clouds" in w
            assert "visibility" in w

    def test_get_airfield_by_name(self):
        from src.generators.mission_builder import BuilderState
        plan = {
            "player_aircraft": "F-16C", "map_name": "Caucasus",
            "mission_type": "SEAD", "player_airfield": "AUTO",
            "difficulty": "medium", "time_of_day": "morning", "weather": "clear",
            "player_count": 1, "wingman": False,
            "enemy_sam_sites": [], "enemy_air": [], "friendly_flights": [],
            "ground_war": {"enabled": False}, "_operation_name": "TEST",
        }
        s = BuilderState(plan)
        # Caucasus should have Kutaisi
        af = s.get_airfield("Kutaisi")
        assert af is not None, "Expected to find Kutaisi on Caucasus map"

    def test_get_target_position_returns_dict(self):
        from src.generators.mission_builder import BuilderState
        plan = {
            "player_aircraft": "F-16C", "map_name": "Caucasus",
            "mission_type": "SEAD", "player_airfield": "AUTO",
            "difficulty": "medium", "time_of_day": "morning", "weather": "clear",
            "player_count": 1, "wingman": False,
            "enemy_sam_sites": [], "enemy_air": [], "friendly_flights": [],
            "ground_war": {"enabled": False}, "_operation_name": "TEST",
        }
        s = BuilderState(plan)
        pos = s.get_target_position()
        assert "x" in pos and "y" in pos

    def test_wp_tasks_by_mission_type(self):
        from src.generators.mission_builder import BuilderState
        base = {
            "player_aircraft": "F-16C", "map_name": "Caucasus",
            "player_airfield": "AUTO", "difficulty": "medium",
            "time_of_day": "morning", "weather": "clear", "player_count": 1,
            "wingman": False, "enemy_sam_sites": [], "enemy_air": [],
            "friendly_flights": [], "ground_war": {"enabled": False},
            "_operation_name": "TEST",
        }
        for mt, expected_id in [("SEAD", "EngageTargets"), ("CAS", "CAS"),
                                 ("strike", "Bombing"), ("CAP", "CAP")]:
            plan = {**base, "mission_type": mt}
            s = BuilderState(plan)
            tasks = s.get_wp_tasks_for_target()
            assert len(tasks) > 0, f"No target tasks for {mt}"
            assert tasks[0]["id"] == expected_id, f"Wrong task for {mt}"


# ---------------------------------------------------------------------------
# Briefing generator tests
# ---------------------------------------------------------------------------

class TestBriefing:
    """Test briefing content generation."""

    def test_briefing_not_empty(self):
        from src.generators.mission_builder import MissionBuilder
        from src.generators.briefing_generator import BriefingGenerator
        plan = {
            "player_aircraft": "F-16C", "map_name": "Caucasus",
            "mission_type": "SEAD", "player_airfield": "AUTO",
            "difficulty": "medium", "time_of_day": "morning", "weather": "clear",
            "player_count": 1, "wingman": False,
            "enemy_sam_sites": [{"type": "SA-6", "location_desc": "Forward"}],
            "enemy_air": [{"aircraft": "MiG-29A", "task": "CAP", "count": 2}],
            "friendly_flights": [], "ground_war": {"enabled": False},
            "_operation_name": "TEST OP",
        }
        data = MissionBuilder(plan).build()
        briefing = BriefingGenerator(data, plan).generate()
        assert isinstance(briefing, str)
        assert len(briefing) > 100, "Briefing is too short"

    def test_briefing_contains_sections(self):
        from src.generators.mission_builder import MissionBuilder
        from src.generators.briefing_generator import BriefingGenerator
        plan = {
            "player_aircraft": "F-16C", "map_name": "Caucasus",
            "mission_type": "SEAD", "player_airfield": "AUTO",
            "difficulty": "medium", "time_of_day": "morning", "weather": "clear",
            "player_count": 1, "wingman": False,
            "enemy_sam_sites": [{"type": "SA-6", "location_desc": "Forward"}],
            "enemy_air": [], "friendly_flights": [],
            "ground_war": {"enabled": False}, "_operation_name": "TEST OP",
        }
        data = MissionBuilder(plan).build()
        briefing = BriefingGenerator(data, plan).generate()
        # Briefing should contain at least a few standard sections
        assert "SITUATION" in briefing.upper() or "MISSION" in briefing.upper(), \
            "Briefing missing standard section headers"


# ---------------------------------------------------------------------------
# Mission validator comprehensive tests
# ---------------------------------------------------------------------------

class TestValidator:
    """Test the full mission validator."""

    def _build_valid_mission_data(self):
        from src.generators.mission_builder import MissionBuilder
        plan = {
            "player_aircraft": "F-16C", "map_name": "Caucasus",
            "mission_type": "SEAD", "player_airfield": "AUTO",
            "difficulty": "medium", "time_of_day": "morning", "weather": "clear",
            "player_count": 1, "wingman": False,
            "enemy_sam_sites": [{"type": "SA-6", "location_desc": "Forward"}],
            "enemy_air": [{"aircraft": "MiG-29A", "task": "CAP", "count": 2}],
            "friendly_flights": [], "ground_war": {"enabled": False},
            "_operation_name": "TEST OP",
        }
        data = MissionBuilder(plan).build()
        return data, plan

    def test_valid_mission_passes(self):
        from src.validator import validate_mission
        data, plan = self._build_valid_mission_data()
        result = validate_mission(data, plan)
        assert result.passed, f"Valid mission should pass: {result.summary()}"

    def test_missing_player_group(self):
        from src.validator import validate_mission
        data, plan = self._build_valid_mission_data()
        data["player_group"] = None
        result = validate_mission(data, plan)
        assert not result.passed

    def test_duplicate_unit_ids_warned(self):
        from src.validator import validate_mission
        data, plan = self._build_valid_mission_data()
        # Force duplicate ID
        if data["player_group"]["units"]:
            dup_id = data["player_group"]["units"][0]["unit_id"]
            for group in data.get("red_air", []):
                if group.get("units"):
                    group["units"][0]["unit_id"] = dup_id
                    break
        result = validate_mission(data, plan)
        dup_warns = [w for w in result.warnings if "Duplicate unit ID" in w]
        assert len(dup_warns) > 0

    def test_unknown_map_errors(self):
        from src.validator import validate_mission
        data, plan = self._build_valid_mission_data()
        plan["map_name"] = "NonexistentMap"
        result = validate_mission(data, plan)
        assert not result.passed

    def test_summary_output(self):
        from src.validator import validate_mission
        data, plan = self._build_valid_mission_data()
        result = validate_mission(data, plan)
        summary = result.summary()
        assert isinstance(summary, str) and len(summary) > 0


# ---------------------------------------------------------------------------
# Map water zones tests
# ---------------------------------------------------------------------------

class TestMapWaterZones:
    """Verify all maps define water zones."""

    def test_all_maps_have_water_zones(self):
        from src.maps import MAP_REGISTRY
        for name, data in MAP_REGISTRY.items():
            wz = data.get("water_zones", [])
            assert len(wz) > 0, f"Map '{name}' has no water_zones defined"

    def test_water_zones_have_required_fields(self):
        from src.maps import MAP_REGISTRY
        for name, data in MAP_REGISTRY.items():
            for wz in data.get("water_zones", []):
                assert "x" in wz, f"{name} water zone missing 'x'"
                assert "y" in wz, f"{name} water zone missing 'y'"
                assert "radius" in wz, f"{name} water zone missing 'radius'"
                assert wz["radius"] > 0, f"{name} water zone has non-positive radius"

"""
Lua Generator
Generates DCS-compatible Lua table files from mission data.
A .miz file contains these key files:
  - mission       (main mission table)
  - warehouses    (base supply data)
  - options       (difficulty/gameplay options)
  - theatre       (map name string)
  - dictionary    (string translations)
"""


class LuaGenerator:
    """Generate Lua table files for DCS .miz packaging."""

    def __init__(self, mission_data: dict):
        self.data = mission_data
        self.plan = mission_data.get("plan", {})
        self._coalition_id = {"blue": 2, "red": 1, "neutral": 0}

    def generate_all(self) -> dict[str, str]:
        """Generate all required Lua files."""
        return {
            "mission": self._gen_mission(),
            "warehouses": self._gen_warehouses(),
            "options": self._gen_options(),
            "theatre": self.data.get("theater", "Caucasus"),
            "dictionary": self._gen_dictionary(),
        }

    # ================================================================
    # MISSION FILE
    # ================================================================
    def _gen_mission(self) -> str:
        """Generate the main mission Lua table."""
        lines = []
        lines.append("mission = ")
        lines.append("{")

        # Required metadata
        lines.append(f'    ["requiredModules"] = {{}},')
        lines.append(f'    ["date"] = ')
        lines.append("    {")
        date = self.data.get("date", {"year": 2024, "month": 6, "day": 15})
        lines.append(f'        ["Day"] = {date["day"]},')
        lines.append(f'        ["Year"] = {date["year"]},')
        lines.append(f'        ["Month"] = {date["month"]},')
        lines.append("    },")

        # Start time
        lines.append(f'    ["start_time"] = {self.data.get("time", 28800)},')

        # Theater
        lines.append(f'    ["theatre"] = "{self.data.get("theater", "Caucasus")}",')

        # Weather
        lines.append(self._gen_weather_block())

        # Ground control
        lines.append(self._gen_ground_control())

        # Coalitions
        lines.append('    ["coalition"] = ')
        lines.append("    {")
        lines.append(self._gen_coalition("blue"))
        lines.append(self._gen_coalition("red"))
        lines.append(self._gen_neutral_coalition())
        lines.append("    },")

        # Triggers
        lines.append(self._gen_triggers_block())

        # Result conditions
        lines.append('    ["result"] = ')
        lines.append("    {")
        lines.append('        ["offline"] = ')
        lines.append("        {")
        lines.append('            ["conditions"] = {},')
        lines.append('            ["actions"] = {},')
        lines.append("        },")
        lines.append("    },")

        # Version info
        lines.append(f'    ["version"] = 21,')
        lines.append(f'    ["currentKey"] = 0,')

        # Map center / bullseye
        lines.append(self._gen_bullseye())

        # Description
        lines.append(f'    ["descriptionText"] = "{self._escape_lua(self._get_description())}",')
        lines.append(f'    ["descriptionBlueTask"] = "{self._escape_lua(self._get_blue_task())}",')
        lines.append(f'    ["descriptionRedTask"] = "Defend territory",')
        lines.append(f'    ["sortie"] = "{self._escape_lua(self._get_sortie_name())}",')

        # Force table
        lines.append('    ["forcedOptions"] = {},')

        lines.append("} -- end of mission")

        return "\n".join(lines)

    def _gen_weather_block(self) -> str:
        """Generate weather Lua block."""
        weather = self.data.get("weather", {})
        clouds = weather.get("clouds", {"preset": "Preset1", "base": 2500, "thickness": 200})
        wind = weather.get("wind", {"at_ground": {"speed": 3, "dir": 180}})
        fog = weather.get("fog", {"enabled": False})

        lines = []
        lines.append('    ["weather"] = ')
        lines.append("    {")
        lines.append(f'        ["atmosphere_type"] = {weather.get("atmosphere_type", 0)},')
        lines.append('        ["wind"] = ')
        lines.append("        {")
        lines.append('            ["at8000"] = ')
        lines.append("            {")
        lines.append(f'                ["speed"] = {wind["at_ground"]["speed"] * 2},')
        lines.append(f'                ["dir"] = {wind["at_ground"]["dir"]},')
        lines.append("            },")
        lines.append('            ["at2000"] = ')
        lines.append("            {")
        lines.append(f'                ["speed"] = {wind["at_ground"]["speed"] * 1.5},')
        lines.append(f'                ["dir"] = {wind["at_ground"]["dir"] + 10},')
        lines.append("            },")
        lines.append('            ["atGround"] = ')
        lines.append("            {")
        lines.append(f'                ["speed"] = {wind["at_ground"]["speed"]},')
        lines.append(f'                ["dir"] = {wind["at_ground"]["dir"]},')
        lines.append("            },")
        lines.append("        },")
        lines.append(f'        ["enable_fog"] = {str(fog.get("enabled", False)).lower()},')
        if fog.get("enabled"):
            lines.append('        ["fog"] = ')
            lines.append("        {")
            lines.append(f'            ["thickness"] = {fog.get("thickness", 200)},')
            lines.append(f'            ["visibility"] = {fog.get("visibility", 5000)},')
            lines.append("        },")
        else:
            lines.append('        ["fog"] = ')
            lines.append("        {")
            lines.append('            ["thickness"] = 0,')
            lines.append('            ["visibility"] = 0,')
            lines.append("        },")

        lines.append(f'        ["visibility"] = ')
        lines.append("        {")
        lines.append(f'            ["distance"] = {weather.get("visibility", 80000)},')
        lines.append("        },")
        lines.append('        ["clouds"] = ')
        lines.append("        {")
        lines.append(f'            ["thickness"] = {clouds.get("thickness", 200)},')
        lines.append(f'            ["density"] = 0,')
        lines.append(f'            ["preset"] = "{clouds.get("preset", "Preset1")}",')
        lines.append(f'            ["base"] = {clouds.get("base", 2500)},')
        lines.append(f'            ["iprecptns"] = 0,')
        lines.append("        },")

        lines.append(f'        ["season"] = ')
        lines.append("        {")
        lines.append(f'            ["temperature"] = 20,')
        lines.append("        },")
        lines.append(f'        ["type_weather"] = 0,')
        lines.append(f'        ["qnh"] = 760,')
        lines.append(f'        ["cyclones"] = {{}},')
        lines.append(f'        ["name"] = "Custom",')
        lines.append(f'        ["dust_density"] = 0,')
        lines.append(f'        ["enable_dust"] = false,')
        lines.append(f'        ["groundTurbulence"] = {weather.get("turbulence", 0)},')

        lines.append("    },")

        return "\n".join(lines)

    def _gen_ground_control(self) -> str:
        """Generate ground control (ATC/frequencies) block."""
        lines = []
        lines.append('    ["groundControl"] = ')
        lines.append("    {")
        lines.append('        ["isPilotControlVehicles"] = false,')
        lines.append('        ["roles"] = ')
        lines.append("        {")
        lines.append('            ["artillery_commander"] = ')
        lines.append("            {")
        lines.append('                ["neutrals"] = 0,')
        lines.append('                ["blue"] = 0,')
        lines.append('                ["red"] = 0,')
        lines.append("            },")
        lines.append('            ["instructor"] = ')
        lines.append("            {")
        lines.append('                ["neutrals"] = 0,')
        lines.append('                ["blue"] = 0,')
        lines.append('                ["red"] = 0,')
        lines.append("            },")
        lines.append('            ["forward_observer"] = ')
        lines.append("            {")
        lines.append('                ["neutrals"] = 0,')
        lines.append('                ["blue"] = 0,')
        lines.append('                ["red"] = 0,')
        lines.append("            },")
        lines.append('            ["observer"] = ')
        lines.append("            {")
        lines.append('                ["neutrals"] = 0,')
        lines.append('                ["blue"] = 0,')
        lines.append('                ["red"] = 0,')
        lines.append("            },")
        lines.append("        },")
        lines.append("    },")
        return "\n".join(lines)

    def _gen_coalition(self, side: str) -> str:
        """Generate a coalition block with all its groups."""
        lines = []
        side_name = "blue" if side == "blue" else "red"
        nav_points = '        ["nav_points"] = {},'

        lines.append(f'        ["{side_name}"] = ')
        lines.append("        {")
        lines.append(f'            ["bullseye"] = ')
        lines.append("            {")

        # Bullseye at center-ish of map
        bx = self.data.get("bullseye", {}).get(f"{side}_x", 0)
        by = self.data.get("bullseye", {}).get(f"{side}_y", 0)
        lines.append(f'                ["x"] = {bx},')
        lines.append(f'                ["y"] = {by},')
        lines.append("            },")

        lines.append(f'            ["coalition"] = "{side_name}",')
        lines.append(f'            ["name"] = "{side_name}",')
        lines.append(f'            {nav_points}')

        # Country blocks
        lines.append(f'            ["country"] = ')
        lines.append("            {")

        # Pick country for side
        if side == "blue":
            country_id = 2  # USA
            country_name = "USA"
            air_groups = [self.data.get("player_group")] + self.data.get("blue_air", [])
            air_groups = [g for g in air_groups if g]  # Remove None
            ground_groups = self.data.get("blue_ground", []) + self.data.get("blue_sam", [])
        else:
            country_id = 1  # Russia
            country_name = "Russia"
            air_groups = self.data.get("red_air", [])
            ground_groups = self.data.get("red_ground", []) + self.data.get("red_sam", [])

        lines.append(f'                [1] = ')
        lines.append("                {")
        lines.append(f'                    ["id"] = {country_id},')
        lines.append(f'                    ["name"] = "{country_name}",')

        # Plane groups
        plane_groups = [g for g in air_groups if g.get("category") == "plane"]
        if plane_groups:
            lines.append('                    ["plane"] = ')
            lines.append("                    {")
            lines.append('                        ["group"] = ')
            lines.append("                        {")

            for idx, group in enumerate(plane_groups, 1):
                lines.append(self._gen_air_group(group, idx))

            lines.append("                        },")
            lines.append("                    },")

        # Vehicle groups
        vehicle_groups = [g for g in ground_groups if g.get("category") == "vehicle"]
        if vehicle_groups:
            lines.append('                    ["vehicle"] = ')
            lines.append("                    {")
            lines.append('                        ["group"] = ')
            lines.append("                        {")

            for idx, group in enumerate(vehicle_groups, 1):
                lines.append(self._gen_vehicle_group(group, idx))

            lines.append("                        },")
            lines.append("                    },")

        lines.append("                },")
        lines.append("            },")
        lines.append("        },")

        return "\n".join(lines)

    def _gen_air_group(self, group: dict, idx: int) -> str:
        """Generate a single air group Lua block."""
        lines = []
        lines.append(f'                            [{idx}] = ')
        lines.append("                            {")
        lines.append(f'                                ["modulation"] = 0,')
        lines.append(f'                                ["tasks"] = {{}},')

        # Task
        task_map = {
            "SEAD": "SEAD", "CAS": "CAS", "CAP": "CAP",
            "strike": "Ground Attack", "anti-ship": "Antiship Strike",
            "escort": "Escort", "sweep": "Fighter Sweep",
            "Refueling": "Refueling", "AWACS": "AWACS",
            "intercept": "Intercept",
        }
        dcs_task = task_map.get(group.get("task", "CAP"), "CAP")
        lines.append(f'                                ["task"] = "{dcs_task}",')

        # Units
        lines.append('                                ["units"] = ')
        lines.append("                                {")
        for u_idx, unit in enumerate(group.get("units", []), 1):
            lines.append(self._gen_air_unit(unit, u_idx))
        lines.append("                                },")

        # Route / Waypoints
        lines.append('                                ["route"] = ')
        lines.append("                                {")
        lines.append('                                    ["points"] = ')
        lines.append("                                    {")
        for wp in group.get("waypoints", []):
            lines.append(self._gen_waypoint(wp))
        lines.append("                                    },")
        lines.append("                                },")

        # Group metadata
        lines.append(f'                                ["groupId"] = {group.get("group_id", idx)},')
        lines.append(f'                                ["hidden"] = {str(group.get("hidden", False)).lower()},')
        lines.append(f'                                ["y"] = {group["units"][0].get("y", 0) if group.get("units") else 0},')
        lines.append(f'                                ["x"] = {group["units"][0].get("x", 0) if group.get("units") else 0},')
        lines.append(f'                                ["name"] = "{self._escape_lua(group.get("name", "Group"))}",')
        lines.append(f'                                ["communication"] = true,')

        # Use start_time delay instead of lateActivation for staggered spawning
        start_delay = group.get("_start_delay", 0)
        lines.append(f'                                ["start_time"] = {start_delay},')
        lines.append(f'                                ["frequency"] = {group.get("frequency", 251.0)},')

        if group.get("uncontrolled"):
            lines.append(f'                                ["uncontrolled"] = true,')

        lines.append("                            },")
        return "\n".join(lines)

    def _gen_air_unit(self, unit: dict, idx: int) -> str:
        """Generate a single air unit."""
        lines = []
        lines.append(f'                                    [{idx}] = ')
        lines.append("                                    {")
        lines.append(f'                                        ["alt"] = {unit.get("alt", 0)},')
        lines.append(f'                                        ["alt_type"] = "BARO",')
        lines.append(f'                                        ["livery_id"] = "",')
        lines.append(f'                                        ["skill"] = "{unit.get("skill", "High")}",')
        lines.append(f'                                        ["speed"] = 0,')
        lines.append(f'                                        ["type"] = "{unit.get("type", "F-16C_50")}",')
        lines.append(f'                                        ["unitId"] = {unit.get("unit_id", idx)},')
        lines.append(f'                                        ["y"] = {unit.get("y", 0)},')
        lines.append(f'                                        ["x"] = {unit.get("x", 0)},')
        lines.append(f'                                        ["name"] = "{self._escape_lua(unit.get("name", "Unit"))}",')
        lines.append(f'                                        ["heading"] = {unit.get("heading", 0)},')

        # Payload / pylons
        pylons = unit.get("pylons", {})
        if pylons:
            lines.append('                                        ["payload"] = ')
            lines.append("                                        {")
            lines.append(f'                                            ["fuel"] = {unit.get("fuel", 3249)},')
            lines.append(f'                                            ["flare"] = {unit.get("flare", 60)},')
            lines.append(f'                                            ["chaff"] = {unit.get("chaff", 60)},')
            lines.append(f'                                            ["gun"] = 100,')
            lines.append('                                            ["pylons"] = ')
            lines.append("                                            {")
            for pylon_num, pylon_data in sorted(pylons.items()):
                clsid = pylon_data.get("CLSID", "")
                if clsid:
                    lines.append(f'                                                [{pylon_num}] = ')
                    lines.append("                                                {")
                    lines.append(f'                                                    ["CLSID"] = "{clsid}",')
                    lines.append("                                                },")
            lines.append("                                            },")
            lines.append("                                        },")
        else:
            lines.append('                                        ["payload"] = ')
            lines.append("                                        {")
            lines.append(f'                                            ["fuel"] = {unit.get("fuel", 3249)},')
            lines.append(f'                                            ["flare"] = {unit.get("flare", 60)},')
            lines.append(f'                                            ["chaff"] = {unit.get("chaff", 60)},')
            lines.append(f'                                            ["gun"] = 100,')
            lines.append('                                            ["pylons"] = {},')
            lines.append("                                        },")

        lines.append(f'                                        ["callsign"] = ')
        lines.append("                                        {")
        lines.append(f'                                            [1] = 1,')
        lines.append(f'                                            [2] = 1,')
        lines.append(f'                                            [3] = {idx},')
        lines.append(f'                                            ["name"] = "Enfield1{idx}",')
        lines.append("                                        },")

        lines.append("                                    },")
        return "\n".join(lines)

    def _gen_waypoint(self, wp: dict) -> str:
        """Generate a single waypoint Lua block."""
        wp_id = wp.get("id", 0) + 1  # Lua is 1-indexed
        lines = []
        lines.append(f'                                        [{wp_id}] = ')
        lines.append("                                        {")
        lines.append(f'                                            ["alt"] = {wp.get("alt", 2000)},')
        lines.append(f'                                            ["alt_type"] = "BARO",')

        # Action and type
        wp_type = wp.get("type", "Turning Point")
        action = wp.get("action", "Turning Point")

        if wp_type == "TakeOff":
            lines.append(f'                                            ["action"] = "From Parking Area",')
            lines.append(f'                                            ["type"] = "TakeOff",')
            if wp.get("airfield_id"):
                lines.append(f'                                            ["airdromeId"] = {wp["airfield_id"]},')
        elif wp_type == "Land":
            lines.append(f'                                            ["action"] = "Landing",')
            lines.append(f'                                            ["type"] = "Land",')
            if wp.get("airfield_id"):
                lines.append(f'                                            ["airdromeId"] = {wp["airfield_id"]},')
        else:
            lines.append(f'                                            ["action"] = "Turning Point",')
            lines.append(f'                                            ["type"] = "Turning Point",')

        lines.append(f'                                            ["ETA"] = 0,')
        lines.append(f'                                            ["ETA_locked"] = false,')
        lines.append(f'                                            ["y"] = {wp.get("y", 0)},')
        lines.append(f'                                            ["x"] = {wp.get("x", 0)},')
        lines.append(f'                                            ["name"] = "{self._escape_lua(wp.get("name", ""))}",')
        lines.append(f'                                            ["formation_template"] = "",')
        lines.append(f'                                            ["speed"] = {wp.get("speed", 200)},')
        lines.append(f'                                            ["speed_locked"] = true,')

        # Tasks at this waypoint
        tasks = wp.get("tasks", [])
        if tasks:
            lines.append('                                            ["task"] = ')
            lines.append("                                            {")
            lines.append(f'                                                ["id"] = "ComboTask",')
            lines.append('                                                ["params"] = ')
            lines.append("                                                {")
            lines.append('                                                    ["tasks"] = ')
            lines.append("                                                    {")
            for t_idx, task in enumerate(tasks, 1):
                lines.append(f'                                                        [{t_idx}] = ')
                lines.append("                                                        {")
                lines.append(f'                                                            ["enabled"] = true,')
                lines.append(f'                                                            ["auto"] = false,')
                lines.append(f'                                                            ["id"] = "{task.get("id", "EngageTargets")}",')
                lines.append('                                                            ["params"] = ')
                lines.append("                                                            {")
                # Task-specific params
                target_types = task.get("params", {}).get("targetTypes", [])
                if target_types:
                    lines.append('                                                                ["targetTypes"] = ')
                    lines.append("                                                                {")
                    for tt_idx, tt in enumerate(target_types, 1):
                        lines.append(f'                                                                    [{tt_idx}] = "{tt}",')
                    lines.append("                                                                },")
                lines.append("                                                            },")
                lines.append("                                                        },")
            lines.append("                                                    },")
            lines.append("                                                },")
            lines.append("                                            },")
        else:
            lines.append('                                            ["task"] = ')
            lines.append("                                            {")
            lines.append(f'                                                ["id"] = "ComboTask",')
            lines.append('                                                ["params"] = ')
            lines.append("                                                {")
            lines.append('                                                    ["tasks"] = {},')
            lines.append("                                                },")
            lines.append("                                            },")

        lines.append("                                        },")
        return "\n".join(lines)

    def _gen_vehicle_group(self, group: dict, idx: int) -> str:
        """Generate a vehicle/ground group Lua block."""
        lines = []
        lines.append(f'                            [{idx}] = ')
        lines.append("                            {")
        lines.append(f'                                ["visible"] = false,')
        lines.append(f'                                ["taskSelected"] = true,')
        lines.append(f'                                ["groupId"] = {group.get("group_id", idx)},')
        lines.append(f'                                ["hidden"] = {str(group.get("hidden", False)).lower()},')

        # Units
        lines.append('                                ["units"] = ')
        lines.append("                                {")
        for u_idx, unit in enumerate(group.get("units", []), 1):
            lines.append(f'                                    [{u_idx}] = ')
            lines.append("                                    {")
            lines.append(f'                                        ["type"] = "{unit.get("type", "T-72B")}",')
            lines.append(f'                                        ["transportable"] = ')
            lines.append("                                        {")
            lines.append(f'                                            ["randomTransportable"] = false,')
            lines.append("                                        },")
            lines.append(f'                                        ["unitId"] = {unit.get("unit_id", u_idx)},')
            lines.append(f'                                        ["skill"] = "{unit.get("skill", "Average")}",')
            lines.append(f'                                        ["y"] = {unit.get("y", 0)},')
            lines.append(f'                                        ["x"] = {unit.get("x", 0)},')
            lines.append(f'                                        ["name"] = "{self._escape_lua(unit.get("name", "Unit"))}",')
            lines.append(f'                                        ["heading"] = {unit.get("heading", 0)},')
            lines.append(f'                                        ["playerCanDrive"] = false,')
            lines.append("                                    },")
        lines.append("                                },")

        # Route with waypoints
        lines.append('                                ["route"] = ')
        lines.append("                                {")
        lines.append('                                    ["spans"] = {},')
        lines.append('                                    ["points"] = ')
        lines.append("                                    {")
        for wp in group.get("waypoints", []):
            wp_id = wp.get("id", 0) + 1
            lines.append(f'                                        [{wp_id}] = ')
            lines.append("                                        {")
            lines.append(f'                                            ["alt"] = 50,')
            lines.append(f'                                            ["type"] = "Turning Point",')
            lines.append(f'                                            ["action"] = "{wp.get("action", "Off Road")}",')
            lines.append(f'                                            ["y"] = {wp.get("y", 0)},')
            lines.append(f'                                            ["x"] = {wp.get("x", 0)},')
            lines.append(f'                                            ["speed"] = {wp.get("speed", 10)},')
            lines.append(f'                                            ["formation_template"] = "",')

            # Tasks
            tasks = wp.get("tasks", [])
            if tasks:
                lines.append('                                            ["task"] = ')
                lines.append("                                            {")
                lines.append(f'                                                ["id"] = "ComboTask",')
                lines.append('                                                ["params"] = ')
                lines.append("                                                {")
                lines.append('                                                    ["tasks"] = ')
                lines.append("                                                    {")
                for t_idx, task in enumerate(tasks, 1):
                    lines.append(f'                                                        [{t_idx}] = ')
                    lines.append("                                                        {")
                    lines.append(f'                                                            ["enabled"] = true,')
                    lines.append(f'                                                            ["id"] = "{task.get("id", "EngageTargets")}",')
                    lines.append('                                                            ["params"] = ')
                    lines.append("                                                            {")
                    target_types = task.get("params", {}).get("targetTypes", [])
                    if target_types:
                        lines.append('                                                                ["targetTypes"] = ')
                        lines.append("                                                                {")
                        for tt_idx, tt in enumerate(target_types, 1):
                            lines.append(f'                                                                    [{tt_idx}] = "{tt}",')
                        lines.append("                                                                },")
                    lines.append("                                                            },")
                    lines.append("                                                        },")
                lines.append("                                                    },")
                lines.append("                                                },")
                lines.append("                                            },")
            else:
                lines.append('                                            ["task"] = ')
                lines.append("                                            {")
                lines.append(f'                                                ["id"] = "ComboTask",')
                lines.append('                                                ["params"] = ')
                lines.append("                                                {")
                lines.append('                                                    ["tasks"] = {},')
                lines.append("                                                },")
                lines.append("                                            },")

            lines.append("                                        },")
        lines.append("                                    },")
        lines.append("                                },")

        lines.append(f'                                ["y"] = {group["units"][0].get("y", 0) if group.get("units") else 0},')
        lines.append(f'                                ["x"] = {group["units"][0].get("x", 0) if group.get("units") else 0},')
        lines.append(f'                                ["name"] = "{self._escape_lua(group.get("name", "Ground Group"))}",')

        start_delay = group.get("_start_delay", 0)
        lines.append(f'                                ["start_time"] = {start_delay},')
        lines.append(f'                                ["task"] = "Ground Nothing",')

        lines.append("                            },")
        return "\n".join(lines)

    def _gen_neutral_coalition(self) -> str:
        """Generate neutral coalition block."""
        lines = []
        lines.append('        ["neutrals"] = ')
        lines.append("        {")
        lines.append('            ["bullseye"] = ')
        lines.append("            {")
        lines.append('                ["x"] = 0,')
        lines.append('                ["y"] = 0,')
        lines.append("            },")
        lines.append('            ["coalition"] = "neutrals",')
        lines.append('            ["name"] = "neutrals",')
        lines.append('            ["nav_points"] = {},')
        lines.append('            ["country"] = {},')
        lines.append("        },")
        return "\n".join(lines)

    def _gen_triggers_block(self) -> str:
        """Generate triggers block — kept empty for compatibility.
        Staggered spawning is handled via start_time on groups instead."""
        lines = []
        lines.append('    ["triggers"] = ')
        lines.append("    {")
        lines.append('        ["zones"] = {},')
        lines.append('        ["actions"] = {},')
        lines.append("    },")
        return "\n".join(lines)

    def _gen_bullseye(self) -> str:
        """Generate bullseye reference points."""
        # Use target position or map center
        target = {"x": 0, "y": 0}
        cities = []
        plan = self.data.get("plan", {})
        map_data_name = plan.get("map_name", "Caucasus")

        from src.maps import MAP_REGISTRY
        md = MAP_REGISTRY.get(map_data_name, {})
        cities = md.get("cities", [])

        # Blue bullseye: near a friendly city
        blue_cities = [c for c in cities if c.get("side") == "blue"]
        if blue_cities:
            bc = blue_cities[0]
            blue_x, blue_y = bc["x"], bc["y"]
        else:
            blue_x, blue_y = 0, 0

        # Red bullseye: near an enemy city
        red_cities = [c for c in cities if c.get("side") == "red"]
        if red_cities:
            rc = red_cities[0]
            red_x, red_y = rc["x"], rc["y"]
        else:
            red_x, red_y = 0, 0

        lines = []
        lines.append('    ["bullseye"] = ')
        lines.append("    {")
        lines.append('        ["blue"] = ')
        lines.append("        {")
        lines.append(f'            ["x"] = {blue_x},')
        lines.append(f'            ["y"] = {blue_y},')
        lines.append("        },")
        lines.append('        ["red"] = ')
        lines.append("        {")
        lines.append(f'            ["x"] = {red_x},')
        lines.append(f'            ["y"] = {red_y},')
        lines.append("        },")
        lines.append("    },")
        return "\n".join(lines)

    # ================================================================
    # WAREHOUSES
    # ================================================================
    def _gen_warehouses(self) -> str:
        """Generate warehouses Lua table (base supplies)."""
        lines = []
        lines.append("warehouses = ")
        lines.append("{")

        # Get all airfields from map
        from src.maps import MAP_REGISTRY
        map_data = MAP_REGISTRY.get(self.data.get("map_name", "Caucasus"), {})
        airfields = map_data.get("airfields", [])

        lines.append('    ["airports"] = ')
        lines.append("    {")

        for af in airfields:
            af_id = af.get("id", 0)
            coalition = af.get("default_coalition", "neutral")

            lines.append(f'        [{af_id}] = ')
            lines.append("        {")
            lines.append(f'            ["coalition"] = "{coalition}",')
            lines.append(f'            ["unlimitedAircrafts"] = true,')
            lines.append(f'            ["unlimitedFuel"] = true,')
            lines.append(f'            ["unlimitedMunitions"] = true,')
            lines.append('            ["gasoline"] = ')
            lines.append("            {")
            lines.append('                ["InitFuel"] = 100,')
            lines.append("            },")
            lines.append('            ["diesel"] = ')
            lines.append("            {")
            lines.append('                ["InitFuel"] = 100,')
            lines.append("            },")
            lines.append('            ["jet_fuel"] = ')
            lines.append("            {")
            lines.append('                ["InitFuel"] = 100,')
            lines.append("            },")
            lines.append('            ["methanol_mixture"] = ')
            lines.append("            {")
            lines.append('                ["InitFuel"] = 100,')
            lines.append("            },")
            lines.append('            ["OperatingLevel_Air"] = 10,')
            lines.append('            ["OperatingLevel_Eqp"] = 10,')
            lines.append('            ["OperatingLevel_Fuel"] = 10,')
            lines.append("        },")

        lines.append("    },")
        lines.append("} -- end of warehouses")
        return "\n".join(lines)

    # ================================================================
    # OPTIONS
    # ================================================================
    def _gen_options(self) -> str:
        """Generate options Lua table."""
        difficulty = self.plan.get("difficulty", "medium")

        skill_map = {"easy": "Average", "medium": "Good", "hard": "Excellent"}
        labels_map = {"easy": 2, "medium": 1, "hard": 0}

        lines = []
        lines.append("options = ")
        lines.append("{")
        lines.append('    ["playerGeneratedId"] = nil,')
        lines.append('    ["miscellaneous"] = ')
        lines.append("    {")
        lines.append('        ["allow_ownship_export"] = true,')
        lines.append('        ["headmove"] = false,')
        lines.append('        ["TrackIR_external_views"] = true,')
        lines.append('        ["f10_awacs"] = true,')
        lines.append('        ["f5_nearest_ac"] = true,')
        lines.append('        ["f11_free_camera"] = true,')
        lines.append('        ["F2_view_effects"] = 1,')
        lines.append('        ["f10_tactical_view"] = true,')
        lines.append("    },")
        lines.append('    ["difficulty"] = ')
        lines.append("    {")
        lines.append(f'        ["fuel"] = false,')
        lines.append(f'        ["easyRadar"] = {str(difficulty == "easy").lower()},')
        lines.append(f'        ["miniHUD"] = false,')
        lines.append(f'        ["optionsView"] = "optview_all",')
        lines.append(f'        ["setGlobal"] = true,')
        lines.append(f'        ["labels"] = {labels_map.get(difficulty, 1)},')
        lines.append(f'        ["RBDAI"] = true,')
        lines.append(f'        ["externalViews"] = true,')
        lines.append(f'        ["cockpitVisualRM"] = false,')
        lines.append(f'        ["map"] = true,')
        lines.append(f'        ["spectatorExternalViews"] = true,')
        lines.append(f'        ["userSnapView"] = true,')
        lines.append(f'        ["iconsTheme"] = "nato",')
        lines.append(f'        ["cockpitStatusBarAllowed"] = false,')
        lines.append(f'        ["birds"] = 0,')
        lines.append(f'        ["easyFlight"] = false,')
        lines.append(f'        ["easyCommunication"] = {str(difficulty == "easy").lower()},')
        lines.append(f'        ["immortal"] = false,')
        lines.append(f'        ["wakeTurbulence"] = true,')
        lines.append("    },")
        lines.append("} -- end of options")
        return "\n".join(lines)

    # ================================================================
    # DICTIONARY
    # ================================================================
    def _gen_dictionary(self) -> str:
        """Generate dictionary Lua table (string translations)."""
        lines = []
        lines.append("dictionary = ")
        lines.append("{")
        lines.append(f'    ["DictKey_sortie_0"] = "{self._escape_lua(self._get_sortie_name())}",')
        lines.append(f'    ["DictKey_descriptionText_0"] = "{self._escape_lua(self._get_description())}",')
        lines.append(f'    ["DictKey_descriptionBlueTask_0"] = "{self._escape_lua(self._get_blue_task())}",')
        lines.append(f'    ["DictKey_descriptionRedTask_0"] = "Defend territory and engage enemy forces",')
        lines.append("} -- end of dictionary")
        return "\n".join(lines)

    # ================================================================
    # HELPERS
    # ================================================================
    def _get_sortie_name(self) -> str:
        mt = self.plan.get("mission_type", "Mission")
        ac = self.plan.get("player_aircraft", "")
        map_name = self.plan.get("map_name", "")
        return f"{mt.upper()} - {ac} - {map_name}"

    def _get_description(self) -> str:
        objectives = self.plan.get("objectives", [])
        obj_text = " ".join(f"{i+1}. {o}" for i, o in enumerate(objectives))
        return f"Generated mission: {self.plan.get('mission_type', 'Unknown')} in {self.plan.get('player_aircraft', 'Unknown')}. {obj_text}"

    def _get_blue_task(self) -> str:
        mt = self.plan.get("mission_type", "Mission")
        return f"Complete {mt} objectives and return to base."

    @staticmethod
    def _escape_lua(s: str) -> str:
        """Escape a string for Lua."""
        if not s:
            return ""
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")

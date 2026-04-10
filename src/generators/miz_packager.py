"""
MIZ Packager
Packages generated Lua files into a valid .miz file (renamed .zip).
A DCS .miz file is a ZIP archive containing:
  - mission       (Lua table)
  - warehouses    (Lua table)
  - options       (Lua table)
  - theatre       (plain text — just the map name)
  - l10n/DEFAULT/dictionary  (Lua table)
  - l10n/DEFAULT/mapResource (Lua table — usually empty)
"""

import zipfile
import os

from src.generators.kneeboard_generator import generate_kneeboard_png, get_dcs_aircraft_folder


class MizPackager:
    """Package Lua files into a .miz archive."""

    def package(self, lua_files: dict[str, str], briefing_text: str, output_path: str,
                aircraft_type: str = ""):
        """
        Create a .miz file from generated Lua content.

        Args:
            lua_files: Dict mapping filename to Lua content string
                Expected keys: mission, warehouses, options, theatre, dictionary
            briefing_text: Briefing text — also rendered as a kneeboard PNG inside the .miz
            output_path: Full path for the output .miz file
            aircraft_type: DCS unit type string used to place kneeboard in the right folder
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as miz:
            # Main mission file
            if "mission" in lua_files:
                miz.writestr("mission", lua_files["mission"])

            # Warehouses
            if "warehouses" in lua_files:
                miz.writestr("warehouses", lua_files["warehouses"])

            # Options
            if "options" in lua_files:
                miz.writestr("options", lua_files["options"])

            # Theatre (just the map name as plain text)
            if "theatre" in lua_files:
                miz.writestr("theatre", lua_files["theatre"])

            # Dictionary (in l10n folder)
            if "dictionary" in lua_files:
                miz.writestr("l10n/DEFAULT/dictionary", lua_files["dictionary"])

            # Map resource (usually empty but required)
            miz.writestr("l10n/DEFAULT/mapResource", self._gen_map_resource())

            # Kneeboard card — rendered as PNG inside KNEEBOARD/<aircraft>/
            if briefing_text:
                try:
                    png_bytes = generate_kneeboard_png(briefing_text, aircraft_type)
                    folder = get_dcs_aircraft_folder(aircraft_type) if aircraft_type else "COMMON"
                    miz.writestr(f"KNEEBOARD/{folder}/01_briefing.png", png_bytes)
                except Exception as e:
                    print(f"    Warning: kneeboard generation failed — {e}")

        print(f"    .miz file: {os.path.getsize(output_path)} bytes")

    @staticmethod
    def _gen_map_resource() -> str:
        """Generate an empty mapResource Lua table."""
        return "mapResource = \n{\n} -- end of mapResource\n"

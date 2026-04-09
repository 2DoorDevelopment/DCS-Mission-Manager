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


class MizPackager:
    """Package Lua files into a .miz archive."""

    def package(self, lua_files: dict[str, str], briefing_text: str, output_path: str):
        """
        Create a .miz file from generated Lua content.

        Args:
            lua_files: Dict mapping filename to Lua content string
                Expected keys: mission, warehouses, options, theatre, dictionary
            briefing_text: Briefing text (saved separately, not in .miz)
            output_path: Full path for the output .miz file
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

        print(f"    .miz file: {os.path.getsize(output_path)} bytes")

    @staticmethod
    def _gen_map_resource() -> str:
        """Generate an empty mapResource Lua table."""
        return "mapResource = \n{\n} -- end of mapResource\n"

@echo off
REM ══════════════════════════════════════════════════════════
REM  DCS Mission Generator — Build Windows EXE
REM  Requires: pip install pyinstaller
REM ══════════════════════════════════════════════════════════

echo.
echo  DCS Mission Generator — EXE Builder
echo  ════════════════════════════════════
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Install Python 3.10+ first.
    pause
    exit /b 1
)

REM Install PyInstaller if needed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  Installing PyInstaller...
    pip install pyinstaller
)

echo  Building EXE...
echo.

pyinstaller ^
    --name "DCS_Mission_Generator" ^
    --onefile ^
    --windowed ^
    --add-data "src;src" ^
    --add-data "custom_aircraft;custom_aircraft" ^
    --hidden-import "src.llm" ^
    --hidden-import "src.llm.ollama_client" ^
    --hidden-import "src.llm.mission_parser" ^
    --hidden-import "src.generators" ^
    --hidden-import "src.generators.mission_builder" ^
    --hidden-import "src.generators.lua_generator" ^
    --hidden-import "src.generators.miz_packager" ^
    --hidden-import "src.generators.briefing_generator" ^
    --hidden-import "src.maps" ^
    --hidden-import "src.maps.caucasus" ^
    --hidden-import "src.maps.syria" ^
    --hidden-import "src.maps.cold_war_germany" ^
    --hidden-import "src.units" ^
    --hidden-import "src.naming" ^
    --hidden-import "src.difficulty" ^
    --hidden-import "src.campaign" ^
    --hidden-import "src.dcs_detect" ^
    --hidden-import "src.custom_mods" ^
    --hidden-import "src.flight_profile" ^
    --hidden-import "src.callsigns" ^
    --hidden-import "src.mission_events" ^
    gui.py

if errorlevel 1 (
    echo.
    echo  BUILD FAILED. Check errors above.
    pause
    exit /b 1
)

echo.
echo  ✓ Build complete!
echo  EXE location: dist\DCS_Mission_Generator.exe
echo.
echo  Copy the EXE anywhere and run it.
echo  The custom_aircraft folder will be created automatically on first run.
echo.
pause

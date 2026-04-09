#!/usr/bin/env python3
"""
DCS Mission Generator — GUI Frontend
Dark military-themed interface using tkinter (no external dependencies).
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import os
import sys
from pathlib import Path

# Add project root to path
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    BASE_DIR = Path(sys.executable).parent
    sys.path.insert(0, str(BASE_DIR))
    # PyInstaller extracts data files to a temp dir
    BUNDLE_DIR = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else BASE_DIR
else:
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, str(BASE_DIR))
    BUNDLE_DIR = BASE_DIR

from src.llm.ollama_client import OllamaClient
from src.llm.mission_parser import MissionParser
from src.generators.mission_builder import MissionBuilder
from src.generators.lua_generator import LuaGenerator
from src.generators.miz_packager import MizPackager
from src.generators.briefing_generator import BriefingGenerator
from src.maps import MAP_REGISTRY
from src.units import PLAYER_AIRCRAFT, MISSION_TEMPLATES
from src.naming import generate_mission_name, generate_filename
from src.difficulty import scale_plan
from src.dcs_detect import find_dcs_missions_folder, deploy_mission, deploy_briefing
from src.custom_mods import load_custom_aircraft, register_custom_aircraft, ensure_custom_dir

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════
# COLORS — dark military theme
# ══════════════════════════════════════════════════════════
COLORS = {
    "bg_dark": "#0a0e14",
    "bg_panel": "#111820",
    "bg_input": "#1a2230",
    "bg_button": "#1e3a2f",
    "bg_button_hover": "#2a5440",
    "bg_button_generate": "#2d5a1e",
    "bg_button_generate_hover": "#3d7a2e",
    "bg_accent": "#1a3045",
    "fg_main": "#c8d6e5",
    "fg_dim": "#6b7b8d",
    "fg_bright": "#e8f0f8",
    "fg_accent": "#4ecdc4",
    "fg_warning": "#f0a030",
    "fg_success": "#4ecdc4",
    "fg_error": "#e74c3c",
    "border": "#2a3a4a",
    "highlight": "#3a5a3a",
}


class DCSMissionGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DCS Mission Generator v2.0")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        self.root.configure(bg=COLORS["bg_dark"])

        # State
        self.client = OllamaClient(model="llama3.1:8b")
        self.ollama_connected = False
        self.dcs_folder = find_dcs_missions_folder()
        self.last_miz_path = None

        # Load custom aircraft
        custom_dir = ensure_custom_dir()
        custom = load_custom_aircraft(custom_dir)
        if custom:
            register_custom_aircraft(custom)

        # Build aircraft and mission type lists from current state
        self.aircraft_list = list(PLAYER_AIRCRAFT.keys())
        self.aircraft_display = [PLAYER_AIRCRAFT[k].get("display_name", k) for k in self.aircraft_list]
        self.mission_types = list(MISSION_TEMPLATES.keys())
        self.map_list = list(MAP_REGISTRY.keys())
        self.map_display = [MAP_REGISTRY[k]["display_name"] for k in self.map_list]

        # Style
        self._setup_styles()
        self._build_ui()
        self._check_ollama()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Dark.TFrame", background=COLORS["bg_dark"])
        style.configure("Panel.TFrame", background=COLORS["bg_panel"])
        style.configure("Dark.TLabel", background=COLORS["bg_dark"],
                         foreground=COLORS["fg_main"], font=("Consolas", 10))
        style.configure("Header.TLabel", background=COLORS["bg_dark"],
                         foreground=COLORS["fg_accent"], font=("Consolas", 14, "bold"))
        style.configure("Status.TLabel", background=COLORS["bg_panel"],
                         foreground=COLORS["fg_dim"], font=("Consolas", 9))
        style.configure("Dark.TLabelframe", background=COLORS["bg_panel"],
                         foreground=COLORS["fg_accent"])
        style.configure("Dark.TLabelframe.Label", background=COLORS["bg_panel"],
                         foreground=COLORS["fg_accent"], font=("Consolas", 10, "bold"))
        style.configure("Dark.TCombobox", fieldbackground=COLORS["bg_input"],
                         background=COLORS["bg_input"], foreground=COLORS["fg_main"],
                         selectbackground=COLORS["highlight"],
                         arrowcolor=COLORS["fg_accent"])
        style.map("Dark.TCombobox",
                   fieldbackground=[("readonly", COLORS["bg_input"]),
                                    ("focus", COLORS["bg_input"])],
                   foreground=[("readonly", COLORS["fg_main"])],
                   selectbackground=[("readonly", COLORS["highlight"])],
                   selectforeground=[("readonly", COLORS["fg_bright"])])
        style.configure("Dark.TCheckbutton", background=COLORS["bg_panel"],
                         foreground=COLORS["fg_main"], font=("Consolas", 10))
        style.map("Dark.TCheckbutton",
                   background=[("active", COLORS["bg_panel"])])

        # Fix the dropdown listbox colors on Windows
        # This targets the Tk popdown listbox that comboboxes use
        self.root.option_add("*TCombobox*Listbox.background", COLORS["bg_input"])
        self.root.option_add("*TCombobox*Listbox.foreground", COLORS["fg_main"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLORS["highlight"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", COLORS["fg_bright"])
        self.root.option_add("*TCombobox*Listbox.font", ("Consolas", 10))

    def _build_ui(self):
        # ── Title bar ──
        title_frame = tk.Frame(self.root, bg=COLORS["bg_dark"], pady=8)
        title_frame.pack(fill="x")

        tk.Label(title_frame, text="DCS MISSION GENERATOR",
                 bg=COLORS["bg_dark"], fg=COLORS["fg_accent"],
                 font=("Consolas", 16, "bold")).pack(side="left", padx=15)

        self.status_label = tk.Label(title_frame, text="",
                                     bg=COLORS["bg_dark"], fg=COLORS["fg_dim"],
                                     font=("Consolas", 9))
        self.status_label.pack(side="right", padx=15)

        # ── Main content — two columns ──
        main_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left column — controls
        left = tk.Frame(main_frame, bg=COLORS["bg_panel"], relief="flat",
                         bd=1, highlightbackground=COLORS["border"], highlightthickness=1)
        left.pack(side="left", fill="both", expand=False, padx=(0, 5))
        left.configure(width=340)
        left.pack_propagate(False)

        # Right column — output
        right = tk.Frame(main_frame, bg=COLORS["bg_panel"], relief="flat",
                          bd=1, highlightbackground=COLORS["border"], highlightthickness=1)
        right.pack(side="right", fill="both", expand=True)

        self._build_controls(left)
        self._build_output(right)

        # ── Bottom bar ──
        bottom = tk.Frame(self.root, bg=COLORS["bg_dark"], pady=5)
        bottom.pack(fill="x")

        self.bottom_status = tk.Label(bottom, text="Ready",
                                       bg=COLORS["bg_dark"], fg=COLORS["fg_dim"],
                                       font=("Consolas", 9))
        self.bottom_status.pack(side="left", padx=15)

    def _build_controls(self, parent):
        pad = {"padx": 10, "pady": 3}

        # ── Natural Language Input ──
        nl_frame = tk.LabelFrame(parent, text=" DESCRIBE YOUR MISSION ",
                                  bg=COLORS["bg_panel"], fg=COLORS["fg_accent"],
                                  font=("Consolas", 9, "bold"),
                                  relief="flat", bd=1)
        nl_frame.pack(fill="x", padx=8, pady=(8, 4))

        self.nl_input = tk.Text(nl_frame, height=4, wrap="word",
                                 bg=COLORS["bg_input"], fg=COLORS["fg_bright"],
                                 insertbackground=COLORS["fg_accent"],
                                 font=("Consolas", 10), relief="flat", bd=0)
        self.nl_input.pack(fill="x", padx=6, pady=6)
        self.nl_input.insert("1.0", "SEAD mission in the F-16 on Caucasus with SA-6 and SA-11")

        # ── OR: Manual Selection ──
        manual_frame = tk.LabelFrame(parent, text=" OR SELECT MANUALLY ",
                                      bg=COLORS["bg_panel"], fg=COLORS["fg_accent"],
                                      font=("Consolas", 9, "bold"), relief="flat", bd=1)
        manual_frame.pack(fill="x", padx=8, pady=4)

        # Aircraft
        tk.Label(manual_frame, text="Aircraft:", bg=COLORS["bg_panel"],
                 fg=COLORS["fg_main"], font=("Consolas", 9)).grid(
                     row=0, column=0, sticky="w", **pad)
        self.aircraft_var = tk.StringVar(value=self.aircraft_display[0])
        aircraft_cb = ttk.Combobox(manual_frame, textvariable=self.aircraft_var,
                                    values=self.aircraft_display, state="readonly",
                                    width=22, style="Dark.TCombobox")
        aircraft_cb.grid(row=0, column=1, sticky="ew", **pad)

        # Map
        tk.Label(manual_frame, text="Map:", bg=COLORS["bg_panel"],
                 fg=COLORS["fg_main"], font=("Consolas", 9)).grid(
                     row=1, column=0, sticky="w", **pad)
        self.map_var = tk.StringVar(value=self.map_display[0])
        map_cb = ttk.Combobox(manual_frame, textvariable=self.map_var,
                               values=self.map_display, state="readonly",
                               width=22, style="Dark.TCombobox")
        map_cb.grid(row=1, column=1, sticky="ew", **pad)

        # Mission type
        tk.Label(manual_frame, text="Mission:", bg=COLORS["bg_panel"],
                 fg=COLORS["fg_main"], font=("Consolas", 9)).grid(
                     row=2, column=0, sticky="w", **pad)
        self.mission_var = tk.StringVar(value="SEAD")
        mission_cb = ttk.Combobox(manual_frame, textvariable=self.mission_var,
                                   values=self.mission_types, state="readonly",
                                   width=22, style="Dark.TCombobox")
        mission_cb.grid(row=2, column=1, sticky="ew", **pad)

        # Difficulty
        tk.Label(manual_frame, text="Difficulty:", bg=COLORS["bg_panel"],
                 fg=COLORS["fg_main"], font=("Consolas", 9)).grid(
                     row=3, column=0, sticky="w", **pad)
        self.difficulty_var = tk.StringVar(value="medium")
        diff_cb = ttk.Combobox(manual_frame, textvariable=self.difficulty_var,
                                values=["easy", "medium", "hard"], state="readonly",
                                width=22, style="Dark.TCombobox")
        diff_cb.grid(row=3, column=1, sticky="ew", **pad)

        # Weather
        tk.Label(manual_frame, text="Weather:", bg=COLORS["bg_panel"],
                 fg=COLORS["fg_main"], font=("Consolas", 9)).grid(
                     row=4, column=0, sticky="w", **pad)
        self.weather_var = tk.StringVar(value="clear")
        weather_cb = ttk.Combobox(manual_frame, textvariable=self.weather_var,
                                   values=["clear", "scattered", "overcast", "rain", "storm"],
                                   state="readonly", width=22, style="Dark.TCombobox")
        weather_cb.grid(row=4, column=1, sticky="ew", **pad)

        # Time
        tk.Label(manual_frame, text="Time:", bg=COLORS["bg_panel"],
                 fg=COLORS["fg_main"], font=("Consolas", 9)).grid(
                     row=5, column=0, sticky="w", **pad)
        self.time_var = tk.StringVar(value="morning")
        time_cb = ttk.Combobox(manual_frame, textvariable=self.time_var,
                                values=["morning", "afternoon", "evening", "night"],
                                state="readonly", width=22, style="Dark.TCombobox")
        time_cb.grid(row=5, column=1, sticky="ew", **pad)

        manual_frame.columnconfigure(1, weight=1)

        # ── Options ──
        opt_frame = tk.LabelFrame(parent, text=" OPTIONS ",
                                   bg=COLORS["bg_panel"], fg=COLORS["fg_accent"],
                                   font=("Consolas", 9, "bold"), relief="flat", bd=1)
        opt_frame.pack(fill="x", padx=8, pady=4)

        self.wingman_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="Include wingman",
                        variable=self.wingman_var,
                        bg=COLORS["bg_panel"], fg=COLORS["fg_main"],
                        selectcolor=COLORS["bg_input"],
                        activebackground=COLORS["bg_panel"],
                        font=("Consolas", 9)).pack(anchor="w", padx=10, pady=2)

        self.ground_war_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="Ground war active",
                        variable=self.ground_war_var,
                        bg=COLORS["bg_panel"], fg=COLORS["fg_main"],
                        selectcolor=COLORS["bg_input"],
                        activebackground=COLORS["bg_panel"],
                        font=("Consolas", 9)).pack(anchor="w", padx=10, pady=2)

        self.auto_deploy_var = tk.BooleanVar(value=bool(self.dcs_folder))
        tk.Checkbutton(opt_frame, text="Auto-deploy to DCS",
                        variable=self.auto_deploy_var,
                        bg=COLORS["bg_panel"], fg=COLORS["fg_main"],
                        selectcolor=COLORS["bg_input"],
                        activebackground=COLORS["bg_panel"],
                        font=("Consolas", 9)).pack(anchor="w", padx=10, pady=2)

        # ── Buttons ──
        btn_frame = tk.Frame(parent, bg=COLORS["bg_panel"])
        btn_frame.pack(fill="x", padx=8, pady=(8, 4))

        self.gen_nl_btn = tk.Button(
            btn_frame, text="⚡ GENERATE FROM DESCRIPTION",
            command=self._on_generate_nl,
            bg=COLORS["bg_button_generate"], fg=COLORS["fg_bright"],
            activebackground=COLORS["bg_button_generate_hover"],
            activeforeground=COLORS["fg_bright"],
            font=("Consolas", 10, "bold"), relief="flat", bd=0, pady=8)
        self.gen_nl_btn.pack(fill="x", pady=(0, 4))

        self.gen_manual_btn = tk.Button(
            btn_frame, text="▶ GENERATE FROM SELECTIONS",
            command=self._on_generate_manual,
            bg=COLORS["bg_button"], fg=COLORS["fg_main"],
            activebackground=COLORS["bg_button_hover"],
            activeforeground=COLORS["fg_bright"],
            font=("Consolas", 10), relief="flat", bd=0, pady=6)
        self.gen_manual_btn.pack(fill="x", pady=(0, 4))

        self.open_folder_btn = tk.Button(
            btn_frame, text="📁 Open Output Folder",
            command=self._on_open_folder,
            bg=COLORS["bg_accent"], fg=COLORS["fg_main"],
            activebackground=COLORS["bg_button_hover"],
            font=("Consolas", 9), relief="flat", bd=0, pady=4)
        self.open_folder_btn.pack(fill="x")

    def _build_output(self, parent):
        # Tab-like header
        header = tk.Frame(parent, bg=COLORS["bg_panel"])
        header.pack(fill="x", padx=8, pady=(8, 0))

        tk.Label(header, text="OUTPUT / BRIEFING",
                 bg=COLORS["bg_panel"], fg=COLORS["fg_accent"],
                 font=("Consolas", 10, "bold")).pack(side="left")

        self.copy_btn = tk.Button(header, text="Copy", command=self._on_copy,
                                   bg=COLORS["bg_accent"], fg=COLORS["fg_main"],
                                   font=("Consolas", 8), relief="flat", bd=0, padx=8)
        self.copy_btn.pack(side="right", padx=4)

        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            parent, wrap="word",
            bg=COLORS["bg_input"], fg=COLORS["fg_main"],
            insertbackground=COLORS["fg_accent"],
            font=("Consolas", 9), relief="flat", bd=0,
            selectbackground=COLORS["highlight"])
        self.output_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.output_text.insert("1.0", "Ready. Describe a mission or select options and generate.\n\n"
                                       "Natural language mode uses Ollama for smart parsing.\n"
                                       "Manual mode bypasses the LLM entirely.\n")
        self.output_text.configure(state="disabled")

    def _log(self, text, tag=None):
        """Append text to the output area."""
        self.output_text.configure(state="normal")
        self.output_text.insert("end", text + "\n")
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

    def _clear_output(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")

    def _set_status(self, text, color=None):
        self.bottom_status.configure(text=text, fg=color or COLORS["fg_dim"])

    def _set_buttons_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.gen_nl_btn.configure(state=state)
        self.gen_manual_btn.configure(state=state)

    def _check_ollama(self):
        """Check Ollama connection in background."""
        def check():
            connected = self.client.check_connection()
            self.ollama_connected = connected
            self.root.after(0, lambda: self.status_label.configure(
                text=f"Ollama: {'Connected ✓' if connected else 'Offline ✗'}  |  "
                     f"DCS: {'Found ✓' if self.dcs_folder else 'Not found'}",
                fg=COLORS["fg_success"] if connected else COLORS["fg_warning"]))
        threading.Thread(target=check, daemon=True).start()

    def _on_generate_nl(self):
        """Generate from natural language description."""
        description = self.nl_input.get("1.0", "end").strip()
        if not description:
            messagebox.showwarning("Empty", "Enter a mission description first.")
            return
        self._generate_mission(description=description)

    def _on_generate_manual(self):
        """Generate from manual dropdown selections."""
        # Map display name back to key
        ac_idx = self.aircraft_display.index(self.aircraft_var.get()) \
            if self.aircraft_var.get() in self.aircraft_display else 0
        map_idx = self.map_display.index(self.map_var.get()) \
            if self.map_var.get() in self.map_display else 0

        plan = {
            "map_name": self.map_list[map_idx],
            "player_aircraft": self.aircraft_list[ac_idx],
            "mission_type": self.mission_var.get(),
            "player_airfield": "AUTO",
            "time_of_day": self.time_var.get(),
            "weather": self.weather_var.get(),
            "difficulty": self.difficulty_var.get(),
            "player_count": 1,
            "wingman": self.wingman_var.get(),
            "ground_war": {
                "enabled": self.ground_war_var.get(),
                "front_line_desc": "Dynamic",
                "blue_advancing": True,
                "red_advancing": True,
                "intensity": "medium",
            },
            "special_requests": "",
        }
        self._generate_mission(plan=plan)

    def _generate_mission(self, description=None, plan=None):
        """Run generation in a background thread."""
        self._set_buttons_enabled(False)
        self._clear_output()
        self._set_status("Generating...", COLORS["fg_accent"])
        self._log("═" * 50)
        self._log("  GENERATING MISSION...")
        self._log("═" * 50)

        def run():
            try:
                if description:
                    self._log(f"\n  Description: \"{description}\"\n")
                    parser = MissionParser(self.client)
                    self._log("  Parsing with LLM..." if self.ollama_connected
                              else "  Parsing with rule engine (Ollama offline)...")
                    mission_plan = parser.parse_description(description)
                    if not mission_plan:
                        self.root.after(0, lambda: self._log("  ERROR: Could not parse description."))
                        return
                else:
                    mission_plan = plan
                    # Fill defaults the parser would normally handle
                    from src.llm.mission_parser import MissionParser as MP
                    p = MP(self.client)
                    mission_plan = p._validate_and_fill(mission_plan, "")

                # Operation name
                op_name = generate_mission_name(mission_plan.get("mission_type", "general"))
                mission_plan["_operation_name"] = op_name
                self.root.after(0, lambda: self._log(f"\n  {op_name}\n"))

                # Show plan
                self.root.after(0, lambda: self._log_plan(mission_plan))

                # Scale difficulty
                self.root.after(0, lambda: self._log("  Applying difficulty scaling..."))
                scaled = scale_plan(mission_plan)

                # Build
                self.root.after(0, lambda: self._log("  Building mission structure..."))
                builder = MissionBuilder(scaled)
                data = builder.build()

                # Lua
                self.root.after(0, lambda: self._log("  Generating Lua files..."))
                lua_files = LuaGenerator(data).generate_all()

                # Briefing
                self.root.after(0, lambda: self._log("  Generating briefing..."))
                briefing = BriefingGenerator(data, scaled).generate()

                # Package
                filename = generate_filename(
                    mission_plan.get("mission_type", "mission"),
                    mission_plan.get("map_name", "unknown"),
                    op_name)
                output_path = OUTPUT_DIR / filename
                MizPackager().package(lua_files, briefing, str(output_path))

                # Save briefing
                briefing_path = output_path.with_suffix(".txt")
                with open(briefing_path, "w", encoding="utf-8") as f:
                    f.write(briefing)

                self.last_miz_path = output_path

                # Auto-deploy
                deployed_path = None
                if self.auto_deploy_var.get() and self.dcs_folder:
                    deployed_path = deploy_mission(output_path, self.dcs_folder)
                    deploy_briefing(briefing_path, self.dcs_folder)

                # Show results
                def show_results():
                    self._log(f"\n  ✓ Mission saved: {output_path.name}")
                    if deployed_path:
                        self._log(f"  ✓ Deployed to DCS: {deployed_path}")
                    else:
                        self._log(f"  ℹ Copy to: %USERPROFILE%\\Saved Games\\DCS\\Missions\\")
                    self._log(f"\n{'═' * 50}")
                    self._log("  KNEEBOARD BRIEFING")
                    self._log("═" * 50)
                    self._log(briefing)
                    self._set_status(f"✓ {op_name} — {output_path.name}", COLORS["fg_success"])

                self.root.after(0, show_results)

            except Exception as e:
                self.root.after(0, lambda: self._log(f"\n  ERROR: {e}"))
                self.root.after(0, lambda: self._set_status(f"Error: {e}", COLORS["fg_error"]))
                import traceback
                traceback.print_exc()
            finally:
                self.root.after(0, lambda: self._set_buttons_enabled(True))

        threading.Thread(target=run, daemon=True).start()

    def _log_plan(self, plan):
        self._log(f"  Map:        {plan.get('map_name', '?')}")
        self._log(f"  Aircraft:   {plan.get('player_aircraft', '?')}")
        self._log(f"  Mission:    {plan.get('mission_type', '?')}")
        self._log(f"  Difficulty: {plan.get('difficulty', 'medium').upper()}")
        self._log(f"  Weather:    {plan.get('weather', 'clear')}")
        self._log(f"  Departure:  {plan.get('player_airfield', 'AUTO')}")

        sams = plan.get("enemy_sam_sites", [])
        if sams:
            self._log(f"  SAMs:       {', '.join(s.get('type', '?') for s in sams)}")

        enemy_air = plan.get("enemy_air", [])
        if enemy_air:
            parts = []
            for e in enemy_air:
                cnt = e.get("count", 2)
                ac = e.get("aircraft", "?")
                parts.append(f"{cnt}x {ac}")
            self._log(f"  Enemy Air:  {', '.join(parts)}")
        self._log("")

    def _on_open_folder(self):
        folder = str(OUTPUT_DIR.resolve())
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')

    def _on_copy(self):
        content = self.output_text.get("1.0", "end")
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self._set_status("Copied to clipboard", COLORS["fg_success"])


def main():
    root = tk.Tk()

    # Set icon if available
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = DCSMissionGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

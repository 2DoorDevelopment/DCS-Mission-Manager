#!/usr/bin/env python3
"""
DCS Mission Generator — GUI Frontend
Dark military-themed interface using tkinter (no external dependencies).
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import os
import sys
from pathlib import Path

# Add project root to path
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
    sys.path.insert(0, str(BASE_DIR))
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
from src.units import PLAYER_AIRCRAFT, MISSION_TEMPLATES, WEAPON_CATALOG, AIRCRAFT_PYLONS
from src.naming import generate_mission_name, generate_filename
from src.difficulty import scale_plan
from src.dcs_detect import find_dcs_missions_folder, deploy_mission, deploy_briefing
from src.custom_mods import load_custom_aircraft, register_custom_aircraft, ensure_custom_dir

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────────────────
# PALETTE — dark military, slightly modernized
# ──────────────────────────────────────────────────────────────
C = {
    "bg":          "#0d1117",   # near-black page background
    "surface":     "#161b22",   # card / panel surface
    "surface2":    "#1c2333",   # slightly lighter surface (inputs, hover)
    "border":      "#30363d",   # subtle border
    "accent":      "#4ecdc4",   # teal — primary accent
    "accent2":     "#3ab8b0",   # slightly darker teal for hover
    "green":       "#2ea043",   # generate button
    "green_h":     "#3fb452",   # generate button hover
    "blue_btn":    "#1f6feb",   # secondary blue button
    "blue_h":      "#388bfd",   # secondary blue hover
    "fg":          "#c9d1d9",   # primary text
    "fg_dim":      "#8b949e",   # dimmed text / labels
    "fg_bright":   "#f0f6fc",   # bright / highlighted text
    "fg_success":  "#56d364",   # success green
    "fg_warning":  "#e3b341",   # warning amber
    "fg_error":    "#f85149",   # error red
    "tag_head":    "#4ecdc4",   # output section headers
    "tag_ok":      "#56d364",
    "tag_err":     "#f85149",
    "tag_dim":     "#8b949e",
    "select":      "#264f78",   # text selection
}

FONT_MONO  = ("Consolas", 10)
FONT_MONO_SM = ("Consolas", 9)
FONT_MONO_LG = ("Consolas", 13, "bold")
FONT_MONO_MD = ("Consolas", 11, "bold")


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _sep(parent, color=None):
    """Thin horizontal separator line."""
    tk.Frame(parent, bg=color or C["border"], height=1).pack(fill="x")


def _hover(btn: tk.Button, normal: str, hover: str):
    btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
    btn.bind("<Leave>", lambda e: btn.configure(bg=normal))


def _card(parent, title: str = "", accent: str = None) -> tk.Frame:
    """
    A card-style container: thin colored top bar, section title, content frame.
    Returns the inner content frame to pack widgets into.
    """
    outer = tk.Frame(parent, bg=C["border"], bd=0)
    outer.pack(fill="x", padx=12, pady=(0, 10))

    # Accent bar at top
    tk.Frame(outer, bg=accent or C["accent"], height=2).pack(fill="x")

    # Header row
    if title:
        header = tk.Frame(outer, bg=C["surface"])
        header.pack(fill="x")
        tk.Label(header, text=title.upper(), bg=C["surface"], fg=C["fg_dim"],
                 font=("Consolas", 8, "bold"), padx=10, pady=5).pack(side="left")

    # Content area
    inner = tk.Frame(outer, bg=C["surface"])
    inner.pack(fill="x")
    return inner


class DCSMissionGeneratorGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DCS Mission Generator  v2.0")
        self.root.geometry("980x720")
        self.root.minsize(820, 600)
        self.root.configure(bg=C["bg"])

        self.client = OllamaClient(model="llama3.1:8b")
        self.ollama_connected = False
        self.dcs_folder = find_dcs_missions_folder()
        self.last_miz_path = None
        self._progress_running = False
        self.custom_pylons: dict | None = None   # None = use preset

        # Load custom aircraft
        custom_dir = ensure_custom_dir()
        custom = load_custom_aircraft(custom_dir)
        if custom:
            register_custom_aircraft(custom)

        self.aircraft_list    = list(PLAYER_AIRCRAFT.keys())
        self.aircraft_display = [PLAYER_AIRCRAFT[k].get("display_name", k) for k in self.aircraft_list]
        self.mission_types    = list(MISSION_TEMPLATES.keys())
        self.map_list         = list(MAP_REGISTRY.keys())
        self.map_display      = [MAP_REGISTRY[k]["display_name"] for k in self.map_list]

        self._setup_styles()
        self._build_ui()
        self._check_ollama()

    # ── ttk styles ────────────────────────────────────────────

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Dark.TCombobox",
                         fieldbackground=C["surface2"],
                         background=C["surface2"],
                         foreground=C["fg"],
                         selectbackground=C["select"],
                         arrowcolor=C["accent"],
                         bordercolor=C["border"],
                         lightcolor=C["surface2"],
                         darkcolor=C["surface2"])
        style.map("Dark.TCombobox",
                   fieldbackground=[("readonly", C["surface2"]), ("focus", C["surface2"])],
                   foreground=[("readonly", C["fg"])],
                   selectbackground=[("readonly", C["select"])],
                   selectforeground=[("readonly", C["fg_bright"])],
                   bordercolor=[("focus", C["accent"])])

        style.configure("Accent.TProgressbar",
                         troughcolor=C["surface2"],
                         background=C["accent"],
                         bordercolor=C["surface2"],
                         lightcolor=C["accent"],
                         darkcolor=C["accent2"])

        # Dropdown listbox colors (applied lazily via _style_combobox too)
        self.root.option_add("*TCombobox*Listbox.background",       C["surface2"])
        self.root.option_add("*TCombobox*Listbox.foreground",       C["fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", C["select"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", C["fg_bright"])
        self.root.option_add("*TCombobox*Listbox.font",             "Consolas 10")

    def _style_combobox(self, cb: ttk.Combobox):
        """Also configure the lazy-created popdown listbox directly via Tcl."""
        def _apply(event=None):
            try:
                popdown = self.root.tk.eval(f"ttk::combobox::PopdownWindow {cb}")
                self.root.tk.eval(
                    f"{popdown}.f.l configure"
                    f" -background {C['surface2']}"
                    f" -foreground {C['fg']}"
                    f" -selectbackground {C['select']}"
                    f" -selectforeground {C['fg_bright']}"
                    f" -font {{Consolas 10}}"
                )
            except Exception:
                pass
        cb.bind("<ButtonPress-1>", _apply)

    # ── UI construction ───────────────────────────────────────

    def _build_ui(self):
        self._build_titlebar()

        # ── Two-column body ──
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=0, pady=0)

        # Left panel — fixed width controls
        self._left_panel = tk.Frame(body, bg=C["bg"], width=340)
        self._left_panel.pack(side="left", fill="y", padx=(12, 6), pady=8)
        self._left_panel.pack_propagate(False)

        # Right panel — expanding output
        self._right_panel = tk.Frame(body, bg=C["surface"],
                                      highlightbackground=C["border"], highlightthickness=1)
        self._right_panel.pack(side="right", fill="both", expand=True, padx=(6, 12), pady=8)

        self._build_controls(self._left_panel)
        self._build_output(self._right_panel)
        self._build_statusbar()

    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=C["bg"])
        bar.pack(fill="x", padx=12, pady=(10, 4))

        tk.Label(bar, text="DCS MISSION GENERATOR",
                 bg=C["bg"], fg=C["accent"], font=FONT_MONO_LG).pack(side="left")

        tk.Label(bar, text="v2.0", bg=C["bg"], fg=C["fg_dim"],
                 font=("Consolas", 9)).pack(side="left", padx=(6, 0), pady=(4, 0))

        # Indicator dots (updated after Ollama check)
        self._ind_frame = tk.Frame(bar, bg=C["bg"])
        self._ind_frame.pack(side="right")

        self._ollama_dot   = tk.Label(self._ind_frame, text="●", bg=C["bg"],
                                      fg=C["fg_dim"], font=("Consolas", 11))
        self._ollama_dot.pack(side="right", padx=(0, 2))
        tk.Label(self._ind_frame, text="Ollama", bg=C["bg"], fg=C["fg_dim"],
                 font=FONT_MONO_SM).pack(side="right", padx=(6, 0))

        self._dcs_dot = tk.Label(self._ind_frame, text="●", bg=C["bg"],
                                  fg=C["fg_success"] if self.dcs_folder else C["fg_dim"],
                                  font=("Consolas", 11))
        self._dcs_dot.pack(side="right", padx=(16, 2))
        tk.Label(self._ind_frame, text="DCS", bg=C["bg"], fg=C["fg_dim"],
                 font=FONT_MONO_SM).pack(side="right", padx=(6, 0))

        _sep(self.root)

    def _build_controls(self, parent):
        # ── Natural language input card ──
        nl_inner = _card(parent, "Describe your mission")
        self.nl_input = tk.Text(nl_inner, height=4, wrap="word",
                                 bg=C["surface2"], fg=C["fg_bright"],
                                 insertbackground=C["accent"],
                                 font=FONT_MONO, relief="flat", bd=0,
                                 padx=10, pady=8)
        self.nl_input.pack(fill="x", padx=1, pady=(0, 1))
        self.nl_input.insert("1.0", "SEAD mission in the F-16 on Caucasus with SA-6 and SA-11")
        self.nl_input.bind("<FocusIn>",  lambda e: self.nl_input.configure(
                                                     highlightbackground=C["accent"],
                                                     highlightthickness=1, highlightcolor=C["accent"]))
        self.nl_input.bind("<FocusOut>", lambda e: self.nl_input.configure(highlightthickness=0))

        # ── Manual selection card ──
        sel_inner = _card(parent, "Or select manually")
        self._build_selectors(sel_inner)

        # ── Options card ──
        opt_inner = _card(parent, "Options")
        self._build_options(opt_inner)

        # ── Buttons ──
        self._build_buttons(parent)

    def _row(self, parent, label: str, row: int) -> tk.Frame:
        """Helper: add a label in column 0, return the frame for column 1."""
        tk.Label(parent, text=label, bg=C["surface"], fg=C["fg_dim"],
                 font=FONT_MONO_SM, anchor="w").grid(
                     row=row, column=0, sticky="w", padx=(10, 4), pady=4)
        cell = tk.Frame(parent, bg=C["surface"])
        cell.grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=4)
        return cell

    def _combo(self, parent, var: tk.StringVar, values: list) -> ttk.Combobox:
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                           state="readonly", style="Dark.TCombobox")
        cb.pack(fill="x")
        self._style_combobox(cb)
        return cb

    def _build_selectors(self, parent):
        parent.columnconfigure(1, weight=1)

        self.aircraft_var = tk.StringVar(value=self.aircraft_display[0])
        ac_cb = self._combo(self._row(parent, "Aircraft", 0), self.aircraft_var, self.aircraft_display)

        self.map_var = tk.StringVar(value=self.map_display[0])
        self._combo(self._row(parent, "Map", 1), self.map_var, self.map_display)

        self.mission_var = tk.StringVar(value="SEAD")
        miss_cb = self._combo(self._row(parent, "Mission", 2), self.mission_var, self.mission_types)

        self.difficulty_var = tk.StringVar(value="medium")
        self._combo(self._row(parent, "Difficulty", 3), self.difficulty_var,
                    ["easy", "medium", "hard"])

        self.weather_var = tk.StringVar(value="clear")
        self._combo(self._row(parent, "Weather", 4), self.weather_var,
                    ["clear", "scattered", "overcast", "rain", "storm"])

        self.time_var = tk.StringVar(value="morning")
        self._combo(self._row(parent, "Time", 5), self.time_var,
                    ["morning", "afternoon", "evening", "night"])

        self.players_var = tk.StringVar(value="1")
        self._combo(self._row(parent, "Players", 6), self.players_var,
                    ["1", "2", "3", "4"])

        # Loadout row — description + Customize button
        loadout_cell = self._row(parent, "Loadout", 7)
        self._loadout_desc_var = tk.StringVar(value=self._get_loadout_desc())
        self._loadout_desc_lbl = tk.Label(
            loadout_cell, textvariable=self._loadout_desc_var,
            bg=C["surface"], fg=C["fg_dim"],
            font=("Consolas", 8), anchor="w", wraplength=140, justify="left")
        self._loadout_desc_lbl.pack(side="left", fill="x", expand=True)

        self._customize_btn = tk.Button(
            loadout_cell, text="✏",
            command=self._open_loadout_editor,
            bg=C["surface2"], fg=C["accent"],
            activebackground=C["border"], activeforeground=C["fg_bright"],
            font=("Consolas", 9), relief="flat", bd=0,
            padx=6, pady=2, cursor="hand2")
        self._customize_btn.pack(side="right")
        _hover(self._customize_btn, C["surface2"], C["border"])

        # Refresh loadout desc + clear custom pylons when aircraft/mission changes
        def _on_selection_change(event=None):
            self.custom_pylons = None
            self._loadout_desc_var.set(self._get_loadout_desc())
        ac_cb.bind("<<ComboboxSelected>>", _on_selection_change)
        miss_cb.bind("<<ComboboxSelected>>", _on_selection_change)

    # ── Loadout helpers ───────────────────────────────────────

    def _current_aircraft_key(self) -> str:
        """Return the PLAYER_AIRCRAFT key for the currently selected aircraft."""
        idx = self.aircraft_display.index(self.aircraft_var.get()) \
              if self.aircraft_var.get() in self.aircraft_display else 0
        return self.aircraft_list[idx]

    def _get_loadout_desc(self) -> str:
        """Return the preset loadout description string for current selections."""
        if self.custom_pylons is not None:
            return "Custom"
        ac_key = self._current_aircraft_key()
        mission = self.mission_var.get()
        ac_data = PLAYER_AIRCRAFT.get(ac_key, {})
        loadout = ac_data.get("default_loadouts", {}).get(mission, {})
        return loadout.get("description", "Default")

    def _get_preset_pylons(self) -> dict:
        """Return the preset pylon dict for current aircraft + mission."""
        ac_key = self._current_aircraft_key()
        mission = self.mission_var.get()
        ac_data = PLAYER_AIRCRAFT.get(ac_key, {})
        loadout = ac_data.get("default_loadouts", {}).get(mission, {})
        return dict(loadout.get("pylons", {}))

    def _open_loadout_editor(self):
        """Open a Toplevel dialog to build a custom pylon loadout."""
        ac_key = self._current_aircraft_key()
        mission = self.mission_var.get()
        weapons = WEAPON_CATALOG.get(ac_key, [])
        pylons  = AIRCRAFT_PYLONS.get(ac_key, list(range(1, 10)))

        # Build lookup maps
        name_to_clsid = {w["name"]: w["CLSID"] for w in weapons}
        clsid_to_name = {w["CLSID"]: w["name"] for w in weapons}
        weapon_names  = ["— Empty —"] + [w["name"] for w in weapons]

        # Starting values: custom if already set, else preset
        start_pylons = self.custom_pylons if self.custom_pylons is not None \
                       else self._get_preset_pylons()

        # ── Dialog window ──
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Custom Loadout  —  {ac_key}  /  {mission}")
        dlg.configure(bg=C["bg"])
        dlg.resizable(False, False)
        dlg.grab_set()

        # Header
        tk.Label(dlg, text=f"{ac_key}  ·  {mission}",
                 bg=C["bg"], fg=C["accent"], font=FONT_MONO_MD,
                 padx=16, pady=10).pack(anchor="w")
        _sep(dlg)

        # Scrollable pylon grid
        canvas_frame = tk.Frame(dlg, bg=C["bg"])
        canvas_frame.pack(fill="both", expand=True, padx=12, pady=8)

        canvas = tk.Canvas(canvas_frame, bg=C["bg"], highlightthickness=0,
                           width=480, height=min(40 * len(pylons), 320))
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                  command=canvas.yview)
        inner = tk.Frame(canvas, bg=C["bg"])
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_inner_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(inner_id, width=canvas.winfo_width())
        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(
            inner_id, width=e.width))

        canvas.pack(side="left", fill="both", expand=True)
        if len(pylons) * 40 > 320:
            scrollbar.pack(side="right", fill="y")

        # Pylon rows — two columns
        inner.columnconfigure(1, weight=1)
        inner.columnconfigure(3, weight=1)
        pylon_vars: dict[int, tk.StringVar] = {}
        pylon_combos: list[ttk.Combobox] = []

        for idx, pylon_num in enumerate(pylons):
            row_grid = idx // 2
            col_offset = (idx % 2) * 2   # 0 or 2

            current_clsid = start_pylons.get(pylon_num, {}).get("CLSID", "")
            current_name  = clsid_to_name.get(current_clsid, "— Empty —") \
                            if current_clsid else "— Empty —"

            tk.Label(inner, text=f"P{pylon_num}", bg=C["bg"], fg=C["fg_dim"],
                     font=FONT_MONO_SM, width=3, anchor="e").grid(
                         row=row_grid, column=col_offset,
                         padx=(8 if col_offset == 0 else 12, 4), pady=3, sticky="e")

            var = tk.StringVar(value=current_name)
            cb  = ttk.Combobox(inner, textvariable=var, values=weapon_names,
                               state="readonly", style="Dark.TCombobox", width=18)
            cb.grid(row=row_grid, column=col_offset + 1,
                    padx=(0, 8), pady=3, sticky="ew")
            self._style_combobox(cb)
            pylon_vars[pylon_num] = var
            pylon_combos.append(cb)

        _sep(dlg)

        # Bottom buttons
        btn_row = tk.Frame(dlg, bg=C["bg"])
        btn_row.pack(fill="x", padx=12, pady=8)

        def _reset():
            preset = self._get_preset_pylons()
            for pnum, var in pylon_vars.items():
                clsid = preset.get(pnum, {}).get("CLSID", "")
                var.set(clsid_to_name.get(clsid, "— Empty —") if clsid else "— Empty —")

        def _apply():
            result: dict[int, dict] = {}
            for pnum, var in pylon_vars.items():
                name = var.get()
                if name != "— Empty —" and name in name_to_clsid:
                    result[pnum] = {"CLSID": name_to_clsid[name]}
            self.custom_pylons = result
            self._loadout_desc_var.set("Custom")
            dlg.destroy()

        def _cancel():
            dlg.destroy()

        tk.Button(btn_row, text="Reset to Preset", command=_reset,
                  bg=C["surface2"], fg=C["fg_dim"],
                  activebackground=C["border"], activeforeground=C["fg"],
                  font=FONT_MONO_SM, relief="flat", bd=0,
                  padx=10, pady=6, cursor="hand2").pack(side="left")

        tk.Button(btn_row, text="Clear Loadout", command=lambda: [
                      var.set("— Empty —") for var in pylon_vars.values()],
                  bg=C["surface2"], fg=C["fg_dim"],
                  activebackground=C["border"], activeforeground=C["fg"],
                  font=FONT_MONO_SM, relief="flat", bd=0,
                  padx=10, pady=6, cursor="hand2").pack(side="left", padx=(6, 0))

        tk.Button(btn_row, text="  Cancel  ", command=_cancel,
                  bg=C["surface2"], fg=C["fg"],
                  activebackground=C["border"], activeforeground=C["fg_bright"],
                  font=FONT_MONO_SM, relief="flat", bd=0,
                  padx=10, pady=6, cursor="hand2").pack(side="right")

        tk.Button(btn_row, text="  Apply  ", command=_apply,
                  bg=C["accent"], fg=C["bg"],
                  activebackground=C["accent2"], activeforeground=C["bg"],
                  font=FONT_MONO_SM, relief="flat", bd=0,
                  padx=14, pady=6, cursor="hand2").pack(side="right", padx=(0, 6))

        dlg.update_idletasks()
        # Center on parent
        px = self.root.winfo_x() + self.root.winfo_width() // 2
        py = self.root.winfo_y() + self.root.winfo_height() // 2
        dlg.geometry(f"+{px - dlg.winfo_width() // 2}+{py - dlg.winfo_height() // 2}")

    def _build_options(self, parent):
        def _check(text, var):
            tk.Checkbutton(parent, text=text, variable=var,
                            bg=C["surface"], fg=C["fg"], activebackground=C["surface"],
                            activeforeground=C["fg_bright"], selectcolor=C["surface2"],
                            font=FONT_MONO_SM, cursor="hand2").pack(
                                anchor="w", padx=10, pady=2)

        self.wingman_var     = tk.BooleanVar(value=True)
        self.ground_war_var  = tk.BooleanVar(value=True)
        self.auto_deploy_var = tk.BooleanVar(value=bool(self.dcs_folder))

        _check("Include wingman",    self.wingman_var)
        _check("Ground war active",  self.ground_war_var)
        _check("Auto-deploy to DCS", self.auto_deploy_var)
        tk.Frame(parent, bg=C["surface"], height=4).pack()

    def _build_buttons(self, parent):
        tk.Frame(parent, bg=C["bg"], height=4).pack()

        # Primary — generate from description
        self.gen_nl_btn = tk.Button(
            parent, text="⚡  GENERATE FROM DESCRIPTION",
            command=self._on_generate_nl,
            bg=C["green"], fg=C["fg_bright"], activeforeground=C["fg_bright"],
            activebackground=C["green_h"], font=FONT_MONO_MD,
            relief="flat", bd=0, pady=10, cursor="hand2")
        self.gen_nl_btn.pack(fill="x")
        _hover(self.gen_nl_btn, C["green"], C["green_h"])

        tk.Frame(parent, bg=C["bg"], height=5).pack()

        # Secondary — generate from selections
        self.gen_manual_btn = tk.Button(
            parent, text="▶  GENERATE FROM SELECTIONS",
            command=self._on_generate_manual,
            bg=C["surface2"], fg=C["fg"], activeforeground=C["fg_bright"],
            activebackground=C["surface2"], font=FONT_MONO,
            relief="flat", bd=0, pady=8, cursor="hand2",
            highlightbackground=C["border"], highlightthickness=1)
        self.gen_manual_btn.pack(fill="x")
        _hover(self.gen_manual_btn, C["surface2"], C["border"])

        tk.Frame(parent, bg=C["bg"], height=5).pack()

        # Utility — open folder
        self.open_folder_btn = tk.Button(
            parent, text="📁  Open Output Folder",
            command=self._on_open_folder,
            bg=C["bg"], fg=C["fg_dim"], activeforeground=C["fg"],
            activebackground=C["surface2"], font=FONT_MONO_SM,
            relief="flat", bd=0, pady=5, cursor="hand2")
        self.open_folder_btn.pack(fill="x")
        _hover(self.open_folder_btn, C["bg"], C["surface2"])

    def _build_output(self, parent):
        # Header row
        hdr = tk.Frame(parent, bg=C["surface"])
        hdr.pack(fill="x", padx=10, pady=(8, 4))

        tk.Label(hdr, text="OUTPUT  /  BRIEFING",
                 bg=C["surface"], fg=C["fg_dim"],
                 font=("Consolas", 9, "bold")).pack(side="left")

        # Action buttons top-right
        for label, cmd, color in [
            ("Clear", self._on_clear, C["fg_dim"]),
            ("Copy",  self._on_copy,  C["accent"]),
        ]:
            b = tk.Button(hdr, text=label, command=cmd,
                           bg=C["surface"], fg=color, activebackground=C["surface2"],
                           activeforeground=C["fg_bright"], font=("Consolas", 8),
                           relief="flat", bd=0, padx=8, cursor="hand2")
            b.pack(side="right", padx=2)
            _hover(b, C["surface"], C["surface2"])

        _sep(parent)

        # Progress bar (hidden until generation starts)
        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Progressbar(
            parent, variable=self._progress_var,
            mode="indeterminate", style="Accent.TProgressbar", length=100)
        # Don't pack yet — shown dynamically

        # Output text with syntax coloring
        self.output_text = scrolledtext.ScrolledText(
            parent, wrap="word",
            bg=C["surface"], fg=C["fg"],
            insertbackground=C["accent"],
            font=("Consolas", 9), relief="flat", bd=0,
            padx=12, pady=8,
            selectbackground=C["select"])
        self.output_text.pack(fill="both", expand=True)

        # Configure text tags for colored output
        self.output_text.tag_configure("head",    foreground=C["tag_head"],  font=("Consolas", 9, "bold"))
        self.output_text.tag_configure("ok",      foreground=C["tag_ok"])
        self.output_text.tag_configure("err",     foreground=C["tag_err"])
        self.output_text.tag_configure("dim",     foreground=C["tag_dim"])
        self.output_text.tag_configure("bright",  foreground=C["fg_bright"])
        self.output_text.tag_configure("warning", foreground=C["fg_warning"])

        self._log("Ready — describe a mission above or use manual selections.\n", "dim")
        self._log("Natural language mode uses Ollama for smart parsing.\n", "dim")
        self._log("Manual mode bypasses the LLM entirely.\n", "dim")
        self.output_text.configure(state="disabled")

    def _build_statusbar(self):
        _sep(self.root)
        bar = tk.Frame(self.root, bg=C["bg"], pady=5)
        bar.pack(fill="x", padx=12)

        self.bottom_status = tk.Label(bar, text="Ready",
                                       bg=C["bg"], fg=C["fg_dim"],
                                       font=("Consolas", 8))
        self.bottom_status.pack(side="left")

    # ── Logging helpers ───────────────────────────────────────

    def _log(self, text: str, tag: str = ""):
        self.output_text.configure(state="normal")
        if tag:
            self.output_text.insert("end", text + "\n", tag)
        else:
            self.output_text.insert("end", text + "\n")
        self.output_text.see("end")
        self.output_text.configure(state="disabled")

    def _clear_output(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")

    def _set_status(self, text: str, color: str = ""):
        self.bottom_status.configure(text=text, fg=color or C["fg_dim"])

    def _set_buttons_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.gen_nl_btn.configure(state=state)
        self.gen_manual_btn.configure(state=state)

    def _start_progress(self):
        self._progress_bar.pack(fill="x", padx=0, pady=0,
                                 before=self.output_text)
        self._progress_bar.start(12)

    def _stop_progress(self):
        self._progress_bar.stop()
        self._progress_bar.pack_forget()

    # ── Status indicators ─────────────────────────────────────

    def _check_ollama(self):
        def check():
            connected = self.client.check_connection()
            self.ollama_connected = connected
            def update():
                color = C["fg_success"] if connected else C["fg_warning"]
                self._ollama_dot.configure(fg=color)
                tip = "Connected" if connected else "Offline"
                self._ollama_dot.configure(text="●")
                self._set_status(
                    f"Ollama {tip}  ·  DCS {'found' if self.dcs_folder else 'not detected'}")
            self.root.after(0, update)
        threading.Thread(target=check, daemon=True).start()

    # ── Generation handlers ───────────────────────────────────

    def _on_generate_nl(self):
        description = self.nl_input.get("1.0", "end").strip()
        if not description:
            messagebox.showwarning("Empty", "Enter a mission description first.")
            return
        self._generate_mission(description=description)

    def _on_generate_manual(self):
        ac_idx  = self.aircraft_display.index(self.aircraft_var.get()) \
                  if self.aircraft_var.get() in self.aircraft_display else 0
        map_idx = self.map_display.index(self.map_var.get()) \
                  if self.map_var.get() in self.map_display else 0

        plan = {
            "map_name":        self.map_list[map_idx],
            "player_aircraft": self.aircraft_list[ac_idx],
            "mission_type":    self.mission_var.get(),
            "player_airfield": "AUTO",
            "time_of_day":     self.time_var.get(),
            "weather":         self.weather_var.get(),
            "difficulty":      self.difficulty_var.get(),
            "player_count":    int(self.players_var.get()),
            "wingman":         self.wingman_var.get(),
            "ground_war": {
                "enabled":         self.ground_war_var.get(),
                "front_line_desc": "Dynamic",
                "blue_advancing":  True,
                "red_advancing":   True,
                "intensity":       "medium",
            },
            "special_requests": "",
            "custom_pylons":   self.custom_pylons,  # None = use preset
        }
        self._generate_mission(plan=plan)

    def _generate_mission(self, description=None, plan=None):
        self._set_buttons_enabled(False)
        self._clear_output()
        self._set_status("Generating…", C["accent"])
        self.root.after(0, self._start_progress)
        self._log("GENERATING MISSION", "head")
        self._log("─" * 48, "dim")

        def run():
            try:
                if description:
                    self._log(f'\n"{description}"\n', "bright")
                    parser = MissionParser(self.client)
                    parse_msg = "Parsing with LLM…" if self.ollama_connected \
                                else "Parsing with rule engine (Ollama offline)…"
                    self._log(parse_msg, "dim")
                    mission_plan = parser.parse_description(description)
                    if not mission_plan:
                        self.root.after(0, lambda: self._log("ERROR: Could not parse description.", "err"))
                        return
                else:
                    mission_plan = plan
                    from src.llm.mission_parser import MissionParser as MP
                    mission_plan = MP(self.client)._validate_and_fill(mission_plan, "")

                op_name = generate_mission_name(mission_plan.get("mission_type", "general"))
                mission_plan["_operation_name"] = op_name
                self.root.after(0, lambda: self._log(f"\n{op_name}", "head"))
                self.root.after(0, lambda: self._log_plan(mission_plan))

                self._log("Scaling difficulty…", "dim")
                scaled = scale_plan(mission_plan)

                self._log("Building mission structure…", "dim")
                data = MissionBuilder(scaled).build()

                self._log("Generating Lua files…", "dim")
                lua_files = LuaGenerator(data).generate_all()

                self._log("Generating briefing…", "dim")
                briefing = BriefingGenerator(data, scaled).generate()

                filename    = generate_filename(
                    mission_plan.get("mission_type", "mission"),
                    mission_plan.get("map_name", "unknown"),
                    op_name)
                output_path = OUTPUT_DIR / filename
                ac_type     = PLAYER_AIRCRAFT.get(
                    mission_plan.get("player_aircraft", ""), {}).get("type", "")
                MizPackager().package(lua_files, briefing, str(output_path),
                                      aircraft_type=ac_type)

                briefing_path = output_path.with_suffix(".txt")
                with open(briefing_path, "w", encoding="utf-8") as f:
                    f.write(briefing)

                self.last_miz_path = output_path

                deployed_path = None
                if self.auto_deploy_var.get() and self.dcs_folder:
                    deployed_path = deploy_mission(output_path, self.dcs_folder)
                    deploy_briefing(briefing_path, self.dcs_folder)

                def show_results():
                    self._log(f"\n✓  Mission saved:  {output_path.name}", "ok")
                    if deployed_path:
                        self._log(f"✓  Deployed to DCS: {deployed_path}", "ok")
                    else:
                        self._log("ℹ  Copy .miz to your DCS Saved Games\\Missions\\ folder", "dim")
                    self._log("\n" + "─" * 48, "dim")
                    self._log("BRIEFING", "head")
                    self._log("─" * 48, "dim")
                    self._log(briefing)
                    self._set_status(f"✓  {op_name}  ·  {output_path.name}", C["fg_success"])

                self.root.after(0, show_results)

            except Exception as e:
                self.root.after(0, lambda: self._log(f"\nERROR: {e}", "err"))
                self.root.after(0, lambda: self._set_status(f"Error: {e}", C["fg_error"]))
                import traceback; traceback.print_exc()
            finally:
                self.root.after(0, self._stop_progress)
                self.root.after(0, lambda: self._set_buttons_enabled(True))

        threading.Thread(target=run, daemon=True).start()

    def _log_plan(self, plan):
        pairs = [
            ("Map",        plan.get("map_name", "?")),
            ("Aircraft",   plan.get("player_aircraft", "?")),
            ("Mission",    plan.get("mission_type", "?")),
            ("Difficulty", plan.get("difficulty", "medium").upper()),
            ("Weather",    plan.get("weather", "clear")),
            ("Departure",  plan.get("player_airfield", "AUTO")),
        ]
        sams = plan.get("enemy_sam_sites", [])
        if sams:
            pairs.append(("SAMs", ", ".join(s.get("type", "?") for s in sams)))
        enemy_air = plan.get("enemy_air", [])
        if enemy_air:
            pairs.append(("Enemy Air", ", ".join(
                f"{e.get('count', 2)}× {e.get('aircraft', '?')}" for e in enemy_air)))

        for label, value in pairs:
            line = f"  {label:<12} {value}"
            self._log(line)
        self._log("")

    # ── Utility handlers ──────────────────────────────────────

    def _on_clear(self):
        self._clear_output()
        self._set_status("Ready")

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
        self._set_status("Copied to clipboard", C["fg_success"])


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    DCSMissionGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

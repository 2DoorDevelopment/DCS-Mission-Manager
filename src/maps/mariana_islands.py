"""
Mariana Islands Map Database
Covers Guam, Saipan, Tinian, Rota, and surrounding Pacific ocean areas.
DCS coordinates use a local X/Y system (meters) relative to the map origin.
"""

MARIANA_ISLANDS_MAP = {
    "display_name": "Mariana Islands",
    "theater_id": "MarianaIslands",
    "dcs_theater": "MarianaIslands",

    "bounds": {
        "x_min": -400000, "x_max": 400000,
        "y_min": -400000, "y_max": 400000,
    },

    "default_date": {"year": 2024, "month": 6, "day": 15},

    "airfields": [
        # ---- BLUE (US / Coalition) ----
        {
            "name": "Andersen AFB",
            "id": 1,
            "x": 13600,
            "y": 144700,
            "alt": 191,
            "default_coalition": "blue",
            "runways": [{"heading": 6, "length": 3350}, {"heading": 186, "length": 3350}],
            "tacan": "54X",
            "ils": "109.10",
            "atis": "126.200",
        },
        {
            "name": "Antonio B. Won Pat International (Guam)",
            "id": 2,
            "x": 6500,
            "y": 136500,
            "alt": 91,
            "default_coalition": "blue",
            "runways": [{"heading": 60, "length": 3048}, {"heading": 240, "length": 3048}],
            "tacan": "112X",
            "ils": "111.10",
        },
        {
            "name": "Saipan International",
            "id": 3,
            "x": 137400,
            "y": 172000,
            "alt": 64,
            "default_coalition": "blue",
            "runways": [{"heading": 70, "length": 2560}],
            "tacan": "66X",
        },
        {
            "name": "Tinian International",
            "id": 4,
            "x": 117000,
            "y": 162000,
            "alt": 57,
            "default_coalition": "blue",
            "runways": [{"heading": 95, "length": 2950}],
        },
        {
            "name": "Rota International",
            "id": 5,
            "x": 60000,
            "y": 110000,
            "alt": 187,
            "default_coalition": "blue",
            "runways": [{"heading": 90, "length": 2130}],
        },

        # ---- RED (OPFOR) ----
        {
            "name": "Pagan Island Airstrip",
            "id": 10,
            "x": 305000,
            "y": 230000,
            "alt": 57,
            "default_coalition": "red",
            "runways": [{"heading": 105, "length": 1500}],
        },
        {
            "name": "Agrihan Airstrip",
            "id": 11,
            "x": 347000,
            "y": 260000,
            "alt": 45,
            "default_coalition": "red",
            "runways": [{"heading": 90, "length": 1200}],
        },
    ],

    "cities": [
        {"name": "Hagatna (Guam)", "x": 4000, "y": 134000, "side": "blue"},
        {"name": "Tamuning", "x": 6000, "y": 136000, "side": "blue"},
        {"name": "Chalan Kanoa (Saipan)", "x": 133000, "y": 170000, "side": "blue"},
        {"name": "Garapan (Saipan)", "x": 133500, "y": 172500, "side": "blue"},
    ],

    "sam_zones": [
        {"name": "Andersen AFB Defense", "x": 13600, "y": 144700, "radius": 25000, "side": "blue"},
        {"name": "Guam Harbor Defense", "x": 4000, "y": 133000, "radius": 20000, "side": "blue"},
        {"name": "Saipan Defense", "x": 137400, "y": 172000, "radius": 15000, "side": "blue"},
        {"name": "Pagan OPFOR SAM", "x": 305000, "y": 230000, "radius": 30000, "side": "red"},
        {"name": "Northern Islands OPFOR", "x": 340000, "y": 250000, "radius": 25000, "side": "red"},
    ],

    "front_lines": [
        {
            "name": "Northern Island Chain",
            "description": "OPFOR has seized northern islands; coalition holds southern Marianas",
            "blue_start": {"x": 200000, "y": 190000},
            "red_start": {"x": 280000, "y": 220000},
            "axis": "south",
            "width": 60000,
        },
    ],

    # Pacific carrier operations — this map is built for blue-water naval combat
    "naval_zones": [
        {"name": "Philippine Sea Carrier Station", "x": -100000, "y": 150000, "radius": 100000},
        {"name": "Western Pacific Patrol", "x": 200000, "y": 180000, "radius": 80000},
        {"name": "Guam Approaches", "x": 0, "y": 110000, "radius": 60000},
        {"name": "Northern Marianas Sea", "x": 220000, "y": 210000, "radius": 70000},
    ],

    "cap_orbits": [
        {"name": "Southern CAP", "x1": 80000, "y1": 140000, "x2": 100000, "y2": 160000, "alt": 9000, "side": "blue"},
        {"name": "Saipan CAP", "x1": 120000, "y1": 165000, "x2": 140000, "y2": 175000, "alt": 8500, "side": "blue"},
        {"name": "OPFOR CAP North", "x1": 290000, "y1": 225000, "x2": 310000, "y2": 240000, "alt": 8000, "side": "red"},
    ],

    "support_orbits": {
        "tanker": {"name": "Arco", "x1": 50000, "y1": 140000, "x2": 60000, "y2": 160000, "alt": 7600, "freq": 251.0, "tacan": "51Y"},
        "awacs": {"name": "Darkstar", "x1": 30000, "y1": 140000, "x2": 40000, "y2": 160000, "alt": 9500, "freq": 252.0},
    },

    "convoy_routes": {
        "red": [
            {
                "name": "Northern Supply Chain",
                "waypoints": [
                    {"x": 347000, "y": 260000},   # Agrihan
                    {"x": 305000, "y": 230000},   # Pagan
                    {"x": 250000, "y": 205000},   # Forward position
                ],
            },
        ],
        "blue": [
            {
                "name": "Saipan-Guam Logistics",
                "waypoints": [
                    {"x": 13600, "y": 144700},    # Andersen
                    {"x": 60000, "y": 110000},    # Rota
                    {"x": 117000, "y": 162000},   # Tinian
                    {"x": 137400, "y": 172000},   # Saipan
                ],
            },
        ],
    },

    # Water zones — Marianas is mostly ocean; only islands are valid for ground units
    # Using exclusion zones for obvious deep water areas far from any island
    "water_zones": [
        {"name": "Pacific West", "x": 50000, "y": -50000, "radius": 100000},
        {"name": "Pacific East", "x": 50000, "y": 300000, "radius": 100000},
    ],
}

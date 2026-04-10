"""
Persian Gulf Map Database
Covers UAE, Oman, Iran, Qatar, Bahrain, and the Strait of Hormuz.
DCS coordinates use a local X/Y system (meters) relative to the map origin.
"""

PERSIAN_GULF_MAP = {
    "display_name": "Persian Gulf",
    "theater_id": "PersianGulf",
    "dcs_theater": "PersianGulf",

    "bounds": {
        "x_min": -200000, "x_max": 900000,
        "y_min": -200000, "y_max": 900000,
    },

    "default_date": {"year": 2024, "month": 3, "day": 21},

    "airfields": [
        # ---- BLUE (UAE / Coalition) ----
        {
            "name": "Al Dhafra",
            "id": 1,
            "x": 95000,
            "y": 573000,
            "alt": 27,
            "default_coalition": "blue",
            "runways": [{"heading": 132, "length": 3660}, {"heading": 312, "length": 3660}],
            "tacan": "25X",
            "ils": "109.10",
            "atis": "127.850",
        },
        {
            "name": "Al Minhad",
            "id": 2,
            "x": 131000,
            "y": 609000,
            "alt": 66,
            "default_coalition": "blue",
            "runways": [{"heading": 160, "length": 3660}, {"heading": 340, "length": 3660}],
            "tacan": "99X",
            "ils": "110.30",
        },
        {
            "name": "Dubai International",
            "id": 3,
            "x": 152000,
            "y": 637000,
            "alt": 19,
            "default_coalition": "blue",
            "runways": [{"heading": 121, "length": 4000}],
            "tacan": "33X",
            "ils": "110.90",
        },
        {
            "name": "Sharjah International",
            "id": 4,
            "x": 162000,
            "y": 652000,
            "alt": 34,
            "default_coalition": "blue",
            "runways": [{"heading": 121, "length": 3660}],
        },
        {
            "name": "Fujairah International",
            "id": 5,
            "x": 183000,
            "y": 686000,
            "alt": 13,
            "default_coalition": "blue",
            "runways": [{"heading": 91, "length": 2440}],
        },
        {
            "name": "Khasab",
            "id": 6,
            "x": 239000,
            "y": 722000,
            "alt": 20,
            "default_coalition": "blue",
            "runways": [{"heading": 20, "length": 1800}],
        },
        {
            "name": "Al Bateen",
            "id": 7,
            "x": 81000,
            "y": 574000,
            "alt": 16,
            "default_coalition": "blue",
            "runways": [{"heading": 99, "length": 2750}],
        },
        {
            "name": "Abu Dhabi International",
            "id": 8,
            "x": 73000,
            "y": 554000,
            "alt": 27,
            "default_coalition": "blue",
            "runways": [{"heading": 131, "length": 4100}],
            "ils": "111.10",
        },
        {
            "name": "Liwa",
            "id": 9,
            "x": 17000,
            "y": 477000,
            "alt": 146,
            "default_coalition": "blue",
            "runways": [{"heading": 90, "length": 3048}],
        },
        {
            "name": "Al Ain International",
            "id": 10,
            "x": 109000,
            "y": 614000,
            "alt": 264,
            "default_coalition": "blue",
            "runways": [{"heading": 100, "length": 4000}],
        },
        {
            "name": "Ras Al Khaimah",
            "id": 11,
            "x": 201000,
            "y": 669000,
            "alt": 31,
            "default_coalition": "blue",
            "runways": [{"heading": 180, "length": 2900}],
        },

        # ---- BLUE (Qatar / Bahrain) ----
        {
            "name": "Al Udeid",
            "id": 20,
            "x": -71000,
            "y": 428000,
            "alt": 20,
            "default_coalition": "blue",
            "runways": [{"heading": 160, "length": 3660}],
            "tacan": "21X",
            "ils": "110.70",
            "atis": "126.300",
        },
        {
            "name": "Doha International",
            "id": 21,
            "x": -67000,
            "y": 435000,
            "alt": 9,
            "default_coalition": "blue",
            "runways": [{"heading": 160, "length": 4572}],
        },

        # ---- RED (Iranian side) ----
        {
            "name": "Bandar Abbas",
            "id": 30,
            "x": 278000,
            "y": 721000,
            "alt": 9,
            "default_coalition": "red",
            "runways": [{"heading": 216, "length": 3560}, {"heading": 36, "length": 3560}],
        },
        {
            "name": "Bandar Lengeh",
            "id": 31,
            "x": 198000,
            "y": 681000,
            "alt": 23,
            "default_coalition": "red",
            "runways": [{"heading": 255, "length": 2650}],
        },
        {
            "name": "Sirri Island",
            "id": 32,
            "x": 119000,
            "y": 636000,
            "alt": 7,
            "default_coalition": "red",
            "runways": [{"heading": 90, "length": 3048}],
        },
        {
            "name": "Lavan Island",
            "id": 33,
            "x": 145000,
            "y": 653000,
            "alt": 22,
            "default_coalition": "red",
            "runways": [{"heading": 100, "length": 2200}],
        },
        {
            "name": "Lar",
            "id": 34,
            "x": 302000,
            "y": 706000,
            "alt": 792,
            "default_coalition": "red",
            "runways": [{"heading": 210, "length": 2700}],
        },
        {
            "name": "Havadarya",
            "id": 35,
            "x": 275000,
            "y": 729000,
            "alt": 19,
            "default_coalition": "red",
            "runways": [{"heading": 128, "length": 2200}],
        },
        {
            "name": "Qeshm Island",
            "id": 36,
            "x": 258000,
            "y": 730000,
            "alt": 16,
            "default_coalition": "red",
            "runways": [{"heading": 100, "length": 2820}],
        },
        {
            "name": "Abu Musa Island",
            "id": 37,
            "x": 158000,
            "y": 655000,
            "alt": 14,
            "default_coalition": "red",
            "runways": [{"heading": 75, "length": 2000}],
        },
    ],

    "cities": [
        {"name": "Abu Dhabi", "x": 83000, "y": 567000, "side": "blue"},
        {"name": "Dubai", "x": 152000, "y": 636000, "side": "blue"},
        {"name": "Sharjah", "x": 162000, "y": 651000, "side": "blue"},
        {"name": "Doha", "x": -67000, "y": 432000, "side": "blue"},
        {"name": "Bandar Abbas", "x": 278000, "y": 720000, "side": "red"},
        {"name": "Bandar Lengeh", "x": 198000, "y": 680000, "side": "red"},
        {"name": "Strait of Hormuz", "x": 245000, "y": 700000, "side": "contested"},
    ],

    "sam_zones": [
        {"name": "Bandar Abbas Defense", "x": 275000, "y": 715000, "radius": 40000, "side": "red"},
        {"name": "Bandar Lengeh Area", "x": 198000, "y": 678000, "radius": 25000, "side": "red"},
        {"name": "Qeshm Island Defense", "x": 258000, "y": 728000, "radius": 20000, "side": "red"},
        {"name": "Strait North Shore", "x": 242000, "y": 708000, "radius": 30000, "side": "red"},
        {"name": "Abu Musa Island", "x": 158000, "y": 654000, "radius": 15000, "side": "red"},
        {"name": "Lavan Island Area", "x": 145000, "y": 650000, "radius": 15000, "side": "red"},
        {"name": "Al Dhafra Defense", "x": 95000, "y": 570000, "radius": 20000, "side": "blue"},
        {"name": "Dubai Air Defense", "x": 152000, "y": 635000, "radius": 15000, "side": "blue"},
    ],

    "front_lines": [
        {
            "name": "Strait of Hormuz Front",
            "description": "Naval and air engagement across the Strait",
            "blue_start": {"x": 195000, "y": 680000},
            "red_start": {"x": 245000, "y": 710000},
            "axis": "north",
            "width": 40000,
        },
    ],

    # Extensive naval zones — carrier ops are the heart of PG missions
    "naval_zones": [
        {"name": "Gulf of Oman Carrier Station", "x": 320000, "y": 690000, "radius": 60000},
        {"name": "Persian Gulf Patrol", "x": 100000, "y": 600000, "radius": 80000},
        {"name": "Strait of Hormuz Transit", "x": 245000, "y": 700000, "radius": 30000},
        {"name": "Southern Gulf", "x": 0, "y": 500000, "radius": 80000},
    ],

    "cap_orbits": [
        {"name": "Gulf CAP Alpha", "x1": 200000, "y1": 660000, "x2": 220000, "y2": 690000, "alt": 7500, "side": "blue"},
        {"name": "Gulf CAP Bravo", "x1": 160000, "y1": 640000, "x2": 180000, "y2": 660000, "alt": 8000, "side": "blue"},
        {"name": "Iranian CAP", "x1": 260000, "y1": 720000, "x2": 280000, "y2": 700000, "alt": 7000, "side": "red"},
        {"name": "Hormuz CAP", "x1": 240000, "y1": 705000, "x2": 250000, "y2": 695000, "alt": 7000, "side": "red"},
    ],

    "support_orbits": {
        "tanker": {"name": "Shell", "x1": 140000, "y1": 600000, "x2": 150000, "y2": 630000, "alt": 7600, "freq": 251.0, "tacan": "51Y"},
        "awacs": {"name": "Magic", "x1": 120000, "y1": 580000, "x2": 130000, "y2": 610000, "alt": 9000, "freq": 252.0},
    },

    "convoy_routes": {
        "red": [
            {
                "name": "Bandar Abbas Supply Route",
                "waypoints": [
                    {"x": 278000, "y": 721000},   # Bandar Abbas
                    {"x": 258000, "y": 730000},   # Qeshm area
                    {"x": 242000, "y": 710000},   # Strait crossing
                ],
            },
        ],
        "blue": [
            {
                "name": "UAE Logistics Route",
                "waypoints": [
                    {"x": 95000, "y": 573000},    # Al Dhafra
                    {"x": 131000, "y": 609000},   # Al Minhad
                    {"x": 152000, "y": 637000},   # Dubai
                ],
            },
        ],
    },
}

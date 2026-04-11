"""
Syria Map Database
Coordinates in DCS internal X/Y system.
"""

SYRIA_MAP = {
    "display_name": "Syria",
    "theater_id": "Syria",
    "dcs_theater": "Syria",

    "bounds": {
        "x_min": -400000, "x_max": 400000,
        "y_min": -400000, "y_max": 400000,
    },

    "default_date": {"year": 2024, "month": 6, "day": 15},

    "airfields": [
        # ---- BLUE (Western coalition / Israeli / Turkish) ----
        {
            "name": "Incirlik",
            "id": 1,
            "x": 221882,
            "y": -36897,
            "alt": 64,
            "default_coalition": "blue",
            "runways": [{"heading": 57, "length": 3049}],
            "tacan": "21X",
            "ils": "109.30",
        },
        {
            "name": "Ramat David",
            "id": 2,
            "x": -26890,
            "y": -74020,
            "alt": 56,
            "default_coalition": "blue",
            "runways": [{"heading": 105, "length": 2700}, {"heading": 150, "length": 2500}],
            "tacan": "84X",
            "ils": "109.70",
        },
        {
            "name": "Hatay",
            "id": 3,
            "x": 141532,
            "y": 34068,
            "alt": 87,
            "default_coalition": "blue",
            "runways": [{"heading": 46, "length": 2400}],
        },
        {
            "name": "Akrotiri",
            "id": 4,
            "x": -31969,
            "y": -283627,
            "alt": 22,
            "default_coalition": "blue",
            "runways": [{"heading": 105, "length": 2750}],
            "tacan": "107X",
        },
        {
            "name": "Paphos",
            "id": 7,
            "x": -12830,
            "y": -318220,
            "alt": 12,
            "default_coalition": "blue",
            "runways": [{"heading": 96, "length": 2700}],
        },
        {
            "name": "King Hussein",
            "id": 8,
            "x": -152930,
            "y": -12450,
            "alt": 680,
            "default_coalition": "blue",
            "runways": [{"heading": 130, "length": 2800}],
        },
        {
            "name": "Muwaffaq Salti",
            "id": 9,
            "x": -173550,
            "y": 7400,
            "alt": 706,
            "default_coalition": "blue",
            "runways": [{"heading": 85, "length": 3500}],
        },
        {
            "name": "Haifa",
            "id": 10,
            "x": -42000,
            "y": -82050,
            "alt": 8,
            "default_coalition": "blue",
            "runways": [{"heading": 160, "length": 1300}],
        },
        {
            "name": "Larnaca",
            "id": 11,
            "x": -15355,
            "y": -269747,
            "alt": 2,
            "default_coalition": "blue",
            "runways": [{"heading": 40, "length": 2980}],
        },
        {
            "name": "Gaziantep",
            "id": 12,
            "x": 219840,
            "y": 63260,
            "alt": 838,
            "default_coalition": "blue",
            "runways": [{"heading": 97, "length": 3000}],
        },

        # ---- RED (Syrian / Russian) ----
        {
            "name": "Damascus Intl",
            "id": 5,
            "x": -177540,
            "y": 83040,
            "alt": 614,
            "default_coalition": "red",
            "runways": [{"heading": 54, "length": 3600}, {"heading": 233, "length": 3600}],
        },
        {
            "name": "Mezzeh",
            "id": 6,
            "x": -165170,
            "y": 68610,
            "alt": 720,
            "default_coalition": "red",
            "runways": [{"heading": 60, "length": 2400}],
        },
        {
            "name": "Bassel Al-Assad (Khmeimim)",
            "id": 13,
            "x": 84540,
            "y": 11990,
            "alt": 25,
            "default_coalition": "red",
            "runways": [{"heading": 178, "length": 2800}],
            "tacan": "44X",
        },
        {
            "name": "Aleppo Intl",
            "id": 14,
            "x": 135960,
            "y": 87240,
            "alt": 390,
            "default_coalition": "red",
            "runways": [{"heading": 94, "length": 2800}],
        },
        {
            "name": "Kuweires",
            "id": 15,
            "x": 148280,
            "y": 102000,
            "alt": 360,
            "default_coalition": "red",
            "runways": [{"heading": 105, "length": 2600}],
        },
        {
            "name": "Jirah",
            "id": 16,
            "x": 156980,
            "y": 130270,
            "alt": 325,
            "default_coalition": "red",
            "runways": [{"heading": 100, "length": 2400}],
        },
        {
            "name": "Tabqa",
            "id": 17,
            "x": 146620,
            "y": 182880,
            "alt": 320,
            "default_coalition": "red",
            "runways": [{"heading": 94, "length": 3000}],
        },
        {
            "name": "Tiyas (T-4)",
            "id": 18,
            "x": 30600,
            "y": 167720,
            "alt": 570,
            "default_coalition": "red",
            "runways": [{"heading": 90, "length": 3100}],
        },
        {
            "name": "Hama",
            "id": 19,
            "x": 49920,
            "y": 97400,
            "alt": 300,
            "default_coalition": "red",
            "runways": [{"heading": 89, "length": 2400}],
        },
        {
            "name": "An Nasiriyah",
            "id": 20,
            "x": 13760,
            "y": 56660,
            "alt": 250,
            "default_coalition": "red",
            "runways": [{"heading": 40, "length": 2400}],
        },
        {
            "name": "Sayqal",
            "id": 21,
            "x": -164780,
            "y": 122870,
            "alt": 680,
            "default_coalition": "red",
            "runways": [{"heading": 60, "length": 3100}],
        },
    ],

    "cities": [
        {"name": "Damascus", "x": -170000, "y": 75000, "side": "red"},
        {"name": "Aleppo", "x": 140000, "y": 85000, "side": "red"},
        {"name": "Homs", "x": 18000, "y": 65000, "side": "red"},
        {"name": "Latakia", "x": 82000, "y": 7000, "side": "red"},
        {"name": "Palmyra", "x": 15000, "y": 210000, "side": "red"},
        {"name": "Raqqa", "x": 155000, "y": 200000, "side": "contested"},
        {"name": "Beirut", "x": -30000, "y": -10000, "side": "neutral"},
        {"name": "Haifa", "x": -42000, "y": -82000, "side": "blue"},
        {"name": "Adana", "x": 210000, "y": -25000, "side": "blue"},
    ],

    "sam_zones": [
        {"name": "Damascus Defense Ring", "x": -172000, "y": 80000, "radius": 25000, "side": "red"},
        {"name": "Latakia/Khmeimim Defense", "x": 85000, "y": 10000, "radius": 15000, "side": "red"},
        {"name": "Aleppo Defense", "x": 138000, "y": 88000, "radius": 12000, "side": "red"},
        {"name": "Homs Industrial", "x": 20000, "y": 68000, "radius": 10000, "side": "red"},
        {"name": "T-4 Air Base Defense", "x": 32000, "y": 168000, "radius": 8000, "side": "red"},
        {"name": "Mezzeh Military", "x": -165000, "y": 69000, "radius": 5000, "side": "red"},
        {"name": "Incirlik Defense", "x": 220000, "y": -35000, "radius": 10000, "side": "blue"},
        {"name": "Ramat David Defense", "x": -27000, "y": -72000, "radius": 8000, "side": "blue"},
    ],

    "front_lines": [
        {
            "name": "Northern Syria Front",
            "description": "Coalition vs Syrian/Russian forces near Aleppo",
            "blue_start": {"x": 180000, "y": 80000},
            "red_start": {"x": 140000, "y": 88000},
            "axis": "south",
            "width": 30000,
        },
        {
            "name": "Euphrates Front",
            "description": "Fighting along the Euphrates river valley",
            "blue_start": {"x": 170000, "y": 200000},
            "red_start": {"x": 145000, "y": 180000},
            "axis": "west",
            "width": 20000,
        },
    ],

    "naval_zones": [
        {"name": "Eastern Med Patrol", "x": 0, "y": -200000, "radius": 100000},
        {"name": "Latakia Coast", "x": 80000, "y": -30000, "radius": 40000},
    ],

    "cap_orbits": [
        {"name": "Northern CAP", "x1": 180000, "y1": 40000, "x2": 200000, "y2": 0, "alt": 8000, "side": "blue"},
        {"name": "Syrian CAP", "x1": 100000, "y1": 50000, "x2": 120000, "y2": 80000, "alt": 7000, "side": "red"},
        {"name": "Damascus CAP", "x1": -160000, "y1": 60000, "x2": -180000, "y2": 90000, "alt": 7500, "side": "red"},
    ],

    "support_orbits": {
        "tanker": {"name": "Shell", "x1": 200000, "y1": -50000, "x2": 180000, "y2": -70000, "alt": 6000, "freq": 251.0, "tacan": "51Y"},
        "awacs": {"name": "Magic", "x1": 190000, "y1": -60000, "x2": 170000, "y2": -80000, "alt": 9000, "freq": 252.0},
    },

    "convoy_routes": {
        "red": [
            {
                "name": "Damascus-Homs Highway",
                "waypoints": [
                    {"x": -170000, "y": 75000},
                    {"x": -100000, "y": 70000},
                    {"x": -30000, "y": 67000},
                    {"x": 18000, "y": 65000},
                ],
            },
            {
                "name": "Aleppo-Front Supply",
                "waypoints": [
                    {"x": 140000, "y": 85000},
                    {"x": 155000, "y": 120000},
                    {"x": 155000, "y": 180000},
                ],
            },
        ],
        "blue": [
            {
                "name": "Incirlik-Border Logistics",
                "waypoints": [
                    {"x": 220000, "y": -35000},
                    {"x": 200000, "y": 0},
                    {"x": 180000, "y": 40000},
                    {"x": 170000, "y": 80000},
                ],
            },
        ],
    },

    # Water zones — areas where ground units should not be placed
    "water_zones": [
        {"name": "Mediterranean Sea", "x": 100000, "y": -150000, "radius": 200000},
        {"name": "Mediterranean West", "x": -50000, "y": -80000, "radius": 150000},
    ],
}

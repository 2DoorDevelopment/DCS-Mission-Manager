"""
Caucasus Map Database
DCS coordinates use a local X/Y system (meters) relative to the map origin.
Lat/Lon provided for reference; DCS mission files use X/Y.
"""

CAUCASUS_MAP = {
    "display_name": "Caucasus",
    "theater_id": "Caucasus",
    # DCS internal theater name
    "dcs_theater": "Caucasus",

    # Map bounds (approximate, for placing units sensibly)
    "bounds": {
        "x_min": -300000, "x_max": 800000,
        "y_min": -400000, "y_max": 1000000,
    },

    # Time/date defaults
    "default_date": {"year": 2024, "month": 6, "day": 15},

    "airfields": [
        # ---- BLUE (Georgian/NATO side) ----
        {
            "name": "Kutaisi",
            "id": 22,
            "x": -284860,
            "y": 683839,
            "alt": 44,
            "default_coalition": "blue",
            "runways": [{"heading": 74, "length": 2500}],
            "tacan": "44X",
            "ils": "109.75",
            "atis": "131.000",
        },
        {
            "name": "Senaki-Kolkhi",
            "id": 25,
            "x": -281219,
            "y": 648379,
            "alt": 13,
            "default_coalition": "blue",
            "runways": [{"heading": 93, "length": 2400}],
            "tacan": "31X",
            "ils": "108.90",
        },
        {
            "name": "Batumi",
            "id": 13,
            "x": -355692,
            "y": 617877,
            "alt": 5,
            "default_coalition": "blue",
            "runways": [{"heading": 130, "length": 2400}],
            "tacan": "16X",
            "ils": "110.30",
            "atis": "131.500",
        },
        {
            "name": "Kobuleti",
            "id": 24,
            "x": -317759,
            "y": 635620,
            "alt": 18,
            "default_coalition": "blue",
            "runways": [{"heading": 70, "length": 2400}],
            "tacan": "67X",
            "ils": "111.50",
        },
        {
            "name": "Tbilisi-Lochini",
            "id": 31,
            "x": -314652,
            "y": 895724,
            "alt": 490,
            "default_coalition": "blue",
            "runways": [{"heading": 131, "length": 3000}, {"heading": 136, "length": 2700}],
            "tacan": "25X",
            "ils": "110.30",
        },
        {
            "name": "Vaziani",
            "id": 32,
            "x": -318414,
            "y": 903698,
            "alt": 462,
            "default_coalition": "blue",
            "runways": [{"heading": 136, "length": 2400}],
            "tacan": "22X",
            "ils": "108.75",
        },

        # ---- RED (Russian/Abkhazian side) ----
        {
            "name": "Sukhumi-Babushara",
            "id": 20,
            "x": -220707,
            "y": 565775,
            "alt": 13,
            "default_coalition": "red",
            "runways": [{"heading": 120, "length": 3000}],
        },
        {
            "name": "Gudauta",
            "id": 18,
            "x": -196850,
            "y": 516587,
            "alt": 21,
            "default_coalition": "red",
            "runways": [{"heading": 150, "length": 2400}],
        },
        {
            "name": "Sochi-Adler",
            "id": 19,
            "x": -165163,
            "y": 461198,
            "alt": 30,
            "default_coalition": "red",
            "runways": [{"heading": 60, "length": 2900}],
        },
        {
            "name": "Krasnodar-Center",
            "id": 14,
            "x": -11516,
            "y": 367806,
            "alt": 30,
            "default_coalition": "red",
            "runways": [{"heading": 92, "length": 2400}],
        },
        {
            "name": "Krasnodar-Pashkovsky",
            "id": 15,
            "x": -6974,
            "y": 387874,
            "alt": 30,
            "default_coalition": "red",
            "runways": [{"heading": 42, "length": 3000}],
        },
        {
            "name": "Krymsk",
            "id": 16,
            "x": -7595,
            "y": 293712,
            "alt": 20,
            "default_coalition": "red",
            "runways": [{"heading": 39, "length": 2400}],
        },
        {
            "name": "Maykop-Khanskaya",
            "id": 17,
            "x": -27626,
            "y": 457048,
            "alt": 190,
            "default_coalition": "red",
            "runways": [{"heading": 40, "length": 3200}],
        },
        {
            "name": "Mineralnye Vody",
            "id": 28,
            "x": -52090,
            "y": 707747,
            "alt": 315,
            "default_coalition": "red",
            "runways": [{"heading": 120, "length": 3900}],
        },
        {
            "name": "Mozdok",
            "id": 27,
            "x": -83330,
            "y": 835635,
            "alt": 151,
            "default_coalition": "red",
            "runways": [{"heading": 82, "length": 3200}],
        },
        {
            "name": "Nalchik",
            "id": 26,
            "x": -125500,
            "y": 759400,
            "alt": 430,
            "default_coalition": "red",
            "runways": [{"heading": 60, "length": 2300}],
        },
        {
            "name": "Beslan",
            "id": 30,
            "x": -148340,
            "y": 842760,
            "alt": 530,
            "default_coalition": "red",
            "runways": [{"heading": 96, "length": 3060}],
        },
        {
            "name": "Anapa-Vityazevo",
            "id": 12,
            "x": -4957,
            "y": 243127,
            "alt": 43,
            "default_coalition": "red",
            "runways": [{"heading": 40, "length": 2500}],
        },
        {
            "name": "Gelendzhik",
            "id": 33,
            "x": -50996,
            "y": 297849,
            "alt": 22,
            "default_coalition": "red",
            "runways": [{"heading": 40, "length": 1800}],
        },
        {
            "name": "Novorossiysk",
            "id": 34,
            "x": -40299,
            "y": 279854,
            "alt": 45,
            "default_coalition": "red",
            "runways": [{"heading": 40, "length": 1400}],
        },
    ],

    # Key cities/towns for placing ground objectives
    "cities": [
        {"name": "Sukhumi", "x": -220000, "y": 562000, "side": "contested"},
        {"name": "Ochamchira", "x": -237000, "y": 590000, "side": "contested"},
        {"name": "Gali", "x": -249000, "y": 612000, "side": "contested"},
        {"name": "Zugdidi", "x": -265000, "y": 634000, "side": "blue"},
        {"name": "Poti", "x": -276000, "y": 647000, "side": "blue"},
        {"name": "Kutaisi", "x": -285000, "y": 684000, "side": "blue"},
        {"name": "Gudauta", "x": -197000, "y": 515000, "side": "red"},
        {"name": "Tuapse", "x": -100000, "y": 400000, "side": "red"},
        {"name": "Sochi", "x": -165000, "y": 461000, "side": "red"},
        {"name": "Tbilisi", "x": -315000, "y": 895000, "side": "blue"},
    ],

    # Typical SAM placement zones (areas where AI would realistically place SAMs)
    "sam_zones": [
        {"name": "Sukhumi Coastal Defense", "x": -215000, "y": 560000, "radius": 15000, "side": "red"},
        {"name": "Gudauta Air Base Defense", "x": -195000, "y": 518000, "radius": 10000, "side": "red"},
        {"name": "Sochi Approach", "x": -160000, "y": 455000, "radius": 20000, "side": "red"},
        {"name": "Kutaisi Defense", "x": -283000, "y": 680000, "radius": 12000, "side": "blue"},
        {"name": "Senaki Defense", "x": -278000, "y": 645000, "radius": 10000, "side": "blue"},
        {"name": "Front Line Gali", "x": -248000, "y": 610000, "radius": 8000, "side": "red"},
        {"name": "Ochamchira Forward", "x": -235000, "y": 585000, "radius": 8000, "side": "red"},
        {"name": "Krasnodar Region", "x": -10000, "y": 375000, "radius": 25000, "side": "red"},
    ],

    # Front line definitions for ground war
    "front_lines": [
        {
            "name": "Abkhazia Front",
            "description": "Main front between Georgian and Abkhazian/Russian forces",
            "blue_start": {"x": -260000, "y": 625000},
            "red_start": {"x": -235000, "y": 590000},
            "axis": "northwest",  # direction of red advance
            "width": 20000,
        },
        {
            "name": "Coastal Front",
            "description": "Coastal road fighting between Poti and Sukhumi",
            "blue_start": {"x": -270000, "y": 640000},
            "red_start": {"x": -225000, "y": 570000},
            "axis": "northwest",
            "width": 10000,
        },
    ],

    # Naval areas
    "naval_zones": [
        {"name": "Black Sea Patrol", "x": -180000, "y": 400000, "radius": 80000},
        {"name": "Batumi Coastal", "x": -360000, "y": 600000, "radius": 30000},
    ],

    # CAP/patrol orbits
    "cap_orbits": [
        {"name": "Western CAP", "x1": -250000, "y1": 600000, "x2": -250000, "y2": 650000, "alt": 7000, "side": "blue"},
        {"name": "Eastern CAP", "x1": -200000, "y1": 550000, "x2": -200000, "y2": 500000, "alt": 8000, "side": "red"},
        {"name": "Sochi CAP", "x1": -160000, "y1": 440000, "x2": -170000, "y2": 480000, "alt": 8000, "side": "red"},
    ],

    # Tanker/AWACS orbits
    "support_orbits": {
        "tanker": {"name": "Texaco", "x1": -300000, "y1": 680000, "x2": -310000, "y2": 720000, "alt": 6000, "freq": 251.0, "tacan": "51Y"},
        "awacs": {"name": "Overlord", "x1": -310000, "y1": 700000, "x2": -320000, "y2": 740000, "alt": 9000, "freq": 252.0},
    },

    # Convoy routes (sequences of waypoints along roads)
    "convoy_routes": {
        "red": [
            {
                "name": "Sochi-Sukhumi Supply Line",
                "waypoints": [
                    {"x": -165000, "y": 461000},   # Sochi area
                    {"x": -185000, "y": 490000},   # Coastal road
                    {"x": -197000, "y": 516000},   # Gudauta
                    {"x": -220000, "y": 562000},   # Sukhumi
                ],
            },
            {
                "name": "Gudauta-Front Resupply",
                "waypoints": [
                    {"x": -197000, "y": 516000},   # Gudauta
                    {"x": -220000, "y": 562000},   # Sukhumi
                    {"x": -237000, "y": 590000},   # Ochamchira
                    {"x": -248000, "y": 610000},   # Gali (front)
                ],
            },
        ],
        "blue": [
            {
                "name": "Kutaisi-Front Supply",
                "waypoints": [
                    {"x": -285000, "y": 684000},   # Kutaisi
                    {"x": -276000, "y": 647000},   # Poti
                    {"x": -265000, "y": 634000},   # Zugdidi
                    {"x": -255000, "y": 620000},   # Front area
                ],
            },
            {
                "name": "Batumi-Senaki Logistics",
                "waypoints": [
                    {"x": -355000, "y": 618000},   # Batumi
                    {"x": -317000, "y": 636000},   # Kobuleti
                    {"x": -281000, "y": 648000},   # Senaki
                ],
            },
        ],
    },
}

"""
Cold War Germany Map Database (Falklands-era / Cold War themed)
This is a newer DCS map — coordinates approximate based on available data.
"""

COLD_WAR_GERMANY_MAP = {
    "display_name": "Cold War Germany",
    "theater_id": "ColdWarGermany",
    "dcs_theater": "Germany",  # DCS internal theater name for Cold War Germany map

    "bounds": {
        "x_min": -300000, "x_max": 300000,
        "y_min": -300000, "y_max": 300000,
    },

    "default_date": {"year": 1985, "month": 8, "day": 15},

    "airfields": [
        # ---- BLUE (NATO / West Germany) ----
        {
            "name": "Ramstein",
            "id": 1,
            "x": -25000,
            "y": -120000,
            "alt": 237,
            "default_coalition": "blue",
            "runways": [{"heading": 92, "length": 3050}],
            "tacan": "40X",
        },
        {
            "name": "Spangdahlem",
            "id": 2,
            "x": 15000,
            "y": -160000,
            "alt": 370,
            "default_coalition": "blue",
            "runways": [{"heading": 55, "length": 2440}],
            "tacan": "18X",
        },
        {
            "name": "Hahn",
            "id": 3,
            "x": 25000,
            "y": -145000,
            "alt": 500,
            "default_coalition": "blue",
            "runways": [{"heading": 39, "length": 3050}],
            "tacan": "96X",
        },
        {
            "name": "Bitburg",
            "id": 4,
            "x": 10000,
            "y": -155000,
            "alt": 380,
            "default_coalition": "blue",
            "runways": [{"heading": 60, "length": 2900}],
            "tacan": "19X",
        },
        {
            "name": "Sembach",
            "id": 5,
            "x": -18000,
            "y": -110000,
            "alt": 312,
            "default_coalition": "blue",
            "runways": [{"heading": 58, "length": 1800}],
        },
        {
            "name": "Norvenich",
            "id": 6,
            "x": 90000,
            "y": -130000,
            "alt": 86,
            "default_coalition": "blue",
            "runways": [{"heading": 74, "length": 2430}],
            "tacan": "61X",
        },
        {
            "name": "Wiesbaden",
            "id": 7,
            "x": 25000,
            "y": -85000,
            "alt": 140,
            "default_coalition": "blue",
            "runways": [{"heading": 85, "length": 1800}],
        },
        {
            "name": "Geilenkirchen",
            "id": 8,
            "x": 105000,
            "y": -155000,
            "alt": 90,
            "default_coalition": "blue",
            "runways": [{"heading": 93, "length": 3050}],
            "tacan": "63X",
        },

        # ---- RED (Warsaw Pact / East Germany) ----
        {
            "name": "Erfurt-Bindersleben",
            "id": 20,
            "x": 80000,
            "y": 30000,
            "alt": 315,
            "default_coalition": "red",
            "runways": [{"heading": 100, "length": 2400}],
        },
        {
            "name": "Altenburg-Nobitz",
            "id": 21,
            "x": 120000,
            "y": 60000,
            "alt": 195,
            "default_coalition": "red",
            "runways": [{"heading": 75, "length": 2400}],
        },
        {
            "name": "Merseburg",
            "id": 22,
            "x": 140000,
            "y": 70000,
            "alt": 104,
            "default_coalition": "red",
            "runways": [{"heading": 60, "length": 2500}],
        },
        {
            "name": "Grossenhain",
            "id": 23,
            "x": 180000,
            "y": 90000,
            "alt": 147,
            "default_coalition": "red",
            "runways": [{"heading": 100, "length": 2500}],
        },
        {
            "name": "Brand-Briesen",
            "id": 24,
            "x": 200000,
            "y": 120000,
            "alt": 55,
            "default_coalition": "red",
            "runways": [{"heading": 90, "length": 2400}],
        },
        {
            "name": "Parchim",
            "id": 25,
            "x": 200000,
            "y": 160000,
            "alt": 45,
            "default_coalition": "red",
            "runways": [{"heading": 100, "length": 2400}],
        },
        {
            "name": "Laage",
            "id": 26,
            "x": 230000,
            "y": 170000,
            "alt": 15,
            "default_coalition": "red",
            "runways": [{"heading": 100, "length": 2400}],
        },
    ],

    "cities": [
        {"name": "Frankfurt", "x": 20000, "y": -70000, "side": "blue"},
        {"name": "Kassel", "x": 55000, "y": -15000, "side": "blue"},
        {"name": "Fulda", "x": 40000, "y": 0, "side": "contested"},
        {"name": "Erfurt", "x": 80000, "y": 30000, "side": "red"},
        {"name": "Bonn", "x": 75000, "y": -130000, "side": "blue"},
        {"name": "Cologne", "x": 80000, "y": -130000, "side": "blue"},
        {"name": "Leipzig", "x": 150000, "y": 75000, "side": "red"},
        {"name": "Eisenach", "x": 60000, "y": 20000, "side": "contested"},
        {"name": "Goettingen", "x": 60000, "y": -20000, "side": "blue"},
        {"name": "Bad Hersfeld", "x": 45000, "y": -5000, "side": "contested"},
    ],

    "sam_zones": [
        {"name": "Fulda Gap Forward SAM", "x": 50000, "y": 5000, "radius": 10000, "side": "red"},
        {"name": "Erfurt Air Defense", "x": 80000, "y": 32000, "radius": 12000, "side": "red"},
        {"name": "Leipzig Defense Ring", "x": 148000, "y": 73000, "radius": 15000, "side": "red"},
        {"name": "IGB Forward Defense", "x": 55000, "y": 15000, "radius": 8000, "side": "red"},
        {"name": "Ramstein Defense", "x": -23000, "y": -118000, "radius": 10000, "side": "blue"},
        {"name": "Frankfurt Defense", "x": 22000, "y": -68000, "radius": 12000, "side": "blue"},
        {"name": "Kassel Defense", "x": 57000, "y": -13000, "radius": 8000, "side": "blue"},
    ],

    "front_lines": [
        {
            "name": "Fulda Gap",
            "description": "Primary Warsaw Pact axis of advance through the Fulda Gap",
            "blue_start": {"x": 35000, "y": -5000},
            "red_start": {"x": 60000, "y": 20000},
            "axis": "west",
            "width": 25000,
        },
        {
            "name": "North German Plain",
            "description": "Secondary axis across the North German Plain",
            "blue_start": {"x": 100000, "y": -80000},
            "red_start": {"x": 140000, "y": -30000},
            "axis": "west",
            "width": 30000,
        },
    ],

    "naval_zones": [],  # Landlocked theater

    "cap_orbits": [
        {"name": "NATO Forward CAP", "x1": 30000, "y1": -30000, "x2": 50000, "y2": -10000, "alt": 7000, "side": "blue"},
        {"name": "NATO Rear CAP", "x1": 0, "y1": -100000, "x2": 20000, "y2": -80000, "alt": 7500, "side": "blue"},
        {"name": "Warsaw Pact CAP", "x1": 90000, "y1": 40000, "x2": 110000, "y2": 60000, "alt": 7000, "side": "red"},
    ],

    "support_orbits": {
        "tanker": {"name": "Arco", "x1": -10000, "y1": -120000, "x2": -30000, "y2": -140000, "alt": 6000, "freq": 251.0, "tacan": "51Y"},
        "awacs": {"name": "Darkstar", "x1": -20000, "y1": -130000, "x2": -40000, "y2": -150000, "alt": 9000, "freq": 252.0},
    },

    "convoy_routes": {
        "red": [
            {
                "name": "Erfurt-Fulda Advance Route",
                "waypoints": [
                    {"x": 80000, "y": 30000},
                    {"x": 65000, "y": 18000},
                    {"x": 50000, "y": 5000},
                    {"x": 40000, "y": 0},
                ],
            },
        ],
        "blue": [
            {
                "name": "Frankfurt-Kassel Supply Line",
                "waypoints": [
                    {"x": 20000, "y": -70000},
                    {"x": 35000, "y": -40000},
                    {"x": 45000, "y": -15000},
                    {"x": 55000, "y": -5000},
                ],
            },
        ],
    },
}

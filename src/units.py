"""
DCS Unit Type Database
All type strings must match DCS internal identifiers exactly.
"""

# ============================================================
# PLAYER AIRCRAFT (modules Noah owns)
# ============================================================
PLAYER_AIRCRAFT = {
    "F-16C": {
        "type": "F-16C_50",
        "display_name": "F-16C Viper",
        "category": "fighter",
        "roles": ["SEAD", "CAP", "strike", "escort", "sweep"],
        "fuel": 3249,
        "chaff": 60,
        "flare": 60,
        "radio_freq": 305.0,
        "default_loadouts": {
            "SEAD": {
                "description": "2x AGM-88C HARM, 2x AIM-120C, 2x AIM-9X, ECM pod, targeting pod",
                "pylons": {
                    1: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},  # AIM-9X
                    2: {"CLSID": "{6D21ECEA-F85B-4E8D-9D51-31DC9B8AA4EF}"},  # AGM-88C
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},  # AIM-120C
                    4: {"CLSID": "{8A0BE8AE-58D4-4572-9263-3144C45E5D75}"},  # ECM pod AN/ALQ-184
                    5: {"CLSID": "{F376DBEE-4CAE-41BA-ADD9-B2910AC95DEC}"},  # 370gal tank
                    6: {"CLSID": "{AAQ-28_LITENING}"},  # Targeting pod
                    7: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},  # AIM-120C
                    8: {"CLSID": "{6D21ECEA-F85B-4E8D-9D51-31DC9B8AA4EF}"},  # AGM-88C
                    9: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},  # AIM-9X
                },
            },
            "CAP": {
                "description": "4x AIM-120C, 2x AIM-9X, ECM, centerline tank",
                "pylons": {
                    1: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    2: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    4: {"CLSID": "{8A0BE8AE-58D4-4572-9263-3144C45E5D75}"},
                    5: {"CLSID": "{F376DBEE-4CAE-41BA-ADD9-B2910AC95DEC}"},
                    6: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},  # AIM-9X
                    7: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    8: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    9: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                },
            },
            "strike": {
                "description": "4x GBU-31 JDAM, 2x AIM-9X, targeting pod, ECM",
                "pylons": {
                    1: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    2: {"CLSID": "{GBU-31}"},
                    3: {"CLSID": "{GBU-31}"},
                    4: {"CLSID": "{8A0BE8AE-58D4-4572-9263-3144C45E5D75}"},
                    5: {"CLSID": "{F376DBEE-4CAE-41BA-ADD9-B2910AC95DEC}"},
                    6: {"CLSID": "{AAQ-28_LITENING}"},
                    7: {"CLSID": "{GBU-31}"},
                    8: {"CLSID": "{GBU-31}"},
                    9: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                },
            },
        },
    },
    "F/A-18C": {
        "type": "FA-18C_hornet",
        "display_name": "F/A-18C Hornet",
        "category": "fighter",
        "roles": ["SEAD", "CAP", "strike", "anti-ship", "escort"],
        "fuel": 4900,
        "chaff": 60,
        "flare": 60,
        "radio_freq": 305.0,
        "default_loadouts": {
            "SEAD": {
                "description": "2x AGM-88C HARM, 2x AIM-120C, 2x AIM-9X",
                "pylons": {},
            },
            "CAP": {
                "description": "6x AIM-120C, 2x AIM-9X, centerline tank",
                "pylons": {},
            },
            "strike": {
                "description": "4x GBU-38 JDAM, 2x AIM-9X, ATFLIR",
                "pylons": {},
            },
            "anti-ship": {
                "description": "2x AGM-84D Harpoon, 2x AIM-120C, 2x AIM-9X",
                "pylons": {},
            },
        },
    },
    "A-10C": {
        "type": "A-10C_2",
        "display_name": "A-10C II Thunderbolt",
        "category": "attacker",
        "roles": ["CAS", "CSAR", "FAC"],
        "fuel": 5029,
        "chaff": 240,
        "flare": 480,
        "radio_freq": 305.0,
        "default_loadouts": {
            "CAS": {
                "description": "2x AGM-65D Maverick, 2x GBU-12, rocket pods, ECM, targeting pod",
                "pylons": {},
            },
        },
    },
    "JF-17": {
        "type": "JF-17",
        "display_name": "JF-17 Thunder",
        "category": "fighter",
        "roles": ["strike", "anti-ship", "CAP", "SEAD"],
        "fuel": 2325,
        "chaff": 36,
        "flare": 36,
        "radio_freq": 305.0,
        "default_loadouts": {
            "strike": {
                "description": "2x LS-6 GPS bombs, 2x PL-5E, centerline tank",
                "pylons": {},
            },
            "anti-ship": {
                "description": "2x C-802AK, 2x PL-5E",
                "pylons": {},
            },
            "CAP": {
                "description": "4x SD-10A, 2x PL-5E",
                "pylons": {},
            },
        },
    },
    "F-15C": {
        "type": "F-15C",
        "display_name": "F-15C Eagle",
        "category": "fighter",
        "roles": ["CAP", "escort", "sweep"],
        "fuel": 6100,
        "chaff": 60,
        "flare": 60,
        "radio_freq": 305.0,
        "default_loadouts": {
            "CAP": {
                "description": "6x AIM-120C, 2x AIM-9M, centerline tank",
                "pylons": {
                    1: {"CLSID": "{6CEB49FC-DED8-4DED-B053-E1F033FF72D3}"},   # AIM-9M
                    2: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},   # AIM-120C
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    4: {"CLSID": "{E1F29B21-F291-4589-9FD8-3272EEC69506}"},   # Fuel tank
                    5: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    6: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    7: {"CLSID": "{6CEB49FC-DED8-4DED-B053-E1F033FF72D3}"},
                },
            },
            "escort": {
                "description": "6x AIM-120C, 2x AIM-9M, centerline tank",
                "pylons": {
                    1: {"CLSID": "{6CEB49FC-DED8-4DED-B053-E1F033FF72D3}"},
                    2: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    4: {"CLSID": "{E1F29B21-F291-4589-9FD8-3272EEC69506}"},
                    5: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    6: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    7: {"CLSID": "{6CEB49FC-DED8-4DED-B053-E1F033FF72D3}"},
                },
            },
        },
    },
    "F-15E": {
        "type": "F-15ESE",
        "display_name": "F-15E Strike Eagle",
        "category": "fighter",
        "roles": ["strike", "SEAD", "escort", "anti-ship", "CAP"],
        "fuel": 6100,
        "chaff": 60,
        "flare": 60,
        "radio_freq": 305.0,
        "default_loadouts": {
            "strike": {
                "description": "4x GBU-31 JDAM, 2x AIM-120C, 2x AIM-9M, LANTIRN pod, fuel",
                "pylons": {},
            },
            "SEAD": {
                "description": "4x AGM-88C HARM, 2x AIM-120C, 2x AIM-9M",
                "pylons": {},
            },
            "CAP": {
                "description": "6x AIM-120C, 2x AIM-9M, fuel tank",
                "pylons": {
                    1: {"CLSID": "{6CEB49FC-DED8-4DED-B053-E1F033FF72D3}"},
                    2: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    4: {"CLSID": "{E1F29B21-F291-4589-9FD8-3272EEC69506}"},
                    5: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    6: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    7: {"CLSID": "{6CEB49FC-DED8-4DED-B053-E1F033FF72D3}"},
                },
            },
        },
    },
    "AV-8B": {
        "type": "AV8BNA",
        "display_name": "AV-8B Harrier II",
        "category": "attacker",
        "roles": ["CAS", "strike", "anti-ship"],
        "fuel": 3060,
        "chaff": 60,
        "flare": 60,
        "radio_freq": 305.0,
        "default_loadouts": {
            "CAS": {
                "description": "4x GBU-12, 2x AGM-65E Maverick, 2x AIM-9M, LITENING pod",
                "pylons": {},
            },
            "strike": {
                "description": "6x Mk-83, 2x AIM-9M",
                "pylons": {},
            },
            "anti-ship": {
                "description": "2x AGM-65E Maverick, 2x Mk-83, 2x AIM-9M",
                "pylons": {},
            },
        },
    },
    "M-2000C": {
        "type": "M-2000C",
        "display_name": "Mirage 2000C",
        "category": "fighter",
        "roles": ["CAP", "sweep", "escort", "SEAD"],
        "fuel": 3160,
        "chaff": 54,
        "flare": 54,
        "radio_freq": 305.0,
        "default_loadouts": {
            "CAP": {
                "description": "2x Magic II, 2x Super 530D, centerline tank",
                "pylons": {},
            },
            "SEAD": {
                "description": "2x AS-30L, 2x Magic II",
                "pylons": {},
            },
            "sweep": {
                "description": "2x Magic II, 2x Super 530D",
                "pylons": {},
            },
        },
    },
    "AH-64D": {
        "type": "AH-64D_BLK_II",
        "display_name": "AH-64D Apache",
        "category": "helicopter",
        "roles": ["CAS", "CSAR"],
        "fuel": 1160,
        "chaff": 30,
        "flare": 30,
        "radio_freq": 305.0,
        "default_loadouts": {
            "CAS": {
                "description": "16x Hellfire AGM-114K, 2x rocket pods, 30mm cannon",
                "pylons": {},
            },
            "CSAR": {
                "description": "8x Hellfire AGM-114K, 2x rocket pods, 30mm cannon",
                "pylons": {},
            },
        },
    },
}

# ============================================================
# AI AIRCRAFT (for both sides)
# ============================================================
AI_AIRCRAFT = {
    # ---- BLUE AI ----
    "F-15C": {
        "type": "F-15C",
        "display_name": "F-15C Eagle",
        "coalition": "blue",
        "roles": ["CAP", "sweep", "escort"],
        "skill": "High",
        "loadouts": {
            "CAP": {
                "pylons": {
                    1: {"CLSID": "{6CEB49FC-DED8-4DED-B053-E1F033FF72D3}"},   # AIM-9M
                    2: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},   # AIM-120C
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},   # AIM-120C
                    4: {"CLSID": "{E1F29B21-F291-4589-9FD8-3272EEC69506}"},   # Fuel tank
                    5: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},   # AIM-120C
                    6: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},   # AIM-120C
                    7: {"CLSID": "{6CEB49FC-DED8-4DED-B053-E1F033FF72D3}"},   # AIM-9M
                },
            },
            "sweep": "CAP",  # Alias — same loadout
            "escort": "CAP",
        },
    },
    "F-16C_AI": {
        "type": "F-16C_50",
        "display_name": "F-16C Viper (AI)",
        "coalition": "blue",
        "roles": ["SEAD", "CAP", "strike"],
        "skill": "High",
        "loadouts": {
            "SEAD": {
                "pylons": {
                    1: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},   # AIM-9X
                    2: {"CLSID": "{B06DD79A-F21E-4EB9-BD9D-AB3844618C93}"},   # AGM-88C
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},   # AIM-120C
                    4: {"CLSID": "{8A0BE8AE-58D4-4572-9263-3144C45E5D75}"},   # ECM
                    5: {"CLSID": "{F376DBEE-4CAE-41BA-ADD9-B2910AC95DEC}"},   # 370gal tank
                    7: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},   # AIM-120C
                    8: {"CLSID": "{B06DD79A-F21E-4EB9-BD9D-AB3844618C93}"},   # AGM-88C
                    9: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},   # AIM-9X
                },
            },
            "CAP": {
                "pylons": {
                    1: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},
                    2: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    5: {"CLSID": "{F376DBEE-4CAE-41BA-ADD9-B2910AC95DEC}"},
                    7: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    8: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    9: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},
                },
            },
            "strike": {
                "pylons": {
                    1: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},
                    2: {"CLSID": "{GBU-31}"},
                    3: {"CLSID": "{GBU-31}"},
                    5: {"CLSID": "{F376DBEE-4CAE-41BA-ADD9-B2910AC95DEC}"},
                    6: {"CLSID": "{AAQ-28_LITENING}"},
                    7: {"CLSID": "{GBU-31}"},
                    8: {"CLSID": "{GBU-31}"},
                    9: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},
                },
            },
        },
    },
    "F/A-18C_AI": {
        "type": "FA-18C_hornet",
        "display_name": "F/A-18C Hornet (AI)",
        "coalition": "blue",
        "roles": ["SEAD", "CAP", "strike", "anti-ship"],
        "skill": "High",
        "loadouts": {
            "CAP": {
                "pylons": {
                    1: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},   # AIM-9X
                    2: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},   # AIM-120C
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    5: {"CLSID": "{FPU_8A_FUEL_TANK}"},
                    7: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    8: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    9: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},
                },
            },
            "SEAD": {
                "pylons": {
                    1: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},
                    2: {"CLSID": "{B06DD79A-F21E-4EB9-BD9D-AB3844618C93}"},   # AGM-88
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    5: {"CLSID": "{FPU_8A_FUEL_TANK}"},
                    7: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    8: {"CLSID": "{B06DD79A-F21E-4EB9-BD9D-AB3844618C93}"},
                    9: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},
                },
            },
            "strike": "SEAD",
            "anti-ship": {
                "pylons": {
                    1: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},
                    2: {"CLSID": "{AGM_84D}"},                                 # Harpoon
                    3: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    5: {"CLSID": "{FPU_8A_FUEL_TANK}"},
                    7: {"CLSID": "{40EF17B7-F508-45de-8566-6FBBE0C1A276}"},
                    8: {"CLSID": "{AGM_84D}"},
                    9: {"CLSID": "{9B31BFDB-4411-4B9F-80C4-E78A2D8E3E80}"},
                },
            },
        },
    },
    "A-10C_AI": {
        "type": "A-10C_2",
        "display_name": "A-10C II (AI)",
        "coalition": "blue",
        "roles": ["CAS"],
        "skill": "High",
        "loadouts": {
            "CAS": {
                "pylons": {
                    1: {"CLSID": "{DB434044-F5D0-4F1F-9BA9-B73027E18DD3}"},   # AGM-65D
                    3: {"CLSID": "{BCE4E030-38E9-423E-98ED-24BE3DA87C32}"},   # Mk-82
                    4: {"CLSID": "{BCE4E030-38E9-423E-98ED-24BE3DA87C32}"},
                    7: {"CLSID": "{BCE4E030-38E9-423E-98ED-24BE3DA87C32}"},
                    8: {"CLSID": "{BCE4E030-38E9-423E-98ED-24BE3DA87C32}"},
                    11: {"CLSID": "{DB434044-F5D0-4F1F-9BA9-B73027E18DD3}"},
                },
            },
        },
    },
    "KC-135": {
        "type": "KC135MPRS",
        "display_name": "KC-135 Stratotanker",
        "coalition": "blue",
        "roles": ["tanker"],
        "skill": "High",
        "loadouts": {},
    },
    "E-3A": {
        "type": "E-3A",
        "display_name": "E-3A AWACS",
        "coalition": "blue",
        "roles": ["awacs"],
        "skill": "High",
        "loadouts": {},
    },

    # ---- RED AI ----
    "Su-27": {
        "type": "Su-27",
        "display_name": "Su-27 Flanker",
        "coalition": "red",
        "roles": ["CAP", "sweep", "escort"],
        "skill": "High",
        "loadouts": {
            "CAP": {
                "pylons": {
                    1: {"CLSID": "{FBC29BFE-3D24-4C64-B81D-941239571550}"},   # R-27ER
                    2: {"CLSID": "{B79C48E8-B2E2-4F95-ABB3-A44B4597E2A9}"},   # R-73
                    3: {"CLSID": "{FBC29BFE-3D24-4C64-B81D-941239571550}"},   # R-27ER
                    4: {"CLSID": "{275A2855-4A79-4B2D-B082-91EA2ADF4691}"},   # R-27R
                    7: {"CLSID": "{275A2855-4A79-4B2D-B082-91EA2ADF4691}"},
                    8: {"CLSID": "{FBC29BFE-3D24-4C64-B81D-941239571550}"},
                    9: {"CLSID": "{B79C48E8-B2E2-4F95-ABB3-A44B4597E2A9}"},
                    10: {"CLSID": "{FBC29BFE-3D24-4C64-B81D-941239571550}"},
                },
            },
            "sweep": "CAP",
            "escort": "CAP",
        },
    },
    "Su-33": {
        "type": "Su-33",
        "display_name": "Su-33 Flanker-D",
        "coalition": "red",
        "roles": ["CAP"],
        "skill": "High",
        "loadouts": {
            "CAP": {
                "pylons": {
                    1: {"CLSID": "{FBC29BFE-3D24-4C64-B81D-941239571550}"},
                    2: {"CLSID": "{B79C48E8-B2E2-4F95-ABB3-A44B4597E2A9}"},
                    3: {"CLSID": "{FBC29BFE-3D24-4C64-B81D-941239571550}"},
                    8: {"CLSID": "{FBC29BFE-3D24-4C64-B81D-941239571550}"},
                    9: {"CLSID": "{B79C48E8-B2E2-4F95-ABB3-A44B4597E2A9}"},
                    10: {"CLSID": "{FBC29BFE-3D24-4C64-B81D-941239571550}"},
                },
            },
        },
    },
    "MiG-29A": {
        "type": "MiG-29A",
        "display_name": "MiG-29A Fulcrum",
        "coalition": "red",
        "roles": ["CAP", "sweep"],
        "skill": "High",
        "loadouts": {
            "CAP": {
                "pylons": {
                    1: {"CLSID": "{B79C48E8-B2E2-4F95-ABB3-A44B4597E2A9}"},   # R-73
                    2: {"CLSID": "{9B25D316-0434-4954-868F-D51DB1A38DF0}"},   # R-27R
                    3: {"CLSID": "{9B25D316-0434-4954-868F-D51DB1A38DF0}"},
                    4: {"CLSID": "{2BFC4E04-C5AD-41f6-8495-A18E54B4B0B3}"},   # Fuel tank
                    5: {"CLSID": "{9B25D316-0434-4954-868F-D51DB1A38DF0}"},
                    6: {"CLSID": "{9B25D316-0434-4954-868F-D51DB1A38DF0}"},
                    7: {"CLSID": "{B79C48E8-B2E2-4F95-ABB3-A44B4597E2A9}"},
                },
            },
            "sweep": "CAP",
        },
    },
    "MiG-29S": {
        "type": "MiG-29S",
        "display_name": "MiG-29S Fulcrum",
        "coalition": "red",
        "roles": ["CAP", "sweep"],
        "skill": "High",
        "loadouts": {
            "CAP": {
                "pylons": {
                    1: {"CLSID": "{B79C48E8-B2E2-4F95-ABB3-A44B4597E2A9}"},
                    2: {"CLSID": "{FBC29BFE-3D24-4C64-B81D-941239571550}"},   # R-27ER
                    3: {"CLSID": "{9B25D316-0434-4954-868F-D51DB1A38DF0}"},
                    4: {"CLSID": "{2BFC4E04-C5AD-41f6-8495-A18E54B4B0B3}"},
                    5: {"CLSID": "{9B25D316-0434-4954-868F-D51DB1A38DF0}"},
                    6: {"CLSID": "{FBC29BFE-3D24-4C64-B81D-941239571550}"},
                    7: {"CLSID": "{B79C48E8-B2E2-4F95-ABB3-A44B4597E2A9}"},
                },
            },
            "sweep": "CAP",
        },
    },
    "MiG-31": {
        "type": "MiG-31",
        "display_name": "MiG-31 Foxhound",
        "coalition": "red",
        "roles": ["intercept"],
        "skill": "High",
        "loadouts": {
            "intercept": {
                "pylons": {
                    1: {"CLSID": "{4EDBA993-2E34-444C-95FB-549300BF7CAF}"},   # R-33
                    2: {"CLSID": "{4EDBA993-2E34-444C-95FB-549300BF7CAF}"},
                    3: {"CLSID": "{4EDBA993-2E34-444C-95FB-549300BF7CAF}"},
                    4: {"CLSID": "{4EDBA993-2E34-444C-95FB-549300BF7CAF}"},
                },
            },
            "CAP": "intercept",
        },
    },
    "Su-25": {
        "type": "Su-25",
        "display_name": "Su-25 Frogfoot",
        "coalition": "red",
        "roles": ["CAS"],
        "skill": "High",
        "loadouts": {
            "CAS": {
                "pylons": {
                    1: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},   # FAB-250
                    2: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    3: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    4: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    7: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    8: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    9: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    10: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                },
            },
        },
    },
    "Su-25T": {
        "type": "Su-25T",
        "display_name": "Su-25T Frogfoot",
        "coalition": "red",
        "roles": ["CAS", "SEAD"],
        "skill": "High",
        "loadouts": {
            "CAS": {
                "pylons": {
                    1: {"CLSID": "{D4A8D9B9-5C45-42e7-BBD2-0E54F8B4A4EC}"},   # Kh-25ML
                    2: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},   # FAB-250
                    3: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    8: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    9: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    10: {"CLSID": "{D4A8D9B9-5C45-42e7-BBD2-0E54F8B4A4EC}"},
                },
            },
            "SEAD": {
                "pylons": {
                    1: {"CLSID": "{0243B919-7624-47B6-A489-B3EB547EC2B4}"},    # Kh-25MP ARM
                    2: {"CLSID": "{0243B919-7624-47B6-A489-B3EB547EC2B4}"},
                    9: {"CLSID": "{0243B919-7624-47B6-A489-B3EB547EC2B4}"},
                    10: {"CLSID": "{0243B919-7624-47B6-A489-B3EB547EC2B4}"},
                },
            },
        },
    },
    "Su-24M": {
        "type": "Su-24M",
        "display_name": "Su-24M Fencer",
        "coalition": "red",
        "roles": ["strike"],
        "skill": "High",
        "loadouts": {
            "strike": {
                "pylons": {
                    1: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    2: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    3: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    6: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    7: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                    8: {"CLSID": "{3C612111-C7AD-476E-8A8E-2485812F4E5C}"},
                },
            },
        },
    },
    "Tu-22M3": {
        "type": "Tu-22M3",
        "display_name": "Tu-22M3 Backfire",
        "coalition": "red",
        "roles": ["anti-ship", "strike"],
        "skill": "High",
        "loadouts": {},  # Tu-22M3 uses internal weapons
    },
    "A-50": {
        "type": "A-50",
        "display_name": "A-50 Mainstay",
        "coalition": "red",
        "roles": ["awacs"],
        "skill": "High",
        "loadouts": {},
    },
    "IL-78M": {
        "type": "IL-78M",
        "display_name": "IL-78M Midas",
        "coalition": "red",
        "roles": ["tanker"],
        "skill": "High",
        "loadouts": {},
    },
}

# ============================================================
# SAM SYSTEMS
# ============================================================
SAM_SYSTEMS = {
    # ---- RED SAMs ----
    "SA-2": {
        "display_name": "SA-2 Guideline (S-75)",
        "threat_level": "low",
        "range_km": 30,
        "coalition": "red",
        "units": [
            {"type": "S_75M_Volhov", "name": "SR", "count": 1},
            {"type": "SNR_75V", "name": "TR", "count": 1},
            {"type": "5p73 s-125 ln", "name": "Launcher", "count": 6},
        ],
        "support": [
            {"type": "ZIL-131 APA-80", "name": "Power", "count": 1},
        ],
    },
    "SA-3": {
        "display_name": "SA-3 Goa (S-125)",
        "threat_level": "low",
        "range_km": 25,
        "coalition": "red",
        "units": [
            {"type": "p-19 s-125 sr", "name": "SR", "count": 1},
            {"type": "snr s-125 tr", "name": "TR", "count": 1},
            {"type": "5p73 s-125 ln", "name": "Launcher", "count": 4},
        ],
        "support": [],
    },
    "SA-6": {
        "display_name": "SA-6 Gainful (Kub)",
        "threat_level": "medium",
        "range_km": 24,
        "coalition": "red",
        "units": [
            {"type": "Kub 1S91 str", "name": "STR", "count": 1},
            {"type": "Kub 2P25 ln", "name": "Launcher", "count": 3},
        ],
        "support": [],
    },
    "SA-8": {
        "display_name": "SA-8 Gecko (Osa)",
        "threat_level": "medium",
        "range_km": 10,
        "coalition": "red",
        "units": [
            {"type": "Osa 9A33 ln", "name": "TEL", "count": 2},
        ],
        "support": [],
    },
    "SA-10": {
        "display_name": "SA-10 Grumble (S-300PS)",
        "threat_level": "high",
        "range_km": 75,
        "coalition": "red",
        "units": [
            {"type": "S-300PS 40B6M tr", "name": "TR", "count": 1},
            {"type": "S-300PS 40B6MD sr", "name": "SR", "count": 1},
            {"type": "S-300PS 5P85C ln", "name": "Launcher", "count": 4},
            {"type": "S-300PS 54K6 cp", "name": "CP", "count": 1},
        ],
        "support": [],
    },
    "SA-11": {
        "display_name": "SA-11 Gadfly (Buk)",
        "threat_level": "high",
        "range_km": 35,
        "coalition": "red",
        "units": [
            {"type": "SA-11 Buk SR 9S18M1", "name": "SR", "count": 1},
            {"type": "SA-11 Buk CC 9S470M1", "name": "CC", "count": 1},
            {"type": "SA-11 Buk LN 9A310M1", "name": "Launcher", "count": 3},
        ],
        "support": [],
    },
    "SA-15": {
        "display_name": "SA-15 Gauntlet (Tor)",
        "threat_level": "medium",
        "range_km": 12,
        "coalition": "red",
        "units": [
            {"type": "Tor 9A331", "name": "TEL", "count": 2},
        ],
        "support": [],
    },
    "SA-19": {
        "display_name": "SA-19 Tunguska",
        "threat_level": "medium",
        "range_km": 8,
        "coalition": "red",
        "units": [
            {"type": "2S6 Tunguska", "name": "SPAAG", "count": 2},
        ],
        "support": [],
    },

    # ---- RED MANPADS / SHORAD ----
    "ZSU-23-4": {
        "display_name": "ZSU-23-4 Shilka",
        "threat_level": "low",
        "range_km": 2.5,
        "coalition": "red",
        "units": [
            {"type": "ZSU-23-4 Shilka", "name": "Shilka", "count": 2},
        ],
        "support": [],
    },

    # ---- BLUE SAMs ----
    "Hawk": {
        "display_name": "MIM-23 Hawk",
        "threat_level": "medium",
        "range_km": 40,
        "coalition": "blue",
        "units": [
            {"type": "Hawk sr", "name": "SR", "count": 1},
            {"type": "Hawk tr", "name": "TR", "count": 1},
            {"type": "Hawk ln", "name": "Launcher", "count": 3},
            {"type": "Hawk pcp", "name": "PCP", "count": 1},
        ],
        "support": [],
    },
    "Patriot": {
        "display_name": "MIM-104 Patriot",
        "threat_level": "high",
        "range_km": 70,
        "coalition": "blue",
        "units": [
            {"type": "Patriot str", "name": "STR", "count": 1},
            {"type": "Patriot ECS", "name": "ECS", "count": 1},
            {"type": "Patriot ln", "name": "Launcher", "count": 4},
            {"type": "Patriot cp", "name": "CP", "count": 1},
            {"type": "Patriot EPP", "name": "EPP", "count": 1},
        ],
        "support": [],
    },
}

# ============================================================
# GROUND UNITS
# ============================================================
GROUND_UNITS = {
    # ---- RED GROUND ----
    "red_armor": [
        {"type": "T-72B", "name": "T-72B MBT"},
        {"type": "T-80UD", "name": "T-80UD MBT"},
        {"type": "T-55", "name": "T-55 MBT"},
        {"type": "BMP-2", "name": "BMP-2 IFV"},
        {"type": "BMP-1", "name": "BMP-1 IFV"},
        {"type": "BTR-80", "name": "BTR-80 APC"},
        {"type": "BRDM-2", "name": "BRDM-2 Scout"},
    ],
    "red_infantry": [
        {"type": "Paratrooper RPG-16", "name": "Infantry RPG"},
        {"type": "Infantry AK", "name": "Infantry AK"},
        {"type": "Paratrooper AKS-74", "name": "Paratrooper"},
    ],
    "red_artillery": [
        {"type": "2S1 Gvozdika", "name": "2S1 SPG"},
        {"type": "SAU 2-C9", "name": "2S9 Nona"},
        {"type": "BM-21 Grad", "name": "BM-21 MLRS"},
    ],
    "red_support": [
        {"type": "Ural-375 PBU", "name": "Command Vehicle"},
        {"type": "KAMAZ Truck", "name": "Supply Truck"},
        {"type": "ATZ-10", "name": "Fuel Truck"},
    ],

    # ---- BLUE GROUND ----
    "blue_armor": [
        {"type": "M-1 Abrams", "name": "M1 Abrams MBT"},
        {"type": "Leopard-2", "name": "Leopard 2 MBT"},
        {"type": "M-2 Bradley", "name": "M2 Bradley IFV"},
        {"type": "LAV-25", "name": "LAV-25"},
        {"type": "M1126 Stryker ICV", "name": "Stryker ICV"},
    ],
    "blue_infantry": [
        {"type": "Soldier M4", "name": "Infantry M4"},
        {"type": "Soldier M249", "name": "Infantry SAW"},
    ],
    "blue_artillery": [
        {"type": "M-109", "name": "M109 Paladin SPG"},
        {"type": "MLRS", "name": "M270 MLRS"},
    ],
    "blue_support": [
        {"type": "Hummer", "name": "HMMWV"},
        {"type": "M 818", "name": "M818 Truck"},
    ],
}

# ============================================================
# NAVAL UNITS
# ============================================================
NAVAL_UNITS = {
    "red_navy": [
        {"type": "MOSCOW", "name": "Moskva Cruiser"},
        {"type": "NEUSTRASH", "name": "Neustrashimy Frigate"},
        {"type": "MOLNIYA", "name": "Molniya Corvette"},
        {"type": "ALBATROS", "name": "Grisha Frigate"},
    ],
    "blue_navy": [
        {"type": "TICONDEROG", "name": "Ticonderoga Cruiser"},
        {"type": "PERRY", "name": "Perry Frigate"},
        {"type": "CVN_71", "name": "CVN-71 Roosevelt"},
        {"type": "LHA_Tarawa", "name": "LHA Tarawa"},
    ],
}

# ============================================================
# MISSION TYPE COMPOSITIONS
# Templates for what forces to generate based on mission type
# ============================================================
MISSION_TEMPLATES = {
    "SEAD": {
        "description": "Suppression/Destruction of Enemy Air Defenses",
        "player_goes_first": True,
        "default_enemy_sam": ["SA-6", "SA-11"],
        "default_enemy_air": ["MiG-29A", "Su-27"],
        "default_friendly_flights": [
            {"task": "escort", "aircraft": "F-15C", "count": 2},
            {"task": "sweep", "aircraft": "F-15C", "count": 2},
        ],
        "ground_war_default": True,
    },
    "CAS": {
        "description": "Close Air Support",
        "player_goes_first": False,  # SEAD goes first
        "default_enemy_sam": ["SA-8", "SA-15", "ZSU-23-4"],
        "default_enemy_air": ["MiG-29A"],
        "default_friendly_flights": [
            {"task": "SEAD", "aircraft": "F-16C_AI", "count": 2},
            {"task": "escort", "aircraft": "F-15C", "count": 2},
        ],
        "ground_war_default": True,
    },
    "CAP": {
        "description": "Combat Air Patrol",
        "player_goes_first": True,
        "default_enemy_sam": ["SA-6"],
        "default_enemy_air": ["Su-27", "MiG-29A", "MiG-29S"],
        "default_friendly_flights": [
            {"task": "CAP", "aircraft": "F-15C", "count": 2},
        ],
        "ground_war_default": False,
    },
    "strike": {
        "description": "Precision Strike",
        "player_goes_first": False,
        "default_enemy_sam": ["SA-6", "SA-11", "SA-8"],
        "default_enemy_air": ["MiG-29A", "Su-27"],
        "default_friendly_flights": [
            {"task": "SEAD", "aircraft": "F-16C_AI", "count": 2},
            {"task": "sweep", "aircraft": "F-15C", "count": 2},
            {"task": "escort", "aircraft": "F-15C", "count": 2},
        ],
        "ground_war_default": False,
    },
    "anti-ship": {
        "description": "Anti-Ship Strike",
        "player_goes_first": True,
        "default_enemy_sam": ["SA-6"],
        "default_enemy_air": ["Su-27", "Su-33"],
        "default_friendly_flights": [
            {"task": "escort", "aircraft": "F-15C", "count": 2},
            {"task": "sweep", "aircraft": "F-15C", "count": 2},
        ],
        "ground_war_default": False,
    },
    "escort": {
        "description": "Escort / Sweep",
        "player_goes_first": True,
        "default_enemy_sam": ["SA-6"],
        "default_enemy_air": ["Su-27", "MiG-29A", "MiG-29S"],
        "default_friendly_flights": [
            {"task": "strike", "aircraft": "F/A-18C_AI", "count": 4},
        ],
        "ground_war_default": False,
    },
    "convoy_attack": {
        "description": "Convoy Interdiction — Destroy enemy supply convoy",
        "player_goes_first": False,
        "default_enemy_sam": ["SA-8", "ZSU-23-4"],
        "default_enemy_air": ["MiG-29A"],
        "default_friendly_flights": [
            {"task": "SEAD", "aircraft": "F-16C_AI", "count": 2},
            {"task": "escort", "aircraft": "F-15C", "count": 2},
        ],
        "ground_war_default": False,
        "convoy_side": "red",
    },
    "convoy_defense": {
        "description": "Convoy Escort — Protect friendly supply convoy",
        "player_goes_first": True,
        "default_enemy_sam": ["SA-6"],
        "default_enemy_air": ["Su-25T", "MiG-29A"],
        "default_friendly_flights": [
            {"task": "CAP", "aircraft": "F-15C", "count": 2},
        ],
        "ground_war_default": False,
        "convoy_side": "blue",
    },
    "CSAR": {
        "description": "Combat Search and Rescue — Recover downed aircrew",
        "player_goes_first": False,
        "default_enemy_sam": ["SA-8", "ZSU-23-4"],
        "default_enemy_air": ["MiG-29A"],
        "default_friendly_flights": [
            {"task": "escort", "aircraft": "F-15C", "count": 2},
            {"task": "SEAD", "aircraft": "F-16C_AI", "count": 2},
        ],
        "ground_war_default": True,
    },
    "FAC": {
        "description": "Forward Air Controller (Airborne) — Coordinate CAS package",
        "player_goes_first": False,
        "default_enemy_sam": ["SA-8", "SA-15", "ZSU-23-4"],
        "default_enemy_air": ["MiG-29A"],
        "default_friendly_flights": [
            {"task": "CAS", "aircraft": "A-10C_AI", "count": 4},
            {"task": "escort", "aircraft": "F-15C", "count": 2},
        ],
        "ground_war_default": True,
    },
}

# Mapping from common LLM outputs to our keys
AIRCRAFT_ALIASES = {
    "f-16": "F-16C", "f16": "F-16C", "viper": "F-16C", "f-16c": "F-16C",
    "f-18": "F/A-18C", "f18": "F/A-18C", "hornet": "F/A-18C", "f/a-18c": "F/A-18C",
    "fa-18c": "F/A-18C", "fa18": "F/A-18C", "f/a-18": "F/A-18C",
    "a-10": "A-10C", "a10": "A-10C", "warthog": "A-10C", "a-10c": "A-10C",
    "a10c": "A-10C", "hawg": "A-10C", "thunderbolt": "A-10C",
    "jf-17": "JF-17", "jf17": "JF-17", "thunder": "JF-17",
    "f-15c": "F-15C", "f15c": "F-15C", "eagle": "F-15C", "f-15": "F-15C",
    "f-15e": "F-15E", "f15e": "F-15E", "strike eagle": "F-15E", "mudhen": "F-15E",
    "av-8b": "AV-8B", "av8b": "AV-8B", "harrier": "AV-8B", "av-8": "AV-8B",
    "m-2000c": "M-2000C", "m2000c": "M-2000C", "mirage": "M-2000C",
    "mirage 2000": "M-2000C", "mirage2000": "M-2000C",
    "ah-64": "AH-64D", "ah64": "AH-64D", "apache": "AH-64D", "ah-64d": "AH-64D",
}

MISSION_TYPE_ALIASES = {
    "sead": "SEAD", "dead": "SEAD", "sead/dead": "SEAD", "wild weasel": "SEAD",
    "cas": "CAS", "close air support": "CAS",
    "cap": "CAP", "combat air patrol": "CAP", "patrol": "CAP",
    "barcap": "CAP", "air superiority": "CAP", "dogfight": "CAP",
    "strike": "strike", "bombing": "strike", "attack": "strike",
    "anti-ship": "anti-ship", "anti ship": "anti-ship", "maritime strike": "anti-ship",
    "naval strike": "anti-ship",
    "escort": "escort", "sweep": "escort", "fighter sweep": "escort",
    "convoy attack": "convoy_attack", "convoy interdiction": "convoy_attack",
    "interdict convoy": "convoy_attack", "hit convoy": "convoy_attack",
    "destroy convoy": "convoy_attack", "convoy strike": "convoy_attack",
    "convoy defense": "convoy_defense", "convoy escort": "convoy_defense",
    "protect convoy": "convoy_defense", "defend convoy": "convoy_defense",
    "convoy protection": "convoy_defense",
    "csar": "CSAR", "search and rescue": "CSAR", "rescue": "CSAR",
    "combat sar": "CSAR", "pilot rescue": "CSAR",
    "fac": "FAC", "faca": "FAC", "forward air controller": "FAC",
    "jtac": "FAC", "tac": "FAC", "coordinate cas": "FAC",
}


def resolve_aircraft(name: str) -> str | None:
    """Resolve an aircraft name from LLM output."""
    if not name:
        return None
    lower = name.lower().strip()
    return AIRCRAFT_ALIASES.get(lower, None) or (name if name in PLAYER_AIRCRAFT else None)


def resolve_mission_type(name: str) -> str | None:
    """Resolve a mission type from LLM output."""
    if not name:
        return None
    lower = name.lower().strip()
    return MISSION_TYPE_ALIASES.get(lower, None) or (name if name in MISSION_TEMPLATES else None)


def resolve_ai_loadout(aircraft_key: str, task: str) -> dict:
    """
    Get the appropriate loadout (pylons dict) for an AI aircraft performing a task.
    Handles string aliases (e.g., "sweep" -> "CAP" loadout).
    Returns empty dict if no loadout defined.
    """
    ac_data = AI_AIRCRAFT.get(aircraft_key, {})
    loadouts = ac_data.get("loadouts", {})

    if not loadouts:
        return {}

    loadout = loadouts.get(task)

    # Follow alias chain (max 3 deep to prevent loops)
    depth = 0
    while isinstance(loadout, str) and depth < 3:
        loadout = loadouts.get(loadout)
        depth += 1

    if isinstance(loadout, dict) and "pylons" in loadout:
        return loadout["pylons"]

    # Fallback: try first available loadout
    for key, val in loadouts.items():
        if isinstance(val, dict) and "pylons" in val:
            return val["pylons"]

    return {}


# Convoy unit compositions
CONVOY_UNITS = {
    "red_supply": [
        {"type": "KAMAZ Truck", "name": "Supply Truck"},
        {"type": "KAMAZ Truck", "name": "Supply Truck"},
        {"type": "ATZ-10", "name": "Fuel Tanker"},
        {"type": "KAMAZ Truck", "name": "Ammo Truck"},
        {"type": "Ural-375 PBU", "name": "Command Vehicle"},
    ],
    "red_escort": [
        {"type": "BTR-80", "name": "BTR-80 Escort"},
        {"type": "BRDM-2", "name": "BRDM-2 Scout"},
        {"type": "ZSU-23-4 Shilka", "name": "Shilka AA"},
    ],
    "blue_supply": [
        {"type": "M 818", "name": "Supply Truck"},
        {"type": "M 818", "name": "Supply Truck"},
        {"type": "M 818", "name": "Fuel Truck"},
        {"type": "M 818", "name": "Ammo Truck"},
        {"type": "Hummer", "name": "Command HMMWV"},
    ],
    "blue_escort": [
        {"type": "LAV-25", "name": "LAV-25 Escort"},
        {"type": "Hummer", "name": "HMMWV Scout"},
        {"type": "M1126 Stryker ICV", "name": "Stryker Escort"},
    ],
}

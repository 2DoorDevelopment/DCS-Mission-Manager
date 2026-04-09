"""
Callsign System
Assigns realistic, non-repeating callsigns from NATO pools.
Each flight gets a unique callsign within a mission.
"""

import random

# Real USAF/NATO callsign pools by role
CALLSIGN_POOLS = {
    "fighter": [
        "Viper", "Cobra", "Eagle", "Falcon", "Hawk",
        "Razor", "Jester", "Maverick", "Gunfighter", "Dagger",
        "Talon", "Saber", "Hunter", "Raptor", "Striker",
    ],
    "sead": [
        "Weasel", "Magnum", "Spartan", "Hammer", "Javelin",
        "Titan", "Raider", "Lancer", "Viking", "Phantom",
    ],
    "cas": [
        "Hawg", "Sandy", "Nail", "Misty", "Ugly",
        "Hog", "Tusk", "Boar", "Warthog", "Razorback",
    ],
    "bomber": [
        "Bone", "Buff", "Reaper", "Spectre", "Shadow",
    ],
    "tanker": [
        "Texaco", "Shell", "Arco",
    ],
    "awacs": [
        "Overlord", "Magic", "Darkstar", "Chalice", "Focus",
    ],
    "sweep": [
        "Rampage", "Storm", "Fury", "Blaze", "Lightning",
        "Thunder", "Tempest", "Cyclone", "Tornado", "Havoc",
    ],
    "escort": [
        "Guardian", "Shield", "Sentinel", "Watchdog", "Cover",
        "Defender", "Paladin", "Bastion", "Aegis", "Ward",
    ],
    "red_fighter": [
        "Bandit", "Flanker", "Fulcrum", "Foxhound", "Fencer",
    ],
    "red_cas": [
        "Frogfoot", "Hind", "Havoc",
    ],
}

# Map mission tasks to callsign pools
TASK_TO_POOL = {
    "SEAD": "sead",
    "CAS": "cas",
    "CAP": "fighter",
    "strike": "bomber",
    "anti-ship": "fighter",
    "escort": "escort",
    "sweep": "sweep",
    "convoy_attack": "cas",
    "convoy_defense": "fighter",
    "Refueling": "tanker",
    "AWACS": "awacs",
    "intercept": "red_fighter",
}


class CallsignAssigner:
    """Assigns unique callsigns within a mission — no repeats."""

    def __init__(self):
        self._used: set[str] = set()
        self._flight_num: dict[str, int] = {}  # callsign -> next flight number

    def assign(self, task: str, coalition: str = "blue") -> dict:
        """
        Assign a callsign for a flight.

        Returns:
            {"callsign": "Viper", "flight": 1, "full": "Viper 1-1"}
        """
        if coalition == "red":
            pool_key = "red_fighter" if task not in ("CAS",) else "red_cas"
        else:
            pool_key = TASK_TO_POOL.get(task, "fighter")

        pool = CALLSIGN_POOLS.get(pool_key, CALLSIGN_POOLS["fighter"])

        # Pick unused callsign
        available = [cs for cs in pool if cs not in self._used]
        if not available:
            # All used — allow reuse with different flight numbers
            available = pool

        callsign = random.choice(available)
        self._used.add(callsign)

        # Assign flight number (1, 2, 3...)
        if callsign not in self._flight_num:
            self._flight_num[callsign] = 1
        flight = self._flight_num[callsign]
        self._flight_num[callsign] = flight + 1

        return {
            "callsign": callsign,
            "flight": flight,
            "full": f"{callsign} {flight}-1",
        }

    def assign_player(self, task: str) -> dict:
        """Assign the player's callsign — always gets flight 1."""
        pool_key = TASK_TO_POOL.get(task, "fighter")
        pool = CALLSIGN_POOLS.get(pool_key, CALLSIGN_POOLS["fighter"])

        # Player gets first pick
        callsign = random.choice(pool)
        self._used.add(callsign)
        self._flight_num[callsign] = 2  # Next flight of this callsign is 2

        return {
            "callsign": callsign,
            "flight": 1,
            "full": f"{callsign} 1-1",
        }

    def assign_support(self, role: str, preferred_name: str = "") -> dict:
        """Assign callsign for support assets (tanker, AWACS)."""
        if preferred_name and preferred_name not in self._used:
            self._used.add(preferred_name)
            return {"callsign": preferred_name, "flight": 1, "full": preferred_name}

        pool_key = "tanker" if role == "tanker" else "awacs"
        pool = CALLSIGN_POOLS.get(pool_key, [preferred_name or "Support"])
        available = [cs for cs in pool if cs not in self._used]
        callsign = available[0] if available else pool[0]
        self._used.add(callsign)
        return {"callsign": callsign, "flight": 1, "full": callsign}


# Frequency allocation pools
_BLUE_FREQ_START = 253.0
_RED_FREQ_START = 124.0
_INTER_FLIGHT_START = 270.0


class FrequencyAssigner:
    """Assigns unique radio frequencies."""

    def __init__(self):
        self._next_blue = _BLUE_FREQ_START
        self._next_red = _RED_FREQ_START
        self._next_inter = _INTER_FLIGHT_START
        self._assigned: dict[str, float] = {}

    def assign_flight(self, callsign: str, coalition: str = "blue") -> float:
        """Assign intra-flight frequency."""
        if coalition == "blue":
            freq = self._next_blue
            self._next_blue += 0.5
        else:
            freq = self._next_red
            self._next_red += 0.5
        self._assigned[callsign] = freq
        return freq

    def assign_package(self) -> float:
        """Assign package-wide frequency for inter-flight comms."""
        freq = self._next_inter
        self._next_inter += 1.0
        return freq

    def get_all(self) -> dict[str, float]:
        """Get all assigned frequencies."""
        return dict(self._assigned)

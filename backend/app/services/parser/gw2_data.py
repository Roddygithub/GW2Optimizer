"""GW2 game data constants and mappings."""

from typing import Dict, List

# Specialization IDs to names
SPECIALIZATIONS: Dict[int, str] = {
    # Guardian
    27: "Dragonhunter",
    62: "Firebrand",
    65: "Willbender",
    # Revenant
    52: "Herald",
    63: "Renegade",
    69: "Vindicator",
    # Warrior
    18: "Berserker",
    61: "Spellbreaker",
    68: "Bladesworn",
    # Engineer
    43: "Scrapper",
    57: "Holosmith",
    70: "Mechanist",
    # Ranger
    5: "Druid",
    55: "Soulbeast",
    72: "Untamed",
    # Thief
    7: "Daredevil",
    58: "Deadeye",
    71: "Specter",
    # Elementalist
    48: "Tempest",
    56: "Weaver",
    67: "Catalyst",
    # Mesmer
    40: "Chronomancer",
    59: "Mirage",
    66: "Virtuoso",
    # Necromancer
    34: "Reaper",
    60: "Scourge",
    64: "Harbinger",
}

# Stat combinations
STAT_COMBOS: Dict[str, Dict[str, int]] = {
    "Berserker": {"Power": 3, "Precision": 2, "Ferocity": 2},
    "Assassin": {"Precision": 3, "Power": 2, "Ferocity": 2},
    "Marauder": {"Power": 3, "Precision": 2, "Vitality": 1, "Ferocity": 1},
    "Valkyrie": {"Power": 3, "Vitality": 2, "Ferocity": 2},
    "Soldier": {"Power": 3, "Toughness": 2, "Vitality": 2},
    "Cavalier": {"Toughness": 3, "Power": 2, "Ferocity": 2},
    "Knight": {"Toughness": 3, "Power": 2, "Precision": 2},
    "Nomad": {"Toughness": 3, "Vitality": 2, "Healing": 2},
    "Settler": {"Toughness": 3, "Healing": 2, "Condition": 2},
    "Cleric": {"Healing": 3, "Power": 2, "Toughness": 2},
    "Magi": {"Healing": 3, "Precision": 2, "Vitality": 2},
    "Apothecary": {"Healing": 3, "Toughness": 2, "Condition": 2},
    "Minstrel": {"Healing": 3, "Toughness": 2, "Concentration": 1, "Vitality": 1},
    "Harrier": {"Power": 3, "Healing": 2, "Concentration": 2},
    "Zealot": {"Power": 3, "Precision": 2, "Healing": 2},
    "Rampager": {"Precision": 3, "Power": 2, "Condition": 2},
    "Sinister": {"Condition": 3, "Power": 2, "Precision": 2},
    "Viper": {"Power": 3, "Condition": 2, "Precision": 1, "Expertise": 1},
    "Grieving": {"Power": 3, "Condition": 2, "Precision": 1, "Ferocity": 1},
    "Carrion": {"Condition": 3, "Power": 2, "Vitality": 2},
    "Rabid": {"Condition": 3, "Precision": 2, "Toughness": 2},
    "Dire": {"Condition": 3, "Toughness": 2, "Vitality": 2},
    "Trailblazer": {"Toughness": 3, "Condition": 2, "Vitality": 1, "Expertise": 1},
    "Seraph": {"Precision": 3, "Healing": 2, "Condition": 2},
    "Commander": {"Power": 3, "Precision": 2, "Toughness": 1, "Concentration": 1},
    "Vigilant": {"Power": 3, "Toughness": 2, "Concentration": 1, "Expertise": 1},
    "Crusader": {"Power": 3, "Toughness": 2, "Healing": 1, "Ferocity": 1},
    "Wanderer": {"Power": 3, "Vitality": 2, "Toughness": 1, "Concentration": 1},
    "Diviner": {"Power": 3, "Concentration": 2, "Precision": 1, "Ferocity": 1},
    "Marshal": {"Power": 3, "Healing": 2, "Precision": 1, "Condition": 1},
    "Plaguedoctor": {"Vitality": 3, "Healing": 2, "Condition": 1, "Concentration": 1},
    "Celestial": {"Power": 1, "Precision": 1, "Toughness": 1, "Vitality": 1, "Ferocity": 1, "Healing": 1, "Condition": 1, "Concentration": 1, "Expertise": 1},
}

# Equipment slots
EQUIPMENT_SLOTS: List[str] = [
    "Helm", "Shoulders", "Coat", "Gloves", "Leggings", "Boots",
    "Amulet", "Ring1", "Ring2", "Accessory1", "Accessory2", "Backpack",
    "WeaponA1", "WeaponA2", "WeaponB1", "WeaponB2"
]

# Rune sets
RUNE_SETS: Dict[str, str] = {
    "scholar": "Scholar",
    "eagle": "Eagle",
    "strength": "Strength",
    "pack": "Pack",
    "dragonhunter": "Dragonhunter",
    "firebrand": "Firebrand",
    "durability": "Durability",
    "dolyak": "Dolyak",
    "water": "Water",
    "monk": "Monk",
    "sanctuary": "Sanctuary",
    "nightmare": "Nightmare",
    "tormenting": "Tormenting",
    "balthazar": "Balthazar",
    "thorns": "Thorns",
}

# Sigil types
SIGIL_TYPES: Dict[str, str] = {
    "force": "Force",
    "impact": "Impact",
    "accuracy": "Accuracy",
    "bloodlust": "Bloodlust",
    "air": "Air",
    "fire": "Fire",
    "earth": "Earth",
    "water": "Water",
    "energy": "Energy",
    "concentration": "Concentration",
    "transference": "Transference",
    "malice": "Malice",
    "agony": "Agony",
    "doom": "Doom",
    "torment": "Torment",
}

# Weapon types
WEAPON_TYPES: List[str] = [
    "Greatsword", "Hammer", "Longbow", "Rifle", "Staff",
    "Sword", "Axe", "Dagger", "Mace", "Pistol", "Scepter",
    "Focus", "Shield", "Torch", "Warhorn",
    "Shortbow", "Harpoon", "Speargun", "Trident"
]

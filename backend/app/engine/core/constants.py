"""Guild Wars 2 game constants for combat calculations."""

from typing import Dict, Tuple

# ==================== Armor Values ====================
ARMOR_LIGHT = 1967
ARMOR_MEDIUM = 2262
ARMOR_HEAVY = 2597

# ==================== Weapon Strength ====================
# Average weapon strength at level 80 exotic/ascended
WEAPON_STRENGTH_AVG = 1000

# Weapon strength ranges by weapon type (Min, Max)
WEAPON_STRENGTH_RANGES: Dict[str, Tuple[int, int]] = {
    "Staff": (947, 1053),
    "Greatsword": (1045, 1155),
    "Hammer": (1045, 1155),
    "Rifle": (1045, 1155),
    "Longbow": (1045, 1155),
    "Shortbow": (947, 1053),
    "Sword": (905, 1005),
    "Axe": (905, 1005),
    "Mace": (905, 1005),
    "Scepter": (905, 1005),
    "Dagger": (857, 953),
    "Pistol": (857, 953),
    "Focus": (835, 929),
    "Shield": (835, 929),
    "Torch": (835, 929),
    "Warhorn": (835, 929),
}

# ==================== Attribute Conversions ====================
# These are the divisors for converting stats to percentages
PRECISION_TO_CRIT = 2100  # 21 precision = 1% crit at level 80
FEROCITY_TO_CRIT_DMG = 1500  # 15 ferocity = 1% crit damage
EXPERTISE_TO_CONDI_DURATION = 1500  # 15 expertise = 1% condi duration
CONCENTRATION_TO_BOON_DURATION = 1500  # 15 concentration = 1% boon duration
TOUGHNESS_TO_ARMOR = 1  # 1 toughness = 1 armor
VITALITY_TO_HEALTH = 10  # 1 vitality = 10 health

# ==================== Base Values ====================
BASE_CRIT_CHANCE = 0.05  # 5% base critical chance
BASE_CRIT_DAMAGE = 1.50  # 150% base critical damage multiplier
BASE_HEALTH = 1645  # Base health at level 80 (varies by profession)
BASE_HEALING_POWER = 0

# Level 80 base stats (before gear)
BASE_STATS = {
    "power": 1000,
    "precision": 1000,
    "toughness": 1000,
    "vitality": 1000,
    "ferocity": 0,
    "condition_damage": 0,
    "expertise": 0,
    "concentration": 0,
    "healing_power": 0,
    "agony_resistance": 0,
}

# ==================== Condition Base Damages ====================
# Base damage per second per stack at level 80
CONDITION_BASE_DAMAGE: Dict[str, float] = {
    "Burning": 131.0,  # per stack per second
    "Bleeding": 22.0,  # per stack per second
    "Poison": 33.5,  # per stack per second
    "Torment": 31.8,  # per stack per second (stationary)
    "Torment_Moving": 50.25,  # per stack per second (moving)
    "Confusion": 10.0,  # per stack on skill activation
    "Confusion_Passive": 11.0,  # per stack per second (passive)
}

# Condition stacking types
CONDITION_STACKING = {
    "Intensity": [  # Stack in quantity (up to max stacks)
        "Might",
        "Vulnerability",
        "Bleeding",
        "Torment",
        "Confusion",
        "Stability",
    ],
    "Duration": [  # Stack in duration
        "Burning",
        "Poison",
        "Cripple",
        "Chilled",
        "Weakness",
        "Blind",
        "Immobilize",
        "Slow",
        "Taunt",
        "Fear",
    ],
}

# Maximum stacks for intensity-stacking effects
MAX_STACKS = {
    "Might": 25,
    "Vulnerability": 25,
    "Bleeding": 1500,  # Effectively unlimited in practice
    "Torment": 1500,
    "Confusion": 1500,
    "Stability": 25,
}

# ==================== Boon Effects ====================
# Stat bonuses per stack/application
BOON_STAT_BONUSES: Dict[str, Dict[str, float]] = {
    "Might": {"power": 30, "condition_damage": 30},  # per stack
    "Fury": {"crit_chance_bonus": 0.20},  # flat +20% crit chance
    "Quickness": {"attack_speed_mult": 0.50},  # 50% faster attacks
    "Alacrity": {"cooldown_reduction": 0.25},  # 25% faster cooldowns
    "Protection": {"damage_reduction": 0.33},  # 33% less incoming damage
    "Vigor": {"endurance_regen_mult": 0.50},  # 50% faster endurance regen
    "Swiftness": {"movement_speed_mult": 0.33},  # 33% faster movement
    "Regeneration": {"health_per_sec": 130, "healing_power_coef": 0.125},
    "Resistance": {"condition_immune": True},
    "Resolution": {"condition_damage_reduction": 0.50},  # 50% less condi damage taken
    "Aegis": {"block_next_attack": True},
    "Stability": {},  # Per stack, prevents 1 CC
}

# ==================== Condition Effects (Debuffs) ====================
CONDITION_EFFECTS: Dict[str, Dict[str, float]] = {
    "Vulnerability": {"damage_taken_mult": 0.01},  # +1% per stack
    "Weakness": {"endurance_regen_mult": -0.50, "fumble_chance": 0.50},
    "Cripple": {"movement_speed_mult": -0.50},
    "Chilled": {"movement_speed_mult": -0.66, "skill_recharge_mult": -0.66},
    "Immobilize": {"cannot_move": True},
    "Blind": {"next_attack_misses": True},
    "Slow": {"skill_activation_time_mult": 1.0},  # 100% slower activation
    "Taunt": {"forced_attack": True},
    "Fear": {"forced_flee": True},
}

# ==================== Game Version ====================
# For tracking game updates
GAME_VERSION = "Unknown"
LAST_BALANCE_PATCH = "Unknown"

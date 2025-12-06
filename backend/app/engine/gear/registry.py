"""Registry of common runes, sigils, and consumables with their modifiers."""

from typing import Dict, List, Callable
from ..modifiers.base import Modifier, ModifierType
from ..modifiers.conditions import TargetHealthCondition, TargetHasConditionCheck

# ==================== RUNES ====================


def create_scholar_runes() -> List[Modifier]:
    """Rune of the Scholar: +25 Power, +35 Ferocity, ..., +10% damage above 90% health."""
    return [
        Modifier("Scholar (1)", "Rune: Scholar", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Scholar (2)", "Rune: Scholar", ModifierType.FLAT_STAT, 35, target_stat="ferocity"),
        Modifier("Scholar (3)", "Rune: Scholar", ModifierType.FLAT_STAT, 50, target_stat="power"),
        Modifier("Scholar (4)", "Rune: Scholar", ModifierType.FLAT_STAT, 65, target_stat="ferocity"),
        Modifier("Scholar (5)", "Rune: Scholar", ModifierType.FLAT_STAT, 100, target_stat="power"),
        Modifier(
            "Scholar (6)",
            "Rune: Scholar",
            ModifierType.DAMAGE_MULTIPLIER,
            0.10,
            condition=TargetHealthCondition(">=", 0.9),
        ),
    ]


def create_eagle_runes() -> List[Modifier]:
    """Rune of the Eagle: Power + Precision + Ferocity bonuses."""
    return [
        Modifier("Eagle (1)", "Rune: Eagle", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Eagle (2)", "Rune: Eagle", ModifierType.FLAT_STAT, 35, target_stat="precision"),
        Modifier("Eagle (3)", "Rune: Eagle", ModifierType.FLAT_STAT, 50, target_stat="power"),
        Modifier("Eagle (4)", "Rune: Eagle", ModifierType.FLAT_STAT, 65, target_stat="precision"),
        Modifier("Eagle (5)", "Rune: Eagle", ModifierType.FLAT_STAT, 100, target_stat="ferocity"),
        Modifier("Eagle (6)", "Rune: Eagle", ModifierType.FLAT_STAT, 175, target_stat="ferocity"),
    ]


def create_nightmare_runes() -> List[Modifier]:
    """Rune of the Nightmare: Condi damage + duration."""
    return [
        Modifier("Nightmare (1)", "Rune: Nightmare", ModifierType.FLAT_STAT, 25, target_stat="condition_damage"),
        Modifier("Nightmare (2)", "Rune: Nightmare", ModifierType.CONDITION_DURATION, 0.05),
        Modifier("Nightmare (3)", "Rune: Nightmare", ModifierType.FLAT_STAT, 50, target_stat="condition_damage"),
        Modifier("Nightmare (4)", "Rune: Nightmare", ModifierType.CONDITION_DURATION, 0.10),
        Modifier("Nightmare (5)", "Rune: Nightmare", ModifierType.FLAT_STAT, 100, target_stat="condition_damage"),
        Modifier("Nightmare (6)", "Rune: Nightmare", ModifierType.CONDITION_DURATION, 0.15),
    ]


def create_durability_runes() -> List[Modifier]:
    """Rune of Durability: Toughness + Vitality for survivability (WvW Tank/Support)."""
    return [
        Modifier("Durability (1)", "Rune: Durability", ModifierType.FLAT_STAT, 25, target_stat="toughness"),
        Modifier("Durability (2)", "Rune: Durability", ModifierType.FLAT_STAT, 35, target_stat="vitality"),
        Modifier("Durability (3)", "Rune: Durability", ModifierType.FLAT_STAT, 50, target_stat="toughness"),
        Modifier("Durability (4)", "Rune: Durability", ModifierType.FLAT_STAT, 65, target_stat="vitality"),
        Modifier("Durability (5)", "Rune: Durability", ModifierType.FLAT_STAT, 100, target_stat="toughness"),
        Modifier("Durability (6)", "Rune: Durability", ModifierType.FLAT_STAT, 125, target_stat="vitality"),
    ]


def create_hoelbrak_runes() -> List[Modifier]:
    """Rune of Hoelbrak: Power + Ferocity for balanced DPS (WvW alternative to Scholar)."""
    return [
        Modifier("Hoelbrak (1)", "Rune: Hoelbrak", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Hoelbrak (2)", "Rune: Hoelbrak", ModifierType.FLAT_STAT, 35, target_stat="ferocity"),
        Modifier("Hoelbrak (3)", "Rune: Hoelbrak", ModifierType.FLAT_STAT, 50, target_stat="power"),
        Modifier("Hoelbrak (4)", "Rune: Hoelbrak", ModifierType.FLAT_STAT, 65, target_stat="ferocity"),
        Modifier("Hoelbrak (5)", "Rune: Hoelbrak", ModifierType.FLAT_STAT, 100, target_stat="power"),
        Modifier("Hoelbrak (6)", "Rune: Hoelbrak", ModifierType.FLAT_STAT, 100, target_stat="ferocity"),
    ]


def create_ogre_runes() -> List[Modifier]:
    """Rune of the Ogre: All-around defensive stats (WvW bruiser)."""
    return [
        Modifier("Ogre (1)", "Rune: Ogre", ModifierType.FLAT_STAT, 25, target_stat="toughness"),
        Modifier("Ogre (2)", "Rune: Ogre", ModifierType.FLAT_STAT, 35, target_stat="vitality"),
        Modifier("Ogre (3)", "Rune: Ogre", ModifierType.FLAT_STAT, 50, target_stat="healing_power"),
        Modifier("Ogre (4)", "Rune: Ogre", ModifierType.FLAT_STAT, 65, target_stat="toughness"),
        Modifier("Ogre (5)", "Rune: Ogre", ModifierType.FLAT_STAT, 100, target_stat="vitality"),
        Modifier("Ogre (6)", "Rune: Ogre", ModifierType.BOON_DURATION, 0.20),  # +20% boon duration
    ]


def create_monk_runes() -> List[Modifier]:
    """Rune of the Monk: Healing Power for WvW healers/support."""
    return [
        Modifier("Monk (1)", "Rune: Monk", ModifierType.FLAT_STAT, 25, target_stat="healing_power"),
        Modifier("Monk (2)", "Rune: Monk", ModifierType.BOON_DURATION, 0.05),
        Modifier("Monk (3)", "Rune: Monk", ModifierType.FLAT_STAT, 50, target_stat="healing_power"),
        Modifier("Monk (4)", "Rune: Monk", ModifierType.BOON_DURATION, 0.10),
        Modifier("Monk (5)", "Rune: Monk", ModifierType.FLAT_STAT, 100, target_stat="healing_power"),
        Modifier("Monk (6)", "Rune: Monk", ModifierType.OUTGOING_HEALING, 0.10),  # +10% outgoing healing
    ]


def create_water_runes() -> List[Modifier]:
    """Rune of the Water: Healing Power + regen on crit (WvW support/hybrid)."""
    return [
        Modifier("Water (1)", "Rune: Water", ModifierType.FLAT_STAT, 25, target_stat="healing_power"),
        Modifier("Water (2)", "Rune: Water", ModifierType.FLAT_STAT, 35, target_stat="vitality"),
        Modifier("Water (3)", "Rune: Water", ModifierType.FLAT_STAT, 50, target_stat="healing_power"),
        Modifier("Water (4)", "Rune: Water", ModifierType.FLAT_STAT, 65, target_stat="vitality"),
        Modifier("Water (5)", "Rune: Water", ModifierType.FLAT_STAT, 100, target_stat="healing_power"),
        Modifier("Water (6)", "Rune: Water", ModifierType.OUTGOING_HEALING, 0.15),  # +15% heal to others
    ]


def create_strength_runes() -> List[Modifier]:
    """Rune of Strength: Might duration and power (WvW might stacking)."""
    return [
        Modifier("Strength (1)", "Rune: Strength", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Strength (2)", "Rune: Strength", ModifierType.BOON_DURATION, 0.05),
        Modifier("Strength (3)", "Rune: Strength", ModifierType.FLAT_STAT, 50, target_stat="power"),
        Modifier("Strength (4)", "Rune: Strength", ModifierType.BOON_DURATION, 0.10),
        Modifier("Strength (5)", "Rune: Strength", ModifierType.FLAT_STAT, 100, target_stat="power"),
        Modifier("Strength (6)", "Rune: Strength", ModifierType.BOON_DURATION, 0.20),  # Total +35% boon duration
    ]


def create_pack_runes() -> List[Modifier]:
    """Rune of the Pack: Movement speed for WvW mobility (roaming/scout)."""
    return [
        Modifier("Pack (1)", "Rune: Pack", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Pack (2)", "Rune: Pack", ModifierType.FLAT_STAT, 35, target_stat="precision"),
        Modifier("Pack (3)", "Rune: Pack", ModifierType.FLAT_STAT, 50, target_stat="power"),
        Modifier("Pack (4)", "Rune: Pack", ModifierType.FLAT_STAT, 65, target_stat="precision"),
        Modifier("Pack (5)", "Rune: Pack", ModifierType.FLAT_STAT, 100, target_stat="power"),
        # (6) Bonus: +25% movement speed + Swiftness on dodge (not modeled here, movement not in combat engine)
        Modifier("Pack (6)", "Rune: Pack", ModifierType.FLAT_STAT, 100, target_stat="power"),  # Simplified
    ]


def create_fireworks_runes() -> List[Modifier]:
    """Rune of Fireworks: Condition damage + duration for WvW condi builds."""
    return [
        Modifier("Fireworks (1)", "Rune: Fireworks", ModifierType.FLAT_STAT, 25, target_stat="condition_damage"),
        Modifier("Fireworks (2)", "Rune: Fireworks", ModifierType.FLAT_STAT, 35, target_stat="precision"),
        Modifier("Fireworks (3)", "Rune: Fireworks", ModifierType.FLAT_STAT, 50, target_stat="condition_damage"),
        Modifier("Fireworks (4)", "Rune: Fireworks", ModifierType.FLAT_STAT, 65, target_stat="precision"),
        Modifier("Fireworks (5)", "Rune: Fireworks", ModifierType.FLAT_STAT, 100, target_stat="condition_damage"),
        Modifier("Fireworks (6)", "Rune: Fireworks", ModifierType.CONDITION_DURATION, 0.10),
    ]


def create_traveler_runes() -> List[Modifier]:
    """Rune of the Traveler: Balanced stats for WvW roaming."""
    return [
        Modifier("Traveler (1)", "Rune: Traveler", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Traveler (2)", "Rune: Traveler", ModifierType.FLAT_STAT, 35, target_stat="precision"),
        Modifier("Traveler (3)", "Rune: Traveler", ModifierType.FLAT_STAT, 50, target_stat="vitality"),
        Modifier("Traveler (4)", "Rune: Traveler", ModifierType.FLAT_STAT, 65, target_stat="condition_damage"),
        Modifier("Traveler (5)", "Rune: Traveler", ModifierType.BOON_DURATION, 0.10),
        Modifier("Traveler (6)", "Rune: Traveler", ModifierType.FLAT_STAT, 100, target_stat="power"),
    ]


def create_flock_runes() -> List[Modifier]:
    """Rune of the Flock: Power build alternative for WvW."""
    return [
        Modifier("Flock (1)", "Rune: Flock", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Flock (2)", "Rune: Flock", ModifierType.FLAT_STAT, 35, target_stat="precision"),
        Modifier("Flock (3)", "Rune: Flock", ModifierType.FLAT_STAT, 50, target_stat="power"),
        Modifier("Flock (4)", "Rune: Flock", ModifierType.FLAT_STAT, 65, target_stat="precision"),
        Modifier("Flock (5)", "Rune: Flock", ModifierType.FLAT_STAT, 100, target_stat="power"),
        Modifier("Flock (6)", "Rune: Flock", ModifierType.FLAT_STAT, 125, target_stat="ferocity"),
    ]


def create_dolyak_runes() -> List[Modifier]:
    """Rune of the Dolyak: Ultimate tank rune for WvW frontline."""
    return [
        Modifier("Dolyak (1)", "Rune: Dolyak", ModifierType.FLAT_STAT, 25, target_stat="toughness"),
        Modifier("Dolyak (2)", "Rune: Dolyak", ModifierType.FLAT_STAT, 35, target_stat="vitality"),
        Modifier("Dolyak (3)", "Rune: Dolyak", ModifierType.FLAT_STAT, 50, target_stat="toughness"),
        Modifier("Dolyak (4)", "Rune: Dolyak", ModifierType.FLAT_STAT, 65, target_stat="vitality"),
        Modifier("Dolyak (5)", "Rune: Dolyak", ModifierType.FLAT_STAT, 100, target_stat="toughness"),
        Modifier("Dolyak (6)", "Rune: Dolyak", ModifierType.FLAT_STAT, 125, target_stat="vitality"),
    ]


def create_trooper_runes() -> List[Modifier]:
    """Rune of the Trooper: Condi damage + vitality for WvW condi bruiser."""
    return [
        Modifier("Trooper (1)", "Rune: Trooper", ModifierType.FLAT_STAT, 25, target_stat="condition_damage"),
        Modifier("Trooper (2)", "Rune: Trooper", ModifierType.FLAT_STAT, 35, target_stat="vitality"),
        Modifier("Trooper (3)", "Rune: Trooper", ModifierType.FLAT_STAT, 50, target_stat="condition_damage"),
        Modifier("Trooper (4)", "Rune: Trooper", ModifierType.FLAT_STAT, 65, target_stat="vitality"),
        Modifier("Trooper (5)", "Rune: Trooper", ModifierType.FLAT_STAT, 100, target_stat="condition_damage"),
        Modifier("Trooper (6)", "Rune: Trooper", ModifierType.CONDITION_DURATION, 0.10),
    ]


def create_balthazar_runes() -> List[Modifier]:
    """Rune of Balthazar: Burning specialist for WvW condi builds."""
    return [
        Modifier("Balthazar (1)", "Rune: Balthazar", ModifierType.FLAT_STAT, 25, target_stat="condition_damage"),
        Modifier("Balthazar (2)", "Rune: Balthazar", ModifierType.FLAT_STAT, 35, target_stat="precision"),
        Modifier("Balthazar (3)", "Rune: Balthazar", ModifierType.FLAT_STAT, 50, target_stat="condition_damage"),
        Modifier("Balthazar (4)", "Rune: Balthazar", ModifierType.FLAT_STAT, 65, target_stat="expertise"),
        Modifier("Balthazar (5)", "Rune: Balthazar", ModifierType.FLAT_STAT, 100, target_stat="condition_damage"),
        Modifier("Balthazar (6)", "Rune: Balthazar", ModifierType.CONDITION_DURATION, 0.20),  # Burning duration
    ]


def create_druid_runes() -> List[Modifier]:
    """Rune of the Druid: WvW healer specialist."""
    return [
        Modifier("Druid (1)", "Rune: Druid", ModifierType.FLAT_STAT, 25, target_stat="healing_power"),
        Modifier("Druid (2)", "Rune: Druid", ModifierType.BOON_DURATION, 0.05),
        Modifier("Druid (3)", "Rune: Druid", ModifierType.FLAT_STAT, 50, target_stat="healing_power"),
        Modifier("Druid (4)", "Rune: Druid", ModifierType.BOON_DURATION, 0.10),
        Modifier("Druid (5)", "Rune: Druid", ModifierType.FLAT_STAT, 100, target_stat="healing_power"),
        Modifier("Druid (6)", "Rune: Druid", ModifierType.OUTGOING_HEALING, 0.12),
    ]


def create_aristocracy_runes() -> List[Modifier]:
    """Rune of the Aristocracy: Boon duration for WvW support."""
    return [
        Modifier("Aristocracy (1)", "Rune: Aristocracy", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Aristocracy (2)", "Rune: Aristocracy", ModifierType.BOON_DURATION, 0.05),
        Modifier("Aristocracy (3)", "Rune: Aristocracy", ModifierType.FLAT_STAT, 50, target_stat="power"),
        Modifier("Aristocracy (4)", "Rune: Aristocracy", ModifierType.BOON_DURATION, 0.10),
        Modifier("Aristocracy (5)", "Rune: Aristocracy", ModifierType.FLAT_STAT, 100, target_stat="concentration"),
        Modifier("Aristocracy (6)", "Rune: Aristocracy", ModifierType.BOON_DURATION, 0.15),  # Total +30%
    ]


def create_chronomancer_runes() -> List[Modifier]:
    """Rune of the Chronomancer: WvW boon support specialist."""
    return [
        Modifier("Chronomancer (1)", "Rune: Chronomancer", ModifierType.FLAT_STAT, 25, target_stat="concentration"),
        Modifier("Chronomancer (2)", "Rune: Chronomancer", ModifierType.BOON_DURATION, 0.05),
        Modifier("Chronomancer (3)", "Rune: Chronomancer", ModifierType.FLAT_STAT, 50, target_stat="concentration"),
        Modifier("Chronomancer (4)", "Rune: Chronomancer", ModifierType.BOON_DURATION, 0.10),
        Modifier("Chronomancer (5)", "Rune: Chronomancer", ModifierType.FLAT_STAT, 100, target_stat="concentration"),
        Modifier("Chronomancer (6)", "Rune: Chronomancer", ModifierType.BOON_DURATION, 0.20),  # Total +35%
    ]


def create_herald_runes() -> List[Modifier]:
    """Rune of the Herald: WvW boon share builds."""
    return [
        Modifier("Herald (1)", "Rune: Herald", ModifierType.FLAT_STAT, 25, target_stat="concentration"),
        Modifier("Herald (2)", "Rune: Herald", ModifierType.BOON_DURATION, 0.05),
        Modifier("Herald (3)", "Rune: Herald", ModifierType.FLAT_STAT, 50, target_stat="ferocity"),
        Modifier("Herald (4)", "Rune: Herald", ModifierType.BOON_DURATION, 0.10),
        Modifier("Herald (5)", "Rune: Herald", ModifierType.FLAT_STAT, 100, target_stat="concentration"),
        Modifier("Herald (6)", "Rune: Herald", ModifierType.BOON_DURATION, 0.15),
    ]


def create_vampirism_runes() -> List[Modifier]:
    """Rune of Vampirism: Sustain for WvW roaming."""
    return [
        Modifier("Vampirism (1)", "Rune: Vampirism", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Vampirism (2)", "Rune: Vampirism", ModifierType.FLAT_STAT, 35, target_stat="precision"),
        Modifier("Vampirism (3)", "Rune: Vampirism", ModifierType.FLAT_STAT, 50, target_stat="power"),
        Modifier("Vampirism (4)", "Rune: Vampirism", ModifierType.FLAT_STAT, 65, target_stat="vitality"),
        Modifier("Vampirism (5)", "Rune: Vampirism", ModifierType.FLAT_STAT, 100, target_stat="power"),
        # (6) Siphon health on crit - not modeled, simplified
        Modifier("Vampirism (6)", "Rune: Vampirism", ModifierType.FLAT_STAT, 100, target_stat="vitality"),
    ]


def create_antitoxin_runes() -> List[Modifier]:
    """Rune of Antitoxin: Anti-condi for WvW."""
    return [
        Modifier("Antitoxin (1)", "Rune: Antitoxin", ModifierType.FLAT_STAT, 25, target_stat="vitality"),
        Modifier("Antitoxin (2)", "Rune: Antitoxin", ModifierType.FLAT_STAT, 35, target_stat="healing_power"),
        Modifier("Antitoxin (3)", "Rune: Antitoxin", ModifierType.FLAT_STAT, 50, target_stat="vitality"),
        Modifier("Antitoxin (4)", "Rune: Antitoxin", ModifierType.FLAT_STAT, 65, target_stat="healing_power"),
        Modifier("Antitoxin (5)", "Rune: Antitoxin", ModifierType.FLAT_STAT, 100, target_stat="vitality"),
        # (6) Condi clear on heal - not modeled
        Modifier("Antitoxin (6)", "Rune: Antitoxin", ModifierType.FLAT_STAT, 100, target_stat="healing_power"),
    ]


def create_afflicted_runes() -> List[Modifier]:
    """Rune of the Afflicted: Pure condi damage for WvW."""
    return [
        Modifier("Afflicted (1)", "Rune: Afflicted", ModifierType.FLAT_STAT, 25, target_stat="condition_damage"),
        Modifier("Afflicted (2)", "Rune: Afflicted", ModifierType.FLAT_STAT, 35, target_stat="expertise"),
        Modifier("Afflicted (3)", "Rune: Afflicted", ModifierType.FLAT_STAT, 50, target_stat="condition_damage"),
        Modifier("Afflicted (4)", "Rune: Afflicted", ModifierType.FLAT_STAT, 65, target_stat="expertise"),
        Modifier("Afflicted (5)", "Rune: Afflicted", ModifierType.FLAT_STAT, 100, target_stat="condition_damage"),
        Modifier("Afflicted (6)", "Rune: Afflicted", ModifierType.DAMAGE_MULTIPLIER, 0.10),  # +10% condi dmg
    ]


def create_scavenging_runes() -> List[Modifier]:
    """Rune of Scavenging: Power + sustain for WvW."""
    return [
        Modifier("Scavenging (1)", "Rune: Scavenging", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Scavenging (2)", "Rune: Scavenging", ModifierType.FLAT_STAT, 35, target_stat="vitality"),
        Modifier("Scavenging (3)", "Rune: Scavenging", ModifierType.FLAT_STAT, 50, target_stat="power"),
        Modifier("Scavenging (4)", "Rune: Scavenging", ModifierType.FLAT_STAT, 65, target_stat="ferocity"),
        Modifier("Scavenging (5)", "Rune: Scavenging", ModifierType.FLAT_STAT, 100, target_stat="power"),
        Modifier("Scavenging (6)", "Rune: Scavenging", ModifierType.FLAT_STAT, 100, target_stat="vitality"),
    ]


def create_ranger_runes() -> List[Modifier]:
    """Rune of the Ranger: Power + pet damage for WvW."""
    return [
        Modifier("Ranger (1)", "Rune: Ranger", ModifierType.FLAT_STAT, 25, target_stat="power"),
        Modifier("Ranger (2)", "Rune: Ranger", ModifierType.FLAT_STAT, 35, target_stat="precision"),
        Modifier("Ranger (3)", "Rune: Ranger", ModifierType.FLAT_STAT, 50, target_stat="power"),
        Modifier("Ranger (4)", "Rune: Ranger", ModifierType.FLAT_STAT, 65, target_stat="ferocity"),
        Modifier("Ranger (5)", "Rune: Ranger", ModifierType.FLAT_STAT, 100, target_stat="power"),
        Modifier("Ranger (6)", "Rune: Ranger", ModifierType.FLAT_STAT, 125, target_stat="precision"),
    ]


RUNE_REGISTRY: Dict[str, Callable[[], List[Modifier]]] = {
    # Power DPS Runes
    "Scholar": create_scholar_runes,
    "Eagle": create_eagle_runes,
    "Hoelbrak": create_hoelbrak_runes,
    "Flock": create_flock_runes,
    "Scavenging": create_scavenging_runes,
    "Ranger": create_ranger_runes,
    "Pack": create_pack_runes,
    "Vampirism": create_vampirism_runes,
    # Condi DPS Runes
    "Nightmare": create_nightmare_runes,
    "Fireworks": create_fireworks_runes,
    "Trooper": create_trooper_runes,
    "Balthazar": create_balthazar_runes,
    "Afflicted": create_afflicted_runes,
    # Support/Heal Runes
    "Monk": create_monk_runes,
    "Water": create_water_runes,
    "Druid": create_druid_runes,
    "Strength": create_strength_runes,
    "Aristocracy": create_aristocracy_runes,
    "Chronomancer": create_chronomancer_runes,
    "Herald": create_herald_runes,
    # Tank/Bruiser Runes
    "Durability": create_durability_runes,
    "Ogre": create_ogre_runes,
    "Dolyak": create_dolyak_runes,
    "Antitoxin": create_antitoxin_runes,
    # Roaming/Hybrid Runes
    "Traveler": create_traveler_runes,
}

# ==================== SIGILS ====================


def create_force_sigil() -> Modifier:
    """Sigil of Force: +5% damage."""
    return Modifier("Force", "Sigil: Force", ModifierType.DAMAGE_MULTIPLIER, 0.05)


def create_impact_sigil() -> Modifier:
    """Sigil of Impact: 250 damage on crit (5s ICD)."""
    return Modifier(
        "Impact",
        "Sigil: Impact",
        ModifierType.PROC_DAMAGE,
        250,
        internal_cooldown=5.0,
        proc_chance=1.0,
    )


def create_bloodlust_sigil(stacks: int = 25) -> Modifier:
    """Sigil of Bloodlust: +10 Power per stack (max 25)."""
    return Modifier(
        f"Bloodlust (x{stacks})",
        "Sigil: Bloodlust",
        ModifierType.FLAT_STAT,
        stacks * 10,
        target_stat="power",
        stacks=stacks,
        max_stacks=25,
    )


def create_air_sigil() -> Modifier:
    """Sigil of Air: Lightning strike on crit (50% chance, 3s ICD)."""
    return Modifier(
        "Air",
        "Sigil: Air",
        ModifierType.PROC_DAMAGE,
        264,  # Base damage
        internal_cooldown=3.0,
        proc_chance=0.50,
    )


def create_bursting_sigil() -> Modifier:
    """Sigil of Bursting: +5% damage to foes with conditions."""
    return Modifier(
        "Bursting",
        "Sigil: Bursting",
        ModifierType.DAMAGE_MULTIPLIER,
        0.05,
        condition=TargetHasConditionCheck("Burning", 1),  # Simplified: any condition
    )


def create_energy_sigil() -> Modifier:
    """Sigil of Energy: Gain endurance on kill (WvW sustain for mobility)."""
    # Note: Endurance gain not modeled in combat engine, simplified as utility sigil
    return Modifier(
        "Energy",
        "Sigil: Energy",
        ModifierType.FLAT_STAT,
        50,  # Placeholder: 50% endurance on kill (not in damage calc)
        target_stat="power",  # Minimal power bonus for tracking
    )


def create_strength_sigil() -> Modifier:
    """Sigil of Strength: Gain Might on kill (WvW might stacking)."""
    # Note: Might gain on kill not modeled as proc, simplified
    return Modifier(
        "Strength",
        "Sigil: Strength",
        ModifierType.FLAT_STAT,
        25,  # Tracks the sigil, might stacking happens dynamically
        target_stat="power",
    )


def create_battle_sigil() -> Modifier:
    """Sigil of Battle: Gain adrenaline on weapon swap (WvW warrior)."""
    # Note: Adrenaline not in combat engine, placeholder
    return Modifier(
        "Battle",
        "Sigil: Battle",
        ModifierType.FLAT_STAT,
        25,
        target_stat="power",
    )


def create_absorption_sigil() -> Modifier:
    """Sigil of Absorption: Shield on hit (WvW defense)."""
    # Note: Shield not modeled in damage calc
    return Modifier(
        "Absorption",
        "Sigil: Absorption",
        ModifierType.FLAT_STAT,
        50,
        target_stat="toughness",  # Defensive sigil
    )


def create_hydromancy_sigil() -> Modifier:
    """Sigil of Hydromancy: Extra damage vs burning foes (WvW condition synergy)."""
    return Modifier(
        "Hydromancy",
        "Sigil: Hydromancy",
        ModifierType.PROC_DAMAGE,
        494,  # Base damage vs burning target
        internal_cooldown=2.0,
        proc_chance=1.0,
        condition=TargetHasConditionCheck("Burning", 1),
    )


def create_accuracy_sigil() -> Modifier:
    """Sigil of Accuracy: +7% crit chance (WvW)."""
    return Modifier("Accuracy", "Sigil: Accuracy", ModifierType.FLAT_STAT, 140, target_stat="precision")  # ~7% crit


def create_agility_sigil() -> Modifier:
    """Sigil of Agility: Mobility on kill (WvW roaming)."""
    return Modifier("Agility", "Sigil: Agility", ModifierType.FLAT_STAT, 25, target_stat="power")  # Placeholder


def create_concentration_sigil() -> Modifier:
    """Sigil of Concentration: Boon duration (WvW support)."""
    return Modifier("Concentration", "Sigil: Concentration", ModifierType.BOON_DURATION, 0.10)


def create_doom_sigil() -> Modifier:
    """Sigil of Doom: Poison on crit (WvW condi)."""
    return Modifier(
        "Doom",
        "Sigil: Doom",
        ModifierType.PROC_DAMAGE,
        200,  # Poison damage
        internal_cooldown=5.0,
        proc_chance=0.50,
    )


def create_earth_sigil() -> Modifier:
    """Sigil of Earth: Bleeding on crit (WvW condi)."""
    return Modifier(
        "Earth",
        "Sigil: Earth",
        ModifierType.PROC_DAMAGE,
        180,  # Bleed damage
        internal_cooldown=2.0,
        proc_chance=1.0,
    )


def create_fire_sigil() -> Modifier:
    """Sigil of Fire: Burning on crit (WvW condi)."""
    return Modifier(
        "Fire",
        "Sigil: Fire",
        ModifierType.PROC_DAMAGE,
        220,  # Burn damage
        internal_cooldown=5.0,
        proc_chance=1.0,
    )


def create_geomancy_sigil() -> Modifier:
    """Sigil of Geomancy: Damage on attune (WvW ele)."""
    return Modifier(
        "Geomancy",
        "Sigil: Geomancy",
        ModifierType.PROC_DAMAGE,
        520,  # Burst on attune
        internal_cooldown=9.0,
        proc_chance=1.0,
    )


def create_ice_sigil() -> Modifier:
    """Sigil of Ice: Chill on crit (WvW CC)."""
    return Modifier(
        "Ice",
        "Sigil: Ice",
        ModifierType.PROC_DAMAGE,
        150,  # Chill damage
        internal_cooldown=10.0,
        proc_chance=1.0,
    )


def create_leeching_sigil() -> Modifier:
    """Sigil of Leeching: Lifesteal on hit (WvW sustain)."""
    return Modifier("Leeching", "Sigil: Leeching", ModifierType.FLAT_STAT, 50, target_stat="healing_power")


def create_paralyzation_sigil() -> Modifier:
    """Sigil of Paralyzation: Stun on swap (WvW CC)."""
    return Modifier("Paralyzation", "Sigil: Paralyzation", ModifierType.FLAT_STAT, 25, target_stat="power")


def create_perception_sigil() -> Modifier:
    """Sigil of Perception: +6% crit chance (WvW)."""
    return Modifier("Perception", "Sigil: Perception", ModifierType.FLAT_STAT, 120, target_stat="precision")


def create_corruption_sigil() -> Modifier:
    """Sigil of Corruption: Convert boons to conditions (WvW strip)."""
    return Modifier("Corruption", "Sigil: Corruption", ModifierType.FLAT_STAT, 50, target_stat="condition_damage")


def create_cleansing_sigil() -> Modifier:
    """Sigil of Cleansing: Remove condition on swap (WvW anti-condi)."""
    return Modifier("Cleansing", "Sigil: Cleansing", ModifierType.FLAT_STAT, 25, target_stat="healing_power")


def create_transference_sigil() -> Modifier:
    """Sigil of Transference: Lifesteal on crit (WvW sustain)."""
    return Modifier("Transference", "Sigil: Transference", ModifierType.FLAT_STAT, 50, target_stat="healing_power")


def create_smoldering_sigil() -> Modifier:
    """Sigil of Smoldering: Burning duration (WvW condi)."""
    return Modifier("Smoldering", "Sigil: Smoldering", ModifierType.CONDITION_DURATION, 0.10)  # Burning +10%


def create_torment_sigil() -> Modifier:
    """Sigil of Torment: Torment on hit (WvW condi)."""
    return Modifier(
        "Torment",
        "Sigil: Torment",
        ModifierType.PROC_DAMAGE,
        190,  # Torment damage
        internal_cooldown=5.0,
        proc_chance=1.0,
    )


def create_malice_sigil() -> Modifier:
    """Sigil of Malice: +10% condition damage (WvW condi)."""
    return Modifier("Malice", "Sigil: Malice", ModifierType.FLAT_STAT, 175, target_stat="condition_damage")


def create_agony_sigil() -> Modifier:
    """Sigil of Agony: Confusion on crit (WvW condi)."""
    return Modifier(
        "Agony",
        "Sigil: Agony",
        ModifierType.PROC_DAMAGE,
        160,  # Confusion damage
        internal_cooldown=5.0,
        proc_chance=1.0,
    )


def create_draining_sigil() -> Modifier:
    """Sigil of Draining: Life drain (WvW sustain)."""
    return Modifier("Draining", "Sigil: Draining", ModifierType.FLAT_STAT, 40, target_stat="healing_power")


def create_generosity_sigil() -> Modifier:
    """Sigil of Generosity: Share boons on kill (WvW support)."""
    return Modifier("Generosity", "Sigil: Generosity", ModifierType.BOON_DURATION, 0.05)


def create_demons_sigil() -> Modifier:
    """Sigil of Demons: Damage vs guardians (WvW specific)."""
    return Modifier("Demons", "Sigil: Demons", ModifierType.DAMAGE_MULTIPLIER, 0.05)  # Simplified


def create_frailty_sigil() -> Modifier:
    """Sigil of Frailty: Weakness on crit (WvW debuff)."""
    return Modifier("Frailty", "Sigil: Frailty", ModifierType.FLAT_STAT, 25, target_stat="condition_damage")


def create_momentum_sigil() -> Modifier:
    """Sigil of Momentum: Speed on kill (WvW mobility)."""
    return Modifier("Momentum", "Sigil: Momentum", ModifierType.FLAT_STAT, 25, target_stat="power")


def create_luck_sigil() -> Modifier:
    """Sigil of Luck: +3% crit chance (WvW)."""
    return Modifier("Luck", "Sigil: Luck", ModifierType.FLAT_STAT, 60, target_stat="precision")


SIGIL_REGISTRY: Dict[str, Callable[..., Modifier]] = {
    # Power DPS Sigils
    "Force": create_force_sigil,
    "Impact": create_impact_sigil,
    "Bloodlust": create_bloodlust_sigil,
    "Air": create_air_sigil,
    "Accuracy": create_accuracy_sigil,
    "Perception": create_perception_sigil,
    "Luck": create_luck_sigil,
    # Condi DPS Sigils
    "Bursting": create_bursting_sigil,
    "Hydromancy": create_hydromancy_sigil,
    "Doom": create_doom_sigil,
    "Earth": create_earth_sigil,
    "Fire": create_fire_sigil,
    "Ice": create_ice_sigil,
    "Geomancy": create_geomancy_sigil,
    "Smoldering": create_smoldering_sigil,
    "Torment": create_torment_sigil,
    "Malice": create_malice_sigil,
    "Agony": create_agony_sigil,
    # Support Sigils
    "Energy": create_energy_sigil,
    "Strength": create_strength_sigil,
    "Concentration": create_concentration_sigil,
    "Generosity": create_generosity_sigil,
    # Tank/Sustain Sigils
    "Absorption": create_absorption_sigil,
    "Leeching": create_leeching_sigil,
    "Transference": create_transference_sigil,
    "Draining": create_draining_sigil,
    # Utility Sigils
    "Battle": create_battle_sigil,
    "Paralyzation": create_paralyzation_sigil,
    "Corruption": create_corruption_sigil,
    "Cleansing": create_cleansing_sigil,
    "Frailty": create_frailty_sigil,
    "Agility": create_agility_sigil,
    "Momentum": create_momentum_sigil,
    "Demons": create_demons_sigil,
}

# ==================== RELICS ====================


def create_fireworks_relic() -> List[Modifier]:
    """Relic of Fireworks: offensive relic for power DPS.

    Approximation: small global strike damage bonus.
    """

    return [
        Modifier(
            "Relic of Fireworks",
            "Relic: Fireworks",
            ModifierType.DAMAGE_MULTIPLIER,
            0.05,
        )
    ]


def create_flock_relic() -> List[Modifier]:
    """Relic of the Flock: sustain/heal oriented relic.

    Approximation: outgoing healing bonus.
    """

    return [
        Modifier(
            "Relic of the Flock",
            "Relic: Flock",
            ModifierType.OUTGOING_HEALING,
            0.06,
        )
    ]


def create_monk_relic() -> List[Modifier]:
    """Relic of the Monk: boon-based healing support.

    Approximation: outgoing healing + slight boon duration.
    """

    return [
        Modifier(
            "Relic of the Monk",
            "Relic: Monk",
            ModifierType.OUTGOING_HEALING,
            0.08,
        ),
        Modifier(
            "Relic of the Monk",
            "Relic: Monk",
            ModifierType.BOON_DURATION,
            0.05,
        ),
    ]


def create_herald_relic() -> List[Modifier]:
    """Relic of the Herald: pure boon support relic.

    Approximation: boon duration bonus.
    """

    return [
        Modifier(
            "Relic of the Herald",
            "Relic: Herald",
            ModifierType.BOON_DURATION,
            0.12,
        )
    ]


def create_centaur_relic() -> List[Modifier]:
    """Relic of the Centaur: defensive/stability-oriented relic.

    Approximation: extra toughness for survivability.
    """

    return [
        Modifier(
            "Relic of the Centaur",
            "Relic: Centaur",
            ModifierType.FLAT_STAT,
            120,
            target_stat="toughness",
        )
    ]


def create_scourge_relic() -> List[Modifier]:
    """Relic of the Scourge: condi support relic.

    Approximation: condition duration bonus.
    """

    return [
        Modifier(
            "Relic of the Scourge",
            "Relic: Scourge",
            ModifierType.CONDITION_DURATION,
            0.10,
        )
    ]


RELIC_REGISTRY: Dict[str, Callable[[], List[Modifier]]] = {
    # Offensive relics
    "Fireworks": create_fireworks_relic,
    # Healing / support relics
    "Flock": create_flock_relic,
    "Monk": create_monk_relic,
    # Boon support
    "Herald": create_herald_relic,
    # Defensive / tanky relics
    "Centaur": create_centaur_relic,
    # Condi / barrier support
    "Scourge": create_scourge_relic,
}

# ==================== CONSUMABLES (Food & Utility) ====================


def create_sweet_and_spicy_beans() -> List[Modifier]:
    """Food: +100 Power, +70 Ferocity."""
    return [
        Modifier("Food: S&S Beans", "Food", ModifierType.FLAT_STAT, 100, target_stat="power"),
        Modifier("Food: S&S Beans", "Food", ModifierType.FLAT_STAT, 70, target_stat="ferocity"),
    ]


def create_toxic_focusing_crystal() -> List[Modifier]:
    """Utility: +10% damage, +15% experience."""
    return [
        Modifier("Utility: Toxic Crystal", "Utility", ModifierType.DAMAGE_MULTIPLIER, 0.10),
    ]


FOOD_REGISTRY: Dict[str, Callable[[], List[Modifier]]] = {
    "Sweet_and_Spicy_Beans": create_sweet_and_spicy_beans,
    # Add more food as needed
}

UTILITY_REGISTRY: Dict[str, Callable[[], List[Modifier]]] = {
    "Toxic_Focusing_Crystal": create_toxic_focusing_crystal,
    # Add more utility as needed
}

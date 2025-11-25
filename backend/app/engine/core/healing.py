"""Healing calculations for Guild Wars 2."""

from typing import Optional


def calculate_healing(
    base_heal: float,
    healing_power: int,
    coefficient: float,
    outgoing_healing_mult: float = 1.0,
    incoming_healing_mult: float = 1.0,
) -> float:
    """
    Calculate healing amount.

    Formula:
    Healing = (BaseHeal + HealingPower × Coefficient) × OutgoingMult × IncomingMult

    Args:
        base_heal: Base healing from skill tooltip
        healing_power: Player's Healing Power stat
        coefficient: Healing power coefficient (usually 0.1 to 0.7)
        outgoing_healing_mult: Outgoing healing modifier from traits (e.g., 1.15 = +15%)
        incoming_healing_mult: Incoming healing modifier on target (e.g., 1.25 = +25%)

    Returns:
        Total healing amount
    """
    raw_heal = base_heal + (healing_power * coefficient)
    return raw_heal * outgoing_healing_mult * incoming_healing_mult


def calculate_regeneration_healing(
    healing_power: int,
    duration: float,
    stacks: int = 1,
    outgoing_healing_mult: float = 1.0,
) -> float:
    """
    Calculate healing from Regeneration boon.

    Regeneration: 130 + (0.125 × Healing Power) per second per stack

    Args:
        healing_power: Player's Healing Power stat
        duration: Duration of Regeneration in seconds
        stacks: Number of stacks (usually 1, but can stack in duration)
        outgoing_healing_mult: Outgoing healing modifier

    Returns:
        Total healing from Regeneration
    """
    heal_per_sec = (130 + (0.125 * healing_power)) * stacks
    return heal_per_sec * duration * outgoing_healing_mult


def calculate_heal_over_time(
    base_heal_per_tick: float,
    healing_power: int,
    coefficient: float,
    duration: float,
    tick_rate: float = 1.0,
    outgoing_healing_mult: float = 1.0,
) -> dict:
    """
    Calculate healing over time for DoT healing skills.

    Args:
        base_heal_per_tick: Base healing per tick
        healing_power: Player's Healing Power stat
        coefficient: Healing power coefficient per tick
        duration: Total duration in seconds
        tick_rate: Time between ticks in seconds (default 1s)
        outgoing_healing_mult: Outgoing healing modifier

    Returns:
        Dictionary with:
            - heal_per_tick: Healing per individual tick
            - num_ticks: Total number of ticks
            - total_healing: Total healing over duration
            - hps: Healing per second
    """
    heal_per_tick = calculate_healing(
        base_heal=base_heal_per_tick,
        healing_power=healing_power,
        coefficient=coefficient,
        outgoing_healing_mult=outgoing_healing_mult,
    )

    num_ticks = int(duration / tick_rate)
    total_healing = heal_per_tick * num_ticks

    hps = total_healing / duration if duration > 0 else 0

    return {
        "heal_per_tick": heal_per_tick,
        "num_ticks": num_ticks,
        "total_healing": total_healing,
        "hps": hps,
        "duration": duration,
    }

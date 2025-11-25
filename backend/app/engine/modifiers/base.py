"""Base classes for the modifier system."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


class ModifierType(Enum):
    """Types of modifiers that can be applied."""

    FLAT_STAT = "flat_stat"  # +120 Power
    PERCENT_STAT = "percent_stat"  # +10% Power
    DAMAGE_MULTIPLIER = "damage_mult"  # +10% all damage
    STRIKE_DAMAGE_MULTIPLIER = "strike_mult"  # +10% strike damage only
    CONDITION_DAMAGE_MULTIPLIER = "condi_mult"  # +10% condition damage only
    CONDITION_DURATION = "condi_duration"  # +20% Burning duration
    BOON_DURATION = "boon_duration"  # +20% boon duration
    CONVERSION = "conversion"  # 7% of Vitality as Power
    CRIT_CHANCE = "crit_chance"  # +5% crit chance
    CRIT_DAMAGE = "crit_damage"  # +10% crit damage
    OUTGOING_HEALING = "outgoing_healing"  # +15% healing given
    INCOMING_HEALING = "incoming_healing"  # +15% healing received
    ON_CRIT_EFFECT = "on_crit"  # Trigger effect on critical hit
    ON_HIT_EFFECT = "on_hit"  # Trigger effect on hit
    PROC_DAMAGE = "proc_damage"  # Fixed damage proc (e.g., Sigil of Air)


class ModifierCondition(ABC):
    """Base class for conditions that determine if a modifier is active."""

    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate whether the condition is met.

        Args:
            context: Combat context dictionary with player/target state

        Returns:
            True if condition is met, False otherwise
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class Modifier:
    """
    Generic modifier that can come from Traits, Runes, Sigils, Food, etc.

    A modifier represents any effect that changes stats or damage output.
    """

    def __init__(
        self,
        name: str,
        source: str,
        modifier_type: ModifierType,
        value: float,
        condition: Optional[ModifierCondition] = None,
        target_stat: Optional[str] = None,
        stacks: int = 1,
        max_stacks: int = 1,
        duration: Optional[float] = None,
        cooldown: Optional[float] = None,
        internal_cooldown: Optional[float] = None,
        proc_chance: float = 1.0,
        is_multiplicative: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a modifier.

        Args:
            name: Display name of the modifier
            source: Source of the modifier (e.g., "Trait: Fiery Wrath", "Sigil: Force")
            modifier_type: Type of modification
            value: Numerical value of the modifier
            condition: Optional condition for the modifier to be active
            target_stat: Which stat this modifies (for stat modifiers)
            stacks: Current number of stacks
            max_stacks: Maximum number of stacks
            duration: Duration of the effect in seconds
            cooldown: Cooldown between applications
            internal_cooldown: ICD (for procs like sigils)
            proc_chance: Chance to trigger (0.0 to 1.0)
            is_multiplicative: Whether this stacks multiplicatively with similar modifiers
            metadata: Additional metadata for special cases
        """
        self.name = name
        self.source = source
        self.modifier_type = modifier_type
        self.value = value
        self.condition = condition
        self.target_stat = target_stat
        self.stacks = min(stacks, max_stacks)
        self.max_stacks = max_stacks
        self.duration = duration
        self.cooldown = cooldown
        self.internal_cooldown = internal_cooldown
        self.proc_chance = proc_chance
        self.is_multiplicative = is_multiplicative
        self.metadata = metadata or {}

        # Runtime state
        self._last_proc_time: float = 0.0
        self._is_on_cooldown: bool = False

    def is_active(self, context: Dict[str, Any]) -> bool:
        """
        Check if this modifier is currently active.

        Args:
            context: Combat context dictionary

        Returns:
            True if the modifier should apply
        """
        # If there's no condition, it's always active
        if self.condition is None:
            return True

        # Otherwise, evaluate the condition
        return self.condition.evaluate(context)

    def can_proc(self, current_time: float) -> bool:
        """
        Check if this modifier can proc (respecting ICD).

        Args:
            current_time: Current simulation time in seconds

        Returns:
            True if the effect can proc
        """
        if self.internal_cooldown is None:
            return True

        time_since_last_proc = current_time - self._last_proc_time
        return time_since_last_proc >= self.internal_cooldown

    def record_proc(self, current_time: float) -> None:
        """Record that this modifier has proc'd."""
        self._last_proc_time = current_time

    def get_effective_value(self, context: Dict[str, Any]) -> float:
        """
        Get the effective value of this modifier.

        Accounts for stacks and whether it's active.

        Args:
            context: Combat context

        Returns:
            Effective modifier value (0 if inactive)
        """
        if not self.is_active(context):
            return 0.0

        # For stacking modifiers, multiply by stacks
        if self.max_stacks > 1:
            return self.value * self.stacks

        return self.value

    def add_stacks(self, amount: int = 1) -> int:
        """
        Add stacks to this modifier.

        Args:
            amount: Number of stacks to add

        Returns:
            New total stack count
        """
        self.stacks = min(self.stacks + amount, self.max_stacks)
        return self.stacks

    def remove_stacks(self, amount: int = 1) -> int:
        """
        Remove stacks from this modifier.

        Args:
            amount: Number of stacks to remove

        Returns:
            New total stack count
        """
        self.stacks = max(0, self.stacks - amount)
        return self.stacks

    def __repr__(self) -> str:
        active_str = f", condition={self.condition}" if self.condition else ""
        stacks_str = f" ({self.stacks}/{self.max_stacks} stacks)" if self.max_stacks > 1 else ""
        return f"Modifier({self.name}{stacks_str}: {self.modifier_type.value}={self.value}{active_str})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert modifier to dictionary for serialization."""
        return {
            "name": self.name,
            "source": self.source,
            "type": self.modifier_type.value,
            "value": self.value,
            "stacks": self.stacks,
            "max_stacks": self.max_stacks,
            "target_stat": self.target_stat,
            "is_multiplicative": self.is_multiplicative,
            "has_condition": self.condition is not None,
            "proc_chance": self.proc_chance if self.proc_chance < 1.0 else None,
            "internal_cooldown": self.internal_cooldown,
        }

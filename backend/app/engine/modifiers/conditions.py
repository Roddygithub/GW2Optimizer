"""Condition evaluators for modifiers."""

from typing import Any, Dict, List
from .base import ModifierCondition


class TargetHealthCondition(ModifierCondition):
    """Condition based on target health percentage."""

    def __init__(self, operator: str, threshold: float):
        """
        Initialize health condition.

        Args:
            operator: Comparison operator (">", "<", ">=", "<=", "==")
            threshold: Health percentage threshold (0.0 to 1.0)
        """
        self.operator = operator
        self.threshold = threshold

    def evaluate(self, context: Dict[str, Any]) -> bool:
        target_health_percent = context.get("target_health_percent", 1.0)

        if self.operator == ">":
            return target_health_percent > self.threshold
        elif self.operator == "<":
            return target_health_percent < self.threshold
        elif self.operator == ">=":
            return target_health_percent >= self.threshold
        elif self.operator == "<=":
            return target_health_percent <= self.threshold
        elif self.operator == "==":
            return abs(target_health_percent - self.threshold) < 0.01

        return False

    def __repr__(self) -> str:
        return f"TargetHealth({self.operator} {self.threshold * 100:.0f}%)"


class PlayerHealthCondition(ModifierCondition):
    """Condition based on player health percentage."""

    def __init__(self, operator: str, threshold: float):
        self.operator = operator
        self.threshold = threshold

    def evaluate(self, context: Dict[str, Any]) -> bool:
        player_health_percent = context.get("player_health_percent", 1.0)

        if self.operator == ">":
            return player_health_percent > self.threshold
        elif self.operator == "<":
            return player_health_percent < self.threshold
        elif self.operator == ">=":
            return player_health_percent >= self.threshold
        elif self.operator == "<=":
            return player_health_percent <= self.threshold

        return False

    def __repr__(self) -> str:
        return f"PlayerHealth({self.operator} {self.threshold * 100:.0f}%)"


class TargetHasConditionCheck(ModifierCondition):
    """Condition based on target having a specific condition."""

    def __init__(self, condition_name: str, min_stacks: int = 1):
        """
        Initialize condition check.

        Args:
            condition_name: Name of the condition to check
            min_stacks: Minimum number of stacks required
        """
        self.condition_name = condition_name
        self.min_stacks = min_stacks

    def evaluate(self, context: Dict[str, Any]) -> bool:
        target_conditions = context.get("target_conditions", {})

        if isinstance(target_conditions, list):
            # Simple list format
            return self.condition_name in target_conditions
        elif isinstance(target_conditions, dict):
            # Dict format with stacks
            stacks = target_conditions.get(self.condition_name, 0)
            return stacks >= self.min_stacks

        return False

    def __repr__(self) -> str:
        stack_str = f" x{self.min_stacks}" if self.min_stacks > 1 else ""
        return f"TargetHas({self.condition_name}{stack_str})"


class BoonActiveCondition(ModifierCondition):
    """Condition based on player having a specific boon."""

    def __init__(self, boon_name: str, min_stacks: int = 1):
        """
        Initialize boon check.

        Args:
            boon_name: Name of the boon to check
            min_stacks: Minimum number of stacks required
        """
        self.boon_name = boon_name
        self.min_stacks = min_stacks

    def evaluate(self, context: Dict[str, Any]) -> bool:
        player_boons = context.get("player_boons", {})
        stacks = player_boons.get(self.boon_name, 0)
        return stacks >= self.min_stacks

    def __repr__(self) -> str:
        stack_str = f" x{self.min_stacks}" if self.min_stacks > 1 else ""
        return f"HasBoon({self.boon_name}{stack_str})"


class DistanceCondition(ModifierCondition):
    """Condition based on distance to target."""

    def __init__(self, operator: str, distance: float):
        """
        Initialize distance condition.

        Args:
            operator: Comparison operator (">", "<", ">=", "<=")
            distance: Distance in game units
        """
        self.operator = operator
        self.distance = distance

    def evaluate(self, context: Dict[str, Any]) -> bool:
        current_distance = context.get("distance_to_target", 0.0)

        if self.operator == ">":
            return current_distance > self.distance
        elif self.operator == "<":
            return current_distance < self.distance
        elif self.operator == ">=":
            return current_distance >= self.distance
        elif self.operator == "<=":
            return current_distance <= self.distance

        return False

    def __repr__(self) -> str:
        return f"Distance({self.operator} {self.distance})"


class CombinedCondition(ModifierCondition):
    """Combine multiple conditions with AND/OR logic."""

    def __init__(self, conditions: List[ModifierCondition], logic: str = "AND"):
        """
        Initialize combined condition.

        Args:
            conditions: List of conditions to combine
            logic: "AND" or "OR"
        """
        self.conditions = conditions
        self.logic = logic.upper()

    def evaluate(self, context: Dict[str, Any]) -> bool:
        if not self.conditions:
            return True

        if self.logic == "AND":
            return all(cond.evaluate(context) for cond in self.conditions)
        elif self.logic == "OR":
            return any(cond.evaluate(context) for cond in self.conditions)

        return False

    def __repr__(self) -> str:
        cond_strs = [str(c) for c in self.conditions]
        return f"({f' {self.logic} '.join(cond_strs)})"


class FlankingCondition(ModifierCondition):
    """Condition based on flanking or being behind target."""

    def __init__(self, require_behind: bool = False):
        """
        Initialize flanking condition.

        Args:
            require_behind: If True, requires behind; if False, flanking is enough
        """
        self.require_behind = require_behind

    def evaluate(self, context: Dict[str, Any]) -> bool:
        if self.require_behind:
            return context.get("is_behind_target", False)
        else:
            return context.get("is_flanking", False) or context.get("is_behind_target", False)

    def __repr__(self) -> str:
        return "Behind" if self.require_behind else "Flanking"


class RecentActionCondition(ModifierCondition):
    """Condition based on recent actions (e.g., recently dodged, used heal)."""

    def __init__(self, action: str):
        """
        Initialize recent action condition.

        Args:
            action: Action key (e.g., "dodged", "used_heal", "swapped_weapon")
        """
        self.action = action

    def evaluate(self, context: Dict[str, Any]) -> bool:
        return context.get(f"recently_{self.action}", False)

    def __repr__(self) -> str:
        return f"Recently({self.action})"


# Prebuilt common conditions
COMMON_CONDITIONS = {
    "target_burning": TargetHasConditionCheck("Burning"),
    "target_bleeding": TargetHasConditionCheck("Bleeding"),
    "target_vulnerability": TargetHasConditionCheck("Vulnerability", min_stacks=1),
    "target_health_above_90": TargetHealthCondition(">=", 0.9),
    "target_health_below_50": TargetHealthCondition("<", 0.5),
    "target_health_below_25": TargetHealthCondition("<", 0.25),
    "player_has_fury": BoonActiveCondition("Fury"),
    "player_has_25_might": BoonActiveCondition("Might", 25),
    "player_health_full": PlayerHealthCondition("==", 1.0),
    "player_health_above_90": PlayerHealthCondition(">", 0.9),
    "distance_above_600": DistanceCondition(">", 600),
    "distance_melee": DistanceCondition("<=", 130),
    "flanking": FlankingCondition(require_behind=False),
    "behind_target": FlankingCondition(require_behind=True),
}

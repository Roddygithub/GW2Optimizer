"""Combat context representing the current state of combat."""

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class CombatContext:
    """Represents the current state of combat for calculations."""

    # Game mode (WvW only for this project)
    game_mode: str = "WvW"  # WvW, PvE, PvP - but we focus on WvW only
    
    # Player state
    player_health_percent: float = 1.0
    player_endurance_percent: float = 1.0
    player_boons: Dict[str, int] = field(default_factory=dict)  # {boon_name: stacks}
    player_conditions: Dict[str, int] = field(default_factory=dict)  # {condition_name: stacks}

    # Target state
    target_health_percent: float = 1.0
    target_armor: int = 2597  # Default heavy armor
    target_conditions: Dict[str, int] = field(default_factory=dict)  # {condition_name: stacks}
    target_boons: Dict[str, int] = field(default_factory=dict)  # {boon_name: stacks}

    # Positioning
    distance_to_target: float = 0.0  # in game units (130 = melee range)
    is_flanking: bool = False
    is_behind_target: bool = False

    # Combat flags
    in_combat: bool = True
    recently_dodged: bool = False
    recently_used_heal: bool = False
    recently_swapped_weapon: bool = False

    # Combo fields active
    active_combo_fields: List[str] = field(default_factory=list)

    # Simulation time
    current_time: float = 0.0

    def add_boon(self, boon_name: str, stacks: int = 1, max_stacks: int = 25) -> None:
        """
        Add boon stacks to player.

        Args:
            boon_name: Name of the boon
            stacks: Number of stacks to add
            max_stacks: Maximum stacks for this boon
        """
        current = self.player_boons.get(boon_name, 0)
        self.player_boons[boon_name] = min(current + stacks, max_stacks)

    def remove_boon(self, boon_name: str, stacks: int = 1) -> None:
        """Remove boon stacks from player."""
        if boon_name in self.player_boons:
            self.player_boons[boon_name] = max(0, self.player_boons[boon_name] - stacks)
            if self.player_boons[boon_name] == 0:
                del self.player_boons[boon_name]

    def add_condition_to_target(self, condition_name: str, stacks: int = 1, max_stacks: int = 25) -> None:
        """Add condition stacks to target."""
        current = self.target_conditions.get(condition_name, 0)
        self.target_conditions[condition_name] = min(current + stacks, max_stacks)

    def has_boon(self, boon_name: str, min_stacks: int = 1) -> bool:
        """Check if player has a boon with minimum stacks."""
        return self.player_boons.get(boon_name, 0) >= min_stacks

    def target_has_condition(self, condition_name: str, min_stacks: int = 1) -> bool:
        """Check if target has a condition with minimum stacks."""
        return self.target_conditions.get(condition_name, 0) >= min_stacks

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for condition evaluation."""
        return {
            "game_mode": self.game_mode,
            "player_health_percent": self.player_health_percent,
            "player_boons": self.player_boons,
            "player_conditions": self.player_conditions,
            "target_health_percent": self.target_health_percent,
            "target_armor": self.target_armor,
            "target_conditions": self.target_conditions,
            "target_boons": self.target_boons,
            "distance_to_target": self.distance_to_target,
            "is_flanking": self.is_flanking,
            "is_behind_target": self.is_behind_target,
            "in_combat": self.in_combat,
            "recently_dodged": self.recently_dodged,
            "recently_used_heal": self.recently_used_heal,
            "recently_swapped_weapon": self.recently_swapped_weapon,
            "active_combo_fields": self.active_combo_fields,
            "current_time": self.current_time,
        }

    @classmethod
    def create_default(cls, might_stacks: int = 25, fury: bool = True, game_mode: str = "WvW") -> "CombatContext":
        """
        Create a default combat context with common boons.

        Args:
            might_stacks: Number of Might stacks (default 25)
            fury: Whether Fury is active
            game_mode: Game mode for the combat (default "WvW")

        Returns:
            CombatContext with default boons for WvW
        """
        context = cls(game_mode=game_mode)
        if might_stacks > 0:
            context.add_boon("Might", might_stacks, 25)
        if fury:
            context.add_boon("Fury", 1, 1)
        return context

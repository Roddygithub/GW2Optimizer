"""
Parser for extracting modifiers from GW2 trait data.
WvW ONLY - filters for WvW-specific trait effects.
"""

from typing import Dict, List, Any, Optional
import re
from ..modifiers.base import Modifier, ModifierType


class TraitParser:
    """
    Parses GW2 trait data from API and extracts combat modifiers.
    
    Focus: WvW combat only. PvE/PvP specific traits are ignored.
    """
    
    # Pattern matchers for common trait effects
    DAMAGE_PATTERNS = [
        (r"(\d+)%\s+(?:increased\s+)?damage", ModifierType.DAMAGE_MULTIPLIER),
        (r"deal\s+(\d+)%\s+more\s+damage", ModifierType.DAMAGE_MULTIPLIER),
        (r"\+(\d+)%\s+damage", ModifierType.DAMAGE_MULTIPLIER),
    ]
    
    STAT_PATTERNS = [
        (r"\+(\d+)\s+power", "power"),
        (r"\+(\d+)\s+precision", "precision"),
        (r"\+(\d+)\s+ferocity", "ferocity"),
        (r"\+(\d+)\s+condition\s+damage", "condition_damage"),
        (r"\+(\d+)\s+expertise", "expertise"),
        (r"\+(\d+)\s+toughness", "toughness"),
        (r"\+(\d+)\s+vitality", "vitality"),
        (r"\+(\d+)\s+healing\s+power", "healing_power"),
    ]
    
    CONDITION_KEYWORDS = {
        "while above 90%": "health_above_90",
        "when foe is burning": "target_burning",
        "against burning foes": "target_burning",
        "when foe has condition": "target_has_condition",
        "in combat": "in_combat",
        "when wielding": "weapon_type",
    }
    
    def __init__(self, game_mode: str = "WvW"):
        """
        Initialize parser.
        
        Args:
            game_mode: Game mode to filter for (default "WvW")
        """
        self.game_mode = game_mode
    
    def parse_trait(self, trait_data: Dict[str, Any]) -> List[Modifier]:
        """
        Parse a single trait from GW2 API and extract modifiers.
        
        Args:
            trait_data: Raw trait data from GW2 API
        
        Returns:
            List of Modifier objects extracted from the trait
        """
        modifiers: List[Modifier] = []
        
        trait_name = trait_data.get("name", "Unknown Trait")
        description = trait_data.get("description", "")
        
        # Skip if PvE/PvP only (basic filter)
        if self._is_pve_only(description):
            return modifiers
        
        # Extract damage modifiers
        modifiers.extend(self._extract_damage_modifiers(trait_name, description))
        
        # Extract stat bonuses
        modifiers.extend(self._extract_stat_modifiers(trait_name, description))
        
        # Parse facts (structured data from API)
        facts = trait_data.get("facts", [])
        for fact in facts:
            modifiers.extend(self._parse_fact(trait_name, fact))
        
        return modifiers
    
    def parse_traits(self, traits_data: List[Dict[str, Any]]) -> List[Modifier]:
        """
        Parse multiple traits.
        
        Args:
            traits_data: List of trait data from GW2 API
        
        Returns:
            Combined list of all modifiers
        """
        all_modifiers: List[Modifier] = []
        for trait in traits_data:
            all_modifiers.extend(self.parse_trait(trait))
        return all_modifiers
    
    def _is_pve_only(self, description: str) -> bool:
        """Check if trait is PvE-only (basic heuristic)."""
        pve_keywords = ["strikes mission", "fractal", "dungeon", "raid boss"]
        desc_lower = description.lower()
        return any(keyword in desc_lower for keyword in pve_keywords)
    
    def _extract_damage_modifiers(self, trait_name: str, description: str) -> List[Modifier]:
        """Extract damage % modifiers from description."""
        modifiers: List[Modifier] = []
        desc_lower = description.lower()
        
        for pattern, mod_type in self.DAMAGE_PATTERNS:
            matches = re.finditer(pattern, desc_lower)
            for match in matches:
                value = float(match.group(1)) / 100.0  # Convert % to decimal
                
                # Check for conditional modifiers
                condition = self._extract_condition(desc_lower)
                
                mod = Modifier(
                    name=f"{trait_name} (Damage)",
                    source=f"Trait: {trait_name}",
                    modifier_type=mod_type,
                    value=value,
                    condition=condition,
                )
                modifiers.append(mod)
        
        return modifiers
    
    def _extract_stat_modifiers(self, trait_name: str, description: str) -> List[Modifier]:
        """Extract flat stat bonuses from description."""
        modifiers: List[Modifier] = []
        desc_lower = description.lower()
        
        for pattern, stat_name in self.STAT_PATTERNS:
            matches = re.finditer(pattern, desc_lower)
            for match in matches:
                value = int(match.group(1))
                
                mod = Modifier(
                    name=f"{trait_name} ({stat_name.title()})",
                    source=f"Trait: {trait_name}",
                    modifier_type=ModifierType.FLAT_STAT,
                    value=value,
                    target_stat=stat_name,
                )
                modifiers.append(mod)
        
        return modifiers
    
    def _parse_fact(self, trait_name: str, fact: Dict[str, Any]) -> List[Modifier]:
        """Parse structured fact data from API."""
        modifiers: List[Modifier] = []
        
        fact_type = fact.get("type")
        
        # AttributeAdjust facts (e.g., "+180 Power")
        if fact_type == "AttributeAdjust":
            target = fact.get("target", "").lower()
            value = fact.get("value", 0)
            
            # Map GW2 API attribute names to our stat names
            stat_mapping = {
                "power": "power",
                "precision": "precision",
                "ferocity": "ferocity",
                "conditiondamage": "condition_damage",
                "expertise": "expertise",
                "toughness": "toughness",
                "vitality": "vitality",
                "healingpower": "healing_power",
            }
            
            stat_name = stat_mapping.get(target.replace(" ", "").lower())
            if stat_name:
                mod = Modifier(
                    name=f"{trait_name} ({stat_name.title()})",
                    source=f"Trait: {trait_name}",
                    modifier_type=ModifierType.FLAT_STAT,
                    value=value,
                    target_stat=stat_name,
                )
                modifiers.append(mod)
        
        # Damage facts
        elif fact_type == "Damage":
            dmg_multiplier = fact.get("dmg_multiplier")
            if dmg_multiplier:
                mod = Modifier(
                    name=f"{trait_name} (Damage Bonus)",
                    source=f"Trait: {trait_name}",
                    modifier_type=ModifierType.DAMAGE_MULTIPLIER,
                    value=float(dmg_multiplier) / 100.0,
                )
                modifiers.append(mod)
        
        # Buff facts (boon duration, etc.)
        elif fact_type == "Buff":
            # Future: parse boon duration modifiers
            pass
        
        return modifiers
    
    def _extract_condition(self, description: str) -> Optional[Any]:
        """
        Extract condition from description text.
        
        Returns condition object if found, None otherwise.
        """
        # Basic implementation - can be extended with actual condition classes
        for keyword, condition_type in self.CONDITION_KEYWORDS.items():
            if keyword in description:
                # Return a simple dict for now - could be a Condition object
                return {"type": condition_type, "description": keyword}
        
        return None


# Convenience function
def parse_traits_for_build(traits_data: List[Dict[str, Any]], game_mode: str = "WvW") -> List[Modifier]:
    """
    Parse all traits for a build and return combined modifiers.
    
    Args:
        traits_data: List of trait data from GW2 API
        game_mode: Game mode filter (default "WvW")
    
    Returns:
        List of all extracted modifiers
    """
    parser = TraitParser(game_mode=game_mode)
    return parser.parse_traits(traits_data)

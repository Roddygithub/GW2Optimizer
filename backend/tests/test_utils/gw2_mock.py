"""Mock data and utilities for GW2 API testing."""

from typing import Dict, List, Any

# Sample profession data
MOCK_PROFESSIONS = {
    "Guardian": {
        "id": "Guardian",
        "name": "Guardian",
        "icon": "https://render.guildwars2.com/file/6106BDCAEE0D2DBA32AE3D5710AE29CC09F7C9DD/156642.png",
        "weapons": {
            "Axe": {"specialization": 6, "flags": ["Mainhand"], "skills": [9093, 9084]},
            "Mace": {"specialization": 27, "flags": ["Mainhand", "Offhand"], "skills": [9088, 9098]}
        },
        "skills": [
            {"id": 9093, "name": "Strike", "slot": "Weapon", "type": "Weapon"},
            {"id": 9084, "name": "Wrath of Justice", "slot": "Weapon", "type": "Weapon"},
            {"id": 9088, "name": "Mace Smash", "slot": "Weapon", "type": "Weapon"},
            {"id": 9098, "name": "Shield of Judgment", "slot": "Weapon", "type": "Weapon"}
        ]
    },
    "Warrior": {
        "id": "Warrior",
        "name": "Warrior",
        "icon": "https://render.guildwars2.com/file/61AA49E9E9FF1714D533D01C442655E89EA7141E/1012831.png",
        "weapons": {
            "Greatsword": {"specialization": 18, "flags": ["TwoHand"], "skills": [14354, 14402]},
            "Rifle": {"specialization": 18, "flags": ["TwoHand"], "skills": [14389, 14407]}
        },
        "skills": [
            {"id": 14354, "name": "Strike", "slot": "Weapon", "type": "Weapon"},
            {"id": 14402, "name": "Hundred Blades", "slot": "Weapon", "type": "Weapon"},
            {"id": 14389, "name": "Kneeling Shot", "slot": "Weapon", "type": "Weapon"},
            {"id": 14407, "name": "Brutal Shot", "slot": "Weapon", "type": "Weapon"}
        ]
    }
}

# Sample specialization data
MOCK_SPECIALIZATIONS = {
    6: {
        "id": 6,
        "name": "Zeal",
        "profession": "Guardian",
        "elite": False,
        "minor_traits": [642, 653, 654],
        "major_traits": [642, 653, 654, 655, 656, 657],
        "icon": "https://render.guildwars2.com/file/6106BDCAEE0D2DBA32AE3D5710AE29CC09F7C9DD/156642.png"
    },
    27: {
        "id": 27,
        "name": "Firebrand",
        "profession": "Guardian",
        "elite": True,
        "minor_traits": [1950, 1964, 1973],
        "major_traits": [1950, 1964, 1973, 1977, 1991, 2004],
        "icon": "https://render.guildwars2.com/file/4E1A079D3CBB5571007A6A957CB0E4C9CFA02680/1128516.png"
    },
    18: {
        "id": 18,
        "name": "Berserker",
        "profession": "Warrior",
        "elite": True,
        "minor_traits": [1706, 1707, 1708],
        "major_traits": [1706, 1707, 1708, 1709, 1710, 1711],
        "icon": "https://render.guildwars2.com/file/4E1A079D3CBB5571007A6A957CB0E4C9CFA02680/1128516.png"
    }
}

# Sample trait data
MOCK_TRAITS = {
    642: {
        "id": 642,
        "name": "Zealous Blade",
        "description": "Gain increased strike damage. Gain additional strike damage while wielding a greatsword.",
        "icon": "https://render.guildwars2.com/file/6106BDCAEE0D2DBA32AE3D5710AE29CC09F7C9DD/156642.png",
        "specialization": 6,
        "tier": "Minor",
        "slot": "Minor",
        "facts": [
            {"type": "AttributeAdjust", "value": 120, "target": "ConditionDamage"},
            {"type": "AttributeAdjust", "value": 120, "target": "Power"}
        ]
    },
    653: {
        "id": 653,
        "name": "Zealot's Speed",
        "description": "Gain swiftness when you kill a foe. Gain superspeed when you kill a foe while under the effects of quickness.",
        "icon": "https://render.guildwars2.com/file/6106BDCAEE0D2DBA32AE3D5710AE29CC09F7C9DD/156642.png",
        "specialization": 6,
        "tier": "Major",
        "slot": "Major",
        "facts": [
            {"type": "Buff", "status": "Swiftness", "duration": 5, "description": "Movement speed increased by 33%; stacks duration."},
            {"type": "Buff", "status": "Superspeed", "duration": 2, "description": "Movement speed is greatly increased. Maximum duration: 10s"}
        ]
    }
}

# Sample skill data
MOCK_SKILLS = {
    9093: {
        "id": 9093,
        "name": "Strike",
        "description": "Slash your foe with a powerful attack.",
        "icon": "https://render.guildwars2.com/file/6106BDCAEE0D2DBA32AE3D5710AE29CC09F7C9DD/156642.png",
        "type": "Weapon",
        "weapon_type": "Sword",
        "slot": "Weapon_1",
        "professions": ["Guardian"],
        "facts": [
            {"type": "Damage", "hit_count": 1, "dmg_multiplier": 0.8}
        ]
    },
    9084: {
        "id": 9084,
        "name": "Wrath of Justice",
        "description": "Strike your foe with the power of justice, burning them.",
        "icon": "https://render.guildwars2.com/file/6106BDCAEE0D2DBA32AE3D5710AE29CC09F7C9DD/156642.png",
        "type": "Weapon",
        "weapon_type": "Sword",
        "slot": "Weapon_2",
        "professions": ["Guardian"],
        "facts": [
            {"type": "Damage", "hit_count": 1, "dmg_multiplier": 1.0},
            {"type": "Buff", "status": "Burning", "duration": 2, "description": "Deals damage every second; stacks intensity."}
        ]
    }
}

def get_mock_gw2_response(url: str, params: Dict[str, Any] = None) -> Any:
    """Mock GW2 API responses for testing."""
    if url.endswith("/professions"):
        return list(MOCK_PROFESSIONS.keys())
    
    if url.endswith("/specializations"):
        return list(MOCK_SPECIALIZATIONS.keys())
    
    if url.endswith("/traits"):
        return list(MOCK_TRAITS.keys())
    
    if url.endswith("/skills"):
        return list(MOCK_SKILLS.keys())
    
    if "/professions/" in url:
        prof_id = url.split("/")[-1]
        return MOCK_PROFESSIONS.get(prof_id)
    
    if "/specializations/" in url:
        spec_id = int(url.split("/")[-1])
        return MOCK_SPECIALIZATIONS.get(spec_id)
    
    if "/traits/" in url:
        trait_id = int(url.split("/")[-1])
        return MOCK_TRAITS.get(trait_id)
    
    if "/skills/" in url:
        skill_id = int(url.split("/")[-1])
        return MOCK_SKILLS.get(skill_id)
    
    return None

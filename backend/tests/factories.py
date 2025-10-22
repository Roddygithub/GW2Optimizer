"""
Test factories for creating test objects with proper Pydantic validation.
Provides helper functions to create Build, TeamComposition, and TeamSlot objects.
"""

from datetime import datetime
from uuid import uuid4
from typing import Optional

from app.models.build import Build, GameMode, Profession, Role
from app.models.team import TeamComposition, TeamSlot


def create_test_build(
    name: str = "Test Build",
    profession: Profession = Profession.GUARDIAN,
    game_mode: GameMode = GameMode.ZERG,
    role: Role = Role.SUPPORT,
    **kwargs
) -> Build:
    """
    Create a test Build object with all required Pydantic fields.
    
    Args:
        name: Build name
        profession: GW2 profession
        game_mode: Game mode
        role: Team role
        **kwargs: Additional fields to override defaults
    
    Returns:
        Build object with all required fields
    """
    defaults = {
        'id': str(uuid4()),
        'name': name,
        'profession': profession,
        'game_mode': game_mode,
        'role': role,
        'user_id': str(uuid4()),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
    }
    
    # Merge with provided kwargs
    build_data = {**defaults, **kwargs}
    
    return Build(**build_data)


def create_test_team_composition(
    name: str = "Test Team",
    game_mode: GameMode = GameMode.ZERG,
    team_size: int = 10,
    **kwargs
) -> TeamComposition:
    """
    Create a test TeamComposition object with all required Pydantic fields.
    
    Args:
        name: Team name
        game_mode: Game mode
        team_size: Number of players
        **kwargs: Additional fields to override defaults
    
    Returns:
        TeamComposition object with all required fields
    """
    defaults = {
        'id': str(uuid4()),
        'name': name,
        'game_mode': game_mode,
        'team_size': team_size,
        'user_id': str(uuid4()),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
    }
    
    # Merge with provided kwargs
    team_data = {**defaults, **kwargs}
    
    return TeamComposition(**team_data)


def create_test_team_slot(
    slot_number: int = 1,
    build: Optional[Build] = None,
    priority: int = 1,
    **kwargs
) -> TeamSlot:
    """
    Create a test TeamSlot object with all required Pydantic fields.
    
    Args:
        slot_number: Slot position (1-indexed)
        build: Build object (creates default if None)
        priority: Slot priority
        **kwargs: Additional fields to override defaults
    
    Returns:
        TeamSlot object with all required fields
    """
    if build is None:
        build = create_test_build()
    
    defaults = {
        'id': str(uuid4()),
        'slot_number': slot_number,
        'build': build,
        'priority': priority,
    }
    
    # Merge with provided kwargs
    slot_data = {**defaults, **kwargs}
    
    return TeamSlot(**slot_data)


def create_test_team_with_builds(
    name: str = "Test Team",
    game_mode: GameMode = GameMode.ZERG,
    num_builds: int = 5,
    **kwargs
) -> TeamComposition:
    """
    Create a test TeamComposition with multiple builds.
    
    Args:
        name: Team name
        game_mode: Game mode
        num_builds: Number of builds to create
        **kwargs: Additional fields to override defaults
    
    Returns:
        TeamComposition with slots populated
    """
    team = create_test_team_composition(
        name=name,
        game_mode=game_mode,
        team_size=num_builds,
        **kwargs
    )
    
    # Create diverse builds
    professions = [
        Profession.GUARDIAN,
        Profession.WARRIOR,
        Profession.MESMER,
        Profession.REVENANT,
        Profession.ENGINEER,
    ]
    
    roles = [
        Role.SUPPORT,
        Role.TANK,
        Role.DPS,
        Role.DPS,
        Role.DPS,
    ]
    
    base_user_id = str(uuid4())
    now = datetime.utcnow()
    
    builds = []
    for i in range(num_builds):
        profession = professions[i % len(professions)]
        role = roles[i % len(roles)]
        
        build = create_test_build(
            name=f"{profession.value} {role.value}",
            profession=profession,
            game_mode=game_mode,
            role=role,
            user_id=base_user_id,
            created_at=now,
            updated_at=now,
        )
        builds.append(build)
    
    # Create slots
    team.slots = [
        create_test_team_slot(
            slot_number=i + 1,
            build=build,
            priority=1,
        )
        for i, build in enumerate(builds)
    ]
    
    return team

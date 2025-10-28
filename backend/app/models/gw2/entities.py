"""SQLAlchemy models for Guild Wars 2 domain entities."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class MetadataMixin:
    """Shared metadata fields to support incremental updates."""

    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    etag: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# Association tables ---------------------------------------------------------

profession_weapon_table = Table(
    "gw2_profession_weapons",
    Base.metadata,
    Column(
        "profession_id",
        ForeignKey("gw2_professions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "weapon_id",
        ForeignKey("gw2_weapons.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

weapon_skill_table = Table(
    "gw2_weapon_skills",
    Base.metadata,
    Column("weapon_id", ForeignKey("gw2_weapons.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("gw2_skills.id", ondelete="CASCADE"), primary_key=True),
)

skill_trait_table = Table(
    "gw2_skill_traits",
    Base.metadata,
    Column("skill_id", ForeignKey("gw2_skills.id", ondelete="CASCADE"), primary_key=True),
    Column("trait_id", ForeignKey("gw2_traits.id", ondelete="CASCADE"), primary_key=True),
)

build_skill_table = Table(
    "gw2_build_skills",
    Base.metadata,
    Column("build_id", ForeignKey("gw2_builds.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("gw2_skills.id", ondelete="CASCADE"), primary_key=True),
)

build_trait_table = Table(
    "gw2_build_traits",
    Base.metadata,
    Column("build_id", ForeignKey("gw2_builds.id", ondelete="CASCADE"), primary_key=True),
    Column("trait_id", ForeignKey("gw2_traits.id", ondelete="CASCADE"), primary_key=True),
)

build_item_table = Table(
    "gw2_build_items",
    Base.metadata,
    Column("build_id", ForeignKey("gw2_builds.id", ondelete="CASCADE"), primary_key=True),
    Column("item_id", ForeignKey("gw2_items.id", ondelete="CASCADE"), primary_key=True),
)

build_specialization_table = Table(
    "gw2_build_specializations",
    Base.metadata,
    Column("build_id", ForeignKey("gw2_builds.id", ondelete="CASCADE"), primary_key=True),
    Column("specialization_id", ForeignKey("gw2_specializations.id", ondelete="CASCADE"), primary_key=True),
    Column("order_index", Integer, nullable=False, default=0),
)


# Enumerations ---------------------------------------------------------------


class TraitSlot(Enum):
    """Trait tiers documented by the GW2 API."""

    ADEPT = "adept"
    MASTER = "master"
    GRANDMASTER = "grandmaster"


class SkillType(Enum):
    """Skill categories managed by the GW2 API."""

    WEAPON = "weapon"
    UTILITY = "utility"
    HEAL = "heal"
    ELITE = "elite"


class ItemType(Enum):
    """Subset of item types we persist locally."""

    ARMOR = "armor"
    TRINKET = "trinket"
    WEAPON = "weapon"
    CONSUMABLE = "consumable"


# Entity models --------------------------------------------------------------


class Profession(Base, MetadataMixin):
    """Represents a Guild Wars 2 profession."""

    __tablename__ = "gw2_professions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    primary_attributes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    specializations: Mapped[List["Specialization"]] = relationship(
        "Specialization",
        back_populates="profession",
        cascade="all, delete-orphan",
    )

    skills: Mapped[List["Skill"]] = relationship(
        "Skill",
        back_populates="profession",
    )

    weapons: Mapped[List["Weapon"]] = relationship(
        "Weapon",
        secondary=profession_weapon_table,
        back_populates="usable_by",
    )

    builds: Mapped[List["Build"]] = relationship(
        "Build",
        back_populates="profession",
    )


class Specialization(Base, MetadataMixin):
    """Elite or core specialization unlocked within a profession."""

    __tablename__ = "gw2_specializations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    elite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    minor_traits: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    major_traits: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    profession_id: Mapped[int] = mapped_column(
        ForeignKey("gw2_professions.id", ondelete="CASCADE"), nullable=False
    )

    profession: Mapped[Profession] = relationship("Profession", back_populates="specializations")

    traits: Mapped[List["Trait"]] = relationship(
        "Trait",
        back_populates="specialization",
        cascade="all, delete-orphan",
    )

    skills: Mapped[List["Skill"]] = relationship(
        "Skill",
        back_populates="specialization",
    )

    builds: Mapped[List["Build"]] = relationship(
        "Build",
        secondary=build_specialization_table,
        back_populates="specializations",
    )


class Trait(Base, MetadataMixin):
    """Traits provide passive bonuses and are linked to specializations."""

    __tablename__ = "gw2_traits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    slot: Mapped[TraitSlot] = mapped_column(SAEnum(TraitSlot, name="trait_slot"), nullable=False)
    variables: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    specialization_id: Mapped[int] = mapped_column(
        ForeignKey("gw2_specializations.id", ondelete="CASCADE"), nullable=False
    )

    specialization: Mapped[Specialization] = relationship("Specialization", back_populates="traits")

    skills: Mapped[List["Skill"]] = relationship(
        "Skill",
        secondary=skill_trait_table,
        back_populates="traits",
    )

    builds: Mapped[List["Build"]] = relationship(
        "Build",
        secondary=build_trait_table,
        back_populates="traits",
    )


class Skill(Base, MetadataMixin):
    """Active skills that can belong to professions, weapons, or specializations."""

    __tablename__ = "gw2_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    type: Mapped[SkillType] = mapped_column(SAEnum(SkillType, name="skill_type"), nullable=False)
    weapon_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    profession_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("gw2_professions.id", ondelete="SET NULL"), nullable=True
    )
    specialization_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("gw2_specializations.id", ondelete="SET NULL"), nullable=True
    )

    profession: Mapped[Optional[Profession]] = relationship("Profession", back_populates="skills")
    specialization: Mapped[Optional[Specialization]] = relationship(
        "Specialization", back_populates="skills"
    )

    traits: Mapped[List[Trait]] = relationship(
        "Trait",
        secondary=skill_trait_table,
        back_populates="skills",
    )

    weapons: Mapped[List["Weapon"]] = relationship(
        "Weapon",
        secondary=weapon_skill_table,
        back_populates="skills",
    )

    builds: Mapped[List["Build"]] = relationship(
        "Build",
        secondary=build_skill_table,
        back_populates="skills",
    )


class Weapon(Base, MetadataMixin):
    """Weapons with skill sets and profession usage rules."""

    __tablename__ = "gw2_weapons"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    two_handed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    usable_by: Mapped[List[Profession]] = relationship(
        "Profession",
        secondary=profession_weapon_table,
        back_populates="weapons",
    )

    skills: Mapped[List[Skill]] = relationship(
        "Skill",
        secondary=weapon_skill_table,
        back_populates="weapons",
    )


class Item(Base, MetadataMixin):
    """Persisted GW2 items (gear, consumables, etc.)."""

    __tablename__ = "gw2_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    type: Mapped[ItemType] = mapped_column(SAEnum(ItemType, name="item_type"), nullable=False)
    rarity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stats_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    builds: Mapped[List["Build"]] = relationship(
        "Build",
        secondary=build_item_table,
        back_populates="items",
    )


class Build(Base, MetadataMixin):
    """Structured build definition referencing skills, traits, and gear."""

    __tablename__ = "gw2_builds"
    __table_args__ = (UniqueConstraint("name", "profession_id", name="uq_build_name_profession"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    profession_id: Mapped[int] = mapped_column(
        ForeignKey("gw2_professions.id", ondelete="RESTRICT"), nullable=False
    )

    specialization_order: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    profession: Mapped[Profession] = relationship("Profession", back_populates="builds")

    specializations: Mapped[List[Specialization]] = relationship(
        "Specialization",
        secondary=build_specialization_table,
        back_populates="builds",
        order_by=build_specialization_table.c.order_index,
    )

    skills: Mapped[List[Skill]] = relationship(
        "Skill",
        secondary=build_skill_table,
        back_populates="builds",
    )

    traits: Mapped[List[Trait]] = relationship(
        "Trait",
        secondary=build_trait_table,
        back_populates="builds",
    )

    items: Mapped[List[Item]] = relationship(
        "Item",
        secondary=build_item_table,
        back_populates="builds",
    )

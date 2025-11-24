"""Saved build persistence model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base_class import Base
from app.db.types import GUID


class SavedBuildDB(Base):
    """SQLAlchemy model storing user-saved builds.

    This is a lightweight bookmark-style representation of a build, capturing
    the essential metadata and AI evaluation without storing the full build
    structure.
    """

    __tablename__ = "saved_builds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    chat_code = Column(String(255), nullable=True, index=True)
    profession = Column(String(50), nullable=True)
    specialization = Column(String(100), nullable=True)
    game_mode = Column(String(50), nullable=True)
    synergy_score = Column(String(8), nullable=True)
    source_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_saved_builds_user_created_at", "user_id", "created_at"),
    )

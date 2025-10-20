"""Database configuration and session management."""

from app.db.base_class import Base
from app.db.init_db import init_db


# Lazy imports to avoid circular dependencies and engine creation during import
def get_db():
    from app.db.base import get_db as _get_db

    return _get_db


def get_engine():
    from app.db.base import engine

    return engine


def get_session_local():
    from app.db.base import SessionLocal

    return SessionLocal


__all__ = ["Base", "get_db", "init_db", "get_engine", "get_session_local"]

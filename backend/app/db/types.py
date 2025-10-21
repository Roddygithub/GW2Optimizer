"""
Custom SQLAlchemy types for cross-database compatibility.

This module provides custom types that work across different database engines,
particularly for handling UUIDs in both PostgreSQL and SQLite.
"""

from sqlalchemy import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
import uuid


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's native UUID type when available, otherwise uses
    CHAR(36) to store UUID as a string.

    This ensures compatibility with both PostgreSQL (production) and
    SQLite (tests/development).

    Usage:
        class MyModel(Base):
            id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """
        Load the appropriate type implementation for the dialect.

        - PostgreSQL: Use native UUID type
        - SQLite/Others: Use CHAR(36) for string representation
        """
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQL_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        """
        Convert Python UUID to database value.

        - PostgreSQL: Store as UUID
        - SQLite: Store as string (36 chars with hyphens)
        """
        if value is None:
            return value

        if dialect.name == "postgresql":
            return value  # PostgreSQL handles UUID natively
        else:
            # Convert to string for SQLite
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        """
        Convert database value to Python UUID.

        - PostgreSQL: Already UUID
        - SQLite: Parse string to UUID
        """
        if value is None:
            return value

        if dialect.name == "postgresql":
            return value  # Already UUID from PostgreSQL
        else:
            # Parse string to UUID for SQLite
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


__all__ = ["GUID"]

"""
Tests for custom database types (GUID cross-database compatibility).
"""

import pytest
import uuid
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base
from app.db.types import GUID

Base = declarative_base()


class TestModel(Base):
    """Test model using GUID type."""

    __tablename__ = "test_guid"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(50))


@pytest.fixture
def sqlite_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def sqlite_session(sqlite_engine):
    """Create a session for SQLite testing."""
    Session = sessionmaker(bind=sqlite_engine)
    session = Session()
    yield session
    session.close()


def test_guid_creation_sqlite(sqlite_session):
    """Test GUID creation and storage in SQLite."""
    # Create a test record with UUID
    test_id = uuid.uuid4()
    record = TestModel(id=test_id, name="test_record")

    sqlite_session.add(record)
    sqlite_session.commit()

    # Retrieve the record
    retrieved = sqlite_session.query(TestModel).filter(TestModel.id == test_id).first()

    assert retrieved is not None
    assert retrieved.id == test_id
    assert isinstance(retrieved.id, uuid.UUID)
    assert retrieved.name == "test_record"


def test_guid_default_generation_sqlite(sqlite_session):
    """Test GUID auto-generation with default=uuid.uuid4."""
    # Create record without specifying ID
    record = TestModel(name="auto_generated")

    sqlite_session.add(record)
    sqlite_session.commit()

    # Verify UUID was generated
    assert record.id is not None
    assert isinstance(record.id, uuid.UUID)


def test_guid_query_by_uuid_sqlite(sqlite_session):
    """Test querying by UUID in SQLite."""
    # Create multiple records
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()

    record1 = TestModel(id=id1, name="record1")
    record2 = TestModel(id=id2, name="record2")

    sqlite_session.add_all([record1, record2])
    sqlite_session.commit()

    # Query by specific UUID
    found = sqlite_session.query(TestModel).filter(TestModel.id == id1).first()

    assert found is not None
    assert found.id == id1
    assert found.name == "record1"


def test_guid_null_handling_sqlite(sqlite_session):
    """Test GUID handling of NULL values."""
    # GUID column is primary key, so NULL should not be allowed
    # But we can test the type's NULL handling logic
    from app.db.types import GUID

    guid_type = GUID()

    # Test bind parameter with None
    result = guid_type.process_bind_param(None, sqlite_session.bind.dialect)
    assert result is None

    # Test result value with None
    result = guid_type.process_result_value(None, sqlite_session.bind.dialect)
    assert result is None


def test_guid_string_conversion_sqlite(sqlite_session):
    """Test GUID conversion to/from string in SQLite."""
    from app.db.types import GUID

    guid_type = GUID()
    test_uuid = uuid.uuid4()

    # Test bind parameter conversion (UUID -> String for SQLite)
    bound_value = guid_type.process_bind_param(test_uuid, sqlite_session.bind.dialect)
    assert isinstance(bound_value, str)
    assert bound_value == str(test_uuid)

    # Test result value conversion (String -> UUID for SQLite)
    result_value = guid_type.process_result_value(bound_value, sqlite_session.bind.dialect)
    assert isinstance(result_value, uuid.UUID)
    assert result_value == test_uuid


def test_guid_multiple_records_sqlite(sqlite_session):
    """Test multiple records with different UUIDs."""
    # Create 5 records
    records = [TestModel(name=f"record_{i}") for i in range(5)]

    sqlite_session.add_all(records)
    sqlite_session.commit()

    # Verify all have unique UUIDs
    all_records = sqlite_session.query(TestModel).all()
    assert len(all_records) == 5

    uuids = [record.id for record in all_records]
    assert len(set(uuids)) == 5  # All UUIDs are unique
    assert all(isinstance(uid, uuid.UUID) for uid in uuids)


def test_guid_update_sqlite(sqlite_session):
    """Test updating a record with GUID primary key."""
    # Create record
    test_id = uuid.uuid4()
    record = TestModel(id=test_id, name="original")

    sqlite_session.add(record)
    sqlite_session.commit()

    # Update record
    record.name = "updated"
    sqlite_session.commit()

    # Verify update
    retrieved = sqlite_session.query(TestModel).filter(TestModel.id == test_id).first()
    assert retrieved.name == "updated"
    assert retrieved.id == test_id


def test_guid_delete_sqlite(sqlite_session):
    """Test deleting a record with GUID primary key."""
    # Create record
    test_id = uuid.uuid4()
    record = TestModel(id=test_id, name="to_delete")

    sqlite_session.add(record)
    sqlite_session.commit()

    # Delete record
    sqlite_session.delete(record)
    sqlite_session.commit()

    # Verify deletion
    retrieved = sqlite_session.query(TestModel).filter(TestModel.id == test_id).first()
    assert retrieved is None

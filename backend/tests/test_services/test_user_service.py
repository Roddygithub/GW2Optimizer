import pytest
from httpx import AsyncClient
from fastapi import Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserDB, LoginHistory
from app.services.user_service import UserService, get_password_hash


@pytest.mark.asyncio
async def test_get_and_create_user(db_session: AsyncSession) -> None:
    service = UserService(db_session)

    # Create user
    hashed = get_password_hash("Password123!")
    user = await service.create_user("svc@example.com", "svcuser", hashed)

    assert user.id is not None
    assert user.email == "svc@example.com"
    assert user.username == "svcuser"

    # Fetch by id / email / username
    by_id = await service.get_by_id(str(user.id))
    by_email = await service.get_by_email("svc@example.com")
    by_username = await service.get_by_username("svcuser")
    missing = await service.get_by_email("missing@example.com")

    assert by_id is not None and by_id.id == user.id
    assert by_email is not None and by_email.id == user.id
    assert by_username is not None and by_username.id == user.id
    assert missing is None


@pytest.mark.asyncio
async def test_authenticate_user_success_and_fail(db_session: AsyncSession) -> None:
    service = UserService(db_session)

    hashed = get_password_hash("ValidPassword!123")
    user = UserDB(
        email="auth@example.com",
        username="authuser",
        hashed_password=hashed,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    ok = await service.authenticate_user("auth@example.com", "ValidPassword!123")
    bad_password = await service.authenticate_user("auth@example.com", "WrongPassword")
    unknown = await service.authenticate_user("unknown@example.com", "ValidPassword!123")

    assert ok is not None and ok.email == "auth@example.com"
    assert bad_password is None
    assert unknown is None


@pytest.mark.asyncio
async def test_handle_failed_login_and_lockout(db_session: AsyncSession) -> None:
    service = UserService(db_session)

    hashed = get_password_hash("Password123!")
    user = UserDB(
        email="lock@example.com",
        username="lockuser",
        hashed_password=hashed,
        is_active=True,
        is_verified=True,
        failed_login_attempts=0,
    )
    db_session.add(user)
    await db_session.commit()

    # Simuler 5 échecs (MAX_LOGIN_ATTEMPTS par défaut)
    for _ in range(5):
        await service.handle_failed_login("lock@example.com")

    await db_session.refresh(user)
    assert user.failed_login_attempts >= 5
    # En mode test avec ENFORCE_ACCOUNT_LOCKS_IN_TESTS=True, le compte doit être verrouillé
    assert user.is_active is False
    assert user.locked_until is not None


@pytest.mark.asyncio
async def test_reset_failed_login_attempts(db_session: AsyncSession) -> None:
    service = UserService(db_session)

    hashed = get_password_hash("Password123!")
    user = UserDB(
        email="reset@example.com",
        username="resetuser",
        hashed_password=hashed,
        is_active=True,
        is_verified=True,
        failed_login_attempts=3,
    )
    db_session.add(user)
    await db_session.commit()

    await service.reset_failed_login_attempts("reset@example.com")
    await db_session.refresh(user)

    assert user.failed_login_attempts == 0


@pytest.mark.asyncio
async def test_update_user_and_preferences(db_session: AsyncSession) -> None:
    service = UserService(db_session)

    hashed = get_password_hash("Password123!")
    user = UserDB(
        email="profile@example.com",
        username="profileuser",
        hashed_password=hashed,
        is_active=True,
        is_verified=True,
        full_name=None,
        bio=None,
        preferences={"theme": "light"},
    )
    db_session.add(user)
    await db_session.commit()

    # Update profile fields
    updated = await service.update_user(
        user,
        {"full_name": "Profile User", "bio": "My bio"},
    )
    assert updated.full_name == "Profile User"
    assert updated.bio == "My bio"

    # Merge preferences
    updated_prefs = await service.update_preferences(user, {"language": "fr"})
    assert updated_prefs.preferences == {"theme": "light", "language": "fr"}


@pytest.mark.asyncio
async def test_verify_user_email_idempotent(db_session: AsyncSession) -> None:
    service = UserService(db_session)

    hashed = get_password_hash("Password123!")
    user = UserDB(
        email="verify@example.com",
        username="verifyuser",
        hashed_password=hashed,
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    await db_session.commit()

    # Premier appel : passe de False à True
    await service.verify_user_email(user)
    await db_session.refresh(user)
    assert user.is_verified is True

    # Second appel : doit rester True sans erreur
    await service.verify_user_email(user)
    await db_session.refresh(user)
    assert user.is_verified is True


@pytest.mark.asyncio
async def test_login_history_logging_and_retrieval(db_session: AsyncSession) -> None:
    service = UserService(db_session)

    hashed = get_password_hash("Password123!")
    user = UserDB(
        email="history@example.com",
        username="historyuser",
        hashed_password=hashed,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Construire une requête FastAPI minimale
    scope = {
        "type": "http",
        "client": ("127.0.0.1", 12345),
        "headers": [(b"user-agent", b"pytest-agent")],
    }
    request = Request(scope)

    await service.log_login_history(user, request)
    history = await service.get_login_history(user, limit=5)

    assert len(history) == 1
    record = history[0]
    assert isinstance(record, LoginHistory)
    assert record.user_id == user.id
    assert record.ip_address == "127.0.0.1"
    assert "pytest-agent" in (record.user_agent or "")


@pytest.mark.asyncio
async def test_get_login_history_empty(db_session: AsyncSession) -> None:
    service = UserService(db_session)

    hashed = get_password_hash("Password123!")
    user = UserDB(
        email="nohistory@example.com",
        username="nohistoryuser",
        hashed_password=hashed,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    history = await service.get_login_history(user, limit=5)
    assert history == []

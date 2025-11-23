import jwt
import pytest
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing_roundtrip() -> None:
    password = "secret_password"

    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_create_access_token_includes_sub_exp_and_jti() -> None:
    subject = "test@example.com"

    token = create_access_token(subject=subject)

    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert decoded["sub"] == subject
    assert "exp" in decoded
    assert "jti" in decoded and isinstance(decoded["jti"], str) and decoded["jti"]


def test_create_access_token_with_custom_expiration() -> None:
    subject = "test@example.com"
    expires_delta = timedelta(minutes=10)

    token = create_access_token(subject=subject, expires_delta=expires_delta)

    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    # L'expiration doit être dans le futur (par rapport à maintenant)
    now_ts = int(datetime.utcnow().timestamp())
    assert decoded["exp"] > now_ts

    # Et ne doit pas être démesurément loin (<= +20 minutes pour tolérer la latence)
    assert decoded["exp"] <= now_ts + 20 * 60

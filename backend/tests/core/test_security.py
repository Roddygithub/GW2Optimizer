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

    # Capture le temps avant la création du token
    before_creation = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
    token = create_access_token(subject=subject, expires_delta=expires_delta)
    after_creation = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    # L'expiration doit être dans le futur (par rapport à maintenant)
    assert decoded["exp"] > after_creation

    # Vérifie que l'expiration est proche de ce qui est attendu (10 minutes)
    # avec une tolérance de 2 minutes pour la latence du système
    expected_min = before_creation + 8 * 60  # 8 minutes minimum
    expected_max = before_creation + 12 * 60  # 12 minutes maximum
    
    assert decoded["exp"] >= expected_min, f"Token expires too early: {decoded['exp']} vs expected min {expected_min}"
    assert decoded["exp"] <= expected_max, f"Token expires too late: {decoded['exp']} vs expected max {expected_max}"

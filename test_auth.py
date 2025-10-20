import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.core.security import get_password_hash

client = TestClient(app)


@pytest.fixture(scope="module")
def test_user_password():
    return "testpass"


@pytest.fixture(scope="module")
def test_user_hashed_password(test_user_password):
    return get_password_hash(test_user_password)


def test_register_user_success():
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "password": "newpassword123"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data


def test_login_success_and_cookie_set(test_user_password, test_user_hashed_password):
    with patch("app.api.auth.verify_password", return_value=True), \
         patch("app.api.auth.get_password_hash", return_value=test_user_hashed_password):
        
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": test_user_password},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
        assert "access_token_cookie" in response.cookies


def test_login_failure_wrong_password():
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_access_protected_route_with_valid_token(test_user_password, test_user_hashed_password):
    with patch("app.api.auth.verify_password", return_value=True), \
         patch("app.api.auth.get_password_hash", return_value=test_user_hashed_password):
        
        login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": test_user_password},
        )
        token = login_response.json()["access_token"]

        protected_response = client.get(
            "/api/v1/auth/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert protected_response.status_code == status.HTTP_200_OK
        assert protected_response.json() == {"message": "Hello, testuser! You are in a protected area."}


def test_access_protected_route_with_invalid_token():
    response = client.get(
        "/api/v1/auth/protected",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_access_protected_route_without_token():
    response = client.get("/api/v1/auth/protected")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_rate_limiting():
    # Mock verify_password to always fail to simulate failed attempts
    with patch("app.api.auth.verify_password", return_value=False):
        # The limit is 5 per minute. We try 6 times.
        for i in range(6):
            response = client.post(
                "/api/v1/auth/token",
                data={"username": "testuser", "password": "wrongpassword"},
            )
            if i < 5:
                assert response.status_code == status.HTTP_401_UNAUTHORIZED
            else:
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
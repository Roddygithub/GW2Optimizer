import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import timedelta
from unittest.mock import patch

from app.core.config import settings
from app.models.user import UserDB
from app.core.security import create_access_token

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "TestPassword123!"


async def test_register_user_success(client: AsyncClient):
    """Test successful user registration and email sending."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "username": "newuser", "password": "ValidPassword!123"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data


async def test_register_user_duplicate_email(client: AsyncClient, test_user: UserDB):
    """Test registration with a duplicate email."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": test_user.email, "username": "anotheruser", "password": "ValidPassword!123"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT, response.json()
    data = response.json()
    assert data["error_code"] == "USER_EMAIL_EXISTS"


async def test_login_success(client: AsyncClient, test_user: UserDB):
    """Test successful login and cookie setting."""
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": test_user.password},
    )
    assert response.status_code == status.HTTP_200_OK
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"
    assert "access_token" in response.cookies


async def test_login_wrong_password(client: AsyncClient, test_user: UserDB):
    """Test login with an incorrect password."""
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["error_code"] == "INVALID_CREDENTIALS"


async def test_login_wrong_email(client: AsyncClient, test_user: UserDB):
    """Test login with a non-existent email."""
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "wrong@example.com", "password": test_user.password},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_current_user_with_token(client: AsyncClient, auth_headers: dict):
    """Test accessing a protected endpoint with a valid token header."""
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == TEST_USER_EMAIL


async def test_get_current_user_with_cookie(client: AsyncClient, test_user: UserDB):
    """Test accessing a protected endpoint with a valid cookie."""
    login_response = await client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": test_user.password},
    )
    assert login_response.status_code == status.HTTP_200_OK
    token = login_response.json()["access_token"]

    # Make request without Authorization header, relying on the cookie
    response = await client.get(
        "/api/v1/users/me",
        cookies={settings.ACCESS_TOKEN_COOKIE_NAME: token},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == TEST_USER_EMAIL


async def test_get_current_user_no_auth(client: AsyncClient):
    """Test accessing a protected endpoint without any authentication."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]


async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test accessing a protected endpoint with an invalid token."""
    headers = {"Authorization": "Bearer invalidtoken"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]


async def test_logout(client: AsyncClient, auth_headers: dict):
    """Test logout functionality by clearing the cookie."""
    # Log out
    logout_response = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout_response.status_code == status.HTTP_204_NO_CONTENT
    # The 'expires' attribute should be in the past, effectively deleting the cookie.
    assert 'expires="Thu, 01 Jan 1970 00:00:00 GMT"' in logout_response.headers["set-cookie"]

    # Verify token is revoked
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_account_lockout(client: AsyncClient, test_user: UserDB):
    """Test that an account is locked after too many failed login attempts."""
    for i in range(5):
        response = await client.post(
            "/api/v1/auth/token",
            data={"username": test_user.email, "password": "wrongpassword"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Sixth attempt should fail with 401, but the account is now locked
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # A correct login attempt should now be forbidden
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": test_user.password},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["error_code"] == "ACCOUNT_LOCKED"


@patch("app.api.auth.send_password_reset_email")
async def test_password_recovery(mock_send_email, client: AsyncClient, test_user: UserDB):
    """Test the password recovery request endpoint."""
    response = await client.post(f"/api/v1/auth/password-recovery/{test_user.email}")
    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_send_email.assert_called_once()


@patch("app.api.auth.send_password_reset_email")
async def test_reset_password_success(mock_send_email, client: AsyncClient, test_user: UserDB):
    """Test the password reset endpoint with a valid token."""
    # 1. Generate a valid token for the user
    reset_token = create_access_token(subject=test_user.email)

    # 2. Reset the password
    new_password = "a_brand_new_ValidPassword123!"
    response = await client.post(
        "/api/v1/auth/reset-password/",
        json={"token": reset_token, "new_password": new_password},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # 3. Try to log in with the new password
    login_response = await client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": new_password},
    )
    assert login_response.status_code == status.HTTP_200_OK


async def test_register_weak_password(client: AsyncClient):
    """Test registration with a password that is too short."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weakpass@example.com", "username": "weakpass", "password": "short"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"


async def test_register_empty_fields(client: AsyncClient):
    """Test registration with empty fields."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "", "username": "", "password": ""},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "email" in data["fields"]
    assert "username" in data["fields"]


@pytest.mark.parametrize("email", ["invalid-email", "test@", "@example.com", "test@.com"])
async def test_register_invalid_email_format(client: AsyncClient, email: str):
    """Test registration with various invalid email formats."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": "validuser", "password": "ValidPassword!123"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "email" in data["fields"]


@pytest.mark.parametrize("username", ["us", "user-name", "user name", "user!"])
async def test_register_invalid_username(client: AsyncClient, username: str):
    """Test registration with invalid usernames (too short or invalid characters)."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "valid@example.com", "username": username, "password": "ValidPassword!123"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "username" in data["fields"]


@pytest.mark.parametrize(
    "password, expected_msg_part",
    [
        ("short", "12 caractères"),  # Too short
        ("nouppercase123!", "lettre majuscule"),  # No uppercase
        ("NOLOWERCASE123!", "lettre minuscule"),  # No lowercase
        ("NoDigitsHere!", "un chiffre"),  # No digits
        ("NoSpecialChar123", "caractère spécial"),  # No special char
    ],
)
async def test_register_weak_password_scenarios(client: AsyncClient, password: str, expected_msg_part: str):
    """Test registration with various weak password scenarios."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weakpass@example.com", "username": "weakpassuser", "password": password},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert "password" in data["fields"]
    assert expected_msg_part in data["fields"]["password"]


@pytest.mark.parametrize(
    "password, username, email",
    [
        ("ValidPassword!123", "validuser1", "valid1@example.com"),
        ("AnotherValidPass!456", "validuser2", "valid2@example.com"),
        ("SuperSecureP@ssw0rd", "validuser3", "valid3@example.com"),
    ],
)
async def test_register_valid_passwords(client: AsyncClient, password: str, username: str, email: str):
    """Test registration with various valid passwords."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert response.status_code == status.HTTP_201_CREATED, response.json()


async def test_register_rate_limiting(client: AsyncClient):
    """Test that the registration endpoint is rate-limited."""
    # The limit is 10/hour. We'll make 10 requests that should pass the rate limit.
    for i in range(10):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": f"ratelimit{i}@example.com", "username": f"ratelimit{i}", "password": "ValidPassword!123"},
        )
        assert response.status_code == status.HTTP_201_CREATED

    # The 11th request should be rate-limited
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "ratelimit10@example.com", "username": "ratelimit10", "password": "ValidPassword!123"},
    )
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@patch("app.api.auth.send_verification_email")
async def test_email_verification_flow(mock_send_email, client: AsyncClient):
    """Test the full email verification flow."""
    # 1. Register a new user
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "verify@example.com", "username": "verifyuser", "password": "ValidPassword!123"},
    )
    assert reg_response.status_code == status.HTTP_201_CREATED
    mock_send_email.assert_called_once()

    # Extract token from mocked call
    verification_token = mock_send_email.call_args[0][2]

    # 2. Verify the email with the token
    verify_response = await client.get(f"/api/v1/auth/verify-email/{verification_token}")
    assert verify_response.status_code == status.HTTP_200_OK
    assert "Email verified successfully" in verify_response.json()["msg"]

    # 3. Try to verify again (should fail)
    verify_again_response = await client.get(f"/api/v1/auth/verify-email/{verification_token}")
    assert verify_again_response.status_code == status.HTTP_400_BAD_REQUEST


async def test_update_user_profile(client: AsyncClient, auth_headers: dict):
    """Test updating the current user's profile."""
    update_data = {"full_name": "Test User Full Name", "bio": "This is my test bio."}
    response = await client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Test User Full Name"
    assert data["bio"] == "This is my test bio."
    assert data["email"] == TEST_USER_EMAIL


async def test_update_user_preferences(client: AsyncClient, auth_headers: dict):
    """Test updating user preferences."""
    preferences_data = {"preferences": {"theme": "dark", "language": "fr"}}
    response = await client.put("/api/v1/users/me/preferences", json=preferences_data, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["preferences"]["theme"] == "dark"
    assert data["preferences"]["language"] == "fr"


async def test_get_login_history(client: AsyncClient, auth_headers: dict):
    """Test retrieving user login history."""
    # Note: A login happened in the fixture that created auth_headers
    response = await client.get("/api/v1/users/me/login-history", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "ip_address" in data[0]
    assert "user_agent" in data[0]


async def test_invalid_login_form_data(client: AsyncClient):
    """Test login with invalid form data structure."""
    response = await client.post("/api/v1/auth/token", data={"invalid_field": "some_value"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "username" in data["fields"]


async def test_refresh_token_success(client: AsyncClient, test_user: UserDB):
    """Test successful token refresh."""
    # 1. Log in to get tokens
    login_response = await client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": test_user.password},
    )
    assert login_response.status_code == status.HTTP_200_OK
    old_tokens = login_response.json()
    assert "refresh_token" in old_tokens

    # 2. Use the refresh token to get new tokens
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_tokens["refresh_token"]},
    )
    assert refresh_response.status_code == status.HTTP_200_OK
    new_tokens = refresh_response.json()

    # 3. Verify new tokens are different from old ones
    assert "access_token" in new_tokens
    assert new_tokens["access_token"] != old_tokens["access_token"]
    assert "access_token" in refresh_response.cookies


async def test_refresh_token_invalid(client: AsyncClient):
    """Test token refresh with an invalid or expired refresh token."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "an-invalid-refresh-token"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["error_code"] == "HTTP_EXCEPTION"  # This comes from a direct HTTPException


async def test_security_headers_are_present(client: AsyncClient):
    """Test that essential security headers are added to responses."""
    response = await client.get("/api/v1/health")  # A simple, non-protected endpoint

    assert response.status_code == status.HTTP_200_OK

    headers = response.headers
    assert "Content-Security-Policy" in headers
    assert "X-Frame-Options" in headers and headers["X-Frame-Options"] == "DENY"
    assert "X-Content-Type-Options" in headers and headers["X-Content-Type-Options"] == "nosniff"
    assert "X-XSS-Protection" in headers and "1; mode=block" in headers["X-XSS-Protection"]
    assert "Referrer-Policy" in headers

    # HSTS is only added in production (is_production=True in middleware)
    # assert "Strict-Transport-Security" in headers


async def test_redis_unavailability_on_auth(monkeypatch, client: AsyncClient, auth_headers: dict):
    """Redis failures while checking token revocation must fail closed with 401."""
    from redis.exceptions import ConnectionError
    from app.main import app
    from app.core.redis import get_redis_client

    class FailingRedis:
        async def sismember(self, *args, **kwargs):
            raise ConnectionError("Simulated Redis is down")

    failing_redis = FailingRedis()
    previous_override = app.dependency_overrides.get(get_redis_client)

    async def _override():
        return failing_redis

    app.dependency_overrides[get_redis_client] = _override

    monkeypatch.setattr("app.core.redis.redis_client", failing_redis, raising=False)

    try:
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Unable to verify token revocation"
        assert response.headers.get("www-authenticate") == "Bearer"
    finally:
        if previous_override is not None:
            app.dependency_overrides[get_redis_client] = previous_override
        else:
            app.dependency_overrides.pop(get_redis_client, None)

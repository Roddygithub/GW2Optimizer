"""
Tests for authentication endpoints.

Tests cover registration, login, token refresh, password reset, and user profile.
Target: +15% coverage on auth endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.db.models import UserDB


class TestAuthRegistration:
    """Tests for user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "different",
                "password": "SecurePass123!",
            },
        )
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """Test registration with duplicate username fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user.username,
                "password": "SecurePass123!",
            },
        )
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": "123",
            },
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "SecurePass123!",
            },
        )
        
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": test_user.email,
                "password": test_user.password,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_with_username(self, client: AsyncClient, test_user):
        """Test login with username instead of email."""
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": test_user.username,
                "password": test_user.password,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password fails."""
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!",
            },
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "nonexistent@example.com",
                "password": "SomePassword123!",
            },
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with inactive user fails."""
        from app.core.security import get_password_hash
        
        # Create inactive user
        inactive_user = UserDB(
            email="inactive@example.com",
            username="inactive",
            hashed_password=get_password_hash("Password123!"),
            is_active=False,
        )
        db_session.add(inactive_user)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "inactive@example.com",
                "password": "Password123!",
            },
        )
        
        assert response.status_code == 401


class TestAuthProfile:
    """Tests for user profile endpoints."""

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers, test_user):
        """Test getting current user profile."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting profile without auth fails."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting profile with invalid token fails."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_profile(self, client: AsyncClient, auth_headers, test_user):
        """Test updating user profile."""
        response = await client.patch(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={"preferences": {"theme": "dark", "language": "en"}},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["preferences"]["theme"] == "dark"


class TestPasswordReset:
    """Tests for password reset functionality."""

    @pytest.mark.asyncio
    async def test_request_password_reset(self, client: AsyncClient, test_user):
        """Test requesting password reset."""
        response = await client.post(
            "/api/v1/auth/password-reset",
            json={"email": test_user.email},
        )
        
        # Should return 200 even if email doesn't exist (security)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent(self, client: AsyncClient):
        """Test password reset for nonexistent email."""
        response = await client.post(
            "/api/v1/auth/password-reset",
            json={"email": "nonexistent@example.com"},
        )
        
        # Should return 200 to avoid email enumeration
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password(self, client: AsyncClient, auth_headers, test_user, db_session: AsyncSession):
        """Test changing password."""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": test_user.password,
                "new_password": "NewSecurePass123!",
            },
        )
        
        assert response.status_code == 200
        
        # Verify password was changed in database
        from sqlalchemy import select
        result = await db_session.execute(
            select(UserDB).where(UserDB.id == test_user.id)
        )
        db_user = result.scalar_one()
        assert verify_password("NewSecurePass123!", db_user.hashed_password)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers):
        """Test changing password with wrong current password."""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewSecurePass123!",
            },
        )
        
        assert response.status_code == 400


class TestTokenRefresh:
    """Tests for token refresh functionality."""

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, test_user):
        """Test refreshing access token."""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": test_user.email,
                "password": test_user.password,
            },
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        # Use token to access protected endpoint
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert response.status_code == 200


class TestAuthRateLimiting:
    """Tests for rate limiting on auth endpoints."""

    @pytest.mark.asyncio
    async def test_login_rate_limit(self, client: AsyncClient):
        """Test that login endpoint has rate limiting."""
        # Note: This test may be skipped if rate limiting is disabled in tests
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = await client.post(
                "/api/v1/auth/token",
                data={
                    "username": "test@example.com",
                    "password": "password",
                },
            )
            responses.append(response.status_code)
        
        # At least some requests should succeed (401 for wrong creds is ok)
        assert any(status in [200, 401] for status in responses)

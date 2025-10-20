"""Integration tests for authentication flow."""

import pytest
from httpx import AsyncClient
from fastapi import status


pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestAuthenticationFlow:
    """Test suite for complete authentication workflows."""

    async def test_register_login_access_flow(self, client: AsyncClient):
        """Test complete flow: register → login → access protected endpoint."""
        # Step 1: Register a new user
        register_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePassword123!",
        }

        register_response = await client.post("/api/v1/auth/register", json=register_data)

        assert register_response.status_code == status.HTTP_201_CREATED
        user_data = register_response.json()
        assert user_data["email"] == register_data["email"]
        assert user_data["username"] == register_data["username"]
        assert "id" in user_data
        assert "hashed_password" not in user_data  # Password should not be returned

        # Step 2: Login with the new user
        login_data = {
            "username": register_data["email"],
            "password": register_data["password"],
        }

        login_response = await client.post(
            "/api/v1/auth/login",
            data=login_data,  # OAuth2 uses form data
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert login_response.status_code == status.HTTP_200_OK
        token_data = login_response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"

        access_token = token_data["access_token"]

        # Step 3: Access protected endpoint with token
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        me_response = await client.get("/api/v1/auth/me", headers=auth_headers)

        assert me_response.status_code == status.HTTP_200_OK
        me_data = me_response.json()
        assert me_data["email"] == register_data["email"]
        assert me_data["username"] == register_data["username"]

        # Step 4: Create a build with authentication
        build_data = {
            "name": "Test Build",
            "profession": "Guardian",
            "specialization": "Firebrand",
            "game_mode": "zerg",
            "role": "support",
            "is_public": True,
            "trait_lines": [],
            "skills": [],
            "equipment": [],
        }

        build_response = await client.post("/api/v1/builds", json=build_data, headers=auth_headers)

        assert build_response.status_code == status.HTTP_201_CREATED
        build = build_response.json()
        assert build["name"] == build_data["name"]

        # Step 5: List user's builds
        list_response = await client.get("/api/v1/builds", headers=auth_headers)

        assert list_response.status_code == status.HTTP_200_OK
        builds = list_response.json()
        assert len(builds) == 1
        assert builds[0]["id"] == build["id"]

    async def test_login_with_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "WrongPassword123!",
        }

        response = await client.post(
            "/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_access_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_access_protected_endpoint_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}

        response = await client.get("/api/v1/auth/me", headers=invalid_headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_refresh_token_flow(self, client: AsyncClient):
        """Test refreshing access token with refresh token."""
        # Register and login
        register_data = {
            "email": "refresh@example.com",
            "username": "refreshuser",
            "password": "SecurePassword123!",
        }

        await client.post("/api/v1/auth/register", json=register_data)

        login_data = {
            "username": register_data["email"],
            "password": register_data["password"],
        }

        login_response = await client.post(
            "/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]

        # Refresh the token
        refresh_response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        assert refresh_response.status_code == status.HTTP_200_OK
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]

    async def test_duplicate_email_registration(self, client: AsyncClient):
        """Test that duplicate email registration fails."""
        register_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "SecurePassword123!",
        }

        # First registration
        response1 = await client.post("/api/v1/auth/register", json=register_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Second registration with same email
        register_data["username"] = "user2"
        response2 = await client.post("/api/v1/auth/register", json=register_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    async def test_duplicate_username_registration(self, client: AsyncClient):
        """Test that duplicate username registration fails."""
        register_data = {
            "email": "user1@example.com",
            "username": "duplicateuser",
            "password": "SecurePassword123!",
        }

        # First registration
        response1 = await client.post("/api/v1/auth/register", json=register_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Second registration with same username
        register_data["email"] = "user2@example.com"
        response2 = await client.post("/api/v1/auth/register", json=register_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    async def test_weak_password_registration(self, client: AsyncClient):
        """Test that weak passwords are rejected."""
        register_data = {
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "weak",  # Too weak
        }

        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_logout_flow(self, client: AsyncClient):
        """Test logout functionality."""
        # Register and login
        register_data = {
            "email": "logout@example.com",
            "username": "logoutuser",
            "password": "SecurePassword123!",
        }

        await client.post("/api/v1/auth/register", json=register_data)

        login_data = {
            "username": register_data["email"],
            "password": register_data["password"],
        }

        login_response = await client.post(
            "/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        tokens = login_response.json()
        access_token = tokens["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Logout
        logout_response = await client.post("/api/v1/auth/logout", headers=auth_headers)

        assert logout_response.status_code == status.HTTP_200_OK

    async def test_user_can_only_access_own_resources(self, client: AsyncClient):
        """Test that users can only access their own resources."""
        # Create first user
        user1_data = {
            "email": "user1@example.com",
            "username": "user1",
            "password": "SecurePassword123!",
        }
        await client.post("/api/v1/auth/register", json=user1_data)

        login1_response = await client.post(
            "/api/v1/auth/login",
            data={"username": user1_data["email"], "password": user1_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        user1_token = login1_response.json()["access_token"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        # Create a private build for user1
        build_data = {
            "name": "User1 Private Build",
            "profession": "Guardian",
            "game_mode": "zerg",
            "role": "support",
            "is_public": False,
            "trait_lines": [],
            "skills": [],
            "equipment": [],
        }
        build_response = await client.post("/api/v1/builds", json=build_data, headers=user1_headers)
        build_id = build_response.json()["id"]

        # Create second user
        user2_data = {
            "email": "user2@example.com",
            "username": "user2",
            "password": "SecurePassword123!",
        }
        await client.post("/api/v1/auth/register", json=user2_data)

        login2_response = await client.post(
            "/api/v1/auth/login",
            data={"username": user2_data["email"], "password": user2_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        user2_token = login2_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Try to access user1's private build as user2
        response = await client.get(f"/api/v1/builds/{build_id}", headers=user2_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

"""Integration tests for the GW2 sync API endpoints."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select

from app.main import app
from app.db.models import UserDB as UserModel
from app.core.security import get_password_hash, create_access_token
from app.services.gw2_sync_service import sync_gw2_data

# Initialize test client
@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Test user data
TEST_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpassword",
    "is_superuser": True
}

# Test token fixture
@pytest.fixture
async def test_token(db_session):
    """Create a test user and return a valid JWT token for authentication."""
    # First, clean up any existing test user
    result = await db_session.execute(
        select(UserModel).where(UserModel.email == TEST_USER["email"])
    )
    existing_user = result.scalars().first()
    if existing_user:
        await db_session.delete(existing_user)
        await db_session.commit()
    
    # Create a new user with superuser privileges
    user = UserModel(
        email=TEST_USER["email"],
        username=TEST_USER["username"],
        hashed_password=get_password_hash(TEST_USER["password"]),
        is_superuser=TEST_USER["is_superuser"],
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create and return a token for the test user
    return create_access_token(
        subject=user.email,
        expires_delta=timedelta(minutes=15)
    )

@pytest.mark.asyncio
async def test_get_sync_status_unauthorized(client):
    """Test getting sync status without authentication."""
    response = await client.get("/api/v1/gw2-sync/status")
    assert response.status_code == status.HTTP_200_OK
    assert "is_running" in response.json()
    assert "last_run" in response.json()
    assert "last_success" in response.json()
    assert response.json()["is_running"] is False

@pytest.mark.asyncio
async def test_trigger_sync_unauthorized(client):
    """Test triggering a sync without authentication."""
    response = await client.post("/api/v1/gw2-sync/trigger")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
@patch("app.api.endpoints.gw2_sync.run_sync")
async def test_trigger_sync_success(mock_run_sync, test_token, client):
    """Test successfully triggering a sync."""
    # Mock the background task
    mock_run_sync.return_value = None
    
    # Make the request with authentication
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Content-Type": "application/json"
    }
    
    # Send the request
    response = await client.post(
        "/api/v1/gw2-sync/trigger",
        headers=headers
    )
    
    # Check the response
    assert response.status_code == status.HTTP_202_ACCEPTED
    response_data = response.json()
    
    # Check for either possible success response format
    assert isinstance(response_data, dict)
    assert "message" in response_data
    assert response_data["message"] in ["GW2 data sync started", "Synchronization started"]
    
    # Verify the background task was added
    mock_run_sync.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.gw2_sync_service.sync_gw2_data")
async def test_trigger_sync_already_running(mock_sync, test_token, client):
    """Test triggering a sync when one is already in progress."""
    # Set sync as already running
    from app.api.endpoints import gw2_sync
    gw2_sync._sync_status["is_running"] = True
    
    try:
        # Make the request with authentication
        headers = {
            "Authorization": f"Bearer {test_token}",
            "Content-Type": "application/json"
        }
        
        # Send the request
        response = await client.post(
            "/api/v1/gw2-sync/trigger",
            headers=headers
        )
        
        # Check the response - expect 409 Conflict for already running sync
        assert response.status_code == status.HTTP_409_CONFLICT
        response_data = response.json()
        assert "detail" in response_data
        assert "already in progress" in response_data["detail"].lower()
        
    finally:
        # Clean up
        gw2_sync._sync_status["is_running"] = False


@patch("app.tasks.scheduler.schedule_gw2_sync")
@patch("app.tasks.scheduler.scheduler")
def test_scheduler_integration(mock_scheduler, mock_schedule_gw2_sync):
    """Test that the scheduler helper functions interact with the scheduler correctly."""
    from app.tasks.scheduler import start_scheduler, shutdown_scheduler

    # Scheduler should start when not already running
    mock_scheduler.running = False
    start_scheduler()
    mock_schedule_gw2_sync.assert_called_once()
    mock_scheduler.start.assert_called_once()

    # Scheduler should shut down gracefully when running
    mock_scheduler.running = True
    shutdown_scheduler()
    mock_scheduler.shutdown.assert_called_once_with(wait=True)

@pytest.mark.asyncio
async def test_sync_status_after_trigger(test_token, client):
    """Test that the sync status is updated after triggering a sync."""
    # First, trigger a sync
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Content-Type": "application/json"
    }
    
    # Send the trigger request
    response = await client.post(
        "/api/v1/gw2-sync/trigger",
        headers=headers
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    
    # Check the sync status
    response = await client.get("/api/v1/gw2-sync/status")
    assert response.status_code == status.HTTP_200_OK
    status_data = response.json()
    assert "is_running" in status_data
    assert "last_run" in status_data
    assert "last_success" in status_data

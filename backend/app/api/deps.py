"""Dependency injection for API endpoints."""
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import async_session
from app.db.models import UserDB as User
from app.schemas.token import TokenPayload

# Set USER_SERVICE_AVAILABLE to True since we're using lazy imports
USER_SERVICE_AVAILABLE = True

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


async def get_db() -> Generator:
    """Get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


def get_user_service(db: AsyncSession = Depends(get_db)):
    """Get an instance of UserService with the provided database session."""
    from app.services.user_service import UserService
    return UserService(db)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """Get current active user from token.
    
    Args:
        db: Database session
        token: OAuth2 token
        
    Returns:
        User: Current user if active
        
    Raises:
        HTTPException: If user is not found or inactive
    """
    print("\n=== get_current_user ===")
    print(f"Token: {token}")
    
    if not USER_SERVICE_AVAILABLE:
        error_msg = "User service not available"
        print(f"ERROR: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=error_msg
        )
    
    try:
        print("Decoding token...")
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        print(f"Decoded payload: {payload}")
        
        token_data = TokenPayload(**payload)
        print(f"Token data: {token_data}")
        print(f"Token subject (user ID): {getattr(token_data, 'sub', 'N/A')}")
    except (jwt.JWTError, ValidationError) as e:
        error_msg = f"Could not validate credentials: {str(e)}"
        print(f"ERROR: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg,
        ) from e
    
    # Get user from database
    user_id = token_data.sub
    print(f"Fetching user with ID: {user_id} (type: {type(user_id)})")
    
    try:
        # Handle both string and integer user IDs
        user = None
        if user_id is not None:
            # Try to find the user by ID directly first
            user = await db.get(User, user_id)
            
            # If not found and user_id is a string, try to find by email as a fallback
            if user is None and isinstance(user_id, str):
                print(f"User not found by ID, trying to find by email: {user_id}")
                from sqlalchemy import select
                result = await db.execute(select(User).where(User.email == user_id))
                user = result.scalars().first()
                
                # If still not found, try to convert to int if possible
                if user is None and user_id.isdigit():
                    print(f"User not found by email, trying with integer ID: {int(user_id)}")
                    user = await db.get(User, int(user_id))
        
        if user is None:
            error_msg = f"User with ID/email {user_id} not found"
            print(f"ERROR: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        # Print user details for debugging
        print(f"Found user: ID={user.id}, Email={user.email}")
        print(f"User is_superuser: {getattr(user, 'is_superuser', 'N/A')}")
        print(f"User is_active: {getattr(user, 'is_active', 'N/A')}")
        print(f"User is_verified: {getattr(user, 'is_verified', 'N/A')}")
        
        # Ensure user is active
        if not getattr(user, 'is_active', False):
            error_msg = f"User {user.id} is inactive"
            print(f"ERROR: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        print("User is active, returning user object")
        return user
        
    except Exception as e:
        error_msg = f"Error fetching user: {str(e)}"
        print(f"ERROR: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Check if the current user is a superuser.
    
    Args:
        current_user: Current user
        
    Returns:
        User: Current user if superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    # Debug information
    print("\n=== get_current_active_superuser ===")
    print(f"User ID: {getattr(current_user, 'id', 'N/A')}")
    print(f"Email: {getattr(current_user, 'email', 'N/A')}")
    print(f"Is superuser: {getattr(current_user, 'is_superuser', 'N/A')}")
    print(f"Is active: {getattr(current_user, 'is_active', 'N/A')}")
    print(f"Is verified: {getattr(current_user, 'is_verified', 'N/A')}")
    
    if not getattr(current_user, 'is_superuser', False):
        print("ERROR: User is not a superuser")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    
    print("User is a superuser, access granted")
    return current_user

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_current_user,
    verify_password,
    get_password_hash,
)
# Replace with your actual schemas and services
from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str

class UserCreate(BaseModel):
    username: str
    password: str


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. The password will be hashed.",
    responses={
        409: {"description": "Username already registered"},
    },
)
async def register_user(user_in: UserCreate):
    """
    - **username**: The username for the new account.
    - **password**: The password for the new account.
    """
    # In a real app, you would check if the user exists in the DB
    # and then create them.
    hashed_password = get_password_hash(user_in.password)
    print(f"User '{user_in.username}' registered with hash: {hashed_password}")
    # For demonstration, we return a mock user
    return User(id=1, username=user_in.username)


@router.post(
    "/token",
    summary="Get an access token",
    description="Authenticate and receive an access token. The token is returned in the response body and as an `HttpOnly` cookie.",
    responses={
        401: {"description": "Incorrect username or password"},
        429: {"description": "Too many requests"},
    },
)
@limiter.limit("5/minute")
async def login_for_access_token(
    response: Response, form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate with username and password.
    """
    # In a real app, you would fetch the user from the DB
    # user = await user_service.get_by_username(form_data.username)
    # For demonstration, we use a mock user and password
    is_valid_user = (
        form_data.username == "testuser"
        and verify_password(form_data.password, get_password_hash("testpass"))
    )

    if not is_valid_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=form_data.username, expires_delta=access_token_expires
    )

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=True,
        samesite="strict",
        secure=not settings.DEBUG,  # Use secure cookies in production
        max_age=int(access_token_expires.total_seconds()),
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/refresh",
    summary="Refresh an access token",
    description="This is a placeholder for a refresh token endpoint.",
    responses={501: {"description": "Not implemented"}},
)
async def refresh_token():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get(
    "/me",
    response_model=User,
    summary="Get current user",
    description="Get the profile of the currently authenticated user.",
    responses={401: {"description": "Not authenticated"}},
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Requires a valid access token.
    """
    # In a real app, current_user would be a full user model object
    # For demonstration, we create a User object from the mock user
    return User(id=1, username=current_user.id)


@router.post(
    "/logout",
    summary="Logout",
    description="Clears the authentication cookie.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(response: Response):
    """
    Invalidates the session by removing the access token cookie.
    """
    response.delete_cookie(key=settings.ACCESS_TOKEN_COOKIE_NAME)
    return


@router.get(
    "/protected",
    summary="A protected endpoint",
    description="An example endpoint that requires authentication.",
)
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.id}! You are in a protected area."}
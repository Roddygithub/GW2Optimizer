"""Authentication service."""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.models.token import Token, TokenData
from app.models.user import UserCreate, UserDB, UserLogin

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication and user management."""

    def __init__(self):
        """Initialize auth service."""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.

        Args:
            data: Data to encode in token
            expires_delta: Token expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)

        to_encode.update({"exp": expire, "type": "access", "iat": datetime.utcnow(), "sub": str(data.get("sub", ""))})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """
        Create JWT refresh token.

        Args:
            data: Data to encode in token

        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire)
        to_encode.update({"exp": expire, "type": "refresh", "iat": datetime.utcnow(), "sub": str(data.get("sub", ""))})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[TokenData]:
        """
        Decode and verify JWT token.

        Args:
            token: JWT token to decode

        Returns:
            TokenData if valid, None otherwise

        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            if not token:
                logger.warning("Empty token provided")
                return None

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_aud": False},  # Désactive la vérification de l'audience si non utilisée
            )

            user_id = payload.get("sub")
            email = payload.get("email")

            if not user_id:
                logger.warning("Token is missing 'sub' claim")
                return None

            logger.debug(f"Successfully decoded token for user_id: {user_id}")
            return TokenData(user_id=str(user_id), email=email)

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error decoding token: {str(e)}", exc_info=True)
            return None

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[UserDB]:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(select(UserDB).where(UserDB.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[UserDB]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID (UUID string)

        Returns:
            User if found, None otherwise
        """
        try:
            logger.debug(f"Looking up user by ID: {user_id} (type: {type(user_id)})")
            result = await db.execute(select(UserDB).where(UserDB.id == user_id))
            user = result.scalar_one_or_none()

            if user is None:
                logger.warning(f"User not found with ID: {user_id}")
            else:
                logger.debug(f"Found user: {user.email} (ID: {user.id})")

            return user

        except Exception as e:
            logger.error(f"Error in get_user_by_id for user_id {user_id}: {str(e)}", exc_info=True)
            raise

    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[UserDB]:
        """
        Get user by username.

        Args:
            db: Database session
            username: Username

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(select(UserDB).where(UserDB.username == username))
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, user_create: UserCreate) -> UserDB:
        """
        Create a new user with hashed password.

        Args:
            db: Database session
            user_create: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If user creation fails (email/username already exists, etc.)
            Exception: For other unexpected errors during user creation
        """
        logger.info(f"Starting user creation for email: {user_create.email}, username: {user_create.username}")

        try:
            # Check if user with email already exists
            logger.debug(f"Checking if email {user_create.email} already exists...")
            existing_user = await self.get_user_by_email(db, user_create.email)
            if existing_user:
                error_msg = f"Email {user_create.email} already exists"
                logger.warning(f"User creation failed: {error_msg}")
                raise ValueError(error_msg)

            # Check if username is already taken
            logger.debug(f"Checking if username {user_create.username} is available...")
            existing_username = await self.get_user_by_username(db, user_create.username)
            if existing_username:
                error_msg = f"Username {user_create.username} already taken"
                logger.warning(f"User creation failed: {error_msg}")
                raise ValueError(error_msg)

            # Hash the password
            logger.debug("Hashing password...")
            hashed_password = self.get_password_hash(user_create.password)

            # Get current timestamp
            now = datetime.utcnow()

            # Create user object with all required fields
            logger.debug("Creating user object...")
            db_user = UserDB(
                email=user_create.email,
                username=user_create.username,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=False,
                created_at=now,
                updated_at=now,
            )

            # Save to database
            logger.debug("Saving user to database...")
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)

            logger.info(f"✅ User created successfully: {db_user.email} (ID: {db_user.id})")
            return db_user

        except ValueError as ve:
            # Re-raise validation errors
            await db.rollback()
            logger.error(f"User creation validation error: {ve}")
            raise ValueError(str(ve)) from ve

        except Exception as e:
            # Handle unexpected errors
            await db.rollback()
            logger.error(f"Unexpected error creating user: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create user: {str(e)}") from e

    async def authenticate_user(self, db: AsyncSession, user_login: UserLogin) -> Optional[UserDB]:
        """
        Authenticate a user with either email or username.

        Args:
            db: Database session
            user_login: User login data (email or username + password)

        Returns:
            User if authentication successful, None otherwise

        Raises:
            ValueError: If neither email nor username is provided
        """
        logger.info(f"Starting authentication for user: {user_login.email or user_login.username}")

        if not user_login.email and not user_login.username:
            logger.error("Authentication failed: Neither email nor username provided")
            raise ValueError("Either email or username must be provided")

        try:
            user = None

            # Try to find user by email if provided
            if user_login.email:
                try:
                    user = await self.get_user_by_email(db, user_login.email)
                    logger.debug(f"User lookup by email {user_login.email}: {'found' if user else 'not found'}")
                except Exception as e:
                    logger.error(f"Error looking up user by email {user_login.email}: {str(e)}", exc_info=True)

            # If not found by email and username is provided, try by username
            if not user and user_login.username:
                try:
                    user = await self.get_user_by_username(db, user_login.username)
                    logger.debug(f"User lookup by username {user_login.username}: {'found' if user else 'not found'}")
                except Exception as e:
                    logger.error(f"Error looking up user by username {user_login.username}: {str(e)}", exc_info=True)

            # If user not found, log and return None
            if not user:
                logger.warning(
                    f"Authentication failed: User not found with email={user_login.email}, username={user_login.username}"
                )
                return None

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Authentication failed: User {user.email} is inactive")
                return None

            # Verify password
            if not user_login.password:
                logger.warning(f"Authentication failed: No password provided for user {user.email}")
                return None

            if not user.hashed_password:
                logger.warning(f"Authentication failed: No password set for user {user.email}")
                return None

            if not self.verify_password(user_login.password, user.hashed_password):
                logger.warning(f"Authentication failed: Invalid password for user {user.email}")
                return None

            logger.info(f"✅ User authenticated successfully: {user.email} (ID: {user.id})")
            return user

        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}", exc_info=True)
            return None

    async def create_tokens(self, user: UserDB) -> Token:
        """
        Create access and refresh tokens for user.

        Args:
            user: User to create tokens for

        Returns:
            Token pair

        Raises:
            Exception: If token creation fails
        """
        try:
            logger.debug(f"Creating tokens for user: {user.email} (ID: {user.id})")

            # Create access token
            access_token = self.create_access_token(data={"sub": str(user.id), "email": user.email})

            # Create refresh token
            refresh_token = self.create_refresh_token(data={"sub": str(user.id), "email": user.email})

            logger.debug(f"Tokens created successfully for user: {user.email}")

            return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

        except Exception as e:
            logger.error(f"❌ Failed to create tokens for user {user.email}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create tokens: {str(e)}")

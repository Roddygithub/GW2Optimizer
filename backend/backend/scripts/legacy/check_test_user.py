import asyncio
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import UserDB as User


async def check_test_user():
    async for db in get_db():
        # Récupérer l'utilisateur test
        result = await db.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalars().first()

        if user:
            print(f"User found: {user.email}")
            print(f"Is active: {user.is_active}")
            print(f"Hashed password: {user.hashed_password}")
            print(f"Is verified: {user.is_verified}")
            print(f"Is superuser: {user.is_superuser}")
            print(f"Failed login attempts: {user.failed_login_attempts}")
            print(f"Locked until: {user.locked_until}")
        else:
            print("Test user not found")


# Exécuter la fonction asynchrone
if __name__ == "__main__":
    asyncio.run(check_test_user())

import asyncio
from app.db.session import get_db
from app.services.user_service import UserService
from app.db.models import UserDB as User
from app.core.security import get_password_hash


async def create_test_user():
    async for db in get_db():
        service = UserService(db)

        # Vérifier si l'utilisateur existe déjà
        test_user = await service.get_by_email("test@example.com")

        if test_user:
            print("Test user already exists:", test_user.email)
            return

        # Créer un nouvel utilisateur
        hashed_password = get_password_hash("TestPass123!")
        new_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        print("Test user created successfully:", new_user.email)


# Exécuter la fonction asynchrone
if __name__ == "__main__":
    asyncio.run(create_test_user())

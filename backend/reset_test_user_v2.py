import asyncio
import bcrypt
from sqlalchemy import select, delete
from app.db.session import get_db
from app.db.models import UserDB as User

async def reset_test_user():
    async for db in get_db():
        # Supprimer l'utilisateur existant
        await db.execute(delete(User).where(User.email == "test@example.com"))
        await db.commit()
        
        # Créer un hash bcrypt directement
        password = "Test123!"
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        new_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            is_verified=True
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        print(f"✅ Test user reset successfully: {new_user.email}")
        print(f"   Password: Test123!")
        print(f"   Is active: {new_user.is_active}")
        print(f"   Hash: {hashed_password[:20]}...")

if __name__ == "__main__":
    asyncio.run(reset_test_user())

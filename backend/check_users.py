import asyncio
from sqlalchemy import text
from app.db.session import get_db
from app.services.user_service import UserService

async def check_users():
    async for db in get_db():
        service = UserService(db)
        users = (await db.execute(text('SELECT email FROM users'))).fetchall()
        print("Users in database:", users)
        
        # Vérifier l'utilisateur test
        test_user = await service.get_by_email("test@example.com")
        if test_user:
            print("Test user found:", test_user.email)
            print("Is active:", test_user.is_active)
        else:
            print("Test user not found")

# Exécuter la fonction asynchrone
if __name__ == "__main__":
    asyncio.run(check_users())

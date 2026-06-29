import asyncio
import os
from uuid import UUID
from app.database import crud
from app.database.models import init_db

async def test():
    await init_db()
    user_id = UUID(os.getenv("TEST_USER_ID", "00000000-0000-0000-0000-000000000001"))
    config = await crud.get_automation_config(user_id)
    print(f"Configuração carregada: {config}")
    print(f"Chave descriptografada: {config.get('gemini_api_key')}")

if __name__ == "__main__":
    asyncio.run(test())

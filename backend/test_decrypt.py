import asyncio
from app.database import crud
from app.database.models import init_db

async def test():
    await init_db()
    config = await crud.get_automation_config()
    print(f"Configuração carregada: {config}")
    print(f"Chave descriptografada: {config.get('gemini_api_key')}")

if __name__ == "__main__":
    asyncio.run(test())

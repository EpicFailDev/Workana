import asyncio
from app.database import crud
from app.database.models import init_db

async def test_persistence():
    await init_db()
    
    # 1. Salvar uma chave de teste
    test_key = "SK-TEST-12345"
    print(f"Salvando chave: {test_key}")
    config = await crud.get_automation_config()
    config['gemini_api_key'] = test_key
    await crud.save_automation_config(config)
    
    # 2. Simular reload (limpar cache/reler do banco)
    # CRUD já faz isso a cada chamada com async_session()
    config_after = await crud.get_automation_config()
    print(f"Chave após reload: {config_after.get('gemini_api_key')}")
    
    if config_after.get('gemini_api_key') == test_key:
        print("✅ Persistência verificada com sucesso!")
    else:
        print("❌ Falha na persistência!")

if __name__ == "__main__":
    asyncio.run(test_persistence())

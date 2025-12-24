
import httpx
import asyncio

async def confirm_login():
    async with httpx.AsyncClient() as client:
        try:
            print("Enviando requisição de confirmação de login...")
            response = await client.post("http://localhost:8000/api/automation/confirm-manual-login", timeout=30.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Erro ao conectar com API: {e}")

if __name__ == "__main__":
    asyncio.run(confirm_login())

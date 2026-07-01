import asyncio
from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_conn(url, name):
    print(f"Testing {name}...")
    try:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            print(f"-> {name} SUCCESS: {res.scalar()}")
            return True
    except Exception as e:
        print(f"-> {name} FAILED: {e}")
        return False

async def main():
    database_url = dotenv_values("backend/.env")["DATABASE_URL"]
    await test_conn(database_url, "configured database")

if __name__ == "__main__":
    asyncio.run(main())

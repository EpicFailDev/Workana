import asyncio
from app.database.models import async_session
from sqlalchemy import text

async def check():
    async with async_session() as s:
        res = await s.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema IN ('public', 'private')"))
        print("TABLES BY SCHEMA:", res.fetchall())
        try:
            res2 = await s.execute(text("SELECT slug, version, name FROM private.system_proposal_templates"))
            print("SYSTEM TEMPLATES:", res2.fetchall())
        except Exception as e:
            print("ERROR QUERYING SYSTEM TEMPLATES:", e)

asyncio.run(check())

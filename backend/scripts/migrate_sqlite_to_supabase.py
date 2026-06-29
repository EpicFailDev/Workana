"""
Script opcional para migrar dados do SQLite (workana.db) para o Supabase Postgres.
Associa todas as entradas ao primeiro usuário encontrado em auth.users no Supabase.
"""
import asyncio
import os
import sys
import json
from datetime import datetime
import sqlite3
import asyncpg

# Adiciona o diretório backend ao path para conseguir importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import settings

SQLITE_DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workana.db"))

TABLES = [
    "credentials",
    "saved_filters",
    "proposal_templates",
    "proposal_history",
    "automation_config",
    "projects",
    "activity_logs",
    "daily_statistics",
    "blacklisted_clients",
    "profile_metrics",
    "profile_config"
]

async def get_supabase_user_id(conn) -> str:
    """Busca o primeiro user_id de auth.users no Postgres."""
    row = await conn.fetchrow("SELECT id, email FROM auth.users LIMIT 1;")
    if not row:
        print("⚠️ ERRO: Nenhum usuário encontrado em auth.users no Supabase.")
        print("Crie um usuário no frontend ou dashboard do Supabase primeiro antes de rodar a migração.")
        sys.exit(1)
    print(f"✅ Associando registros ao usuário do Supabase: {row['email']} ({row['id']})")
    return str(row['id'])

def adapt_json(value):
    """Adapta dados JSON do SQLite para o Postgres JSONB."""
    if not value:
        return None
    try:
        # Se já for uma string contendo JSON, tenta carregar e salvar como JSON/dict
        if isinstance(value, str):
            return json.loads(value)
        return value
    except Exception:
        return value

async def migrate():
    if not os.path.exists(SQLITE_DB):
        print(f"❌ Banco de dados SQLite não encontrado em {SQLITE_DB}")
        return

    # Extrai a connection string do asyncpg
    # Se a connection string começar com postgresql+asyncpg://, substitui por postgresql:// para o asyncpg nativo
    pg_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgres+asyncpg://", "postgresql://")
    if pg_url.startswith("sqlite"):
        print("❌ DATABASE_URL no .env aponta para SQLite. Mude para a connection string do Supabase para migrar.")
        return

    print("🔌 Conectando ao Supabase Postgres...")
    pg_conn = await asyncpg.connect(pg_url)
    
    # Obter o user_id do primeiro usuário do Supabase
    user_id = await get_supabase_user_id(pg_conn)

    print("🔌 Conectando ao SQLite...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    try:
        for table in TABLES:
            print(f"📦 Migrando tabela: {table}...")
            
            # Verificar se a tabela existe no SQLite
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
            if not cursor.fetchone():
                print(f"  ⚠️ Tabela {table} não existe no SQLite, pulando.")
                continue

            # Obter linhas do SQLite
            cursor.execute(f"SELECT * FROM {table};")
            rows = cursor.fetchall()
            if not rows:
                print(f"  ℹ️ Tabela {table} vazia no SQLite, pulando.")
                continue

            print(f"  ⬇️ Lendo {len(rows)} linhas...")

            # Limpar dados existentes na tabela do Supabase (para evitar conflitos)
            await pg_conn.execute(f"DELETE FROM public.{table} WHERE user_id = $1;", user_id)

            # Inserir no Postgres
            inserted_count = 0
            for row in rows:
                row_dict = dict(row)
                
                # Remover chave primária antiga para deixar o Postgres auto-incrementar
                if "id" in row_dict:
                    del row_dict["id"]

                # Injetar user_id
                row_dict["user_id"] = user_id

                # Tratar campos de data e JSON
                for col, val in row_dict.items():
                    # Tratar strings contendo JSON
                    if col in ["filters_json", "skills", "details"]:
                        row_dict[col] = adapt_json(val)
                    # Converter strings de data do SQLite para datetime
                    elif isinstance(val, str) and ("_at" in col or col == "date" or col == "sent_at" or col == "found_at" or col == "scraped_at"):
                        try:
                            # Tenta parsear formato padrão datetime do SQLite
                            row_dict[col] = datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")
                        except ValueError:
                            try:
                                row_dict[col] = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                pass

                # Se a tabela for credentials, automation_config ou profile_config, elas são UNIQUE(user_id)
                # Garantimos que apenas o último registro seja mantido se houver múltiplos no SQLite
                if table in ["credentials", "automation_config", "profile_config"] and inserted_count >= 1:
                    print(f"  ⚠️ Ignorando duplicata para tabela singleton {table} (mantendo apenas o primeiro registro)")
                    continue

                # Preparar query de inserção
                columns = list(row_dict.keys())
                placeholders = [f"${i+1}" for i in range(len(columns))]
                query = f"INSERT INTO public.{table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)});"
                
                try:
                    await pg_conn.execute(query, *row_dict.values())
                    inserted_count += 1
                except Exception as e:
                    # Se der erro de unique constraint em projetos, apenas loga e pula
                    if "uix_user_id_workana_id" in str(e) or "uix_user_id_date" in str(e):
                        continue
                    print(f"  ❌ Erro ao inserir linha na tabela {table}: {e}")

            print(f"  🚀 Inseridas {inserted_count} de {len(rows)} linhas na tabela {table}.")

        print("🎉 Migração concluída com sucesso!")
        
    finally:
        sqlite_conn.close()
        await pg_conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

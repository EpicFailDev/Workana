import sqlite3
import os

db_path = 'workana.db'

if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE automation_config ADD COLUMN user_full_name TEXT")
        conn.commit()
        print("✅ Coluna 'user_full_name' adicionada com sucesso à tabela 'automation_config'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ A coluna 'user_full_name' já existe.")
        else:
            print(f"❌ Erro ao adicionar coluna: {e}")
    finally:
        conn.close()

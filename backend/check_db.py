import sqlite3
import os

db_path = 'workana.db'

if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM automation_config")
        rows = cursor.fetchall()
        print(f"Encontrados {len(rows)} registros na tabela 'automation_config':")
        for row in rows:
            print(row)
    except sqlite3.OperationalError as e:
        print(f"❌ Erro ao ler tabela: {e}")
    finally:
        conn.close()
